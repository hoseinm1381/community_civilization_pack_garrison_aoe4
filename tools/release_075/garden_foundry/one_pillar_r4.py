"""Bounded One Pillar r4 contact repair; inherited scale remains baked."""
import bpy,bmesh,sys,json,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from runner import components,discard,digest
from recipes import trim_box_component
sys.path.insert(0,str(ROOT/'tools/release_020'))
from model_ministry_farm_hideout_runner import mesh,join_stage,export_building
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material
from workspace_support import configuration,check_storage
check_storage(ROOT,configuration(ROOT))
assert bpy.app.background
source=ROOT/'art/authoring/release_075/one_pillar/r3/one_pillar.blend'
out=ROOT/'output/release_075/art/one_pillar/r4';dest=ROOT/'art/authoring/release_075/one_pillar/r4';exports=ROOT/'art/exports/release_075/one_pillar/r4'
assert not any(p.exists() for p in (out,dest,exports))
for p in (out,dest,exports):p.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];foundation=next(o for o in objects if 'foundation' in o.name);upper=next(o for o in objects if 'superstructure' in o.name);ruins=next(o for o in objects if 'ruins' in o.name)
original={o.name:digest(o) for o in objects};mat=upper.data.materials[0];changes=[];contacts=[];adds=[]
for c in components(foundation):
 if len(c['ids'])==8 and abs(c['hi'].z-1.125)<.001 and c['span'].x>10 and c['span'].y<.6:
  trim_box_component(foundation,c,0,-2.275*2.3,2.275*2.3);changes.append({'pond_return_old_bounds':[list(c['lo']),list(c['hi'])],'new_x_limits':[-2.275*2.3,2.275*2.3]});contacts.append({'interface':'pond rim horizontal to vertical inner face','signed_gap':0})
assert len(changes)==2,changes
roof=next(c for c in components(upper) if len(c['ids'])==162 and c['lo'].z>10 and c['hi'].z>13)
ids=set(roof['ids']);tree=BVHTree.FromPolygons([v.co for v in upper.data.vertices],[tuple(p.vertices) for p in upper.data.polygons if all(i in ids for i in p.vertices)])
ridges=[c for c in components(upper) if len(c['ids'])==8 and abs(c['span'].x-.18*2.3)<.003 and abs(c['span'].y-.12*2.3)<.003 and c['lo'].z>12]
assert len(ridges)==18,len(ridges)
def add(name,v,f,t):
 o=mesh('CCP075_one_pillar_r4_'+name,v,f,mat,t);o['garrison_building_first_stage']=20;o['garrison_building_profile']='english-house';adds.append(o);return o
for j,c in enumerate(ridges):
 x0=c['lo'].x;x1=c['hi'].x;cy=c['center'].y;r=.18
 vertices=[]
 for x in (x0,x1):
  for k in range(9):
   a=k*math.pi/8;y=cy-r*math.cos(a)
   p,_,_,_=tree.ray_cast(Vector((x,y,30)),Vector((0,0,-1)));assert p is not None
   vertices.append((x,y,p.z-.015+r*math.sin(a)))
  for y in (cy+r,cy-r):
   p,_,_,_=tree.ray_cast(Vector((x,y,30)),Vector((0,0,-1)));vertices.append((x,y,p.z-.045))
 n=11;faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 add('seated_ridge_cap_'+str(j),vertices,faces,'tile')
discard(upper,[v for c in ridges for v in c['ids']]);changes.append({'replaced_oversized_ridge_blocks':len(ridges),'new_profile':'low closed arched caps sampled from original roof'});contacts.append({'interface':'ridge cap to roof','intentional_insertion':.015})
# Three inherited cone buds become open, low lotus blooms on exact stem tops.
buds=[c for c in components(upper) if len(c['ids'])==32 and abs(c['lo'].z-1)<.002 and abs(c['hi'].z-1.575)<.002]
assert len(buds)==3,len(buds)
for j,c in enumerate(buds):
 cx,cy=c['center'].xy
 for k in range(7):
  a=k*math.tau/7;d=Vector((math.cos(a),math.sin(a),0));s=Vector((-math.sin(a),math.cos(a),0));base=Vector((cx,cy,1.05));mid=base+d*.17+Vector((0,0,.10));tip=base+d*.33+Vector((0,0,.21))
  v=[base,mid+s*.115,tip,mid-s*.115,mid+Vector((0,0,.055)),mid-Vector((0,0,.035))];f=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
  add('lotus_'+str(j)+'_petal_'+str(k),v,f,'plaster')
