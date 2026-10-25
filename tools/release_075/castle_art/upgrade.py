"""Release-owned deterministic Castle upgrade. Factory-startup background only.

Usage: blender --background --factory-startup --python upgrade.py -- citadel|hq
Preserves old blends and lifecycle meshes; does not cook or activate resources.
"""
import sys, json, hashlib, shutil, math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import baseline_recipe as b

ROOT=Path(__file__).resolve().parents[3]
KEY=sys.argv[sys.argv.index('--')+1]
NAME={'citadel':'imperial_citadel','hq':'resistance_hq'}[KEY]
SOURCE=ROOT/'art/authoring/release_075'/KEY
EXPORT=ROOT/'art/exports/release_075'/KEY
OUT=ROOT/'output/release_075/art'/KEY
BASE=ROOT/'art/authoring/castle_next/landmarks'/NAME/(NAME+'.blend')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def digest(o):
    return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
def tri(o):return sum(len(p.vertices)-2 for p in o.data.polygons)

class Revised(b.Model):
    def block(self,name,center,size,tile,stage='upper'):
        # Perimeter thickness grows inward, retaining the external bounds.
        if stage=='upper' and name.startswith('IC_outer_return_'):
            side=1 if center[1]>0 else -1
            center=(center[0],center[1]-side*.065,center[2]);size=(size[0],.35,size[2])
        if name.startswith('IC_outer_terrace') or name.startswith('IC_court_fired_brick'):
            tile='stone'
        if name.startswith('IC_outer_gallery') and ('rear_wall' in name or 'side_wall' in name):tile='stone'
        obj=super().block(name,center,size,tile,stage)
        if tile=='timber':self.grain(obj)
        return obj
    def grain(self,obj):
        # The atlas grain runs V. Align V to the longest geometric axis,
        # with restrained grain frequency across its narrow dimension.
        data=obj.data;uv=data.uv_layers.active
        for p in data.polygons:
            points=[data.vertices[data.loops[i].vertex_index].co for i in p.loop_indices]
            spans=[max(v[k] for v in points)-min(v[k] for v in points) for k in range(3)]
            long,short=sorted(range(3),key=lambda k:spans[k],reverse=True)[:2]
            for i,v in zip(p.loop_indices,points):
                uv.data[i].uv=(.27+.18*(v[short]-min(q[short] for q in points))/max(spans[short],1e-8),
                                .035+.43*(v[long]-min(q[long] for q in points))/max(spans[long],1e-8))
    def stake(self,name,xy,z0,height,radius=.105,stage='upper'):
        if stage=='upper':
            n=sum(ord(c) for c in name)
            height+=((n*17)%9-4)*.022
            radius*=.92+((n*7)%5)*.035
        obj=super().stake(name,xy,z0,height,radius,stage);self.grain(obj);return obj
    def roof(self,name,xy,width,depth,eave,rise,material='tile',stage='upper'):
        if material!='thatch' or stage!='upper':return super().roof(name,xy,width,depth,eave,rise,material,stage)
        # Closed base retains exact roof support plane. Layered rectangular reed
        # courses replace ceramic crowns; every course rests on the same surface.
        base=b.hipped_tile_roof(name+'_reed_core',xy,width,depth,eave,rise,.15,self.mat)
        for loop in base.data.uv_layers.active.data:loop.uv.x+=.25;loop.uv.y+=.5
        self.add(base)
        def surface(x,y):
            sx=abs(x-xy[0])/(width/2);sy=abs(y-xy[1])/(depth/2)
            return eave+rise*(1-sy)*(1-.29*max(0,(sx-.73)/.27))+.12*max(0,(sy-.78)/.22)**2+.06*max(0,(sx-.77)/.23)*max(0,(sy-.75)/.25)
        nx=max(7,round(width*9));ny=max(3,round(depth*2.4))
        # A single watertight grid avoids coplanar internal panel walls and
        # records each reed course as a shallow connected lip in the roof skin.
        xs=[xy[0]-width/2+width*i/nx for i in range(nx+1)]
        ys=[]
        for side in (-1,1):
            for j in range(ny+1):
                y=side*depth*j/(2*ny)
                ys.extend([y] if j in (0,ny) else [y-.012,y+.012])
        ys=sorted(set(ys));nv=len(ys)
        verts=[]
        for lower in (False,True):
            for i,x in enumerate(xs):
                for yrel in ys:
                    y=xy[1]+yrel
                    phase=(abs(yrel)/(depth/(2*ny)))%1
                    course=.028*(1-phase)
                    fiber=.004*math.sin(i*2.37)+.003*math.sin(i*.71+yrel*2)
                    verts.append((x,y,surface(x,y)+(-.015 if lower else .065+course+fiber)))
        n=(nx+1)*nv;faces=[]
        for i in range(nx):
            for j in range(nv-1):
                q=i*nv+j;r=(i+1)*nv+j
                faces.extend([(q,r,r+1,q+1),(q+n,q+1+n,r+1+n,r+n)])
        edge=list(range(nv))+[i*nv+nv-1 for i in range(1,nx+1)]+[nx*nv+j for j in range(nv-2,-1,-1)]+[i*nv for i in range(nx-1,0,-1)]
        for a,c in zip(edge,edge[1:]+edge[:1]):faces.append((a,c,c+n,a+n))
        skin=self.add(b.mesh(name+'_connected_reed_courses',verts,faces,self.mat,'thatch'))
        for loop in skin.data.loops:
            v=skin.data.vertices[loop.vertex_index].co
            vbase=.53 if 'command_hall' in name else .76
            skin.data.uv_layers.active.data[loop.index].uv=(.77+.20*(v.x-xs[0])/width,vbase+.20*(v.y-(xy[1]-depth/2))/depth)
        self.contact(name+' base to carrying beam',eave-.15,eave-.15)

