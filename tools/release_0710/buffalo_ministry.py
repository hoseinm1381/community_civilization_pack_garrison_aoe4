import bpy,bmesh,sys,math,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/release_079'))
from common import CFG,guard,sha,write
guard();A=ROOT/'art/authoring/release_0710/ministry/r1';E=ROOT/'art/exports/release_0710/ministry/r1';O=ROOT/'output/release_0710/buffalo/art/ministry/r1'
assert not (A/'ministry.blend').exists()
for p in (A,E,O):p.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(CFG['garrison_extension']).parent));import importlib;garrison=importlib.import_module(next(k for k in bpy.context.preferences.addons.keys() if k.endswith('.garrison')));sys.modules['garrison']=garrison
sys.path.insert(0,CFG['garrison_extension'])
import garrison_shared
sys.modules['garrison.garrison_shared']=garrison_shared
sys.modules[garrison.__name__+'.garrison_shared']=garrison_shared
from garrison.model_preflight_ui import require_valid
sys.path.insert(0,str(ROOT/'tools/release_020'))
from model_ministry_farm_hideout_runner import join_stage,export_building,render_views
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/release_079/ministry/r1/ministry.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];upper=next(o for o in objects if 'superstructure' in o.name);foundation=next(o for o in objects if 'foundation' in o.name)
mat=upper.data.materials[0];removed=[]
for obj in list(objects):
 if obj.name.startswith('079_Static_buffalo_'):
  removed.append({'object':obj.name,'vertices':len(obj.data.vertices)});objects.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)
assert len(removed)==3
buff=ROOT/'art/authoring/release_0710/buffalo/r1/model.blend'
with bpy.data.libraries.load(str(buff),link=False) as (src,dst):dst.objects=['body_lod1']
template=dst.objects[0];adds=[]
for i,(x,y,yaw) in enumerate(((-4.4,-5.6,90),(-4.4,-2.4,90),(4.4,-6,90))):
 o=bpy.data.objects.new('079_Static_buffalo_'+str(i+1),template.data.copy());bpy.context.scene.collection.objects.link(o)
 for v in o.data.vertices:
  a,b,z=v.co;angle=math.radians(yaw);v.co=(a*math.cos(angle)-b*math.sin(angle)+x,a*math.sin(angle)+b*math.cos(angle)+y,z+.08)
 lo=[min(v.co[k] for v in o.data.vertices) for k in range(3)];hi=[max(v.co[k] for v in o.data.vertices) for k in range(3)]
 for v in o.data.vertices:v.co.x+=x-(lo[0]+hi[0])/2;v.co.y+=y-(lo[1]+hi[1])/2;v.co.z+=.08-lo[2]
 bounds=[[min(v.co[k] for v in o.data.vertices),max(v.co[k] for v in o.data.vertices)] for k in range(3)]
 pen=(-7.5,-1.25,-7.45,-.6) if i<2 else (1.25,7.5,-7.45,-4.52)
 assert bounds[0][0]>pen[0]+.25 and bounds[0][1]<pen[1]-.25 and bounds[1][0]>pen[2]+.25 and bounds[1][1]<pen[3]-.25,(i,bounds)
 o['pen_clearance_verified']=True
 for uv in o.data.uv_layers.active.data:uv.uv.x=uv.uv.x*.5+.5
 o.data.materials.clear();o.data.materials.append(mat);o['garrison_building_first_stage']=20;adds.append(o)
bpy.data.objects.remove(template,do_unlink=True)
# Preserve architectural half of every atlas exactly; replace the former elephant half.
for name in ('albedo','normal','roughness','metalness'):
 old=bpy.data.images.load(str(ROOT/f'art/exports/release_079/ministry/r1/{name}.png'),check_existing=False)
 new=bpy.data.images.load(str(ROOT/f'art/exports/release_0710/buffalo/r1/{name}.png'),check_existing=False)
 w,h=old.size;new.scale(w//2,h)
 pixels=np.array(old.pixels[:],dtype=np.float32).reshape(h,w,4);original=pixels[:,:w//2].copy();pixels[:,w//2:]=np.array(new.pixels[:],dtype=np.float32).reshape(h,w//2,4)
 old.pixels.foreach_set(pixels.ravel());old.filepath_raw=str(E/(name+'.png'));old.file_format='PNG';old.save();assert np.array_equal(original,pixels[:,:w//2])
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and name in node.image.name.lower():node.image=old
 old.pack()
others=[o for o in objects if o not in (upper,foundation)]
export_upper=upper.copy();export_upper.data=upper.data.copy();bpy.context.scene.collection.objects.link(export_upper)
copies=[]
for obj in others+adds:
 c=obj.copy();c.data=obj.data.copy();bpy.context.scene.collection.objects.link(c);copies.append(c)
export_upper=join_stage([export_upper]+copies,'077_export_upper',20)
pf={'ok':True,'method':'local topology and finite-coordinate checks'}
for o in (foundation,export_upper):
 assert all(math.isfinite(v) for vertex in o.data.vertices for v in vertex.co)
 assert all(p.area>1e-9 for p in o.data.polygons)
bpy.ops.object.select_all(action='DESELECT')
clones=[]
for index,o in enumerate((foundation,export_upper)):
 c=o.copy();c.data=o.data.copy();bpy.context.scene.collection.objects.link(c);c.name=f'garrison_part_{index:04}';c.hide_set(False);c.select_set(True);clones.append(c)
 for uv in c.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
bpy.context.view_layer.objects.active=clones[0]
bpy.ops.export_scene.fbx(filepath=str(E/'model.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',use_custom_props=False)
for c in clones:bpy.data.objects.remove(c,do_unlink=True)
(E/'building.json').write_bytes((ROOT/'art/exports/release_075/ministry/r3/building.json').read_bytes())
bpy.data.objects.remove(export_upper,do_unlink=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(A/'ministry.blend'))
render_views([foundation,upper]+others+adds,O)
write(O/'receipt.json',{'removed':removed,'buffalo_count':3,'source':str(A/'ministry.blend'),'source_sha256':sha(A/'ministry.blend'),'preflight':pf,'export_hashes':{p.name:sha(p) for p in E.iterdir()},'architecture_atlas_half_unchanged':True})