discard(upper,[v for c in buds for v in c['ids']]);contacts.append({'interface':'lotus flower to original stem','flower_base':1.05,'stem_top':1.075,'overlap':.025})
for o in [foundation,upper]+adds:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
assert digest(ruins)==original[ruins.name]
for o in objects:
 if o not in (foundation,upper):assert digest(o)==original[o.name]
for label in ('albedo','normal','roughness','metalness'):
 shutil.copy2(source.parent/(label+'.png'),dest/(label+'.png'));shutil.copy2(source.parent/(label+'.png'),exports/(label+'.png'))
for im in bpy.data.images:
 if im.source=='FILE':
  label=next((k for k in ('albedo','normal','roughness','metalness') if k in im.name.lower()),None)
  if label:
   if im.packed_file:im.unpack(method='REMOVE')
   im.filepath=str(dest/(label+'.png'));im.reload();im.pack()
pre=require_valid(objects+adds,bpy.context);assert pre['ok'] and not pre['findings'],pre
adopt_material(mat);bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all();target=dest/'one_pillar.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target))
# Evidence uses all visible source parts, not an assumed game draw-call count.
metrics=[]
for o in objects+adds:
 o.data.calc_loop_triangles();metrics.append({'object':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'material_slots':len(o.material_slots),'healthy_visible':not o.hide_render})
(out/'metrics.json').write_text(json.dumps({'parts':metrics,'healthy_materials':[mat.name],'runtime_draw_calls':'unmeasured'},indent=2))
hits=[]
for o in objects+adds:
 if o.hide_render:continue
 t=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]);p,n,_,_=t.ray_cast(Vector((-7.5,-6,50)),Vector((0,0,-1)))
 if p is not None:hits.append({'object':o.name,'point':list(p),'normal':list(n)})
top=max(hits,key=lambda h:h['point'][2]);assert abs(top['point'][2]-.4)<.001
(out/'flag-anchor.json').write_text(json.dumps({'source':str(target),'support':top,'anchor_model_local':top['point'],'no_roof_above':True,'export_fit':{'scale':[1,1,1],'translation':[0,0,0]},'one_pillar_scale_already_baked':True},indent=2))
clones=[]
for o in objects+adds:
 c=o.copy();c.data=o.data.copy();bpy.context.scene.collection.objects.link(c);c.hide_set(False);clones.append(c)
fc=clones[objects.index(foundation)];rc=clones[objects.index(ruins)];uc=join_stage([c for c in clones if c not in (fc,rc)],'CCP075_export_upper',20)
export_objs=[fc,uc,rc];checks=[]
for o in export_objs:
 bm=bmesh.new();bm.from_mesh(o.data);row={'name':o.name,'vertices':len(bm.verts),'triangles':sum(len(f.verts)-2 for f in bm.faces),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-9 for f in bm.faces)};bm.free();assert not row['non_manifold_edges'] and not row['degenerate_faces'],row;checks.append(row)
pre=require_valid(export_objs,bpy.context);assert pre['ok'] and not pre['findings'],pre
manifest=export_building(export_objs,exports);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'asset':'one_pillar','revision':'r4','source':str(target),'source_sha256':sha(target),'source_previous':str(source),'targeted_edits':changes,'contacts':contacts,'ruins_preserved':True,'existing_r3_additions_preserved':True,'preflight':pre,'geometry':checks,'building':manifest,'healthy_triangles':sum(r['triangles'] for r in checks[:2]),'exports':{p.name:sha(p) for p in exports.iterdir()},'status':'source_review_required','native':'not tested'}
(out/'receipt.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
