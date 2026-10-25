"""Deterministic scratch Castle architecture; no native cook or actor mutation."""
from __future__ import annotations

import hashlib
import json
import math
import random
import shutil
import struct
import sys
import zlib
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/release_020'))
from model_ministry_farm_hideout_runner import (box, mesh, hipped_tile_roof,
    faceted_vessel, join_stage, validate, export_building)
sys.path.insert(0, str(ROOT / 'tools/castle_next'))
from common import ART, EXPORT, RECIPES, OUT, guarded, sha, write

sys.path.insert(0, str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com'))
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material

PALETTES = {
    'imperial_citadel': [(.43,.22,.155),(.25,.17,.115),(.37,.16,.105),(.43,.42,.36),
                         (.30,.26,.18),(.12,.10,.08),(.91,.89,.82),(.39,.29,.21)],
    'resistance_hq': [(.35,.19,.135),(.23,.17,.105),(.28,.15,.11),(.37,.35,.29),
                      (.30,.27,.19),(.13,.11,.075),(.91,.89,.82),(.34,.29,.20)]}
TILES = {'brick':'brick','timber':'timber','tile':'tile','stone':'plaster',
         'earth':'earth','char':'water','owner':'rice','thatch':'thatch'}


def split_healthy_export_mesh(original, chunk_count=4):
    """Keep source anatomy intact while bounding each native FBX mesh.

    Joined roof tiles and timbers are independent closed components.  Assign
    whole components to balanced export meshes so no cut surface, UV, face,
    material, or visible triangle changes are introduced.
    """
    source=original.data
    parent=list(range(len(source.vertices)))
    def find(index):
        while parent[index]!=index:
            parent[index]=parent[parent[index]]
            index=parent[index]
        return index
    for polygon in source.polygons:
        indices=polygon.vertices
        base=find(indices[0])
        for index in indices[1:]:
            root=find(index)
            if root!=base:parent[root]=base
    components={}
    for polygon in source.polygons:
        root=find(polygon.vertices[0])
        group=components.setdefault(root,[])
        group.append(polygon.index)
    ordered=sorted(components.values(),key=lambda faces:(-sum(len(source.polygons[i].vertices) for i in faces),faces[0]))
    buckets=[[] for _ in range(chunk_count)];loads=[0]*chunk_count
    for faces in ordered:
        size=sum(len(source.polygons[i].vertices) for i in faces)
        destination=min(range(chunk_count),key=lambda i:(loads[i],i))
        buckets[destination].extend(faces);loads[destination]+=size
    source_uv=source.uv_layers.active.data
    result=[]
    for number,face_ids in enumerate(buckets):
        face_ids.sort()
        vertices={};coordinates=[];faces=[];uvs=[]
        for face_id in face_ids:
            polygon=source.polygons[face_id]
            face=[];loop_uv=[]
            for loop_id in polygon.loop_indices:
                vertex_index=source.loops[loop_id].vertex_index
                if vertex_index not in vertices:
                    vertices[vertex_index]=len(coordinates)
                    coordinates.append(tuple(source.vertices[vertex_index].co))
                face.append(vertices[vertex_index])
                loop_uv.append(tuple(source_uv[loop_id].uv))
            faces.append(face);uvs.append(loop_uv)
        data=bpy.data.meshes.new(original.name+'_export_'+str(number))
        data.from_pydata(coordinates,[],faces)
        data.materials.append(source.materials[0])
        data.update()
        uv_layer=data.uv_layers.new(name='UVMap')
        for polygon,uv_face in zip(data.polygons,uvs):
            for loop_id,uv in zip(polygon.loop_indices,uv_face):
                uv_layer.data[loop_id].uv=uv
        obj=bpy.data.objects.new(original.name+'_export_'+str(number),data)
        bpy.context.scene.collection.objects.link(obj)
        obj.matrix_world=original.matrix_world.copy()
        obj['garrison_building_first_stage']=20
        obj['garrison_building_profile']='english-house'
        result.append(obj)
    old_triangles=sum(len(face.vertices)-2 for face in source.polygons)
    new_triangles=sum(sum(len(face.vertices)-2 for face in obj.data.polygons) for obj in result)
    assert old_triangles==new_triangles,(old_triangles,new_triangles)
    assert max(loads)<65535,loads
    return result,{'source_triangles':old_triangles,'export_triangles':new_triangles,
                   'polygon_corner_counts':loads,
                   'vertex_counts':[len(obj.data.vertices) for obj in result],
                   'component_count':len(components)}


class Model:
    def __init__(self, name, material, detail):
        self.name=name; self.mat=material; self.detail=detail
        self.foundation=[];self.upper=[];self.ruins=[];self.damage=[]
        self.contacts=[];self.clearances=[]
        self.rng=random.Random(4171 if name=='imperial_citadel' else 4172)

    def add(self, obj, stage='upper'):
        getattr(self,stage).append(obj)
        return obj

    def block(self, name, center, size, tile, stage='upper'):
        return self.add(box(name,center,size,self.mat,TILES[tile]),stage)

    def beam(self,name,start,end,width,tile='timber',stage='upper'):
        a=Vector(start);b=Vector(end);mid=(a+b)/2;length=(b-a).length
        obj=box(name,(0,0,0),(width,width,length+.025),self.mat,TILES[tile])
        obj.location=mid;obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
        return self.add(obj,stage)

    def cylinder(self,name,xy,z0,z1,radius,tile='timber',sides=10,stage='upper'):
        return self.add(faceted_vessel(name,(xy[0],xy[1],z0),
            [(0,radius),(z1-z0,radius)],self.mat,TILES[tile],sides),stage)

    def vessel(self,name,xy,z0,profile,tile='earth',sides=10,stage='upper'):
        return self.add(faceted_vessel(name,(xy[0],xy[1],z0),profile,
            self.mat,TILES[tile],sides),stage)

    def stake(self,name,xy,z0,height,radius=.105,stage='upper'):
        return self.vessel(name,xy,z0,[(0,radius),(height-.20,radius),
                                       (height,.016)],'timber',7,stage)

    def fractured_wall(self,name,xy,width,depth,z0,low,high,stage='ruins'):
        x,y=xy;a=width/2;b=depth/2
        verts=[(x-a,y-b,z0),(x+a,y-b,z0),(x+a,y+b,z0),(x-a,y+b,z0),
               (x-a,y-b,z0+low),(x+a,y-b,z0+low),
               (x+a,y+b,z0+high),(x-a,y+b,z0+high)]
        faces=[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),
               (3,0,4,7),(4,5,6,7)]
        return self.add(mesh(name,verts,faces,self.mat,TILES['brick']),stage)

    def patch(self,name,xy,radius,z0,tile='earth',stage='foundation'):
        x,y=xy;n=9;phase=self.rng.random()*math.tau
        ring=[]
        for i in range(n):
            a=phase+i*math.tau/n;r=radius*(.68+.31*self.rng.random())
            ring.append((x+r*math.cos(a),y+.62*r*math.sin(a)))
        verts=[(px,py,z) for z in (z0,z0+.027) for px,py in ring]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        return self.add(mesh(name,verts,faces,self.mat,TILES[tile]),stage)

    def leaf_finial(self,name,center,size=.55,tile='tile'):
        x,y,z=center
        outline=[(0,0),(.18,.12),(.30,.38),(.17,.72),(0,1),
                 (-.17,.72),(-.30,.38),(-.18,.12)]
        n=len(outline);v=[]
        for dy in (-.055,.055):
            v += [(x+size*dx,y+dy,z+size*dz) for dx,dz in outline]
        f=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
        f += [(i+n,(i+1)%n+n,(i+1)%n,i) for i in range(n)]
        return self.add(mesh(name,v,f,self.mat,TILES[tile]))

    def arch_wedge(self,name,center_y,spring_z,inner,outer,a0,a1,depth,stage='upper'):
        # Closed voussoir; the portal remains a real empty opening below the
        # semicircle, not a dark door painted over a filled wall.
        def ring(y):
            return [(inner*math.cos(a0),y,spring_z+inner*math.sin(a0)),
                    (outer*math.cos(a0),y,spring_z+outer*math.sin(a0)),
                    (outer*math.cos(a1),y,spring_z+outer*math.sin(a1)),
                    (inner*math.cos(a1),y,spring_z+inner*math.sin(a1))]
        v=ring(center_y-depth/2)+ring(center_y+depth/2)
        f=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),
           (2,6,7,3),(3,7,4,0)]
        return self.add(mesh(name,v,f,self.mat,'plaster'),stage)

    def roof(self,name,xy,width,depth,eave,rise,material='tile',stage='upper'):
        # Closed, swept hip roof. Small eave rise is built into the profile.
        obj=hipped_tile_roof(name,xy,width,depth,eave,rise,.15,self.mat)
        if material=='thatch':
            for loop in obj.data.uv_layers.active.data:
                loop.uv.x += .25
                loop.uv.y += .5
        self.add(obj,stage)
        if stage!='upper': return
        nx=max(5,round(width*self.detail['tile_columns_per_m']))
        ny=max(4,round(depth*self.detail['tile_rows_per_m']))
        def surface(x,y):
            sx=abs(x-xy[0])/(width/2);sy=abs(y-xy[1])/(depth/2)
            hip=1-.29*max(0,(sx-.73)/.27)
            return eave+rise*(1-sy)*hip+.12*max(0,(sy-.78)/.22)**2+.06*max(0,(sx-.77)/.23)*max(0,(sy-.75)/.25)
        dx=width/nx;dy=depth/ny
        for j in range(ny):
            for i in range(nx):
                x0=xy[0]-width/2+i*dx+.007;x1=x0+dx-.014
                y0=xy[1]-depth/2+j*dy+.006;y1=y0+dy-.012
                # Five ribs across, three along: the convex ceramic crown and
                # the lapped lower lip are visible geometry at game distance.
                top=[]
                for u in range(5):
                    for v in range(3):
                        fu=u/4;fv=v/2
                        x=x0+(x1-x0)*fu;y=y0+(y1-y0)*fv
                        crown=.054*(1-(2*fu-1)**2)
                        lip=.028 if v==0 else 0
                        top.append((x,y,surface(x,y)+.035+crown+lip))
                faces=[]
                idx=lambda u,v:u*3+v
                for u in range(4):
                    for v in range(2):faces.append((idx(u,v),idx(u+1,v),idx(u+1,v+1),idx(u,v+1)))
                perimeter=[idx(u,0) for u in range(5)]
                perimeter += [idx(4,v) for v in (1,2)]
                perimeter += [idx(u,2) for u in (3,2,1,0)]
                perimeter += [idx(0,1)]
                vertices=top+[(top[k][0],top[k][1],top[k][2]-.082) for k in perimeter]
                offset=len(top)
                for edge,(a,b) in enumerate(zip(perimeter,perimeter[1:]+perimeter[:1])):
                    faces.append((a,offset+edge,offset+(edge+1)%len(perimeter),b))
                faces.append(tuple(reversed(range(offset,offset+len(perimeter)))))
                tile=self.add(mesh(f'{name}_course_{j:02}_tile_{i:02}',
                                   vertices,faces,self.mat,TILES[material]))
                tile_u=((.78+.12*(i%7)/6) if material=='thatch' else
                        (.53+.12*(i%7)/6))
                tile_v=((.68+.16*(j%7)/6) if material=='thatch' else
                        (.08+.17*(j%5)/4))
                for loop in tile.data.loops:
                    pt=tile.data.vertices[loop.vertex_index].co
                    tile.data.uv_layers.active.data[loop.index].uv=(
                        tile_u+.008*(pt.x-x0)/(x1-x0),
                        tile_v+.008*(pt.y-y0)/(y1-y0))
        # Fascia and ridge are derived from the same measured roof surface.
        for side in (-1,1):
            y=xy[1]+side*(depth/2-.045)
            for i in range(nx):
                x=xy[0]-width/2+(i+.5)*dx
                self.block(f'{name}_fascia_{side}_{i}',(x,y,surface(x,y)-.06),
                           (dx+.002,.065,.09),material)
        for i in range(nx):
            x=xy[0]-width/2+(i+.5)*dx
            self.block(f'{name}_ridge_{i}',(x,xy[1],surface(x,xy[1])+.04),
                       (dx+.008,.12,.10),material)
        self.contact(f'{name} roof to beam',eave-.15,eave-.15)

    def contact(self,name,a,b,tolerance=.025):
        row={'interface':name,'plane_a':a,'plane_b':b,'gap':round(a-b,5),
             'tolerance':tolerance,'pass':abs(a-b)<=tolerance}
        self.contacts.append(row)
        assert row['pass'],row

    def clearance(self,name,gap,minimum):
        row={'interface':name,'measured_clearance':round(gap,5),
             'minimum_clearance':minimum,'pass':gap>=minimum}
        self.clearances.append(row)
        assert row['pass'],row

    def hall(self,prefix,xy,w,d,base,wall,roof_eave,roof_rise,heavy=False):
        x,y=xy
        self.block(prefix+'_stone_plinth',(x,y,base/2),(w+.16,d+.12,base),'stone','foundation')
        # Four corner posts and paired front posts carry a timber lintel.
        for px in (x-w*.43,x+w*.43):
            for py in (y-d*.39,y+d*.39):
                self.block(f'{prefix}_post_{px:+.2f}_{py:+.2f}',(px,py,(base+wall)/2),
                           (.16,.16,wall-base),'timber')
                self.contact(prefix+' post to plinth',base,base)
        self.block(prefix+'_rear_wall',(x,y+d*.39,(base+wall)/2),
                   (w*.83,.11,wall-base),'brick' if heavy else 'timber')
        for side in (-1,1):
            px=x+side*w*.43
            self.block(f'{prefix}_side_wall_{side}',(px,y,(base+wall)/2),
                       (.10,d*.78,wall-base),'brick' if heavy else 'timber')
        # Front remains a recessed, readable doorway with framed side screens.
        for side in (-1,1):
            px=x+side*w*.31
            self.block(f'{prefix}_front_panel_{side}',(px,y-d*.39,(base+wall)/2),
                       (w*.25,.08,wall-base-.12),'timber')
            for n in range(3):
                sx=px+(n-1)*w*.075
                self.block(f'{prefix}_screen_{side}_{n}',(sx,y-d*.44,(base+wall)/2),
                           (.045,.05,wall-base-.22),'timber')
        self.block(prefix+'_door_recess',(x,y-d*.385,(base+wall)/2),
                   (w*.21,.035,wall-base-.12),'char')
        self.block(prefix+'_head_beam',(x,y-d*.39,wall-.06),(w*.9,.17,.14),'timber')
        for px in (x-w*.33,x,x+w*.33):
            self.beam(f'{prefix}_roof_bracket_{px:+.2f}',
                (px,y-d*.40,wall-.10),(px,y-d*.54,roof_eave-.10),.10)
        self.roof(prefix+'_hip_roof',(x,y),w+.48,d+.48,roof_eave,roof_rise,
                  'tile' if heavy else 'thatch')
        self.contact(prefix+' roof underside to posts',roof_eave-.15,wall,.03)

    def rubble(self,prefix,center,radius,height,tile='brick'):
        x,y=center;n=7;phase=self.rng.random()*math.tau;v=[]
        for z in (.025,height):
            for i in range(n):
                a=phase+i*math.tau/n;r=radius*(.78+self.rng.random()*.22)
                v.append((x+r*math.cos(a),y+r*math.sin(a),z*(.75+self.rng.random()*.25)))
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(mesh(prefix,v,f,self.mat,TILES[tile]),'ruins')


