"""Render four Age-II remodeled donor + detail atlas composites without saving art.

This opens only task-owned editable sources and writes offline QA PNGs/receipts.
"""
import bpy
import hashlib
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_040/buildings/details'
MODELS=json.loads((ROOT/'output/release_040/buildings/model-validation.json').read_text())['models']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
receipts=[]
selected=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
for family in ('blacksmith','stable','archery_range','market'):
    if selected and family not in selected:continue
    age=2
    source=next(row for row in MODELS if row['family']==family and row['age']==age)
    detail=json.loads((OUT/family/'age02'/'source.json').read_text())
    donor_blend=Path(source['editable_blend']);detail_blend=Path(detail['source_blend'])
    assert sha(donor_blend)==source['editable_blend_sha256']
    assert sha(detail_blend)==detail['source_blend_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(donor_blend))
    with bpy.data.libraries.load(str(detail_blend),link=False) as (src,dst):
        dst.objects=[name for name in src.objects if name.startswith('vn_'+family+'_age02_detail_')]
    imported=[]
    for obj in dst.objects:
        assert obj and obj.type=='MESH'
        bpy.context.scene.collection.objects.link(obj);imported.append(obj)
    assert len(imported)==3
    for material in bpy.data.materials:
        if not material.use_nodes:continue
        control=material.node_tree.nodes.get('GARRISON Material Controls')
        if control and control.inputs.get('Team Colour Strength'):
            control.inputs['Team Colour Strength'].default_value=0
    allmesh=[o for o in bpy.context.scene.objects if o.type=='MESH']
    coords=[v.co for o in allmesh for v in o.data.vertices]
    lo=Vector([min(v[i] for v in coords) for i in range(3)])
    hi=Vector([max(v[i] for v in coords) for i in range(3)])
    center=(lo+hi)/2;span=(hi-lo).length
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.resolution_x=900;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    if scene.world is None:scene.world=bpy.data.worlds.new('CCP040 textured preview')
    scene.world.color=(.28,.28,.28)
    sun=bpy.data.objects.new('Preview only sun',bpy.data.lights.new('Preview only sun','SUN'))
    scene.collection.objects.link(sun);sun.rotation_euler=(.45,-.65,-.5)
    sun.data.energy=3;sun.data.angle=.15
    camera=bpy.data.objects.new('Preview only camera',bpy.data.cameras.new('Preview only camera'))
    scene.collection.objects.link(camera);camera.data.type='ORTHO';scene.camera=camera
    # The game view shows front (-Y) and one side, retaining the donor frame.
    for name,vector in (('game',(1,-1,.85)),('facade',(0,-1,.25))):
        camera.location=center+Vector(vector).normalized()*span*2
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=span*1.30
        path=OUT/family/'age02'/f'composite-{name}-textured.png'
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        receipts.append({'family':family,'age':age,'view':name,'donor_blend':str(donor_blend),
            'donor_blend_sha256':sha(donor_blend),'detail_blend':str(detail_blend),
            'detail_blend_sha256':sha(detail_blend),'image':str(path),'image_sha256':sha(path),
            'donor_mesh_count':len(allmesh)-3,'detail_mesh_count':3,'offline_only':True})
    print('TEXTURED_COMPOSITE_READY',family,flush=True)
if not selected:
    assert len(receipts)==8
    (OUT/'textured-composite-validation.json').write_text(json.dumps({'schema':'ccp.release040.building-textured-composite/v1',
        'status':'offline_preview_only','images':receipts},indent=2)+'\n',encoding='utf8')
