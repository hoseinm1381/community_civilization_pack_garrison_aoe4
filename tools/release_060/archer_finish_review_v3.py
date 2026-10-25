"""Actual Blender material renders from saved Archer v3 source checkpoints."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, sha, write

VISIBLE = {'CCP060 · Archer II weighted body · base',
           'CCP060 · Archer v2 fitted upper trousers',
           'CCP060 · Bound hair cloth headwrap',
           'CCP060 · Archer v3 clean split tunic',
           'CCP060 · Archer v3 low collar',
           'CCP060 · Archer v3 cloth shoulders',
           'CCP060 · Archer v3 front overlap',
           'CCP060 · Archer v3 waist tie',
           'CCP060 · Archer v3 waist tie knot',
           'CCP060 · Archer v3 rear headcloth knot'}


def render_set(checkpoint, label, views=('front','side','back')):
    guard()
    source = ART/'archer'/checkpoint
    destination = owned(OUT/'qualification'/label)
    if Path(bpy.data.filepath).resolve() != source.resolve():
        raise RuntimeError('Open the saved authoring checkpoint')
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.hide_render = obj.name not in VISIBLE
        elif obj.type == 'LIGHT':
            obj.hide_render = True
    for name, pos, energy in [('key',(-3,-4,5),450),('fill',(3,-2,3),240),('rim',(0,3,4),220)]:
        data=bpy.data.lights.new('CCP060 v3 review '+name,'AREA')
        data.energy,data.shape,data.size=energy,'DISK',4
        obj=bpy.data.objects.new(data.name,data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location=pos
        obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x,scene.render.resolution_y=700,900
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    cam=scene.camera
    cam.data.type,cam.data.ortho_scale='ORTHO',2.20
    positions={'front':(0,-5,1),'side':(5,0,1),'back':(0,5,1),
               'left':(-5,0,1),'top':(0,-.001,6),'bottom':(0,-.001,-5)}
    results={}
    for view in views:
        path=owned(destination/(view+'-material.png'))
        cam.location=positions[view]
        cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        results[view]={'path':str(path),'sha256':sha(path)}
    write(destination/'presentation.json', {'schema':'ccp-060-archer-review/v1',
          'source':str(source),'source_sha256':sha(source),
          'renders':results,'actual_blender_render':True,'native_game':False,
          'style_approved':False,'visible_meshes':sorted(VISIBLE)})
    return results
