import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
report={}
for family,rev in read(RECIPES/'unit-selection.json').items():
 bpy.ops.wm.open_mainfile(filepath=str(ART/family/rev/'model.blend'))
 report[family]={}
 for lod in (1,2,3):
  mesh=bpy.data.objects['body_lod'+str(lod)].data;mesh.calc_loop_triangles()
  areas=sorted(t.area for t in mesh.loop_triangles)
  report[family][str(lod)]={'triangles':len(areas),'smallest':areas[:8],'below_1e_10':sum(a<1e-10 for a in areas)}
write(OUT/'diagnosis/production-triangle-areas.json',report)
print(json.dumps(report))
