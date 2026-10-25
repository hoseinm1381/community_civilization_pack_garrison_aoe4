"""Read-only material probe for the Age-II stable awning intersection."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
row=json.loads((ROOT/'output/release_040/buildings/details/stable/age02/source.json').read_text())
model=next(r for r in json.loads((ROOT/'output/release_040/buildings/model-validation.json').read_text())['models'] if r['family']=='stable' and r['age']==2)
bpy.ops.wm.open_mainfile(filepath=row['source_blend'])
scene=bpy.context.scene
lo=Vector(model['before_bounds']['minimum']);hi=Vector(model['before_bounds']['maximum'])
center=(lo+hi)/2;span=(hi-lo).length
sun=bpy.data.objects.new('Probe only sun',bpy.data.lights.new('Probe only sun','SUN'))
scene.collection.objects.link(sun);sun.rotation_euler=(.45,-.65,-.5);sun.data.energy=3
camera=bpy.data.objects.new('Probe only camera',bpy.data.cameras.new('Probe only camera'))
scene.collection.objects.link(camera);camera.location=center+Vector((1,-1,.85)).normalized()*span*2
camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=span*1.30;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=900;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.filepath=str(ROOT/'output/release_040/buildings/details/stable/age02/detail-only-textured.png')
bpy.ops.render.render(write_still=True)
print('STABLE_DETAIL_PROBE_READY')