assert bpy.app.background and not bpy.data.filepath
b.guarded()
for p in (SOURCE,EXPORT,OUT):p.mkdir(parents=True,exist_ok=True)
inputs={str(BASE):sha(BASE),str(ROOT/'tools/castle_next/landmark_shared.py'):sha(ROOT/'tools/castle_next/landmark_shared.py')}
shutil.copy2(BASE,SOURCE/'baseline.blend')
with bpy.data.libraries.load(str(BASE),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith('Castle_'+NAME+'_')]
baseline=[o for o in dst.objects if o and o.type=='MESH']
for o in baseline:bpy.context.scene.collection.objects.link(o)
healthy=[o for o in baseline if o.name.endswith('_foundation') or o.name.endswith('_superstructure')]
baseline_count=sum(tri(o) for o in healthy)
b.preview(healthy,healthy[0].data.materials[0],OUT/'before')
preserve=[o for o in baseline if o.name.endswith('_ruins') or o.name.endswith('_heavy_damage')]
old_geometry={o.name:digest(o) for o in preserve}
for o in baseline:
    o.hide_render=True;o.hide_set(True)
    o.name='Baseline_'+o.name
# A quieter warm limestone field makes red masonry and dark timber legible.
b.PALETTES['imperial_citadel']=[(.35,.235,.18),(.215,.145,.09),(.32,.16,.105),(.42,.405,.34),(.27,.25,.17),(.09,.075,.055),(.91,.89,.82),(.37,.30,.19)]
b.PALETTES['resistance_hq']=[(.32,.21,.14),(.235,.18,.105),(.29,.16,.10),(.35,.34,.28),(.25,.235,.16),(.09,.08,.055),(.91,.89,.82),(.38,.315,.20)]
mat=b.atlas(NAME,SOURCE,EXPORT)
# More linear fibers and fewer wide knots; keep existing object-PBR sockets.
img=mat.node_tree.nodes['albedo'].image
import numpy as np
pixels=np.array(img.pixels[:],dtype=np.float32).reshape(1024,1024,4)
yy,xx=np.mgrid[:512,:256]
fiber=np.sin(xx*.82+np.sin(yy*.018))*.018+np.sin(xx*2.13+yy*.008)*.010
for tile,color in [(1,b.PALETTES[NAME][1]),(7,b.PALETTES[NAME][7])]:
    row,col=tile//4,tile%4
    region=pixels[row*512:(row+1)*512,col*256:(col+1)*256]
    for c in range(3):region[:,:,c]=color[c]+fiber+((np.sin(yy*.071)*.008-.065*yy/512) if tile==7 else 0)
