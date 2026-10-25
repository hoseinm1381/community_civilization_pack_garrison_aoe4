"""Presentation of the saved v2c checkpoint; no geometry or texture edits."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, sha, write

SOURCE = ART/'archer/archer-garment-v2c.blend'
SOURCE_SHA = '5a4a32ed8e55e19feb9f863cd10788daaa38e64c9e91a409ebf07786069e0754'
TARGET = ART/'archer/archer-garment-v2c-review.blend'
DEST = OUT/'qualification/archer-v2c-review'
KEEP = {'CCP060 · Archer II weighted body · base',
        'CCP060 · Archer v2 fitted upper trousers',
        'CCP060 · Bound hair cloth headwrap'}


def setup():
    guard()
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve() or sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Open the pinned saved v2c checkpoint')
    if TARGET.exists() or DEST.exists():
        raise FileExistsError('Preserve earlier presentation')
    owned(TARGET)
    owned(DEST).mkdir(parents=True)
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.hide_render = obj.name not in KEEP
            obj.hide_set(obj.name not in KEEP)
        if obj.type == 'LIGHT':
            obj.hide_render = True
    for name, position, energy in [('key',(-3,-4,5),450), ('fill',(3,-2,3),240), ('rim',(0,3,4),220)]:
        data = bpy.data.lights.new('CCP060 v2c review '+name, 'AREA')
        data.energy, data.shape, data.size = energy, 'DISK', 4
        obj = bpy.data.objects.new(data.name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 700, 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.camera.data.type, scene.camera.data.ortho_scale = 'ORTHO', 2.20
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), check_existing=False)
    write(DEST/'presentation.json', {'schema':'ccp-060-garment-presentation/v1',
        'source':str(SOURCE), 'source_sha256':SOURCE_SHA,
        'blend':str(TARGET), 'blend_sha256':sha(TARGET),
        'scope':'Actual Blender material renders; source UV correction only. Head/shoulder redesign pending.',
        'geometry_edits':False, 'native_match':False, 'style_approved':False,
        'visible_meshes':sorted(KEEP)})


def render_view(view):
    guard()
    if Path(bpy.data.filepath).resolve() != TARGET.resolve():
        raise ValueError('Open the owned review blend')
    directions = {'front':(0,-5,1.0), 'side':(5,0,1.0), 'back':(0,5,1.0)}
    destination = owned(DEST/(view+'-material.png'))
    if destination.exists():
        raise FileExistsError(destination)
    camera = bpy.context.scene.camera
    camera.location = directions[view]
    camera.rotation_euler = (Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.render.filepath = str(destination)
    bpy.ops.render.render(write_still=True)
    write(DEST/(view+'.json'), {'path':str(destination), 'sha256':sha(destination),
        'view':view, 'actual_blender_render':True, 'native_game':False})
    return str(destination)
