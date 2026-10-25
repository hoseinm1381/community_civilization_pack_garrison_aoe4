"""Actual Blender-only Archer representative renders; never save the scene."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, sha, write

BASE = {
    'CCP060 · Archer II weighted body · base',
    'CCP060 · Archer v2 fitted upper trousers',
    'CCP060 · Bound hair cloth headwrap',
    'CCP060 · Archer v3 clean split tunic',
    'CCP060 · Archer v3 rear headcloth knot',
}
RATTAN = {
    'CCP060 · Representative rattan vest',
    'CCP060 · Back carried rattan shield',
    'CCP060 · Shield bound rounded rim',
    'CCP060 · Shield diagonal carrying strap',
    'CCP060 · Shield rear shoulder strap',
    'CCP060 · Cross reed 1', 'CCP060 · Cross reed 3',
    'CCP060 · Raised vertical reed 1', 'CCP060 · Raised vertical reed 3',
}
COLORS = {
    'stock': (None, 0.0),
    'red': ((0.8, 0.025, 0.018, 1.0), 1.0),
    'blue': ((0.018, 0.15, 0.8, 1.0), 1.0),
}


def render_representative(checkpoint, label, rattan=False):
    guard()
    source = ART/'archer'/checkpoint
    destination = owned(OUT/'qualification'/label)
    if Path(bpy.data.filepath).resolve() != source.resolve():
        raise RuntimeError('Open the saved Archer representative checkpoint')
    if destination.exists():
        raise FileExistsError(destination)
    visible = BASE | (RATTAN if rattan else set())
    absent = visible - {obj.name for obj in bpy.data.objects}
    if absent:
        raise RuntimeError(f'Missing expected representative meshes: {sorted(absent)}')
    destination.mkdir(parents=True)
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.hide_render = obj.name not in visible
        elif obj.type == 'LIGHT':
            obj.hide_render = True
    for name, position, energy in [('key', (-3,-4,5),450),
                                   ('fill',(3,-2,3),240),
                                   ('rim',(0,3,4),220)]:
        light = bpy.data.lights.new('CCP060 representative '+name,'AREA')
        light.energy, light.shape, light.size = energy, 'DISK', 4
        obj = bpy.data.objects.new(light.name, light)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    cam=scene.camera
    cam.data.type='ORTHO'
    material=bpy.data.objects['CCP060 · Archer II weighted body · base'].data.materials[0]
    nodes=material.node_tree.nodes
    preview=nodes.get('GARRISON Team Colour Preview')
    strength=nodes.get('GARRISON Team Colour Preview Strength')
    if preview is None or strength is None:
        raise RuntimeError('Native Garrison team-color preview controls absent')
    prior_color=tuple(preview.outputs[0].default_value)
    prior_strength=strength.outputs[0].default_value
    results={}
    try:
        for color in ('stock','red','blue'):
            color_value, amount=COLORS[color]
            strength.outputs[0].default_value=amount
            if color_value is not None:
                preview.outputs[0].default_value=color_value
            scene.render.resolution_x=scene.render.resolution_y=900
            cam.data.ortho_scale=15.0
            cam.location=(6,-8,10)
            cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler()
            path=owned(destination/f'game-{color}.png')
            scene.render.filepath=str(path)
            bpy.ops.render.render(write_still=True)
            results[f'game-{color}']={'path':str(path),'sha256':sha(path),
                                      'resolution':[900,900],
                                      'camera_elevation_degrees':42.0,
                                      'ortho_scale_m':15.0}
        strength.outputs[0].default_value=0.0
        scene.render.resolution_x,scene.render.resolution_y=700,900
        cam.data.ortho_scale=2.2
        for view,position in [('front',(0,-5,1)),('back',(0,5,1))]:
            cam.location=position
            cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler()
            path=owned(destination/f'close-{view}.png')
            scene.render.filepath=str(path)
            bpy.ops.render.render(write_still=True)
            results[f'close-{view}']={'path':str(path),'sha256':sha(path),
                                      'resolution':[700,900]}
    finally:
        preview.outputs[0].default_value=prior_color
        strength.outputs[0].default_value=prior_strength
    write(destination/'presentation.json',{
        'schema':'ccp-060-archer-representative-render/v1',
        'source':str(source),'source_sha256':sha(source),
        'rattan_overlay':rattan,'visible_meshes':sorted(visible),
        'renders':results,'actual_blender_render':True,
        'native_game':False,'style_approved':False,
    })
    return results