img.pixels.foreach_set(pixels.ravel());img.filepath_raw=str(SOURCE/'albedo.png');img.save();img.pack();shutil.copy2(SOURCE/'albedo.png',EXPORT/'albedo.png')
m=Revised(NAME,mat,{'tile_columns_per_m':4.6,'tile_rows_per_m':4.6})
anatomy=b.citadel(m) if KEY=='citadel' else b.headquarters(m)
if KEY=='citadel':
    # Capped wall modules use the established inward-thickened return faces.
    for side in (-1,1):
        for y in (-4.14,4.14):
            cy=y-(.065 if y>0 else -.065)
            m.block(f'IC075_return_coping_{side}_{y}',(side*6.05,cy,1.24),(4.70,.39,.08),'stone')
            m.contact('return coping underside to return wall top',1.20,1.20)
            for dx in (-2.22,0,2.22):
                m.block(f'IC075_return_pier_{side}_{y}_{dx}',(side*6.05+dx,cy,.66),(.22,.39,1.12),'brick')
                m.contact('return pier bottom to terrace',.10,.11,.02)
    for o in m.foundation+m.upper:
        for v in o.data.vertices:v.co.z*=2
    for row in m.contacts:
        for k in ('plane_a','plane_b','gap','tolerance'):row[k]*=2
# Save anatomy as individually editable parts before the runtime partition join.
for o in m.ruins+m.damage:o.hide_render=True;o.hide_set(True)
for o in m.foundation+m.upper:o.hide_render=False;o.hide_set(False)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+'_components.blend')))
objects=[b.join_stage(m.foundation,'Castle_'+NAME+'_foundation',0),b.join_stage(m.upper,'Castle_'+NAME+'_superstructure',20)]
for suffix,stage in [('_ruins',0),('_heavy_damage',80)]:
    obj=next(o for o in preserve if o.name.endswith(suffix));obj.name='Castle_'+NAME+suffix
    assert digest(obj)==old_geometry[obj.name]
    obj.data.materials.clear();obj.data.materials.append(mat);obj['garrison_building_first_stage']=stage
    objects.append(obj)
assert sum(tri(o) for o in objects[:2])<=baseline_count
for o in objects:o['garrison_building_profile']='english-house'
checks=b.validate(objects)
preflight=b.require_valid(objects,bpy.context)
assert preflight['ok'],preflight
write(OUT/'preflight.json',preflight)
b.adopt_material(mat)
chunks,partition=b.split_healthy_export_mesh(objects[1])
for o in objects+chunks:o.hide_set(False)
manifest=b.export_building([objects[0],chunks[0],objects[2],objects[3],*chunks[1:]],EXPORT)
assert [p['first_stage'] for p in manifest['parts']]==[0,20,0,80,20,20,20]
for o in chunks:bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.context.scene.objects:
    if o.type=='MESH':o.hide_render=o not in objects[:2];o.hide_set(o not in objects[:2])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+'.blend')))
b.preview(objects[:2],mat,OUT/'after')
b.preview([objects[2]],mat,OUT/'ruins')
b.preview([objects[0],objects[3]],mat,OUT/'heavy_damage')
assert all(sha(p)==h for p,h in inputs.items())
write(OUT/'receipt.json',{'schema':'ccp.release075.castle-art/v1','name':NAME,'baseline_healthy_triangles':baseline_count,'healthy_triangles':sum(tri(o) for o in objects[:2]),'geometry':checks,'contacts':m.contacts,'clearances':m.clearances,'preserved_lifecycle_geometry':old_geometry,'baseline_inputs_unchanged':inputs,'export_partition':partition,'manifest':manifest,'export_sha256':{p.name:sha(p) for p in EXPORT.iterdir() if p.is_file()},'source_blend':str(SOURCE/(NAME+'.blend')),'editable_components':str(SOURCE/(NAME+'_components.blend')),'anatomy':anatomy,'native_cook':'not run','native_match':'not run','owner_colour':'root native attachment pilot; body remains object-PBR','budget':'does not exceed old healthy mesh; refreshed full visible official compound budget pending','review':'pending rendered inspection; no 9/10 claim'})
print('RELEASE075_CASTLE_ART_COMPLETE',KEY,flush=True)
