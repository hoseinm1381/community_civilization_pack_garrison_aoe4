"""Source-only viewport review: healthy geometry, materials and distance.

University stock body uses its neutral import material in Blender only; the
native layered material is preserved separately. No simulated player tint.
"""
from pathlib import Path
import bpy,json
ROOT=Path('E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison')
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/final-previews')
ASSETS={'garden':('CCP070_Imperial_Garden_Detailed_r4',(-15,15,0)),
        'foundry':('CCP070_Trung_Foundries_Detailed_r3',(15,15,0)),
        'wonder':('CCP070_Kinh_Thien_Detailed_r4',(-15,-15,0)),
        'university':('CCP070_University_Detailed_Overlay_r6',(15,-15,0))}
def capture(kind,mode='solid',direction='iso',distance=None):
    p=ROOT/'tools/release_070/art/blockout_runner.py';ns={};exec(compile(p.read_text(),str(p),'exec'),ns)
    name,anchor=ASSETS[kind];ns['OFFSETS'][name]=anchor;ns['view'](name,direction,color='VERTEX')
    bpy.context.scene.render.engine='BLENDER_EEVEE' if mode=='material' else 'BLENDER_WORKBENCH'
    for o in bpy.data.collections[name].objects:o.hide_set(o.name.endswith(('0002','0003')))
    if kind=='university':
        for o in bpy.data.collections['CCP070_University_Additions_Blockout'].objects:
            if o.get('stock_geometry_unchanged'):o.hide_set(False)
    OUT.mkdir(parents=True,exist_ok=True)
    for a in bpy.context.screen.areas:
        if a.type!='VIEW_3D':continue
        s=a.spaces.active
        if distance:s.region_3d.view_distance=distance
        s.shading.type='MATERIAL' if mode=='material' else 'SOLID'
        if mode=='material':s.shading.use_scene_world=False;s.shading.use_scene_lights=False
        path=OUT/(kind+'-'+mode+'-'+direction+('-distance' if distance else '')+'.png')
        bpy.context.scene.render.filepath=str(path)
        r=next(r for r in a.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=a,region=r):bpy.ops.render.opengl(write_still=True,view_context=True)
        return str(path)
    raise RuntimeError('No viewport')
