"""Export actual 0.5.1 native monastery triangles for a stamp-space preview."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from common import ROOT, OUT, guarded, read, sha, write
sys.path.insert(0,str(ROOT/'tools/castle_next'))
from building_selectors import rc, source_map, parse_state

def mesh(path, groups=None, names=None, retained=None, state='healthy'):
    chunks=[c for c in rc.walk(rc.load(path).roots) if c.tag==b'GEOB']
    assert len(chunks)%2==0
    positions=[];faces=[];materials=[];offset=0;stats=[]
    for gi in range(len(chunks)//2):
        v,i=chunks[2*gi:2*gi+2]
        n,_,stride,_=struct.unpack_from('<4I',v.payload)
        count,_,width,_=struct.unpack_from('<4I',i.payload)
        assert stride in (20,24) and width==2 and count%3==0
        raw=np.ndarray((n,4),dtype='<f2',buffer=v.payload,offset=16,strides=(stride,2))
        xyz=np.stack((-raw[:,0],-raw[:,2],raw[:,1]),axis=1).astype(np.float32)
        idx=np.frombuffer(i.payload,dtype='<u2',offset=16,count=count).astype(np.int32).reshape((-1,3))
        assert idx.max()<n
        if groups is None:
            valid=np.array([len(set(face))==3 for face in idx])
            mat=3
        else:
            group_names=names[gi] if retained is None else [names[gi][ordinal] for ordinal in retained[gi]]
            assert len(idx)==len(group_names)
            if state=='all':
                valid=np.array([len(set(face))==3 for face in idx])
            elif state=='healthy':
                # The intact roof material includes source labels that also
                # contain "debris"; excluding by name left only a skeletal
                # proxy. Render its complete native mesh as an envelope while
                # runtime selector visibility remains a separate match gate.
                valid=np.array([len(set(face))==3 and (groups[gi]['preview_material']=='roof' or
                                (('disappear' in source or 'sel_base' in source) and 'debris' not in source))
                                for face,source in zip(idx,group_names)])
            else:
                valid=np.array([len(set(face))==3 and ('ruins' in source or 'debris' in source or 'sel_base' in source)
                                for face,source in zip(idx,group_names)])
            mat={'main':0,'extra':1,'roof':2}[groups[gi]['preview_material']]
        kept=idx[valid]
        positions.append(xyz)
        faces.append(kept+offset)
        materials.extend([mat]*len(kept))
        stats.append({'group':gi,'vertex_count':n,'triangle_count':len(idx),'drawn_healthy_proxy_triangles':len(kept),
                      'material':groups[gi]['preview_material'] if groups is not None else 'detail'})
        offset+=n
    return np.concatenate(positions),np.concatenate(faces),np.asarray(materials,dtype=np.uint8),stats

def stamp_points(points,transform):
    q=np.asarray(transform[:4],dtype=np.float64)
    q/=np.linalg.norm(q)
    xyz=np.column_stack((-points[:,0],points[:,2],-points[:,1])).astype(np.float64)
    xyz*=np.asarray(transform[7:10],dtype=np.float64)
    v=q[:3];w=q[3]
    t=2*np.cross(np.broadcast_to(v,xyz.shape),xyz)
    xyz=xyz+w*t+np.cross(np.broadcast_to(v,xyz.shape),t)
    xyz+=np.asarray(transform[4:7],dtype=np.float64)
    return np.column_stack((-xyz[:,0],-xyz[:,2],xyz[:,1])).astype(np.float32)

def prop_geometry(model,cache,incense):
    if 'incense_burner_large_' in model:
        file=incense['bronze' if 'bronze' in model else 'iron']
    else:
        row=cache[model+'.rgm'];file=Path(row['decoded_manifest'])
        assert sha(file)==row['decoded_manifest_sha256']
    doc=read(file);assert doc['status']=='decoded'
    chunks=[];faces=[];offset=0
    for group in doc['geometry']['groups']:
        points=np.asarray(group['positions'],dtype=np.float32)
        triangles=np.asarray(group['triangles'],dtype=np.int32)
        assert len(points)==group['vertex_count'] and len(triangles)==group['triangle_count']
        chunks.append(points);faces.append(triangles+offset);offset+=len(points)
    return np.concatenate(chunks),np.concatenate(faces)

def main():
    guarded(); media=read(ROOT/'output/castle_next/integration/building-media.json')
    sources={p['member']:p for p in media['payloads']}
    donors=read(ROOT/'output/castle_next/donors/donor-manifest.json')['donors']
    cache=read(ROOT/'output/castle_next/inventory/native-selector-cache.json')['models']
    incense={}
    for metal,folder in (('iron','incense'),('bronze','incense-bronze')):
        incense_receipt=read(OUT/f'monastery/stock-props/{folder}/receipt.json')
        assert len(incense_receipt['manifests'])==1
        incense[metal]=Path(incense_receipt['manifests'][0])
    bindings=read(OUT.parent/'release_050/integration/private-bindings.json')['bindings']
    result=[]
    for age in (3,4):
        donor=donors[f'monastery{age:02}']
        names,_=source_map(donor)
        base_row=sources[f'art/scenario/cccastle/monastery_age{age:02}/model.rrgeom']
        base=Path(base_row['file']);assert sha(base)==base_row['sha256']
        detail_member=f'art/scenario/cccastle/monastery_detail_age{age:02}/model.rrgeom'
        detailrow=next(r for r in read(OUT/'monastery/receipt.json')['payloads'] if r['member']==detail_member)
        detail=Path(detailrow['file']);assert sha(detail)==detailrow['sha256']
        detail_model=sources[f'art/scenario/cccastle/monastery_detail_age{age:02}/model.rgm']
        detail_states=[parse_state(c.payload) for c in rc.walk(rc.load(detail_model['file']).roots) if c.tag==b'CNBP']
        assert detail_states and all(not any(condition[3]=='life_cycle_state' and condition[4]=='ruins'
                                             for condition in state) for state in detail_states)
        dp,df,dm,ds=mesh(detail)
        visual=next(p for p in bindings[f'monastery{age:02}']['private_stamp_proofs'] if 'base_default' in p['output'])['after']
        owner=next(v for v in visual if v['model']==f'art/scenario/cccastle/monastery_age{age:02}/model')
        props=[v for v in visual if v is not owner]
        prop_parts=[];prop_proof=[]
        for item in props:
            positions,faces=prop_geometry(item['model'],cache,incense)
            positions=stamp_points(positions,item['transform'])
            prop_parts.append((positions,faces,np.full(len(faces),4 if 'incense' in item['model'] else 5,dtype=np.uint8)))
            prop_proof.append({'model':item['model'],'id':item['id'],'triangles':len(faces),'transform':item['transform']})
        state_rows={}
        for state in ('healthy','ruins'):
            bp,bf,bm,bs=mesh(base,donor['decoded_static']['geometry']['groups'],names,None,state)
            bp=stamp_points(bp,owner['transform'])
            pieces=[(bp,bf,bm)]
            if state=='healthy':pieces.append((stamp_points(dp,owner['transform']),df,dm))
            pieces.extend(prop_parts)
            vertices=[];triangles=[];mats=[];offset=0
            for points,faces,material in pieces:
                vertices.append(points);triangles.append(faces+offset);mats.append(material);offset+=len(points)
            target=OUT/f'monastery/previews/age{age:02}/native-{state}-compound.npz'
            target.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(target,positions=np.concatenate(vertices),faces=np.concatenate(triangles),
                                material=np.concatenate(mats))
            state_rows[state]={'file':str(target),'sha256':sha(target),'triangles':sum(len(f) for _,f,_ in pieces),
                               'base':bs,'detail':ds if state=='healthy' else None,
                               'stock_stamp_props':prop_proof}
            print('PREVIEW_MESH',age,state,state_rows[state]['triangles'])
        result.append({'age':age,'states':state_rows,'stamp_transform':owner['transform'],
                       'detail_model_ruins_hidden_by_native_selectors':True,
                       'source_limit':'Healthy roof group is complete native geometry envelope; other body groups use source-name approximation. Exact runtime selector evaluation and materials require match test.',
                       'native_body_rrgeom_sha256':sha(base),'compacted_detail_rrgeom_sha256':sha(detail)})
    write(OUT/'monastery/previews/geometry.json',{'status':'extracted_from_051_payload_and_050_unchanged_detail',
                                                  'ages':result})

if __name__=='__main__':main()
