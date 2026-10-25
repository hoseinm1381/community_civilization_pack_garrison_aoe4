"""Lossless face-attribute FBX partition for the large Castle landmark meshes.

Blender's editable .blend stays the source of the four visual states.  This
post-export step divides only the healthy superstructure into four native-size
mesh nodes, preserving every oriented face, normal, UV and material assignment.
It is deterministic and refuses to update handoffs unless a binary round trip
and expanded face multiset checks pass.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import struct
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from common import ART, EXPORT, OUT, RECIPES, ROOT, guarded, sha, write


@dataclass
class Node:
    name: bytes
    props: list[bytes]
    children: list["Node"]
    sentinel: bool


class FBX:
    def __init__(self, raw: bytes):
        assert raw.startswith(b'Kaydara FBX Binary  \x00\x1a\x00')
        self.prefix=raw[:27]
        self.version=struct.unpack_from('<I',raw,23)[0]
        self.fmt='<QQQB' if self.version>=7500 else '<IIIB'
        self.header=struct.calcsize(self.fmt)
        self.nodes=[];position=27
        while position<len(raw)-self.header:
            if raw[position:position+self.header]==bytes(self.header):break
            node,position=self._read(raw,position)
            self.nodes.append(node)
        self.suffix=raw[position:]
        assert self.serialize()==raw,'Original binary FBX must round-trip byte-for-byte'

    def _read(self, raw: bytes, at: int):
        end,count,property_bytes,size=struct.unpack_from(self.fmt,raw,at)
        assert end>at+self.header and end<=len(raw)
        position=at+self.header
        name=raw[position:position+size];position+=size
        begin=position;properties=[]
        for _ in range(count):
            start=position;kind=chr(raw[position]);position+=1
            if kind in 'YILFDC':position+={'Y':2,'I':4,'L':8,'F':4,'D':8,'C':1}[kind]
            elif kind in 'SR':
                length=struct.unpack_from('<I',raw,position)[0]
                position+=4+length
            elif kind in 'bcilfd':
                _,_,packed=struct.unpack_from('<III',raw,position)
                position+=12+packed
            else:raise ValueError(('FBX property type',kind,name))
            properties.append(raw[start:position])
        assert position-begin==property_bytes,(name,position-begin,property_bytes)
        children=[];sentinel=False
        while position<end:
            if raw[position:position+self.header]==bytes(self.header):
                position+=self.header;sentinel=True;break
            child,position=self._read(raw,position)
            children.append(child)
        assert position==end,(name,position,end)
        return Node(name,properties,children,sentinel),end

    def _pack(self,node:Node,at:int):
        properties=b''.join(node.props)
        body=bytearray(node.name+properties)
        for child in node.children:
            packed=self._pack(child,at+self.header+len(body))
            body.extend(packed)
        if node.sentinel:body.extend(bytes(self.header))
        end=at+self.header+len(body)
        return struct.pack(self.fmt,end,len(node.props),len(properties),len(node.name))+body

    def serialize(self):
        result=bytearray(self.prefix)
        for node in self.nodes:result.extend(self._pack(node,len(result)))
        result.extend(self.suffix)
        return bytes(result)

    def top(self,name:str):return next(node for node in self.nodes if node.name==name.encode())


def child(node:Node,name:str):return next(item for item in node.children if item.name==name.encode())
def children(node:Node,name:str):return [item for item in node.children if item.name==name.encode()]


def integer(raw:bytes):
    assert raw[:1] in (b'I',b'L')
    return struct.unpack('<i' if raw[:1]==b'I' else '<q',raw[1:])[0]


def text(raw:bytes):
    assert raw[:1]==b'S'
    length=struct.unpack_from('<I',raw,1)[0]
    return raw[5:5+length]


def p_int(value:int,kind=b'L'):
    return kind+struct.pack('<q' if kind==b'L' else '<i',value)


def p_text(value:bytes):return b'S'+struct.pack('<I',len(value))+value


def array(node:Node,kind:str):
    value=node.props[0]
    assert value[:1]==kind.encode()
    length,encoding,packed=struct.unpack_from('<III',value,1)
    body=value[13:13+packed]
    raw=zlib.decompress(body) if encoding else body
    assert len(raw)==length*{'i':4,'d':8}[kind]
    return raw,length


def set_array(node:Node,kind:str,raw:bytes):
    itemsize={'i':4,'d':8}[kind]
    assert len(raw)%itemsize==0
    packed=zlib.compress(raw,6)
    node.props[0]=kind.encode()+struct.pack('<III',len(raw)//itemsize,1,len(packed))+packed


def ints(raw:bytes):return struct.unpack('<%di'%(len(raw)//4),raw)
def pack_ints(values):return struct.pack('<%di'%len(values),*values)


def geometry_arrays(geo:Node):
    material_layer=child(geo,'LayerElementMaterial')
    assert text(child(material_layer,'MappingInformationType').props[0])==b'AllSame'
    assert text(child(material_layer,'ReferenceInformationType').props[0])==b'IndexToDirect'
    assert ints(array(child(material_layer,'Materials'),'i')[0])==(0,)
    coordinates,nverts=array(child(geo,'Vertices'),'d')
    polygons,nloops=array(child(geo,'PolygonVertexIndex'),'i')
    normal_layer=child(geo,'LayerElementNormal')
    uv_layer=child(geo,'LayerElementUV')
    normals,nnormal=array(child(normal_layer,'Normals'),'d')
    normal_indices,_=array(child(normal_layer,'NormalsIndex'),'i')
    uv,nuv=array(child(uv_layer,'UV'),'d')
    uv_indices,_=array(child(uv_layer,'UVIndex'),'i')
    assert nverts%3==nnormal%3==nuv%2==0
    assert len(normal_indices)==len(uv_indices)==4*nloops
    indices=ints(polygons)
    normal_index=ints(normal_indices)
    uv_index=ints(uv_indices)
    faces=[];face=[]
    for loop_id,value in enumerate(indices):
        vertex=-value-1 if value<0 else value
        assert 0<=vertex<nverts//3
        face.append((vertex,loop_id))
        if value<0:
            assert len(face)>=3
            faces.append(face);face=[]
    assert not face and sum(map(len,faces))==nloops
    assert all(0<=x<nnormal//3 for x in normal_index)
    assert all(0<=x<nuv//2 for x in uv_index)
    return {'coordinates':coordinates,'normals':normals,'uv':uv,
            'faces':faces,'normal_index':normal_index,'uv_index':uv_index}


def face_multiset(geometries:list[Node]):
    result=Counter();triangles=0
    for geo in geometries:
        data=geometry_arrays(geo)
        for face in data['faces']:
            oriented=bytearray()
            for vertex,loop in face:
                normal=data['normal_index'][loop]
                uv=data['uv_index'][loop]
                oriented.extend(data['coordinates'][24*vertex:24*(vertex+1)])
                oriented.extend(data['normals'][24*normal:24*(normal+1)])
                oriented.extend(data['uv'][16*uv:16*(uv+1)])
            result[hashlib.sha256(oriented).digest()]+=1
            triangles+=len(face)-2
    return result,triangles


def expanded_uv(geo:Node,layer_number:int):
    layer=next(item for item in children(geo,'LayerElementUV')
               if integer(item.props[0])==layer_number)
    raw,count=array(child(layer,'UV'),'d')
    indices=ints(array(child(layer,'UVIndex'),'i')[0])
    assert count%2==0
    assert all(0<=index<count//2 for index in indices)
    return [raw[16*index:16*(index+1)] for index in indices]


def duplicate_uv1(geo:Node):
    uv_layers=children(geo,'LayerElementUV')
    assert len(uv_layers)==1 and integer(uv_layers[0].props[0])==0
    uv0=uv_layers[0]
    uv1=copy.deepcopy(uv0)
    uv1.props[0]=p_int(1,b'I')
    child(uv1,'Name').props[0]=p_text(b'UVMap1')
    uv_at=geo.children.index(uv0)
    geo.children.insert(uv_at+1,uv1)
    base=next(layer for layer in children(geo,'Layer') if integer(layer.props[0])==0)
    second=copy.deepcopy(base)
    second.props[0]=p_int(1,b'I')
    second.children=[element for element in second.children
                     if element.name!=b'LayerElement' or
                     text(child(element,'Type').props[0])==b'LayerElementUV']
    uv_reference=next(element for element in second.children if element.name==b'LayerElement')
    child(uv_reference,'TypedIndex').props[0]=p_int(1,b'I')
    geo.children.insert(geo.children.index(base)+1,second)
    assert expanded_uv(geo,0)==expanded_uv(geo,1)


def split_geometry(geo:Node,parts=4):
    data=geometry_arrays(geo);faces=data['faces']
    count=len(data['coordinates'])//24
    parent=list(range(count))
    def find(index):
        while parent[index]!=index:
            parent[index]=parent[parent[index]]
            index=parent[index]
        return index
    for face in faces:
        base=find(face[0][0])
        for vertex,_ in face[1:]:
            root=find(vertex)
            if root!=base:parent[root]=base
    groups={}
    for index,face in enumerate(faces):groups.setdefault(find(face[0][0]),[]).append(index)
    ordered=sorted(groups.values(),key=lambda group:(-sum(len(faces[i]) for i in group),group[0]))
    buckets=[[] for _ in range(parts)];loads=[0]*parts
    for group in ordered:
        size=sum(len(faces[i]) for i in group)
        destination=min(range(parts),key=lambda i:(loads[i],i))
        buckets[destination].extend(group);loads[destination]+=size
    assert all(0<x<65535 for x in loads),loads
    old_edges=ints(array(child(geo,'Edges'),'i')[0])
    chunks=[];vertices=[];triangles=[]
    for number,face_ids in enumerate(buckets):
        face_ids.sort()
        part=copy.deepcopy(geo)
        vertex_map={};normal_map={};uv_map={};loop_map={}
        coordinate_out=bytearray();normal_out=bytearray();uv_out=bytearray()
        polygon_out=[];normal_index_out=[];uv_index_out=[];triangle_count=0
        for face_id in face_ids:
            face=faces[face_id];triangle_count+=len(face)-2
            for corner,(vertex,old_loop) in enumerate(face):
                if vertex not in vertex_map:
                    vertex_map[vertex]=len(vertex_map)
                    coordinate_out.extend(data['coordinates'][24*vertex:24*(vertex+1)])
                normal=data['normal_index'][old_loop]
                if normal not in normal_map:
                    normal_map[normal]=len(normal_map)
                    normal_out.extend(data['normals'][24*normal:24*(normal+1)])
                uv=data['uv_index'][old_loop]
                if uv not in uv_map:
                    uv_map[uv]=len(uv_map)
                    uv_out.extend(data['uv'][16*uv:16*(uv+1)])
                new_loop=len(polygon_out);loop_map[old_loop]=new_loop
                index=vertex_map[vertex]
                polygon_out.append(-index-1 if corner==len(face)-1 else index)
                normal_index_out.append(normal_map[normal])
                uv_index_out.append(uv_map[uv])
        edges_out=[loop_map[edge] for edge in old_edges if edge in loop_map]
        set_array(child(part,'Vertices'),'d',bytes(coordinate_out))
        set_array(child(part,'PolygonVertexIndex'),'i',pack_ints(polygon_out))
        set_array(child(part,'Edges'),'i',pack_ints(edges_out))
        normal_layer=child(part,'LayerElementNormal')
        set_array(child(normal_layer,'Normals'),'d',bytes(normal_out))
        set_array(child(normal_layer,'NormalsIndex'),'i',pack_ints(normal_index_out))
        uv_layer=child(part,'LayerElementUV')
        set_array(child(uv_layer,'UV'),'d',bytes(uv_out))
        set_array(child(uv_layer,'UVIndex'),'i',pack_ints(uv_index_out))
        assert len(geometry_arrays(part)['faces'])==len(face_ids)
        chunks.append(part);vertices.append(len(vertex_map));triangles.append(triangle_count)
    return chunks,{'component_count':len(groups),'polygon_corners':loads,
                   'vertices':vertices,'triangles':triangles,
                   'total_triangles':sum(triangles)}


def partition_fbx(raw:bytes):
    fbx=FBX(raw)
    objects=fbx.top('Objects');connections=fbx.top('Connections')
    geometry=children(objects,'Geometry');models=children(objects,'Model')
    assert len(geometry)==len(models)==4,(len(geometry),len(models))
    original_all_faces,original_all_triangles=face_multiset(geometry)
    healthy_model=next(node for node in models if text(node.props[1]).startswith(b'garrison_part_0001\x00'))
    healthy_id=integer(healthy_model.props[0])
    relation=next(node for node in children(connections,'C')
                  if text(node.props[0])==b'OO' and integer(node.props[2])==healthy_id
                  and any(integer(g.props[0])==integer(node.props[1]) for g in geometry))
    healthy_geo=next(g for g in geometry if integer(g.props[0])==integer(relation.props[1]))
    original_faces,original_triangles=face_multiset([healthy_geo])
    chunks,metrics=split_geometry(healthy_geo)
    assert metrics['total_triangles']==original_triangles
    all_ids=[integer(node.props[0]) for node in objects.children if node.props and node.props[0][:1]==b'L']
    next_id=max(all_ids)+1
    material=next(node for node in children(connections,'C')
                  if text(node.props[0])==b'OO' and integer(node.props[2])==healthy_id
                  and any(integer(m.props[0])==integer(node.props[1]) for m in children(objects,'Material')))
    material_id=integer(material.props[1])
    new_parts=[]
    for index,part in enumerate(chunks):
        if index==0:
            objects.children[objects.children.index(healthy_geo)]=part
            continue
        model=copy.deepcopy(healthy_model)
        new_model_id=next_id;next_id+=1
        new_geometry_id=next_id;next_id+=1
        name=f'garrison_part_{index+3:04}'.encode()+b'\x00\x01Model'
        model.props[0]=p_int(new_model_id)
        model.props[1]=p_text(name)
        part.props[0]=p_int(new_geometry_id)
        source_name=text(healthy_geo.props[1]).split(b'\x00',1)[0]
        part.props[1]=p_text(source_name+b'_native_chunk_'+str(index).encode()+b'\x00\x01Geometry')
        objects.children.extend([part,model])
        for source,target in ((new_model_id,0),(new_geometry_id,new_model_id),(material_id,new_model_id)):
            connections.children.append(Node(b'C',[p_text(b'OO'),p_int(source),p_int(target)],[],False))
        new_parts.append(f'garrison_part_{index+3:04}')
    defs=fbx.top('Definitions')
    for node in defs.children:
        if node.name==b'Count':node.props[0]=p_int(integer(node.props[0])+6,b'I')
        if node.name==b'ObjectType' and text(node.props[0]) in (b'Geometry',b'Model'):
            item=child(node,'Count');item.props[0]=p_int(integer(item.props[0])+3,b'I')
    all_geometry=children(objects,'Geometry')
    after_all_faces,after_all_triangles=face_multiset(all_geometry)
    assert after_all_faces==original_all_faces
    assert after_all_triangles==original_all_triangles
    for geo in all_geometry:duplicate_uv1(geo)
    final_faces,final_triangles=face_multiset(chunks)
    assert final_faces==original_faces and final_triangles==original_triangles
    transformed=fbx.serialize()
    again=FBX(transformed)
    parsed_geo=children(again.top('Objects'),'Geometry')
    assert len(parsed_geo)==7
    assert all(expanded_uv(geo,0)==expanded_uv(geo,1) for geo in parsed_geo)
    parsed_all_faces,parsed_all_triangles=face_multiset(parsed_geo)
    assert parsed_all_faces==original_all_faces
    assert parsed_all_triangles==original_all_triangles
    final_check,final_count=face_multiset([g for g in parsed_geo if integer(g.props[0]) in
        {integer(chunk.props[0]) for chunk in chunks}])
    assert final_check==original_faces and final_count==original_triangles
    geometry_ids={integer(chunk.props[0]) for chunk in chunks}
    model_ids={integer(model.props[0]) for model in children(again.top('Objects'),'Model')}
    geometry_links=[node for node in children(again.top('Connections'),'C')
                    if text(node.props[0])==b'OO' and integer(node.props[1]) in geometry_ids]
    assert len(geometry_links)==4
    assert all(integer(node.props[2]) in model_ids for node in geometry_links)
    metrics['uv1']='exact per-corner duplicate of UV0 on all seven geometry nodes'
    metrics['uv_layers_per_geometry']=2
    metrics['uv0_preservation']='exact oriented position-normal-UV0 face multiset across all original and exported states'
    metrics['uv1_equals_uv0_per_corner']=True
    metrics['uv1_corner_count']=sum(len(expanded_uv(geo,1)) for geo in parsed_geo)
    metrics['all_state_triangles']=original_all_triangles
    return transformed,metrics,new_parts


def update_asset(key:str):
    guarded()
    folder=EXPORT/'landmarks'/key
    out=OUT/'landmarks'/key
    original=out/'diagnostics'/'model-original.fbx'
    original.parent.mkdir(parents=True,exist_ok=True)
    current=folder/'model.fbx'
    if not original.exists():
        assert len(children(FBX(current.read_bytes()).top('Objects'),'Geometry'))==4
        shutil.copy2(current,original)
    raw=original.read_bytes()
    transformed,metrics,new_parts=partition_fbx(raw)
    if current.read_bytes()!=transformed:
        temporary=current.with_suffix('.fbx.partition.tmp')
        temporary.write_bytes(transformed)
        temporary.replace(current)
    assert current.read_bytes()==transformed
    manifest=json.loads((folder/'building.json').read_text(encoding='utf-8'))
    assert [p['name'] for p in manifest['parts'][:4]]==[f'garrison_part_{i:04}' for i in range(4)]
    assert [p['first_stage'] for p in manifest['parts'][:4]]==[0,20,0,80]
    manifest['parts']=manifest['parts'][:4]+[{'name':name,'first_stage':20} for name in new_parts]
    write(folder/'building.json',manifest)
    validation=json.loads((out/'validation.json').read_text(encoding='utf-8'))
    validation['export_mesh_partition']={'method':'offline FBX connected-component partition',
        'source_fbx':str(original),'source_fbx_sha256':sha(original),
        'export_fbx_sha256':sha(current),**metrics,
        'face_attribute_multiset':'passed exact oriented position-normal-UV bytes',
        'fbx_binary_roundtrip':'passed exact original bytes',
        'native_cook':'not run'}
    write(out/'validation.json',validation)
    handoff=json.loads((out/'handoff.json').read_text(encoding='utf-8'))
    handoff['building']=manifest
    handoff['export_mesh_partition']=validation['export_mesh_partition']
    handoff['healthy_parts']=['garrison_part_0001',*new_parts]
    handoff['export_sha256']={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
    write(out/'handoff.json',handoff)
    recipe_path=RECIPES/(key+'.json')
    recipe=json.loads(recipe_path.read_text(encoding='utf-8'))
    recipe['construction_parts']=[p['first_stage'] for p in manifest['parts']]
    recipe['healthy_parts']=handoff['healthy_parts']
    recipe['export_postprocess']={'script':str(Path(__file__).resolve()),
                                  'script_sha256':sha(__file__),
                                  'input_fbx':str(original),'input_fbx_sha256':sha(original)}
    recipe['source_script_sha256']=sha(ROOT/'tools/castle_next/landmark_shared.py')
    write(recipe_path,recipe)
    print('CASTLE_LANDMARK_FBX_PARTITION_COMPLETE',key,sha(current),metrics,flush=True)


if __name__=='__main__':
    import sys
    assert len(sys.argv)==2 and sys.argv[1] in ('imperial_citadel','resistance_hq')
    update_asset(sys.argv[1])
