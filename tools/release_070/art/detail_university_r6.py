"""Keep all scholarly joinery in the clear approved court, off native roofs."""
from pathlib import Path
import bpy,json
ROOT=Path('E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison')
ns={};p=ROOT/'tools/release_070/art/detail_core.py';exec(compile(p.read_text(),str(p),'exec'),ns)
SOURCE='CCP070_University_Detailed_Overlay_r5';DEST='CCP070_University_Detailed_Overlay_r6'
assert not bpy.data.collections.get(DEST)
c=bpy.data.collections.new(DEST);bpy.context.scene.collection.children.link(c)
parts={}
for o in bpy.data.collections[SOURCE].objects:
    n=o.copy();n.data=o.data.copy();n.name=DEST+'_garrison_part_'+o.name[-4:];c.objects.link(n);parts[int(o.name[-4:])]=n
helper=bpy.data.collections.new(DEST+'_Furniture_Recipe');helper.use_fake_user=True
batch=ns['Batch']('scholarly_joinery',helper,parts[6].data.materials[0],(15,-15,0))
for x in (.75,5.15):
    for dx in (-.23,.23):
        for dy in (-.36,.36):batch.box((x+dx,-4.18+dy,.435),(.10,.10,.45),'wood')
    batch.box((x,-4.18,.705),(.66,1.0,.09),'wood')
    batch.box((x,-4.18,.45),(.12,.8,.10),'wood')
    for y in (-4.48,-3.88):batch.box((x,y,.47),(.56,.08,.09),'wood')
# Low reading table and tied scroll cases. No fabricated readable calligraphy.
for x in (4.0,4.8):
    for y in (-2.1,-1.65):batch.box((x,y,.43),(.09,.09,.44),'wood')
batch.box((4.4,-1.875,.695),(1.05,.65,.09),'wood')
for x in (4.15,4.42,4.68):
    batch.cylinder((x,-1.90,.74),.065,.22,'clay',10)
    batch.box((x,-1.9,.84),(.15,.035,.035),'wood')
obj=batch.emit();old=parts[6].data;old.use_fake_user=True;parts[6].data=obj.data.copy()
for o in helper.objects:o.hide_render=True
for o in bpy.data.collections[SOURCE].objects:o.hide_set(True)
for i,o in parts.items():o.hide_set(i in (2,3))
report={'source':SOURCE,'revision':DEST,'changed_parts':[6],'reason':'Remove stock roof intersections; all additional joinery is now court furniture seated on paving top Z=.21','furniture_min_z':min(v.co.z for v in parts[6].data.vertices),'furniture_max_z':max(v.co.z for v in parts[6].data.vertices),'footprint_or_native_stock_change':False}
out=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail/university-r6-courtyard-furniture.json');out.write_text(json.dumps(report,indent=2));print(report)
