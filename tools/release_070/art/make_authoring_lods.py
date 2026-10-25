"""Editable lower-detail alternatives; native distance activation unqualified.

The current supported building source emits one native LOD, as do the measured
stock owners. These derived collections remain authoring inputs only and are
not silently wired into selectors or represented as camera-driven game LODs.
"""
from pathlib import Path
import bpy,json,math
ROOT=Path('E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison')
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
source={'garden':'CCP070_Imperial_Garden_Detailed_r4','foundry':'CCP070_Trung_Foundries_Detailed_r3','wonder':'CCP070_Kinh_Thien_Detailed_r3','university':'CCP070_University_Detailed_Overlay_r6'}
if globals().get('ONLY_UNIVERSITY'):source={'university':source['university']}
rows=[]
for kind,name in source.items():
    for level,ratio in ((1,.55),(2,.28)):
        label=name+'_LOD%d_AUTHORING_ONLY'%level
        assert not bpy.data.collections.get(label)
        coll=bpy.data.collections.new(label);bpy.context.scene.collection.children.link(coll)
        part_rows=[]
        for old in bpy.data.collections[name].objects:
            o=old.copy();o.data=old.data.copy();o.name=label+'_part_'+old.name[-4:];coll.objects.link(o);o.hide_set(False)
            before=sum(len(p.vertices)-2 for p in o.data.polygons)
            bpy.context.view_layer.objects.active=o
            mod=o.modifiers.new('Authoring_distance_simplification','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
            with bpy.context.temp_override(object=o,active_object=o):bpy.ops.object.modifier_apply(modifier=mod.name)
            after=sum(len(p.vertices)-2 for p in o.data.polygons)
            assert after>0 and after<before
            assert all(math.isfinite(x) for v in o.data.vertices for x in v.co)
            assert all(p.area>1e-12 for p in o.data.polygons)
            assert o.data.uv_layers
            o.hide_set(True);o.hide_render=True
            part_rows.append({'part':int(old.name[-4:]),'source_triangles':before,'triangles':after})
        rows.append({'kind':kind,'collection':label,'level':level,'ratio':ratio,'parts':part_rows,'healthy_triangles':sum(p['triangles'] for p in part_rows if p['part'] in (0,1,4,5,6))})
result={'schema':'ccp-070-authoring-lod-alternatives/v1','status':'finite_nonzero_uv_source_alternatives','native_camera_distance_activation':False,'native_export_cook':False,'stock_university_body_included':False,'alternatives':rows}
(OUT/('university-r6-authoring-lods.json' if globals().get('ONLY_UNIVERSITY') else 'authoring-lods.json')).write_text(json.dumps(result,indent=2));print({r['collection']:r['healthy_triangles'] for r in rows})
