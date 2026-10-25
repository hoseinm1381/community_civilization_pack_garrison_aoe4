import sys,random,math,shutil
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from buffalo_runner import *
from export_pilot import addon
from author_units import weights
from rig_contract import rig_text
from mesh_workshop import Workshop

guard();assert bpy.app.background
art=ART/'buffalo/r1';exp=EXPORT/'buffalo/r1';out=OUT/'art/buffalo/r1'
assert not art.exists()
for p in (art,exp,out):p.mkdir(parents=True)
source=ROOT/'art/authoring/release_079/buffalo/r3/model.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
contract=read(ROOT/'output/release_079/art/buffalo/r3/export.json')['donor_contract']
body=bpy.data.objects['body_lod1'];rig=next(m.object for m in body.modifiers if m.type=='ARMATURE')
lods=[bpy.data.objects['body_lod'+str(i)] for i in (1,2,3)]
original={o.name:len(o.data.vertices) for o in lods};proof=[]
# Fine, sparse hide strokes only in the skin atlas tile, preserving other materials.
for name in ('albedo','normal','roughness','metalness','pattern'):
 src=ROOT/f'art/exports/release_079/buffalo/r3/{name}.png'
 image=bpy.data.images.load(str(src),check_existing=False);w,h=image.size
 px=np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4);before=px.copy()
 if name in ('albedo','normal','roughness'):
  rng=random.Random(710)
  for _ in range(1700):
   x=rng.randrange(14,w//4-14);y=rng.randrange(14,h//4-22)
   for dy in range(rng.randrange(4,11)):
    xx=x+dy//4
    if name=='albedo':px[y+dy,xx,:3]*=.68
    elif name=='roughness':px[y+dy,xx,:3]=np.minimum(1,px[y+dy,xx,:3]+.09)
    else:px[y+dy,xx,0]=.46;px[y+dy,xx,1]=.52
 image.pixels.foreach_set(px.ravel());image.filepath_raw=str(exp/(name+'.png'));image.file_format='PNG';image.save();image.pack()
 for mat in bpy.data.materials:
  if not mat.use_nodes:continue
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE' and node.image and name in node.image.name.lower():node.image=image
 proof.append({'texture':name,'changed_values':int(np.count_nonzero(px!=before)),'outside_hide_tile_exact':bool(np.array_equal(px[h//4:],before[h//4:]) and np.array_equal(px[:h//4,w//4:],before[:h//4,w//4:]))})
# Root each short closed triangular tuft directly to a sampled hide vertex, inherit weights.
for level,obj in enumerate(lods,1):
 rng=random.Random(710);uv=obj.data.uv_layers.active
 allowed=set()
 for poly in obj.data.polygons:
  if all(0<=uv.data[i].uv.x<.25 and 0<=uv.data[i].uv.y<.25 for i in poly.loop_indices):allowed.update(poly.vertices)
 candidates=[v for v in obj.data.vertices if v.index in allowed and v.co.z>.65 and v.normal.z>-.15]
 samples=rng.sample(candidates,min(len(candidates),[140,70,28][level-1]));work=Workshop(rig,obj.data.materials[0]);vs=[];fs=[];ws=[];us=[]
 for v in samples:
  n=v.normal.normalized();t=n.cross(Vector((0,1,0))).normalized();base=v.co-n*.001
  length=rng.uniform(.012,.024);idx=len(vs);vs.extend([base+t*.006,base-t*.006,base+Vector((0,.009,0))+n*length,base+n*.003])
  fs.extend([(idx,idx+1,idx+2),(idx,idx+3,idx+1),(idx,idx+2,idx+3),(idx+1,idx+3,idx+2)])
  weight={obj.vertex_groups[g.group].name:g.weight for g in v.groups};ws.extend([weight]*4);us.extend([(.15,.15)]*4)
 tuft=work.mesh('0710_short_sparse_fur_lod'+str(level),vs,fs,us,ws,0)
 bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);tuft.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.join();weights(obj,contract,level)
 assert len(obj.data.vertices)==original[obj.name]+len(vs)
 if level>1:obj.hide_render=True;obj.hide_set(True)
rig.animation_data_clear();rig.data.pose_position='REST'
addon('unit_export').export_unit_model(rig,lods,exp/'model.fbx',addon('unit_export').skeleton_records(rig),three_lods=False)
(exp/'model.rig').write_text(rig_text(contract))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(art/'model.blend'))
write(out/'export.json',{'family':'buffalo','revision':'r1','source':str(art/'model.blend'),'source_sha256':sha(art/'model.blend'),'export':str(exp),'files':{p.name:sha(p) for p in exp.iterdir()},'lod_triangles':[len(o.data.polygons) for o in lods],'donor_contract':contract,'baseline_source':str(source),'baseline_sha256':sha(source),'existing_vertices_preserved':True,'tufts_per_lod':[140,70,28],'tuft_length_model_units':[.012,.024],'textures':proof,'native_acceptance':False})
