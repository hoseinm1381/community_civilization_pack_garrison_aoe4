"""MCP-only healthy/damage/ruin views and numeric source qualification."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector
ROOT=Path('E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison')
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
STATES={'healthy':(0,1,4,5,6),'heavy_damage':(0,3),'ruins':(2,)}
def review(collection_name,anchor,slug):
    base=ROOT/'tools/release_070/art';ns={};p=base/'blockout_runner.py';exec(compile(p.read_text(),str(p),'exec'),ns)
    ns['OFFSETS'][collection_name]=anchor;c=bpy.data.collections[collection_name]
    target=OUT/slug;target.mkdir(parents=True,exist_ok=True)
    parts={int(o.name[-4:]):o for o in c.objects if o.type=='MESH' and 'garrison_part_' in o.name}
    assert set(parts)==set(range(7)),list(parts)
    audit=[]
    for i,o in parts.items():
        uv=o.data.uv_layers.active
        row={'part':i,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),
             'finite':all(math.isfinite(x) for v in o.data.vertices for x in v.co),
             'uv_finite':bool(uv) and all(math.isfinite(x) for u in uv.data for x in u.uv),
             'uv_inside_atlas':bool(uv) and all(-1e-6<=x<=1+1e-6 for u in uv.data for x in u.uv),
             'zero_area_faces':sum(p.area<1e-12 for p in o.data.polygons),'mesh_users':o.data.users}
        assert row['finite'] and row['uv_finite'] and row['uv_inside_atlas'] and row['mesh_users']==1,row
        audit.append(row)
    for state,indices in STATES.items():
        directions=('iso','front','rear','left','right','top','bottom') if state=='healthy' else ('iso','front','top')
        for direction in directions:
            ns['view'](collection_name,direction,color='VERTEX')
            for i,o in parts.items():o.hide_set(i not in indices);o.hide_render=i not in indices
            ns['scene'].render.filepath=str(target/(state+'-'+direction+'.png'))
            for area in bpy.context.screen.areas:
                if area.type=='VIEW_3D':
                    region=next(r for r in area.regions if r.type=='WINDOW')
                    with bpy.context.temp_override(area=area,region=region):bpy.ops.render.opengl(write_still=True,view_context=True)
                    break
    ns['view'](collection_name,'iso',color='VERTEX')
    for i,o in parts.items():o.hide_set(i not in STATES['healthy']);o.hide_render=i not in STATES['healthy']
    data={'schema':'ccp-070-detailed-source-review/v1','collection':collection_name,'parts':audit,
        'states':{k:{'parts':v,'triangles':sum(r['triangles'] for r in audit if r['part'] in v)} for k,v in STATES.items()},
        'source_only':True,'native_export':False,'native_cook':False,'native_render':False}
    (target/'audit.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data))
