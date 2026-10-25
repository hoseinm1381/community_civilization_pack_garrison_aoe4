"""Read-only vertical ray map of stable donor/awning roof overlap."""
import bpy
import json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
row=json.loads((ROOT/'output/release_040/buildings/details/stable/age02/source.json').read_text())
model=next(r for r in json.loads((ROOT/'output/release_040/buildings/model-validation.json').read_text())['models'] if r['family']=='stable' and r['age']==2)
bpy.ops.wm.open_mainfile(filepath=model['editable_blend'])
donor=[o for o in bpy.context.scene.objects if o.type=='MESH']
with bpy.data.libraries.load(row['source_blend'],link=False) as (src,dst):
    dst.objects=[name for name in src.objects if name.endswith('_detail_structure')]
detail=dst.objects[0]
assert detail
bpy.context.scene.collection.objects.link(detail)
def top(objects,x,y):
    vals=[]
    for obj in objects:
        hit,point,normal,face=obj.ray_cast(Vector((x,y,100)),Vector((0,0,-1)))
        if hit: vals.append((float(point.z),obj.name))
    return max(vals) if vals else None
lines=[]
for y in (-1.95,-1.80,-1.65,-1.50,-1.35,-1.20,-1.05):
    for x in (-3.1,-2.8,-2.4,-2.0,-1.5,-1.0,0,1,2,2.8,3.1):
        d=top(donor,x,y);a=top([detail],x,y)
        if d and a:lines.append({'x':x,'y':y,'donor_top':d[0],'detail_top':a[0],'delta_donor_minus_detail':d[0]-a[0],'donor_object':d[1]})
path=ROOT/'output/release_040/buildings/details/stable/age02/roof-intersection-probe.json'
path.write_text(json.dumps({'donor_objects':[o.name for o in donor],'samples':lines},indent=2)+'\n')
print('STABLE_ROOF_PROBE',len(lines),'higher_stock',sum(r['delta_donor_minus_detail']>0 for r in lines))
