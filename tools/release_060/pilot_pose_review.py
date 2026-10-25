"""Bounded solid pose inspection using evaluated meshes and original stock clips.

Run in the inspected pilot idle scene. These are Blender authoring renders,
never native game evidence. Original rest-pose blends and pose receipts survive.
"""
from pathlib import Path
import bpy
from mathutils import Vector
from common import ART, OUT, guard, owned, read, write, sha


def review(pilot, revision='v1'):
    guard()
    pose = read(OUT / 'pilots' / pilot / 'pose.json')
    if Path(bpy.data.filepath).resolve() != Path(pose['blend']).resolve():
        raise RuntimeError('Open and claim the exact sampled idle review scene')
    if sha(pose['blend']) != pose['blend_sha256']:
        raise RuntimeError('Sampled idle review input changed')
    if revision not in ('v1', 'v2'):
        raise ValueError('Unknown inspection revision')
    suffix = '' if revision == 'v1' else '-v2'
    folder = owned(OUT / 'pilots' / pilot / ('idle-inspection' + suffix))
    if folder.exists():
        raise FileExistsError('Preserve previous pose inspection evidence')
    layer = bpy.context.scene.view_layers['Dai Viet pilot']
    bpy.context.window.view_layer = layer
    # Imported equipment contains all stock LODs. Keep the primary copy only
    # for this review; retain every mesh in the saved authoring collection.
    hidden = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name.endswith(('.001', '.002')) and 'spear_basic' in obj.name:
            obj.hide_render = True
            obj.hide_set(True)
            hidden.append(obj.name)
    objects = [o for o in bpy.context.scene.objects
               if o.type == 'MESH' and o.visible_get() and not o.hide_render and len(o.data.polygons)]
    deps = bpy.context.evaluated_depsgraph_get()
    points = []
    object_bounds = []
    for obj in objects:
        evaluated = obj.evaluated_get(deps)
        vertices = [evaluated.matrix_world @ v.co for v in evaluated.data.vertices]
        points.extend(vertices)
        object_bounds.append({'name': obj.name,
                              'min': [min(p[i] for p in vertices) for i in range(3)],
                              'max': [max(p[i] for p in vertices) for i in range(3)]})
    if not points:
        raise RuntimeError('No visible evaluated pilot geometry')
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (lo + hi) / 2
    camera_data = bpy.data.cameras.new('CCP060_Idle_Inspection_Camera')
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    direction = Vector((1, -1.65, .72)).normalized()
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    camera.location = center + direction * 15
    camera_data.type = 'ORTHO'
    inverse_rotation = camera.rotation_euler.to_matrix().transposed()
    projected = [inverse_rotation @ (p - center) for p in points]
    # A projected world-AABB center need not be the silhouette's image center.
    # Center the actual projected bounds before applying the crop margin.
    midpoint = Vector(((max(p.x for p in projected) + min(p.x for p in projected)) / 2,
                       (max(p.y for p in projected) + min(p.y for p in projected)) / 2, 0))
    camera.location += camera.rotation_euler.to_matrix() @ midpoint
    width = max(p.x for p in projected) - min(p.x for p in projected)
    height = max(p.y for p in projected) - min(p.y for p in projected)
    camera_data.ortho_scale = max(width, height) * 1.20
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.studio_light = 'paint.sl'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'BOTH'
    scene.display.shading.background_type = 'WORLD'
    scene.world.color = (.055, .065, .06)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    for view_layer in scene.view_layers:
        view_layer.use = view_layer == layer
    folder.mkdir(parents=True)
    image = folder / 'native-idle-solid.png'
    scene.render.filepath = str(image)
    bpy.ops.render.render(write_still=True)
    blend_suffix = '' if revision == 'v1' else '_v2'
    blend = owned(ART / 'pilots' / pilot / (pilot + '_stock_idle_inspection' + blend_suffix + '.blend'))
    if blend.exists():
        raise FileExistsError('Preserve previous inspection blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = {'schema': 'ccp-060-pose-inspection/v1', 'pilot': pilot, 'revision': revision,
              'input_pose_receipt': str(OUT / 'pilots' / pilot / 'pose.json'),
              'input_pose_receipt_sha256': sha(OUT / 'pilots' / pilot / 'pose.json'),
              'frame': scene.frame_current, 'blend': str(blend), 'blend_sha256': sha(blend),
              'image': {'path': str(image), 'sha256': sha(image)},
              'evaluated_visible_mesh_bounds': object_bounds,
              'hidden_equipment_lod_duplicates': hidden,
              'framing': 'evaluated full body and equipment, projected bounds plus 20 percent',
              'boundary': 'Blender sampled stock action and solid render; not native match proof',
              'appearance_review': 'pending', 'approval_ready': False}
    write(folder / 'receipt.json', report)
    return report
