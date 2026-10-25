"""Immutable release075 Garden/Foundry source runner. Background Blender only."""
import sys,json,hashlib,math,shutil,re
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com'))
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material
ns={};exec((ROOT/'tools/release_070/art/detail_core.py').read_text(),ns)
Batch=ns['Batch']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(l.uv) for l in o.data.uv_layers.active.data])).encode()).hexdigest()
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def components(obj):
 m=obj.data;parent=list(range(len(m.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for e in m.edges:
  a,c=map(find,e.vertices);parent[a]=c
 groups={}
 for v in m.vertices:groups.setdefault(find(v.index),[]).append(v.index)
 faces={}
 for p in m.polygons:faces.setdefault(find(p.vertices[0]),[]).append(p.index)
 result=[]
 for key,ids in groups.items():
  points=[m.vertices[i].co for i in ids];lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
  result.append({'ids':ids,'faces':faces.get(key,[]),'lo':lo,'hi':hi,'center':(lo+hi)/2,'span':hi-lo})
 return result
def discard(obj,ids):
 bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in sorted(set(ids))],context='VERTS');bm.to_mesh(obj.data);bm.free()
def append(obj,batch):
 new=batch.emit()
 for o in bpy.context.selected_objects:o.select_set(False)
 obj.hide_set(False);new.hide_set(False);obj.select_set(True);new.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
def category(obj,p):
 uv=obj.data.uv_layers.active.data;u=sum(uv[i].uv.x for i in p.loop_indices)/len(p.loop_indices);v=sum(uv[i].uv.y for i in p.loop_indices)/len(p.loop_indices)
 return min(3,int(u*4))+4*min(1,int(v*2))
def remap_planar(obj,faceids,cat,range_u=(.04,.96),range_v=(.04,.96),grain=False):
 m=obj.data;uv=m.uv_layers.active.data
 for fi in faceids:
  p=m.polygons[fi];pts=[m.vertices[m.loops[i].vertex_index].co for i in p.loop_indices]
  spans=[max(v[k] for v in pts)-min(v[k] for v in pts) for k in range(3)];axes=sorted(range(3),key=lambda k:spans[k],reverse=True)[:2]
  if grain:axes.reverse()
  for li,v in zip(p.loop_indices,pts):
   values=[(v[k]-min(q[k] for q in pts))/max(spans[k],1e-8) for k in axes]
   uv[li].uv=((cat%4+range_u[0]+(range_u[1]-range_u[0])*values[0])/4,(cat//4+range_v[0]+(range_v[1]-range_v[0])*values[1])/2)
def normals(obj):
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
def main():
 args=sys.argv[sys.argv.index('--')+1:];family,rev=args[:2]
 assert family in ('garden','foundry') and re.fullmatch('r[0-9]+',rev)
 assert bpy.app.background and not bpy.data.filepath
 check_storage(ROOT,configuration(ROOT))
 out=ROOT/'output/release_075/art'/family/rev;sourceout=ROOT/'art/authoring/release_075'/family/rev;exports=ROOT/'art/exports/release_075'/family/rev
 if any(p.exists() for p in (out,sourceout,exports)):raise FileExistsError('Immutable revision exists; choose next revision')
 for p in (out,sourceout,exports):p.mkdir(parents=True)
 src=ROOT/('art/authoring/release_075/garden/planting-r2.blend' if family=='garden' else 'art/authoring/buildings_070/architecture-final-r4.blend')
 name='CCP075_Garden_Planting_r2' if family=='garden' else 'CCP070_Trung_Foundries_Detailed_r3'
 original_sha=sha(src)
 with bpy.data.libraries.load(str(src),link=False) as (a,c):c.collections=[name]
 col=c.collections[0];bpy.context.scene.collection.children.link(col);col.name='CCP075_'+family+'_'+rev
 for o in bpy.context.scene.objects:
  if o not in list(col.all_objects):o.hide_render=True;o.hide_set(True)
 parts={int(o.name[-4:]):o for o in col.objects if o.type=='MESH'};assert set(parts)==set(range(7))
 before={i:digest(o) for i,o in parts.items()};mat=parts[0].data.materials[0]
 # Library images can retain stale relative paths; use the retained export
 # channel when no pixel data was packed, before recipe pixel edits.
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and not node.image.has_data:
   image=node.image
   channel=next(k for k in ('albedo','normal','roughness','metalness') if k in (image.name+image.filepath).lower())
   retained=ROOT/'art/exports/buildings_070'/('garden-r5' if family=='garden' else 'foundry')/(channel+'.png')
   replacement=bpy.data.images.load(str(retained),check_existing=False)
   replacement.colorspace_settings.name=image.colorspace_settings.name
   assert len(replacement.pixels)>0
   node.image=replacement
 # Capture component inventory before editing, including actual local joins.
 inventory={i:[{'vertices':len(c['ids']),'faces':len(c['faces']),'lo':list(c['lo']),'hi':list(c['hi'])} for c in components(o)] for i,o in parts.items()}
 write(out/'before-components.json',inventory)
 import recipes
 report=recipes.garden(parts,col,mat) if family=='garden' else recipes.foundry(parts,col,mat)
 after={i:digest(o) for i,o in parts.items()}
 assert before[2]==after[2] and before[3]==after[3],'Lifecycle geometry or UV drift'
 # Material is shared by lifecycle states; keep the same four-channel PBR route.
 for image in {n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}:
  if image.source=='FILE':
   channel=next((k for k in ('albedo','normal','roughness','metalness') if k in image.name.lower() or k in image.filepath.lower()),None)
   if channel:
    image.filepath_raw=str(sourceout/(channel+'.png'));image.file_format='PNG';image.save();image.pack();shutil.copy2(sourceout/(channel+'.png'),exports/(channel+'.png'))
 for i,o in parts.items():
  o['garrison_building_first_stage']=(0,20,0,80,20,20,20)[i];o['garrison_building_profile']='english-house'
  o.hide_render=i in (2,3);o.hide_set(i in (2,3));o.data.calc_loop_triangles()
 tris={i:len(o.data.loop_triangles) for i,o in parts.items()};healthy=sum(tris[i] for i in (0,1,4,5,6))
 assert healthy<(59808 if family=='garden' else 59808),(family,healthy)
 preflight=require_valid(list(parts.values()),bpy.context);assert preflight['ok'],preflight
 write(out/'preflight.json',preflight)
 adopt_material(mat)
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all();target=sourceout/(family+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(target))
 fit=json.loads((ROOT/'art/exports/buildings_070'/('garden-r5' if family=='garden' else 'foundry')/'source-receipt.json').read_text())
 if family=='garden':
  f=fit['model_local_fit'];scale=(f['xy_scale'],f['xy_scale'],f['z_scale']);shift=(0,f['y_shift'],f['z_shift'])
 else:
  f=fit['fit'];scale=(f['xy_scale'],f['xy_scale'],f['z_scale']);shift=f['shift']
 exportparts=dict(parts);partition=None
 if max(len(o.data.loops) for o in parts.values())>=60000:
  # All four healthy upper pieces share stage20 and native selectors. Balance
  # whole connected components on export clones without cutting any face/UV.
  sys.path.insert(0,str(ROOT/'tools/castle_next'))
  from landmark_shared import split_healthy_export_mesh
  for o in bpy.context.selected_objects:o.select_set(False)
  temporary=[]
  for i in (1,4,5,6):
   t=parts[i].copy();t.data=parts[i].data.copy();bpy.context.scene.collection.objects.link(t);t.hide_set(False);t.select_set(True);temporary.append(t)
  bpy.context.view_layer.objects.active=temporary[0];bpy.ops.object.join();combined=temporary[0]
  chunks,partition=split_healthy_export_mesh(combined)
  for i,c in zip((1,4,5,6),chunks):exportparts[i]=c
  assert sum(sum(len(p.vertices)-2 for p in c.data.polygons) for c in chunks)==sum(tris[i] for i in (1,4,5,6))
 assert max(len(o.data.loops) for o in exportparts.values())<60000
 for o in bpy.context.selected_objects:o.select_set(False)
 clones=[]
 for i,o in sorted(exportparts.items()):
  clone=o.copy();clone.data=o.data.copy();bpy.context.scene.collection.objects.link(clone);clone.name=f'garrison_part_{i:04}';assert clone.name==f'garrison_part_{i:04}'
  clone.location=(0,0,0);clone.rotation_euler=(0,0,0);clone.scale=(1,1,1);clone.hide_set(False);clone.hide_render=False
  for v in clone.data.vertices:v.co=tuple(v.co[k]*scale[k]+shift[k] for k in range(3))
  for loop in clone.data.uv_layers.active.data:loop.uv.y=1-loop.uv.y
  clone.select_set(True);clones.append(clone)
 bpy.context.view_layer.objects.active=clones[0]
 bpy.ops.export_scene.fbx(filepath=str(exports/'model.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',use_custom_props=False)
 manifest={'schema':'garrison.building-source/v1','profile':'english-house','parts':[{'name':f'garrison_part_{i:04}','first_stage':(0,20,0,80,20,20,20)[i]} for i in range(7)],'material_name':mat.name,'textures':{k:k+'.png' for k in ('albedo','normal','roughness','metalness')}}
 write(exports/'building.json',manifest)
 assert sha(src)==original_sha
 report.update({'source':str(src),'source_sha256_unchanged':original_sha,'target':str(target),'exports':str(exports),'healthy_triangles':healthy,'triangles_by_part':tris,'before_mesh_hashes':before,'after_mesh_hashes':after,'fit_scale':scale,'fit_shift':shift,'lifecycle_exact':[2,3],'healthy_export_partition':partition,'native_cook':'not run','native_game':'not run','export_sha256':{p.name:sha(p) for p in exports.iterdir()}})
 write(out/'receipt.json',report);print(json.dumps(report),flush=True)
if __name__=='__main__':main()