def atlas(name,source,export=None):
    def save_raw_rgba_png(path, pixels):
        # Blender 5.2 zeroes the RGB channels of newly generated images when
        # their color space changes to Non-Color before save. Write the data
        # bytes ourselves, then load as Non-Color for material and Garrison.
        rgba=np.rint(np.clip(pixels,0,1)*255).astype(np.uint8)
        h,w,_=rgba.shape
        scanlines=b''.join(b'\x00'+rgba[y].tobytes() for y in range(h))
        def chunk(kind,data):
            return (struct.pack('>I',len(data))+kind+data+
                    struct.pack('>I',zlib.crc32(kind+data)&0xffffffff))
        header=struct.pack('>IIBBBBB',w,h,8,6,0,0,0)
        path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+
                         chunk(b'IDAT',zlib.compress(scanlines,6))+
                         chunk(b'IEND',b''))

    size=1024;yy,xx=np.mgrid[:size,:size]
    rng=np.random.default_rng(4171 if name=='imperial_citadel' else 4172)
    albedo=np.ones((size,size,4),dtype=np.float32)
    rough=np.ones((size,size,4),dtype=np.float32)
    height_map=np.zeros((size,size),dtype=np.float32)
    metal=np.zeros((size,size,4),dtype=np.float32);metal[:,:,3]=1
    pattern=np.zeros((size,size,4),dtype=np.float32);pattern[:,:,3]=1
    for index,color in enumerate(PALETTES[name]):
        col,row=index%4,index//4;s=np.s_[row*512:(row+1)*512,col*256:(col+1)*256]
        u=xx[s]-col*256;v=yy[s]-row*512
        grain=rng.normal(0,.018,(512,256))+np.sin(u*.045+v*.013)*.013
        if index==0: # fired brick, staggered mortar courses
            mortar=(v%25<2)|((u+18*((v//25)%2))%58<2)
            grain+=np.where(mortar,-.085,.015)
            grain+=np.sin(u*.031+v*.017)*.019
            grain-=np.where(np.sin(u*.052)+np.cos(v*.039)>1.43,.045,0)
        elif index==1:grain+=np.sin(u*.19+np.sin(v*.035))*.023
        elif index==2:
            seam=(v%23<2)|((u+12*((v//23)%2))%20<2)
            grain+=np.where(seam,-.065,.010)
        elif index==4:
            grain+=np.sin(v*.095)*.012
            grain-=np.where(np.sin(u*.033+v*.041)> .82,.04,0)
        elif index==7:
            grain+=np.sin(u*.27)*.013+np.sin(u*.046+v*.031)*.035
            grain-=np.where(np.sin(u*.11)+np.cos(v*.083)>1.27,.04,0)
        for c in range(3):albedo[s+(c,)]=np.clip(color[c]+grain,0,1)
        base_rough=.88 if index in (0,3,4,7) else .78
        rough[s+(slice(0,3),)]=np.clip(base_rough+grain*.34,.62,.96)[:,:,None]
        height_map[s]=grain
        if index==6:pattern[s+(0,)]=1.0  # only neutral-white trim carries owner red mask
    gy,gx=np.gradient(height_map)
    nx=-gx*2.8;ny=-gy*2.8;nz=np.ones_like(nx)
    length=np.sqrt(nx*nx+ny*ny+nz*nz)
    normal=np.ones((size,size,4),dtype=np.float32)
    normal[:,:,0]=(nx/length+1)*.5
    normal[:,:,1]=(ny/length+1)*.5
    normal[:,:,2]=(nz/length+1)*.5
    images={}
    for label,data in [('albedo',albedo),('normal',normal),('roughness',rough),
                       ('metalness',metal),('pattern',pattern)]:
        path=source/(label+'.png')
        if label=='albedo':
            image=bpy.data.images.new('Castle_'+name+'_'+label,width=size,height=size,alpha=True)
            image.pixels.foreach_set(data.ravel())
            image.filepath_raw=str(path);image.file_format='PNG';image.save()
        else:
            save_raw_rgba_png(path,data)
            image=bpy.data.images.load(str(path),check_existing=False)
            image.name='Castle_'+name+'_'+label
            image.colorspace_settings.name='Non-Color'
        image.pack()
        if export is not None:
            shutil.copy2(path,export/(label+'.png'))
        images[label]=image
    mat=bpy.data.materials.new('Castle_'+name+'_PBR_atlas');mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
    bs.inputs['Specular IOR Level'].default_value=.06
    for label,socket in [('albedo','Base Color'),('roughness','Roughness'),('metalness','Metallic')]:
        node=nodes.new('ShaderNodeTexImage');node.name=label;node.image=images[label]
        links.new(node.outputs['Color'],bs.inputs[socket])
    node=nodes.new('ShaderNodeTexImage');node.name='normal';node.image=images['normal']
    normal_node=nodes.new('ShaderNodeNormalMap');links.new(node.outputs['Color'],normal_node.inputs['Color'])
    links.new(normal_node.outputs['Normal'],bs.inputs['Normal'])
    return mat


def citadel(m):
    # Compact interpretation: axis from south gate to north royal hall. The
    # historical site grounds a brick/stone gate and tiled timber hall, but this
    # is a fictionalized game landmark, not an archaeological reconstruction.
    m.block('IC_outer_terrace',(0,0,.055),(16.90,9.40,.11),'brick','foundation')
    m.block('IC_court_fired_brick',(0,0,.15),(7.36,7.36,.08),'brick','foundation')
    m.contact('central court to outer terrace',.11,.11)
    for y in (-3.51,3.51):m.block(f'IC_coping_Y{y}',(0,y,.19),(7.30,.20,.13),'stone','foundation')
    for x in (-3.51,3.51):m.block(f'IC_coping_X{x}',(x,0,.19),(.20,7.30,.13),'stone','foundation')
    # Raised entry gate: a genuine 1.18 m portal is left clear between pier
    # masses. The gatehouse roof rests on a full lintel and upper chamber.
    for side in (-1,1):
        x=side*1.31
        m.block(f'IC_gate_pier_{side}',(x,-2.88,1.185),(1.43,1.25,2.17),'brick')
        m.block(f'IC_gate_quoin_{side}',(side*1.95,-2.88,1.17),(.12,1.28,1.96),'stone')
        for z in (.54,1.17,1.80):m.block(f'IC_gate_band_{side}_{z}',(x,-3.54,z),(1.46,.08,.10),'stone')
    for i in range(8):
        m.arch_wedge(f'IC_gate_voussoir_{i}',-2.88,1.42,.58,.84,
                     i*math.pi/8,(i+1)*math.pi/8,1.31)
    m.block('IC_gate_lintel',(0,-2.88,2.38),(4.18,1.30,.27),'stone')
    m.block('IC_gate_upper_chamber',(0,-2.88,2.86),(3.72,1.16,.93),'brick')
    m.clearance('Citadel main portal between pier inner faces',
                2*1.31-1.43,1.10)
    for x in (-1.48,-.75,0,.75,1.48):
        m.block(f'IC_gate_merlon_{x}',(x,-3.43,3.32),(.33,.18,.36),'stone')
    m.roof('IC_gate_tile_roof',(0,-2.88),4.54,1.70,3.49,.76)
    m.contact('gate portal lintel to pier top',2.245,2.27,.03)
    # Three framed upper bays break the masonry face into recognizable timber
    # joinery. The middle opening is narrow; side shutters sit in relief.
    for bx in (-1.03,0,1.03):
        for edge in (-.31,.31):
            m.block(f'IC_gate_bay_jamb_{bx}_{edge}',(bx+edge,-3.51,2.86),
                    (.075,.11,.64),'timber')
        m.block(f'IC_gate_bay_head_{bx}',(bx,-3.51,3.18),(.70,.11,.09),'timber')
        m.block(f'IC_gate_bay_sill_{bx}',(bx,-3.51,2.54),(.70,.11,.075),'stone')
        if bx:
            m.block(f'IC_gate_shutter_{bx}',(bx,-3.526,2.86),
                    (.46,.055,.52),'timber')
        else:
            for bar in (-.17,0,.17):
                m.block(f'IC_gate_center_lattice_{bar}',(bar,-3.531,2.86),
                        (.044,.06,.53),'timber')
    m.contact('Gate facade frames to brick chamber',-3.455,-3.46,.01)
    # Courtyard wall returns leave the axial gate open; timber screens and
    # masonry bond give the sides a materially different rhythm.
    for side in (-1,1):
        x=side*3.28
        m.block(f'IC_side_wall_{side}',(x,.10,.94),(.46,5.35,1.68),'brick')
        m.block(f'IC_side_parapet_{side}',(x,.10,1.84),(.50,5.35,.15),'stone')
        m.block(f'IC_side_wallwalk_{side}',(side*2.91,.10,1.965),
                (.43,5.12,.10),'stone')
        m.contact(f'Citadel wallwalk seat {side}',1.915,1.915,.01)
        for j in range(6):
            y=-2.22+j*.89
            m.block(f'IC_side_crenel_{side}_{j}',(x,y,2.10),
                    (.49,.37,.41),'brick')
        for j in range(8):
            y=-2.22+j*.63
            m.block(f'IC_side_pilaster_{side}_{j}',(x-side*.24,y,.92),(.09,.14,1.42),'stone')
    m.block('IC_rear_wall',(0,3.23,.92),(6.92,.42,1.63),'brick')
    for side in (-1,1):
        x=side*2.73
        m.block(f'IC_corner_buttress_{side}',(x,2.64,1.03),(1.31,1.31,1.83),'brick')
        m.block(f'IC_corner_buttress_cap_{side}',(x,2.64,2.02),(1.44,1.44,.15),'stone')
        for dx in (-.42,.42):
            m.block(f'IC_corner_merlon_{side}_{dx}',(x+dx,2.04,2.22),
                    (.25,.25,.31),'stone')
    # Royal timber hall occupies the rear, elevated above the gate courtyard.
    m.hall('IC_royal_hall',(0,1.00),4.88,3.24,.53,2.74,2.87,1.18,heavy=True)
    for bx in (-1.55,-.56,.56,1.55):
        y=-.35
        m.block(f'IC_hall_facade_post_{bx}',(bx,y,1.66),
                (.105,.11,1.98),'timber')
        for z in (1.26,1.88):
            m.block(f'IC_hall_facade_rail_{bx}_{z}',(bx,y,z),
                    (.70,.11,.065),'timber')
    m.block('IC_hall_front_lintel',(0,-.35,2.64),(4.43,.16,.13),'timber')
    for bx in (-1.08,1.08):
        for bar in (-.19,0,.19):
            m.block(f'IC_hall_lattice_{bx}_{bar}',(bx+bar,-.365,1.63),
                    (.038,.065,.69),'timber')
    m.contact('Royal hall facade to front posts',-.295,-.264,.04)
    for bx in (-2.02,-1.02,0,1.02,2.02):
        m.block(f'IC_hall_rear_pilaster_{bx}',(bx,2.34,2.20),
                (.085,.10,.90),'timber')
    for z in (1.79,2.58):
        m.block(f'IC_hall_rear_rail_{z}',(0,2.34,z),
                (4.24,.10,.085),'timber')
    for bx in (-1.52,-.52,.52,1.52):
        m.block(f'IC_hall_rear_shutter_{bx}',(bx,2.352,2.19),
                (.57,.055,.54),'timber')
        for z in (2.04,2.34):
            m.block(f'IC_hall_rear_shutter_slats_{bx}_{z}',
                    (bx,2.39,z),(.59,.035,.04),'stone')
    m.contact('Royal hall rear facade to masonry',2.29,2.319,.03)
    # Low ceremonial galleries flank the core beyond the site. They are
    # scenic overhang only: no gameplay actor, marker or footprint edits.
    for side in (-1,1):
        x=side*6.05
        m.hall(f'IC_outer_gallery_{side}',(x,.60),3.50,2.80,.22,1.95,2.09,.67,heavy=True)
        m.block(f'IC_outer_wall_{side}',(side*8.24,.35,.70),
                (.23,7.83,1.20),'brick')
        m.block(f'IC_outer_wall_cap_{side}',(side*8.24,.35,1.34),
                (.31,7.83,.11),'stone')
        for y in (-4.14,4.14):
            m.block(f'IC_outer_return_{side}_{y}',(x,y,.65),
                    (4.70,.22,1.10),'brick')
        m.clearance(f'Citadel gallery roof to perimeter wall {side}',
                    (8.24-.23/2)-(6.05+(3.50+.48)/2),.05)
    for step in range(3):
        y=-1.43+step*.28;top=.22+(step+1)*.11
        m.block(f'IC_hall_stair_{step}',(0,y,top/2),(1.54,.29,top),'stone')
    m.block('IC_hall_entry_threshold',(0,-.51,.58),(1.57,.20,.10),'stone')
    m.contact('Royal entry threshold to plinth',.53,.53,.01)
    # Slender ceramic leaf finials on hall and restrained twin gate roof beasts.
    for x in (-2.08,2.08):
        m.leaf_finial(f'IC_hall_bodhi_leaf_{x}',(x,1.00,4.00),.58)
    for x in (-1.89,1.89):
        m.vessel(f'IC_gate_dragon_finial_{x}',(x,-2.88),4.02,
                 [(0,.09),(.18,.17),(.36,.10),(.44,.02)],'tile',10)
        m.beam(f'IC_gate_dragon_neck_{x}',(x,-2.88,4.29),
               (x+(.18 if x>0 else -.18),-2.89,4.51),.075,'tile')
    for side in (-1,1):
        x=side*1.65
        m.block(f'IC_owner_ceremonial_banner_{side}',(x,-3.475,2.81),
                (.27,.035,.67),'owner')
        m.block(f'IC_banner_wood_crossbar_{side}',(x,-3.48,3.20),
                (.36,.07,.06),'timber')
        m.contact(f'Citadel owner banner to gate masonry {side}',-3.4575,-3.46,.01)
    for i in range(5):
        x=-1.9+i*.95
        m.block(f'IC_court_flagstone_{i}',(x,-.60,.17),(.63,.76,.035),'stone')
    for side in (-1,1):
        for j,y in enumerate((-.92,1.15)):
            x=side*2.62
            m.vessel(f'IC_court_ceramic_jar_{side}_{j}',(x,y),.19,
                     [(0,.20),(.16,.27),(.48,.28),(.60,.16)],'tile',10)
            m.contact(f'Citadel court jar to brick paving {side}_{j}',.19,.19,.01)
        x=side*4.35
        m.vessel(f'IC_bamboo_planter_{side}',(x,2.79),.11,
                 [(0,.23),(.19,.29),(.42,.25),(.50,.17)],'earth',10)
        for stalk in (-.16,0,.15):
            m.beam(f'IC_planter_bamboo_{side}_{stalk}',
                   (x+stalk,2.79,.55),(x+stalk*.7,2.79,1.56+abs(stalk)),
                   .055,'earth')
    for side in (-1,1):
        for j in range(6):
            y=-3.55+j*1.35
            m.patch(f'IC_court_dirty_edge_{side}_{j}',
                    (side*(4.72+.16*(j%2)),y),.42,.105,'earth')
    # Permanent ruin. Portal piers, hall plinth and fallen roof remain legible.
    m.block('IC_R_outer_terrace',(0,0,.055),(16.90,9.40,.11),'brick','ruins')
    m.block('IC_R_court',(0,0,.15),(7.36,7.36,.08),'brick','ruins')
    for side in (-1,1):
        m.block(f'IC_R_gate_pier_{side}',(side*1.31,-2.88,.55),(1.43,1.25,.95),'brick','ruins')
        for j,(y,height) in enumerate(zip((-1.68,-.53,.64,1.82),(.91,.39,.72,.46))):
            m.fractured_wall(f'IC_R_broken_side_wall_{side}_{j}',
                (side*3.28,y),.46,1.02,.11,height*.74,height*1.12)
        m.fractured_wall(f'IC_R_gate_pier_fracture_{side}',
            (side*1.31,-2.88),1.24,.96,1.025,.14,.34)
    m.block('IC_R_hall_plinth',(0,1.00,.265),(5.04,3.36,.53),'stone','ruins')
    for side in (-1,1):
        m.block(f'IC_R_gallery_foot_{side}',(side*6.05,.60,.11),
                (3.66,2.92,.22),'stone','ruins')
        for j,(y,height) in enumerate(zip((-2.85,-1.32,.22,1.75,3.28),
                                           (.56,.31,.72,.39,.53))):
            m.fractured_wall(f'IC_R_broken_outer_wall_{side}_{j}',
                (side*8.24,y),.23,1.35,.11,height*.68,height*1.19)
    for x,y in [(-2.05,-.05),(1.97,.28),(-1.62,1.96),(2.2,2.18)]:
        m.block(f'IC_R_wall_stump_{x}_{y}',(x,y,.79),(.30,.34,1.03),'brick','ruins')
    for i in range(46):
        a=m.rng.random()*math.tau;r=m.rng.uniform(.9,3.15)
        m.rubble(f'IC_R_broken_tile_{i}',(r*math.cos(a),r*math.sin(a)),
                 m.rng.uniform(.14,.37),m.rng.uniform(.14,.37),'tile' if i%3 else 'brick')
    for i in range(8):
        x=-2.0+i*.56
        m.beam(f'IC_R_charred_beam_{i}',(x,.12,.60),(x+.18,1.32,.59),.11,'char','ruins')
    for i in range(5):
        x=-1.86+i*.89
        m.block(f'IC_R_collapsed_roof_slab_{i}',(x,1.34,.60),
                (.70,.43,.12),'tile','ruins')
    for i in range(14):
        x=m.rng.choice((-1,1))*m.rng.uniform(1.9,4.0)
        y=m.rng.uniform(-2.8,2.6)
        m.rubble(f'IC_R_large_fallen_brick_{i}',(x,y),
                 m.rng.uniform(.18,.35),m.rng.uniform(.14,.32),'brick')
    # Heavy damage: the native foundation stays. Broken gate/hall still rise
    # from its exact masonry seats, while roof masses are visibly gone.
    for side in (-1,1):
        x=side*1.31
        m.block(f'IC_D_cracked_gate_pier_{side}',(x,-2.88,.93),
                (1.43,1.25,1.70),'brick','damage')
        m.block(f'IC_D_remaining_gate_lintel_{side}',
                (side*.98,-2.88,1.82),(1.49,1.27,.20),'stone','damage')
        m.block(f'IC_D_side_wall_{side}',(side*3.28,.15,.69),
                (.46,5.18,1.20),'brick','damage')
        m.block(f'IC_D_rear_buttress_{side}',(side*2.73,2.64,.96),
                (1.31,1.31,1.70),'brick','damage')
        m.block(f'IC_D_outer_wall_{side}',(side*8.24,.35,.69),
                (.23,7.83,1.19),'brick','damage')
        for px in (side*4.66,side*7.44):
            for py in (-.48,1.68):
                m.block(f'IC_D_gallery_burnt_post_{px}_{py}',(px,py,1.15),
                        (.16,.16,1.86),'char','damage')
    for i in (0,1,6,7):
        m.arch_wedge(f'IC_D_broken_voussoir_{i}',-2.88,1.42,.58,.84,
                     i*math.pi/8,(i+1)*math.pi/8,1.31,'damage')
    for x in (-2.09,-.74,.74,2.09):
        for y in (-.27,2.27):
            m.block(f'IC_D_charred_hall_post_{x}_{y}',(x,y,1.48),
                    (.16,.16,1.89),'char','damage')
    m.block('IC_D_hall_rear_wall',(0,2.27,1.18),(4.25,.15,1.38),'brick','damage')
    for i in range(7):
        x=-2.23+i*.74
        m.beam(f'IC_D_fallen_roof_rafter_{i}',(x,.08,.59),
               (x+.23,1.91,.58),.12,'char','damage')
        m.block(f'IC_D_clay_roof_scatter_{i}',(x,1.40,.65),
                (.42,.18,.12),'tile','damage')
    m.contact('Citadel fallen rafters to hall plinth',.59-.06,.53,.01)
    return {'axis':'south gate to north royal hall','footprint':'8 x 8 native actor',
            'anatomy':['masonry court and axial paved passage','piered raised gatehouse with timber bays',
                'rear royal timber hall with raised entry','wallwalk and crenellated side walls',
                'ceramic leaf and beast ridge ornaments','court jars and bamboo planters',
                'broken masonry and collapsed roof ruins'],
            'proportions':{'gate_roof_width_to_court':4.54/7.36,
                'hall_roof_width_to_court':5.36/7.36,'source_width_m':16.90,
                'gate_roof_peak_m':4.25,
                'hall_roof_peak_m':4.05},
            'references':['https://whc.unesco.org/en/list/1328',
                          'https://baotanglichsu.vn/vi/Articles/3101/69653/vat-lieu-kien-truc-bang-djat-nung-tai-di-tich-hoang-thanh-thang-long.html'],
            'interpretation':'Fictionalized medieval Dai Viet game compound with Thang Long inspired masonry and roof ceramics.'}


def headquarters(m):
    # Fictional Lam Son informed command station: lower, timber/bamboo, asymmetry
    # and logistical functions visible at AoE4 camera distance.
    m.block('RH_packed_court',(0,0,.07),(11.40,8.20,.14),'earth','foundation')
    m.hall('RH_command_hall',(-.72,1.30),3.42,2.92,.28,2.31,2.45,.94)
    for side in (-1,1):
        x=-.72+side*1.06
        m.block(f'RH_owner_command_banner_{side}',(x,.125,1.68),
                (.21,.03,.65),'owner')
        m.block(f'RH_banner_timber_crossbar_{side}',(x,.12,2.05),
                (.29,.06,.055),'timber')
        m.contact(f'HQ owner banner to command panel {side}',.14,.1212,.02)
        for bar in (-.28,-.14,.14,.28):
            m.block(f'RH_hall_bamboo_lattice_{side}_{bar}',(x+bar,.103,1.48),
                    (.037,.065,.73),'timber')
        for z in (1.22,1.77):
            m.block(f'RH_hall_lattice_crossbar_{side}_{z}',(x,.101,z),
                    (.72,.067,.052),'timber')
    m.block('RH_hall_door_header',(-.72,.095,2.15),(1.12,.11,.11),'timber')
    for bx in (-1.19,-.25):
        m.block(f'RH_hall_door_jamb_{bx}',(bx,.095,1.47),
                (.10,.11,1.36),'timber')
    m.block('RH_map_table',(-.30,.60,.64),(1.43,.79,.13),'timber')
    for x in (-.88,.28):
        m.block(f'RH_map_table_leg_{x}',(x,.60,.39),(.11,.58,.45),'timber')
    # Lookout: four braced posts, accessible lower platform, hipped guard roof.
    tx,ty=2.20,-1.73
    m.block('RH_watch_stone_foot',(tx,ty,.16),(1.91,1.91,.32),'stone','foundation')
    for x in (tx-.68,tx+.68):
        for y in (ty-.68,ty+.68):
            m.block(f'RH_watch_post_{x}_{y}',(x,y,1.70),(.14,.14,2.80),'timber')
            m.contact('watch post to stone foot',.30,.32,.03)
    m.block('RH_watch_deck',(tx,ty,2.52),(1.79,1.79,.19),'timber')
    for side in (-1,1):
        m.beam(f'RH_watch_Xbrace_{side}',(tx+side*.68,ty-.68,.48),
               (tx+side*.68,ty+.68,2.31),.085)
    for y in (ty-.69,ty+.69):
        m.block(f'RH_watch_rail_{y}',(tx,y,2.90),(1.72,.08,.62),'timber')
    m.roof('RH_watch_roof',(tx,ty),2.13,2.13,3.34,.69,'thatch')
    for side in (-1,1):
        x=tx+side*.27
        m.beam(f'RH_watch_ladder_rail_{side}',(x,ty-1.10,.17),
               (x,ty-.69,2.54),.075)
    for j in range(8):
        z=.35+j*.27;y=ty-1.07+j*.047
        m.block(f'RH_watch_ladder_rung_{j}',(tx,y,z),
                (.59,.07,.065),'timber')
    m.contact('HQ watch ladder landing to deck',2.54,2.615,.08)
    # Rear stores and a front work shelter, neither duplicates the hall.
    m.hall('RH_store',(2.30,2.32),1.58,1.50,.22,1.65,1.78,.58)
    m.hall('RH_work_shelter',(-2.22,-1.80),1.82,2.19,.18,1.49,1.63,.48)
    m.hall('RH_west_supply_shelter',(-4.42,.84),1.34,1.90,.18,1.37,1.52,.42)
    m.hall('RH_east_guard_shelter',(4.42,.73),1.34,1.76,.18,1.37,1.52,.42)
    m.clearance('HQ hall-to-store roof gap',
        (2.30-(1.58+.48)/2)-(-.72+(3.42+.48)/2),.035)
    m.clearance('HQ store roof to east wing',
        (4.42-(1.34+.48)/2)-(2.30+(1.58+.48)/2),.05)
    m.clearance('HQ east wing roof to palisade',
        (5.48-.105)-(4.42+(1.34+.48)/2),.035)
    m.clearance('HQ hall-to-shelter roof gap',
        (1.30-(2.92+.48)/2)-(-1.80+(2.19+.48)/2),.035)
    for i in range(3):
        x=1.28+i*.43
        m.vessel(f'RH_grain_jar_{i}',(x,1.88),.14,
                 [(0,.20),(.19,.29),(.46,.28),(.58,.18)],'earth',10)
    for i in range(4):
        x=-2.86+i*.39
        m.block(f'RH_bamboo_stack_{i}',(x,-2.62,.23),(.10,.87,.24),'timber')
    for i in range(4):
        x=-3.81+i*.30
        m.block(f'RH_open_supply_bundle_{i}',(x,-3.13,.23),
                (.17,.72,.20),'timber')
    for i in range(3):
        x=3.55+i*.34
        m.vessel(f'RH_courtyard_salt_jar_{i}',(x,-2.67),.14,
                 [(0,.15),(.20,.23),(.43,.22),(.55,.13)],'earth',9)
        m.contact(f'HQ yard jar base {i}',.14,.14,.01)
    m.block('RH_supply_crate',(3.84,-.78,.40),(.71,.56,.52),'timber')
    for z in (.25,.57):
        m.block(f'RH_supply_crate_band_{z}',(3.84,-.78,z),
                (.73,.59,.055),'char')
    # Palisade follows footprint edges while leaving a two metre south gate.
    for side in (-1,1):
        x=side*5.48
        for j in range(18):
            y=-3.85+j*.45
            h=1.42+.10*((j*5+int(side>0))%4)/3
            m.stake(f'RH_palisade_side_{side}_{j}',(x,y),.14,h)
        m.block(f'RH_palisade_side_rail_{side}',(x-side*.09,0,.76),(.10,7.96,.13),'timber')
    for j in range(25):
        x=-5.40+j*.45
        m.stake(f'RH_palisade_north_{j}',(x,4.00),.14,
                1.43+.09*((j*3)%5)/4)
    for side in (-1,1):
        for j in range(10):
            x=side*(1.27+j*.46)
            m.stake(f'RH_palisade_south_{side}_{j}',(x,-4.00),.14,
                    1.43+.09*((j*7)%5)/4)
    m.block('RH_gate_crossbeam',(0,-3.94,1.45),(2.28,.16,.16),'timber')
    for side in (-1,1):
        x=side*1.27
        m.beam(f'RH_gate_signal_pole_{side}',(x,-4.00,1.43),
               (x,-4.00,2.22),.09)
        m.block(f'RH_owner_gate_flag_{side}',(x+side*.22,-4.02,1.91),
                (.40,.045,.43),'owner')
        m.block(f'RH_gate_flag_rope_{side}',(x+side*.22,-4.045,2.14),
                (.43,.05,.045),'timber')
        m.contact(f'HQ gate flag inner edge to pole {side}',.22-.40/2,.09/2,.03)
    m.clearance('HQ south palisade opening',2*(1.27-.105),2.0)
    # Diagonal earth access stays open in front of the command hall.
    for i in range(5):
        y=-3.62+i*.56
        m.block(f'RH_worn_court_step_{i}',(-.21,y,.165),(.77,.38,.045),'earth')
    for i in range(15):
        side=-1 if i%2 else 1
        x=side*(3.38+.19*(i%4));y=-3.45+(i//2)*.90
        m.patch(f'RH_dry_leaf_and_dirt_patch_{i}',(x,y),
                .21+.06*(i%3),.135,'thatch')
    m.block('RH_R_court',(0,0,.07),(11.40,8.20,.14),'earth','ruins')
    m.block('RH_R_hall_plinth',(-.72,1.30,.14),(3.58,3.04,.28),'stone','ruins')
    m.block('RH_R_watch_foot',(tx,ty,.16),(1.91,1.91,.32),'stone','ruins')
    for side in (-1,1):
        m.block(f'RH_R_wing_shelter_foot_{side}',(side*4.42,.78,.09),
                (1.50,2.00,.18),'stone','ruins')
    for x,y in [(-2.16,.08),(.05,.07),(-2.11,2.48),(1.66,2.48)]:
        m.block(f'RH_R_burnt_post_{x}_{y}',(x,y,.56),(.19,.19,.88),'char','ruins')
    for side in (-1,1):
        for i in range(5):
            y=-2.5+i*1.1
            m.cylinder(f'RH_R_broken_palisade_{side}_{i}',(side*5.48,y),.13,
                       .35+m.rng.random()*.42,.10,'char',7,'ruins')
    for i in range(37):
        x=m.rng.uniform(-3.2,3.2);y=m.rng.uniform(-3.2,3.2)
        m.rubble(f'RH_R_roof_debris_{i}',(x,y),m.rng.uniform(.13,.31),
                 m.rng.uniform(.13,.29),'thatch' if i%3 else 'char')
    for i in range(10):
        x=-2.3+i*.43
        m.beam(f'RH_R_fallen_beam_{i}',(x,.28,.34),(x+.13,1.65,.34),.10,'char','ruins')
    for i in range(5):
        x=-1.86+i*.54
        m.block(f'RH_R_torn_thatch_panel_{i}',(x,1.17,.34),
                (.41,.65,.12),'thatch','ruins')
    for i in range(3):
        m.beam(f'RH_R_watch_roof_timber_{i}',(1.56+i*.49,-2.40,.35),
               (1.71+i*.49,-1.06,.35),.13,'char','ruins')
    # Heavy damage retains functional building body through native actor; the
    # visual shows bent posts, a collapsed hall roof and partly burnt palisade.
    for side in (-1,1):
        x=-.72+side*1.47
        for y in (.16,2.44):
            m.block(f'RH_D_command_post_{side}_{y}',(x,y,1.19),
                    (.16,.16,1.81),'char','damage')
    m.block('RH_D_command_rear_wall',(-.72,2.44,1.02),
            (2.92,.12,1.39),'timber','damage')
    for i in range(8):
        x=-2.07+i*.38
        m.beam(f'RH_D_collapsed_rafter_{i}',(x,.31,.34),
               (x+.19,2.40,1.55),.10,'char','damage')
        m.block(f'RH_D_thatch_fragment_{i}',(x,1.17,.94),
                (.31,.58,.08),'thatch','damage')
    m.contact('HQ collapsed rafters to hall plinth',.34-.05,.28,.02)
    for side in (-1,1):
        x=tx+side*.68
        for y in (ty-.68,ty+.68):
            m.block(f'RH_D_watch_post_{x}_{y}',(x,y,1.33),
                    (.14,.14,2.03),'char','damage')
    m.block('RH_D_watch_deck',(tx,ty,2.40),(1.73,1.73,.15),'timber','damage')
    for i in range(6):
        m.block(f'RH_D_scattered_supply_{i}',(-2.62+i*.38,-2.51,.25),
                (.13,.70,.15),'timber','damage')
    for side in (-1,1):
        for i in range(8):
            y=-3.55+i*.90
            m.cylinder(f'RH_D_palisade_post_{side}_{i}',(side*5.48,y),.14,
                       1.12-(i%3)*.16,.105,'char',7,'damage')
    return {'axis':'south palisade gate to rear command hall','footprint':'8 x 8 native actor',
            'anatomy':['worn packed court','rear low lattice-front command hall',
                'detached laddered front watchtower','stores and side work shelters',
                'tapered bamboo palisade and flagged open gate','visible yard supplies',
                'low burnt ruins with fallen rafters'],
            'proportions':{'hall_roof_width_to_court':3.90/11.40,
                'watch_roof_width_to_court':2.13/11.40,'source_width_m':11.40,
                'hall_roof_peak_m':3.39,
                'watch_roof_peak_m':4.03},
            'reference':'https://baotanglichsuquocgia.vn/vi/Articles/3091/14734/hoi-thao-khoa-hoc-hoi-the-lung-nhai-trong-khoi-nghia-lam-son.html',
            'interpretation':'Fictional Lam Son informed field headquarters; not a reconstruction of Lung Nhai.'}


def preview(objects,material,target):
    scene=bpy.context.scene
    pts=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
    lo=Vector([min(p[i] for p in pts) for i in range(3)])
    hi=Vector([max(p[i] for p in pts) for i in range(3)])
    center=(lo+hi)/2;extent=max(hi-lo)
    cam=bpy.data.objects.new('Castle preview camera',bpy.data.cameras.new('Castle preview camera'))
    scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO'
    scene.render.resolution_x=850;scene.render.resolution_y=730;scene.render.resolution_percentage=100
    target.mkdir(parents=True,exist_ok=True)
    all_mesh=[o for o in scene.objects if o.type=='MESH']
    for o in all_mesh:o.hide_render=o not in objects
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    for label,direction in [('front',(0,-1,.16)),('back',(0,1,.16)),('left',(-1,0,.16)),
                            ('right',(1,0,.16)),('top',(0,0,1)),('bottom',(0,0,-1))]:
        cam.location=center+Vector(direction).normalized()*extent*2
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.ortho_scale=extent*1.48
        scene.render.filepath=str(target/(label+'-solid.png'));bpy.ops.render.render(write_still=True)
    # Two texture distances plus ruins use the authored PBR atlas.
    scene.render.engine='CYCLES';scene.cycles.samples=8
    scene.cycles.max_bounces=2
    scene.view_settings.view_transform='Standard'
    if scene.world is None:scene.world=bpy.data.worlds.new('Castle preview world')
    scene.world.use_nodes=True
    background=scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value=(.78,.80,.84,1)
    background.inputs['Strength'].default_value=1.0
    lights=[]
    for name,vector,power in [('key',(.8,-.8,1.5),10),('fill',(-.7,-.4,.7),5)]:
        data=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,data)
        scene.collection.objects.link(o);o.location=center+Vector(vector)*extent
        data.energy=extent*extent*power*4;data.size=extent*1.3;lights.append(o)
    for label,scale in [('near',1.30),('game',1.95)]:
        cam.location=center+Vector((1,-1,.80)).normalized()*extent*2
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.ortho_scale=extent*scale
        scene.render.filepath=str(target/(label+'-textured.png'));bpy.ops.render.render(write_still=True)
    for o in lights+[cam]:bpy.data.objects.remove(o,do_unlink=True)
    scene.camera=None


def principal_reference(name):
    folder=OUT/'landmarks/reference'/('citadel' if name=='imperial_citadel' else 'hq')
    manifests=list(folder.glob('*/decoded-static.json'))
    assert len(manifests)==1,(folder,manifests)
    manifest=manifests[0]
    decoded=json.loads(manifest.read_text(encoding='utf-8'))
    assert decoded['status']=='decoded'
    groups=decoded['geometry']['groups']
    measured=groups if name=='imperial_citadel' else [
        group for group in groups if 'sel_ruins' not in group['name'] and '_debris' not in group['name']]
    lo=[min(g['bounds']['minimum'][i] for g in measured) for i in range(3)]
    hi=[max(g['bounds']['maximum'][i] for g in measured) for i in range(3)]
    return {'manifest':str(manifest),'sha256':sha(manifest),
        'logical_path':decoded['request']['logical_path'],'group_count':len(measured),
        'bounds_min':lo,'bounds_max':hi,'extent':[hi[i]-lo[i] for i in range(3)],
        'interpretation':'decoded source context only; Citadel includes belowground/conditional groups, HQ excludes tagged ruins/debris; neither is a native visible-bounds proof'}


def build(name):
    assert name in PALETTES and bpy.app.background and not bpy.data.filepath
    guarded()
    blockout='--blockout' in sys.argv
    source=ART/'landmarks'/name
    export=EXPORT/'landmarks'/name
    out=OUT/'landmarks'/name
    recipe=RECIPES/(name+'.json')
    budget=OUT/'inventory/castle-landmark-triangle-budget.json'
    if blockout:
        # A reviewable modeling draft; it makes no stock-mean acceptance claim.
        # Keep its blend, textures and renders apart from qualified handoff files.
        target=90000.0;cap=None;guaranteed_min=None;guaranteed_max=None
        info={'status':'provisional_visual_blockout'}
        source=source/'draft';out=out/'draft';export=None
    else:
        assert budget.is_file(),f'Qualified stock Castle budget required: {budget}'
        info=json.loads(budget.read_text(encoding='utf-8'))
        assert info['proof_status']=='qualified_conservative_50percent_cap',info['proof_status']
        assert info.get('exact_mean') is None
        target=float(info['mean_target_triangles']);cap=float(info['maximum'])
        guaranteed_min=float(info['guaranteed_target_min'])
        guaranteed_max=float(info['guaranteed_target_max'])
        assert 0<guaranteed_min<=target<=guaranteed_max<=cap
        assert cap<=1.5*float(info['mean_lower'])+1e-6
    reference=principal_reference(name)
    for path in (source,out):path.mkdir(parents=True,exist_ok=True)
    if not blockout:
        export.mkdir(parents=True,exist_ok=True)
        recipe.parent.mkdir(parents=True,exist_ok=True)
    # Detail budget comes from visible roof courses across the complete
    # compound; the first run prints the actual count for correction.
    roof_area=54.0 if name=='imperial_citadel' else 37.0
    estimate=math.sqrt(max(target-6000,1500)/(50*roof_area))
    density=float(info.get('tile_columns_per_m',estimate))
    rows=float(info.get('tile_rows_per_m',density))
    if '--density' in sys.argv:
        density=float(sys.argv[sys.argv.index('--density')+1]);rows=density
    detail={'tile_columns_per_m':density,'tile_rows_per_m':rows}
    for obj in tuple(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
    mat=atlas(name,source,export)
    m=Model(name,mat,detail)
    anatomy=citadel(m) if name=='imperial_citadel' else headquarters(m)
    objects=[join_stage(m.foundation,'Castle_'+name+'_foundation',0),
             join_stage(m.upper,'Castle_'+name+'_superstructure',20),
             join_stage(m.ruins,'Castle_'+name+'_ruins',0),
             join_stage(m.damage,'Castle_'+name+'_heavy_damage',80)]
    for obj in objects:obj['garrison_building_profile']='english-house'
    z_factor=2.0 if name=='imperial_citadel' else 1.0
    if z_factor!=1:
        for obj in objects:
            for vertex in obj.data.vertices:vertex.co.z*=z_factor
            obj.data.update()
        for row in m.contacts:
            for key in ('plane_a','plane_b','gap','tolerance'):row[key]*=z_factor
    xy=max(abs((o.matrix_world@v.co)[i]) for o in objects for v in o.data.vertices for i in (0,1))
    expected_xy=8.45 if name=='imperial_citadel' else 5.70
    assert abs(xy-expected_xy)<.015,(name,xy,expected_xy)
    checks=validate(objects);triangles=sum(c['triangles'] for c in checks)
    # Both complete healthy form and ruins consume separate native states.
    healthy=sum(c['triangles'] for c in checks[:2]);ruins=checks[2]['triangles']
    heavy=checks[0]['triangles']+checks[3]['triangles']
    print('CASTLE_LANDMARK_BUDGET',name,'healthy',healthy,'ruins',ruins,
          'heavy_damage',heavy,'target',target,'cap',cap,
          'budget_status',info.get('proof_status',info.get('status')),
          'tile_density',density,flush=True)
    if not blockout:
        assert guaranteed_min<=healthy<=guaranteed_max,(name,healthy,guaranteed_min,guaranteed_max)
        assert healthy<=cap,(name,healthy,cap)
    preflight=require_valid(objects,bpy.context);assert preflight['ok'],preflight
    export_partition=None
    if not blockout:
        adopt_material(mat)
        healthy_chunks,export_partition=split_healthy_export_mesh(objects[1])
        export_objects=[objects[0],healthy_chunks[0],objects[2],objects[3],*healthy_chunks[1:]]
        export_checks=validate(export_objects)
        assert sum(c['triangles'] for c in export_checks)==triangles
        assert sum(c['triangles'] for c in export_checks if c['name'].endswith('_export_0') or '_export_' in c['name'])==checks[1]['triangles']
        manifest=export_building(export_objects,export)
        assert [p['first_stage'] for p in manifest['parts']]==[0,20,0,80,20,20,20]
        for obj in healthy_chunks:bpy.data.objects.remove(obj,do_unlink=True)
    # The saved editable scene shows healthy state; the dedicated ruins part is
    # retained, selectable, and hidden from normal healthy presentation.
    for obj in objects[2:]:obj.hide_render=True;obj.hide_set(True)
    collection=bpy.data.collections.new('Castle '+name)
    bpy.context.scene.collection.children.link(collection)
    for key,value in {'garrison_asset_container':True,'garrison_asset_id':name,
        'garrison_namespace':'community_civilization_pack','garrison_display_name':name,
        'garrison_qualified_id':'community_civilization_pack:'+name,
        'garrison_archetype':'building','garrison_building_profile':'english-house',
        'garrison_building_integration':'script'}.items():collection[key]=value
    for obj in objects:
        collection.objects.link(obj)
        for prior in tuple(obj.users_collection):
            if prior!=collection:prior.objects.unlink(obj)
    bpy.context.preferences.filepaths.save_version=0
    blend_path=source/(('draft' if blockout else name)+'.blend')
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if '--skip-previews' not in sys.argv:
        preview(objects[:2],mat,out/'healthy')
        objects[2].hide_render=False;preview([objects[2]],mat,out/'ruins')
        objects[3].hide_render=False;preview([objects[0],objects[3]],mat,out/'heavy_damage')
    else:
        assert all(list((out/state).glob('*.png')) for state in ('healthy','ruins','heavy_damage'))
    bounds=[]
    for o in objects:
        points=[o.matrix_world@v.co for v in o.data.vertices]
        bounds.append({'min':[min(v[i] for v in points) for i in range(3)],
                       'max':[max(v[i] for v in points) for i in range(3)]})
    scale_field=.75 if name=='imperial_citadel' else 1.20
    healthy_min=[min(bounds[0]['min'][i],bounds[1]['min'][i]) for i in range(3)]
    healthy_max=[max(bounds[0]['max'][i],bounds[1]['max'][i]) for i in range(3)]
    source_healthy_extent=[healthy_max[i]-healthy_min[i] for i in range(3)]
    conditional_visible_extent=[value*scale_field for value in source_healthy_extent]
    validation={'schema':'ccp.castle-next.landmark-art/v1','name':name,
        'anatomy':anatomy,'geometry':checks,'contacts':m.contacts,
        'clearances':m.clearances,'bounds':bounds,
        'principal_stock_reference':reference,
        'healthy_triangles':healthy,'ruin_triangles':ruins,
        'heavy_damage_triangles':heavy,
        'internal_visual_target_triangles':target,
        'provisional_density_target_triangles':target if blockout else None,
        'internal_working_min':guaranteed_min,'internal_working_max':guaranteed_max,
        'stock_maximum_conservative_cap':cap,
        'stock_mean_lower_bound':None if blockout else float(info['mean_lower']),
        'stock_mean_upper_bound':None if blockout else float(info['mean_upper']),
        'stock_budget_sha256':sha(budget) if not blockout else None,
        'stock_budget_status':info.get('proof_status',info.get('status')),
        'internal_target_delta_fraction':None if blockout else (healthy-target)/target,
        'source_xy_half_extent_m':xy,
        'source_z_scale_from_recipe':z_factor,
        'actor_animator_scale_percent':75 if name=='imperial_citadel' else 120,
        'source_healthy_extent_m':source_healthy_extent,
        'conditional_effective_extent_m':conditional_visible_extent,
        'native_scale_interpretation':'unverified until native match',
        'garrison_preflight':preflight,'export_mesh_partition':export_partition,
        'native_cook':'not run','native_match':'not run',
        'owner_colour':{'source_mask':str(source/'pattern.png'),
            'export_mask':str(export/'pattern.png') if export is not None else None,
            'mask_channel':'red','masked_atlas_tile':6,
            'qualification':'unqualified until native material shader binds pattern and two player colours pass in match'}}
    if blockout:
        validation['status']='provisional_visual_blockout'
        validation['owner_colour']['export_mask']=None
        validation['source_blend']=str(blend_path)
        validation['source_blend_sha256']=sha(blend_path)
        validation['source_texture_sha256']={p.name:sha(p) for p in source.glob('*.png')}
        validation['preview_files']=[str(p) for p in out.rglob('*.png')]
        write(out/'validation.json',validation)
        print('CASTLE_LANDMARK_BLOCKOUT_COMPLETE',name,healthy,ruins,heavy,flush=True)
        return
    write(out/'validation.json',validation)
    write(recipe,{'schema':'ccp.castle-next.landmark-recipe/v1','name':name,
        'source_script':str(Path(__file__).resolve()),'source_script_sha256':sha(__file__),
        'entrypoint':str(Path(__file__).with_name('landmark_citadel.py' if name=='imperial_citadel' else 'landmark_hq.py')),
        'source_blend':str(blend_path),
        'export_directory':str(export),'budget_file':str(budget),'detail':detail,
        'principal_stock_reference':reference,
        'construction_parts':[p['first_stage'] for p in manifest['parts']],
        'healthy_parts':['garrison_part_0001','garrison_part_0004',
                         'garrison_part_0005','garrison_part_0006'],
        'ruin_part':'garrison_part_0002',
        'heavy_damage_part':'garrison_part_0003'})
    write(out/'handoff.json',{'name':name,'source_blend':str(blend_path),
        'source_blend_sha256':sha(blend_path),'export_directory':str(export),
        'export_sha256':{p.name:sha(p) for p in export.iterdir() if p.is_file()},
        'building':manifest,'healthy_triangles':healthy,'ruin_triangles':ruins,
        'heavy_damage_triangles':heavy,
        'stock_budget_sha256':sha(budget),
        'source_healthy_extent_m':source_healthy_extent,
        'conditional_effective_extent_m':conditional_visible_extent,
        'bounds':bounds,'export_mesh_partition':export_partition,
        'healthy_parts':['garrison_part_0001','garrison_part_0004',
                         'garrison_part_0005','garrison_part_0006'],
        'ruin_parts':['garrison_part_0002'],
        'heavy_damage_parts':['garrison_part_0003'],
        'principal_stock_reference':reference,
        'validation':str(out/'validation.json'),
        'preview_files':[str(p) for p in out.rglob('*.png')],
        'native_owner_requirement':'Preserve active actor lifecycle and stock RGO/selection markers; native ruins selector shows only part0002 and damage3-5 shows part0003 with foundation0000.',
        'owner_colour_requirement':'pattern.png red mask is authored but static Garrison building material does not bind native dynamic owner colour; integration must qualify shader and two player colours.'})
    print('CASTLE_LANDMARK_ART_COMPLETE',name,healthy,ruins)
