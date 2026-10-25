import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3]
for family,xy in [('garden',(5.7,-8.3)),('foundry',(-9,-8.6))]:
 source=ROOT/'art/authoring/release_075'/family/('r5' if family=='foundry' else 'r4')/(family+'.blend')
 bpy.ops.wm.open_mainfile(filepath=str(source))
 receipt=json.loads((ROOT/'output/release_075/art'/family/('r5/receipt.json' if family=='foundry' else 'r4/receipt.json')).read_text())
 col=next(c for c in bpy.data.collections if c.name.startswith('CCP075_'+family))
 hits=[];metrics=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles();metrics.append({'object':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'material_slots':len(o.material_slots),'healthy_visible':not o.hide_render})
  if o.hide_render:continue
  tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
  hit,n,i,d=tree.ray_cast(Vector((*xy,50)),Vector((0,0,-1)))
  if hit is not None:hits.append({'object':o.name,'point':list(hit),'normal':list(n)})
 top=max(hits,key=lambda h:h['point'][2]);assert top['point'][2]<.25,top
 scale=receipt['fit_scale'];shift=receipt['fit_shift']
 record={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'support':top,'anchor_source_local':top['point'],'anchor_model_local':[top['point'][i]*scale[i]+shift[i] for i in range(3)],'export_fit':{'scale':scale,'translation':shift},'no_roof_above':True,'all_hits':hits,'suggested_flag_visual_scale':1.5}
 out=ROOT/'output/release_075/art'/family/('r5' if family=='foundry' else 'r4')
 (out/'flag-anchor.json').write_text(json.dumps(record,indent=2))
 (out/'metrics.json').write_text(json.dumps({'parts':metrics,'healthy_materials':sorted({m.name for o in col.all_objects if o.type=='MESH' and not o.hide_render for m in o.data.materials}),'runtime_draw_calls':'unmeasured'},indent=2))
 print(json.dumps(record))

