"""Read-only flag surface measurements in final source coordinate space."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3]
records={}
for key,xy,z in [('ministry',(-7.1,-8.9),.08),('pho_minh',(-2.95,-3.0),.21),('one_pillar',(-7.5,-6.0),.4)]:
 source=ROOT/'art/authoring/release_075'/key/'r3'/(key+'.blend')
 bpy.ops.wm.open_mainfile(filepath=str(source))
 hits=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or o.hide_render:continue
  tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
  hit,n,idx,d=tree.ray_cast(Vector((xy[0],xy[1],50)),Vector((0,0,-1)))
  if hit is not None:hits.append({'object':o.name,'point':list(hit),'normal':list(n)})
 top=max(hits,key=lambda h:h['point'][2]);assert abs(top['point'][2]-z)<.001,(key,top)
 records[key]={'source':str(source),'anchor_model_local':top['point'],'support':top,'no_roof_above':True,'export_fit':{'scale':[1,1,1],'translation':[0,0,0]},'one_pillar_scale_already_baked':key=='one_pillar','suggested_flag_visual_scale':2.0 if key=='one_pillar' else 1.5}
 (ROOT/'output/release_075/art'/key/'r3/flag-anchor.json').write_text(json.dumps(records[key],indent=2))
print(json.dumps(records,indent=2))
