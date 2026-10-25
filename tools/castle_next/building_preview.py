"""Render exact healthy-draw donor/remodel/composite Castle comparisons.

Uses the installed native RGM selector predicates and MSCL source-object map to
remove construction, debris, damage and ruin triangles from preview copies.
The saved editable donor/remodel Blends are never changed by this preview job.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, ROOT, CFG, guarded, read, write, sha
from building_selectors import source_map

sys.path.insert(0, str(Path(CFG['garrison_extension'])))
from garrison_shared import relic_chunky as rc

JOBS = (('monastery', 3), ('monastery', 4), ('siege_workshop', 3),
        ('siege_workshop', 4), ('keep', 3))
BASE = OUT / 'buildings'
PREV = BASE / 'previews'


def native_path(path):
    raw = str(path)
    return Path('\\\\?\\' + raw) if os.name == 'nt' and len(raw) >= 240 else Path(raw)


def parse_set(payload):
    name, at = rc.read_lp_string(payload, 0)
    count = struct.unpack_from('<I', payload, at)[0]
    at += 4
    members = []
    for _ in range(count):
        value, at = rc.read_lp_string(payload, at)
        members.append(value)
    assert at == len(payload)
    return {'name': name, 'members': members}


def parse_state(payload):
    count = struct.unpack_from('<I', payload)[0]
    at = 4
    conditions = []
    for _ in range(count):
        op, flag, one = struct.unpack_from('<IBI', payload, at)
        at += 9
        prop, at = rc.read_lp_string(payload, at)
        value, at = rc.read_lp_string(payload, at)
        conditions.append((op, flag, one, prop, value))
    assert at == len(payload)
    return conditions


def healthy_masks(donor, model_override=None):
    doc = donor['decoded_static']
    model = native_path(model_override or doc['structure_collection_contract']['source']['path'])
    if model_override is None:
        assert sha(model) == doc['structure_collection_contract']['source']['sha256']
    chunks = list(rc.walk(rc.load(model).roots))
    sets = [parse_set(c.payload) for c in chunks if c.tag == b'MSD ' and len(c.payload) > 4]
    states = [parse_state(c.payload) for c in chunks if c.tag == b'CNBP']
    assert len(sets) in (len(states), len(states)+1)
    healthy = set()
    names = set(source_map(donor)[1]['all_selector_names'])
    for i, row in enumerate(sets):
        conditions = states[i] if i < len(states) else []
        if (2, 0, 1, 'life_cycle_state', 'healthy') in conditions:
            healthy.update(row['members'])
    assert healthy
    mscl = next(c for c in chunks if c.tag == b'MSCL')
    assert len(mscl.children) == 1 and mscl.children[0].tag == b'DATA'
    payload = mscl.children[0].payload
    source_count = struct.unpack_from('<H', payload)[0]
    offsets = {n: payload.find(rc.lp_string(n)) for n in names}
    assert source_count == len(names)
    assert all(o >= 2 for o in offsets.values()) and len(set(offsets.values())) == source_count
    ordered = sorted(names, key=offsets.get)
    contract = doc['structure_collection_contract']
    groups = doc['geometry']['groups']
    masks = []
    index = 0
    for mapping, span in zip(contract['maps'], contract['geometry_group_spans']):
        inverse = {bone: ordered[i] for i, bone in enumerate(mapping['source_to_local_bone']) if bone >= 0}
        for group in groups[index:index+span]:
            bones = group['collection_bone_indices']
            mask = []
            for tri in group['triangles']:
                a, b, c = (bones[v] for v in tri)
                assert a == b == c and a in inverse
                mask.append(inverse[a] in healthy)
            masks.append(mask)
        index += span
    assert index == len(groups) == len(masks)
    return masks, {'selector_sets': len(sets),
                   'healthy_selector_names': sorted(healthy),
                   'all_triangle_count': sum(len(m) for m in masks),
                   'healthy_triangle_count': sum(sum(m) for m in masks)}


def filter_scene(donor, masks):
    groups = donor['decoded_static']['geometry']['groups']
    rows = []
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH'
              and o.get('garrison_mesh_index') is not None]
    assert len(meshes) == len(groups), (len(meshes), len(groups))
    for obj in meshes:
        index = int(obj['garrison_mesh_index'])
        group = groups[index]
        mask = masks[index]
        polygons = obj.data.polygons
        assert len(polygons) == len(mask) == group['triangle_count']
        # The decoded projection reverses triangle winding but preserves the
        # exact native vertex ids and ordered draw instance.
        for p, native in zip(polygons, group['triangles']):
            assert set(p.vertices) == set(native), (obj.name, p.index)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        erase = [bm.faces[i] for i, selected in enumerate(mask) if not selected]
        bmesh.ops.delete(bm, geom=erase, context='FACES')
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        rows.append({'group': group['name'], 'all_triangles': len(mask),
                     'healthy_triangles': sum(mask),
                     'preview_triangles': len(obj.data.polygons)})
    return meshes, rows


def append_details(family, age):
    source = ROOT / f'art/authoring/castle_next/buildings/{family}/age{age:02}/details/vn_{family}_details_age{age:02}.blend'
    assert source.exists(), source
    with bpy.data.libraries.load(str(source), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(f'vn_{family}_age{age:02}_castle_detail_')]
    objects = []
    for obj in dst.objects:
        if obj is not None and obj.type == 'MESH':
            bpy.context.scene.collection.objects.link(obj)
            objects.append(obj)
    assert len(objects) == 3
    return objects


def world_bounds(objects):
    coords = [o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
    assert coords
    lo = Vector([min(v[i] for v in coords) for i in range(3)])
    hi = Vector([max(v[i] for v in coords) for i in range(3)])
    return lo, hi


def render_views(objects, folder):
    folder.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    lo, hi = world_bounds(objects)
    center = (lo+hi)/2
    span = (hi-lo).length
    scene.render.resolution_x = 720
    scene.render.resolution_y = 570
    scene.render.resolution_percentage = 100
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    views = (('iso', (1,-1,.85)), ('front', (0,-1,.15)),
             ('back', (0,1,.15)), ('left', (-1,0,.15)),
             ('right', (1,0,.15)), ('top', (0,0,1)),
             ('bottom', (0,0,-1)))
    renders = {}
    for label, vec in views:
        camera = bpy.data.objects.new('Preview only', bpy.data.cameras.new('Preview only'))
        scene.collection.objects.link(camera)
        camera.location = center + Vector(vec).normalized()*span*2
        camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = span*1.30
        scene.camera = camera
        dest = folder / f'{label}-solid.png'
        scene.render.filepath = str(dest)
        bpy.ops.render.render(write_still=True)
        renders[dest.name] = sha(dest)
        if label == 'iso':
            for material in bpy.data.materials:
                if material.use_nodes:
                    control = material.node_tree.nodes.get('GARRISON Material Controls')
                    if control and control.inputs.get('Team Colour Strength'):
                        control.inputs['Team Colour Strength'].default_value = 0
            ground_mat = bpy.data.materials.new('Preview earth')
            ground_mat.use_nodes = True
            ground_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.24,.23,.18,1)
            bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.03))
            ground = bpy.context.object
            ground.data.materials.append(ground_mat)
            sun = bpy.data.objects.new('Preview sun', bpy.data.lights.new('Preview sun','SUN'))
            scene.collection.objects.link(sun)
            sun.rotation_euler = (.45,-.65,-.5)
            sun.data.energy = 3
            fill = bpy.data.objects.new('Preview fill', bpy.data.lights.new('Preview fill','SUN'))
            scene.collection.objects.link(fill)
            fill.rotation_euler = (.75,.55,2.4)
            fill.data.energy = 1.6
            scene.render.engine = 'CYCLES'
            scene.cycles.samples = 8
            scene.cycles.use_denoising = True
            scene.view_settings.view_transform = 'AgX'
            dest = folder / 'iso-textured.png'
            scene.render.filepath = str(dest)
            bpy.ops.render.render(write_still=True)
            renders[dest.name] = sha(dest)
            bpy.data.objects.remove(sun, do_unlink=True)
            bpy.data.objects.remove(fill, do_unlink=True)
            bpy.data.objects.remove(ground, do_unlink=True)
            scene.render.engine = 'BLENDER_WORKBENCH'
        bpy.data.objects.remove(camera, do_unlink=True)
    scene.camera = None
    return {'images': renders, 'bounds_m': {'minimum': list(lo), 'maximum': list(hi)}}


def main():
    assert bpy.app.background and not bpy.data.filepath
    guarded()
    donors = read(OUT / 'donors/donor-manifest.json')['donors']
    models = read(BASE / 'model-validation.json')['models']
    details = read(BASE / 'details/details-validation.json')['models']
    requested = set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
    rows = []
    for family, age in JOBS:
        key = f'{family}{age:02}'
        if requested and key not in requested:
            continue
        donor = donors[key]
        model = next(r for r in models if (r['family'],r['age']) == (family,age))
        detail = next(r for r in details if (r['family'],r['age']) == (family,age))
        stock_masks, stock_selector = healthy_masks(donor)
        remodel_masks, remodel_selector = healthy_masks(donor, model['native_model'])
        states = {}
        for state, path in (('stock', model['donor_blend']),
                            ('remodel', model['editable_blend']),
                            ('composite', model['editable_blend'])):
            bpy.ops.wm.open_mainfile(filepath=str(path))
            masks = stock_masks if state == 'stock' else remodel_masks
            selector = stock_selector if state == 'stock' else remodel_selector
            meshes, group_rows = filter_scene(donor, masks)
            objects = list(meshes)
            if state == 'composite':
                objects.extend(append_details(family, age))
            assert sum(r['preview_triangles'] for r in group_rows) == selector['healthy_triangle_count']
            result = render_views(objects, PREV / key / state)
            states[state] = {'source_blend': path, 'source_sha256': sha(path),
                             'healthy_groups': group_rows, **result}
            print('HEALTHY_PREVIEW', key, state, selector['healthy_triangle_count'], flush=True)
        rows.append({'key':key,'stock_selector':stock_selector,
                     'remodel_selector':remodel_selector,'states':states,
                     'detail_export': detail['export_dir'],
                     'proof':'Offline exact healthy-draw geometry; native culling/runtime unverified'})
        write(PREV / 'previews.json',
              {'schema':'ccp.castle-next.healthy-building-previews/v1',
               'status':'running','models':rows})
    write(PREV / 'previews.json',
          {'schema':'ccp.castle-next.healthy-building-previews/v1',
           'status':'passed','models':rows})


if __name__ == '__main__':
    main()
