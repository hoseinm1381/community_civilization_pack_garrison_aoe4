import sys,hashlib,json
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).parent));from buffalo_runner import *
report={}
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path))
 return {o.name:{'vertices':[tuple(v.co) for v in o.data.vertices],'polygons':[tuple(p.vertices) for p in o.data.polygons],'matrix':[list(r) for r in o.matrix_world],'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in o.data.vertices]} for o in bpy.context.scene.objects if o.type=='MESH'}
a=snapshot(ROOT/'art/authoring/release_079/buffalo/r3/model.blend');b=snapshot(ART/'buffalo/r1/model.blend')
for name in ('body_lod1','body_lod2','body_lod3'):
 av,bv=a[name],b[name];n=len(av['vertices']);assert av['vertices']==bv['vertices'][:n];assert av['polygons']==bv['polygons'][:len(av['polygons'])]
 delta=max(abs(v-ws.get(k,0)) for old,ws in zip(av['weights'],bv['weights']) for k,v in old.items());assert delta<1e-6
 report[name]={'old_vertices_exact':n,'old_faces_exact':len(av['polygons']),'max_weight_delta':delta,'added_vertices':len(bv['vertices'])-n}
a=snapshot(ROOT/'art/authoring/release_079/ministry/r1/ministry.blend');b=snapshot(ART/'ministry/r1/ministry.blend')
kept=[n for n in a if not n.startswith('079_Static_buffalo_')];assert all(a[n]==b[n] for n in kept)
clearances=[]
for i in range(3):
 vs=b['079_Static_buffalo_'+str(i+1)]['vertices'];pen=(-7.5,-1.25,-7.45,-.6) if i<2 else (1.25,7.5,-7.45,-4.52)
 gap=min(min(v[0] for v in vs)-pen[0],pen[1]-max(v[0] for v in vs),min(v[1] for v in vs)-pen[2],pen[3]-max(v[1] for v in vs));assert gap>.25;clearances.append(gap)
report['ministry']={'architecture_objects_exact':kept,'buffalo_count':3,'minimum_pen_clearances':clearances,'architecture_atlas_half_preserved':read(OUT/'art/ministry/r1/receipt.json')['architecture_atlas_half_unchanged']}
write(OUT/'source-preservation.json',report)
