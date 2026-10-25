"""Read-only numeric blockout connection checks, executed through Blender MCP."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art')
def bound(name):
    o=bpy.data.objects['CCP070_'+name];vs=[o.matrix_world@v.co for v in o.data.vertices]
    return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
def gap(a,b,axis):return bound(b)[0][axis]-bound(a)[1][axis]
rows=[]
def check(name,actual,expected=0,tolerance=1e-5):
    rows.append({'name':name,'actual':actual,'expected':expected,'tolerance':tolerance,'passed':abs(actual-expected)<=tolerance})
check('Garden bridge north endpoint to pavilion plinth',gap('Garden_Pond_Bridge','Garden_Waterside_Pavilion_Plinth',1))
check('Garden frontpath to bridge south endpoint',gap('Garden_Front_Path','Garden_Pond_Bridge',1))
check('Garden bridge top vs pavilion platform top',bound('Garden_Pond_Bridge')[1][2]-bound('Garden_Waterside_Pavilion_Plinth')[1][2])
for side in ('West','Center','East'):
    check('Wonder '+side+' stair northface vs podium southface',gap('Wonder_'+side+'_Stair_10','Wonder_Kinh_Thien_Podium',1))
    check('Wonder '+side+' topstair top vs platform top',bound('Wonder_'+side+'_Stair_10')[1][2]-bound('Wonder_Kinh_Thien_Podium')[1][2])
podium=bound('Wonder_Kinh_Thien_Podium')
check('Wonder podium width/depth ratio vs 57:41.5',(podium[1][0]-podium[0][0])/(podium[1][1]-podium[0][1]),57/41.5,.003)
check('University lintel to roof overlap',gap('University_Gate_Lintel','University_Entrance_Gate_Roof',2),-.10,.0001)
uc=bpy.data.collections['CCP070_University_Additions_Blockout'];stock=[o for o in uc.objects if o.get('stock_geometry_unchanged')]
add=[o for o in uc.objects if not o.get('stock_geometry_unchanged')]
sb=[[min((o.matrix_world@v.co)[i] for o in stock for v in o.data.vertices) for i in range(3)],[max((o.matrix_world@v.co)[i] for o in stock for v in o.data.vertices) for i in range(3)]]
for i in range(2):
    lo=min((o.matrix_world@v.co)[i] for o in add for v in o.data.vertices)
    hi=max((o.matrix_world@v.co)[i] for o in add for v in o.data.vertices)
    rows.append({'name':'University additions inside stock '+('X','Y')[i]+' bounds','actual':[lo,hi],'stock_bounds':[sb[0][i],sb[1][i]],'passed':lo>=sb[0][i]-1e-5 and hi<=sb[1][i]+1e-5})
decoded=json.loads((OUT.parent/'inventory/university/decoded/012f675cd6b5f5cb1222/decoded-static.json').read_text())
max_delta=0
for i,g in enumerate(decoded['geometry']['groups']):
    o=bpy.data.objects['CCP070_University_STOCK_UNCHANGED_'+str(i)]
    assert len(o.data.vertices)==len(g['positions'])
    max_delta=max(max_delta,max(abs(o.data.vertices[j].co[k]-p[k]) for j,p in enumerate(g['positions']) for k in range(3)))
check('University stockvertex maximum position delta',max_delta,0,1e-6)
data={'schema':'ccp-070-blockout-contacts/v1','status':'passed' if all(r['passed'] for r in rows) else 'failed','checks':rows,'native_footprint_proof':False,'limits':['Design-space blockout contact checks only. Native inherited footprints, transforms, markers and lifecycle qualification remain required before integration.']}
(OUT/'contact-audit.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(data))
