"""Bounded first garment pass on the pinned Archer II prototype.

Run in the claimed live Blender session. This only creates a new v2 authoring
scene and preview; no game resource or animation owner is changed.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/release_060'))
from common import ART, OUT, guard, owned, sha, write  # noqa: E402

SOURCE = ART / 'archer/archer-base-rattan-prototype.blend'
SOURCE_SHA = '19bfead45f5433820facacb855ad589491ebf025e693042c4354f0e9b4b22676'
TARGET = ART / 'archer/archer-garment-v2.blend'
RECEIPT = OUT / 'qualification/archer-v2-garment.json'
TARGET_B = ART / 'archer/archer-garment-v2b.blend'
RECEIPT_B = OUT / 'qualification/archer-v2b-garment.json'
TARGET_SHA = 'de99549e10a0ed58167596ec453d695b2a83119507e1e944ef65fde323ffb9e8'
TARGET_C = ART / 'archer/archer-garment-v2c.blend'
RECEIPT_C = OUT / 'qualification/archer-v2c-garment.json'
TARGET_B_SHA = 'bdb671a37de94f618c5fca2877d9df9ebc97823b518383b92d24523a91a50d00'
BODY_NAME = 'CCP060 · Archer II weighted body · base'
OLD_APRON = 'CCP060 · Short overlapping lower tunic'
OLD_SASH = 'CCP060 · Continuous tied waist sash'
PANTS_NAME = 'CCP060 · Archer v2 fitted upper trousers'


def body_component_indices(mesh):
    """Find the central robe/torso island from its measured seed, never by height alone."""
    adjacency = {v.index: set() for v in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen = {3}
    todo = [3]
    while todo:
        for neighbor in adjacency[todo.pop()]:
            if neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    zs = [mesh.vertices[i].co.z for i in seen]
    if len(seen) != 218 or not (0.44 < min(zs) < 0.46 and 1.67 < max(zs) < 1.69):
        raise RuntimeError(f'Central donor island changed: {len(seen)} vertices, z={min(zs):.3f}..{max(zs):.3f}')
    return seen


def cut_lower_robe(body):
    mesh = body.data
    island = body_component_indices(mesh)
    before = len(mesh.polygons)
    # Lower hem is the existing donor ring at 0.725 m, just above the knees.
    # Open the short side vents at the next measured ring (0.855 m). The
    # original UV loops and all surviving weights stay untouched.
    cut = set()
    vents = set()
    for poly in mesh.polygons:
        if not all(i in island for i in poly.vertices):
            continue
        coords = [mesh.vertices[i].co for i in poly.vertices]
        high = max(v.z for v in coords)
        if high <= 0.729:
            cut.add(poly.index)
        elif high <= 0.858 and min(v.z for v in coords) < 0.855:
            center = sum(coords, coords[0].copy() * 0.0) / len(coords)
            if abs(center.x) >= 0.225 and abs(center.y) <= 0.105:
                vents.add(poly.index)
    if not (50 <= len(cut) <= 80 and 2 <= len(vents) <= 20):
        raise RuntimeError(f'Unexpected robe face selection: hem={len(cut)} vent={len(vents)}')
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    doomed = [bm.faces[i] for i in sorted(cut | vents)]
    bmesh.ops.delete(bm, geom=doomed, context='FACES')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    if len(mesh.polygons) != before - len(cut | vents):
        raise RuntimeError('Robe removal face count mismatch')
    return {'original_faces': before, 'hem_faces_removed': len(cut), 'side_vent_faces_removed': len(vents),
            'remaining_faces': len(mesh.polygons), 'hem_height_m': 0.725, 'side_vent_top_m': 0.855}


def make_trousers(body):
    # Existing stock trouser cuffs finish at z=.529 m. Two separate fitted
    # trouser legs bridge to the native hip under the new knee-length tunic.
    # Centers/radii are measured from the stock leg components, not the robe.
    rings = [
        (0.505, 0.139, -0.003, 0.106, 0.107),
        (0.575, 0.139, -0.005, 0.108, 0.111),
        (0.705, 0.130, -0.008, 0.118, 0.119),
        (0.835, 0.120, -0.010, 0.128, 0.126),
        (0.925, 0.116, -0.012, 0.126, 0.122),
    ]
    segments = 12
    verts = []
    faces = []
    face_uv = []
    for side in (-1, 1):
        offset = len(verts)
        for ring_index, (z, cx, cy, rx, ry) in enumerate(rings):
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                verts.append((side * (cx + rx * math.cos(angle)), cy + ry * math.sin(angle), z))
        for r in range(len(rings) - 1):
            for i in range(segments):
                j = (i + 1) % segments
                quad = (offset + r * segments + i, offset + r * segments + j,
                        offset + (r + 1) * segments + j, offset + (r + 1) * segments + i)
                # Stock trouser UV swatches, keeping the donor atlas/material.
                u0, u1 = ((0.755, 0.845) if side < 0 else (0.925, 0.985))
                q0, q1 = i / segments, (i + 1) / segments
                v0 = 0.55 + r / (len(rings) - 1) * 0.28
                v1 = 0.55 + (r + 1) / (len(rings) - 1) * 0.28
                uvquad = ((u0 + (u1 - u0) * q0, v0), (u0 + (u1 - u0) * q1, v0),
                          (u0 + (u1 - u0) * q1, v1), (u0 + (u1 - u0) * q0, v1))
                if side < 0:
                    quad = tuple(reversed(quad))
                    uvquad = tuple(reversed(uvquad))
                faces.append(quad)
                face_uv.append(uvquad)
    mesh = bpy.data.meshes.new(PANTS_NAME)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name=body.data.uv_layers.active.name)
    for poly, coords in zip(mesh.polygons, face_uv):
        for loop_index, value in zip(poly.loop_indices, coords):
            uv.data[loop_index].uv = value
    mesh.materials.append(body.data.materials[0])
    obj = bpy.data.objects.new(PANTS_NAME, mesh)
    body.users_collection[0].objects.link(obj)
    obj.parent = body.parent
    obj.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    obj.matrix_world = body.matrix_world.copy()
    arm = obj.modifiers.new('AoE4 Armature', 'ARMATURE')
    arm.object = next(mod.object for mod in body.modifiers if mod.type == 'ARMATURE')
    for group in body.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    for side in (-1, 1):
        leg = 'metarig_rleg' if side < 0 else 'metarig_lleg'
        for ring_index in range(len(rings)):
            ids = [((0 if side < 0 else 1) * len(rings) + ring_index) * segments + i for i in range(segments)]
            if ring_index == 0:
                weights = {leg + '2': .82, leg + '1': .18}
            elif ring_index == 1:
                weights = {leg + '2': .43, leg + '1': .57}
            elif ring_index == 2:
                weights = {leg + '1': 1.0}
            elif ring_index == 3:
                weights = {leg + '1': .82, 'metarig_pelvis': .18}
            else:
                weights = {leg + '1': .60, 'metarig_pelvis': .40}
            for name, value in weights.items():
                obj.vertex_groups[name].add(ids, value, 'REPLACE')
    return {'name': obj.name, 'vertices': len(mesh.vertices), 'faces': len(mesh.polygons),
            'ring_heights_m': [r[0] for r in rings], 'segments_per_leg': segments,
            'armature': arm.object.name, 'material': mesh.materials[0].name}


def main():
    guard()
    owned(TARGET)
    owned(RECEIPT)
    if TARGET.exists() or RECEIPT.exists():
        raise FileExistsError('The garment v2 target already exists; preserve it')
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve() or sha(SOURCE) != SOURCE_SHA:
        raise RuntimeError('Live file or pinned Archer II source changed')
    body = bpy.data.objects[BODY_NAME]
    if len(body.data.vertices) != 988 or len(body.data.polygons) != 1236:
        raise RuntimeError('Unexpected donor body geometry')
    if PANTS_NAME in bpy.data.objects:
        raise RuntimeError('V2 trouser object already exists')
    mesh_receipt = cut_lower_robe(body)
    for name in (OLD_APRON, OLD_SASH):
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f'Missing expected old overlay: {name}')
        bpy.data.objects.remove(obj, do_unlink=True)
    pants_receipt = make_trousers(body)
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), check_existing=False)
    write(RECEIPT, {
        'schema': 'ccp-060-archer-garment-v2/v1',
        'status': 'authoring_first_step_only_not_export_or_native_qualified',
        'source': str(SOURCE), 'source_sha256': SOURCE_SHA,
        'target': str(TARGET), 'target_sha256': sha(TARGET),
        'robe': mesh_receipt, 'trousers': pants_receipt,
        'removed_separate_apron_and_pale_sash': [OLD_APRON, OLD_SASH],
        'untouched': ['stock head', 'stock hands', 'stock boots', 'stock armature', 'stock bow and quiver'],
        'next_gate': 'Inspect actual solid and material front/side/back, then bent-leg and bow-draw diagnostic pose before further detailing.'
    })
    return {'target': str(TARGET), 'robe': mesh_receipt, 'trousers': pants_receipt}


def refine_v2b():
    """Repair only first-pass hem remnant and trouser/cuff fit in a new scene."""
    guard()
    owned(TARGET_B)
    owned(RECEIPT_B)
    if TARGET_B.exists() or RECEIPT_B.exists():
        raise FileExistsError('Preserve the existing garment v2b target')
    if Path(bpy.data.filepath).resolve() != TARGET.resolve() or sha(TARGET) != TARGET_SHA:
        raise RuntimeError('Live scene must be the pinned garment v2 checkpoint')
    body = bpy.data.objects[BODY_NAME]
    if body.data.users != 1 or len(body.data.polygons) != 1170:
        raise RuntimeError('Weighted donor body is shared or the first pass changed')
    mesh = body.data
    adjacency = {v.index: set() for v in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen = set()
    disc = None
    for vertex in mesh.vertices:
        if vertex.index in seen:
            continue
        todo = [vertex.index]
        seen.add(vertex.index)
        component = []
        while todo:
            current = todo.pop()
            component.append(current)
            for adjacent in adjacency[current]:
                if adjacent not in seen:
                    seen.add(adjacent)
                    todo.append(adjacent)
        points = [mesh.vertices[i].co for i in component]
        if (len(component) == 12 and 0.444 < min(p.z for p in points) < 0.446
                and 0.460 < max(p.z for p in points) < 0.462
                and min(p.x for p in points) < -0.30 and max(p.x for p in points) > 0.31):
            disc = set(component)
    if disc is None:
        raise RuntimeError('Measured 12-vertex detached old robe hem cap not found')
    faces = [p.index for p in mesh.polygons if all(i in disc for i in p.vertices)]
    if len(faces) != 10:
        raise RuntimeError(f'Unexpected old hem cap: {len(faces)} faces')
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in faces], context='FACES')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    if len(mesh.polygons) != 1160:
        raise RuntimeError('Detached hem cap removal changed unexpected body faces')

    old = bpy.data.objects[PANTS_NAME]
    bpy.data.objects.remove(old, do_unlink=True)
    # Fit each new tube to the actual native lower-trouser top boundary. The
    # first loop sits 12 mm inside and ~1.5 mm radially under the stock cuff;
    # weights on that loop copy the exact nearest donor vertices.
    source_rings = {}
    for side in (-1, 1):
        candidates = [v for v in mesh.vertices if 0.520 <= v.co.z <= 0.532
                      and v.co.x * side > 0.015 and abs(v.co.x) < 0.26
                      and -0.14 < v.co.y < 0.14]
        unique = []
        for vertex in candidates:
            if not any((vertex.co - prior.co).length < 0.001 for prior in unique):
                unique.append(vertex)
        if len(unique) != 7:
            raise RuntimeError(f'Expected seven unique stock cuff rim points for side {side}, found {len(unique)}')
        cx = sum(v.co.x for v in unique) / len(unique)
        cy = sum(v.co.y for v in unique) / len(unique)
        unique.sort(key=lambda v: math.atan2(v.co.y - cy, v.co.x - cx))
        source_rings[side] = (unique, cx, cy)

    verts = []
    quads = []
    uvquads = []
    weights = []
    ring_specs = ((-0.012, .985), (.045, 1.01), (.18, 1.04), (.31, 1.12), (.40, 1.10))
    for side in (-1, 1):
        rim, cx, cy = source_rings[side]
        offset = len(verts)
        leg = 'metarig_rleg' if side < 0 else 'metarig_lleg'
        for ring_index, (dz, scale) in enumerate(ring_specs):
            for vertex in rim:
                verts.append((cx + (vertex.co.x - cx) * scale,
                              cy + (vertex.co.y - cy) * scale,
                              vertex.co.z + dz))
                if ring_index == 0:
                    weights.append({body.vertex_groups[g.group].name: g.weight for g in vertex.groups})
                elif ring_index == 1:
                    weights.append({leg + '1': .62, leg + '2': .38})
                elif ring_index == 2:
                    weights.append({leg + '1': 1.0})
                elif ring_index == 3:
                    weights.append({leg + '1': .82, 'metarig_pelvis': .18})
                else:
                    weights.append({leg + '1': .60, 'metarig_pelvis': .40})
        for r in range(len(ring_specs) - 1):
            for i in range(len(rim)):
                j = (i + 1) % len(rim)
                quads.append((offset + r * len(rim) + i, offset + r * len(rim) + j,
                              offset + (r + 1) * len(rim) + j, offset + (r + 1) * len(rim) + i))
                q0, q1 = i / len(rim), (i + 1) / len(rim)
                v0 = .10 + .09 * r / (len(ring_specs) - 1)
                v1 = .10 + .09 * (r + 1) / (len(ring_specs) - 1)
                uvquads.append(((.50 + .10 * q0, v0), (.50 + .10 * q1, v0),
                                (.50 + .10 * q1, v1), (.50 + .10 * q0, v1)))
    pants_mesh = bpy.data.meshes.new(PANTS_NAME + ' · fitted cuff')
    pants_mesh.from_pydata(verts, [], quads)
    pants_mesh.update()
    uv = pants_mesh.uv_layers.new(name=mesh.uv_layers.active.name)
    for poly, coords in zip(pants_mesh.polygons, uvquads):
        for loop_index, value in zip(poly.loop_indices, coords):
            uv.data[loop_index].uv = value
    pants_mesh.materials.append(mesh.materials[0])
    pants = bpy.data.objects.new(PANTS_NAME, pants_mesh)
    body.users_collection[0].objects.link(pants)
    pants.parent = body.parent
    pants.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    pants.matrix_world = body.matrix_world.copy()
    arm = pants.modifiers.new('AoE4 Armature', 'ARMATURE')
    arm.object = next(mod.object for mod in body.modifiers if mod.type == 'ARMATURE')
    for group in body.vertex_groups:
        pants.vertex_groups.new(name=group.name)
    for index, group_weights in enumerate(weights):
        if abs(sum(group_weights.values()) - 1.0) > 0.002:
            raise RuntimeError(f'Unnormalized trouser vertex {index}: {group_weights}')
        for name, weight in group_weights.items():
            pants.vertex_groups[name].add([index], weight, 'REPLACE')
    for polygon in pants_mesh.polygons:
        p = polygon.center
        side = -1 if p.x < 0 else 1
        cx = source_rings[side][1]
        cy = source_rings[side][2]
        outward = (p.x - cx, p.y - cy)
        if polygon.normal.x * outward[0] + polygon.normal.y * outward[1] <= 0:
            raise RuntimeError(f'Inward trouser wall at face {polygon.index}')
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET_B), check_existing=False)
    write(RECEIPT_B, {
        'schema': 'ccp-060-archer-garment-v2b/v1',
        'status': 'authoring_first_step_repaired_not_export_or_native_qualified',
        'parent_blend': str(TARGET), 'parent_sha256': TARGET_SHA,
        'blend': str(TARGET_B), 'blend_sha256': sha(TARGET_B),
        'old_detached_robe_hem_cap': {'vertices': len(disc), 'faces_removed': len(faces),
                                      'z_m': [0.4446, 0.4609]},
        'trouser_cuff': {'source_unique_boundary_points_per_leg': 7,
                         'first_loop_depth_below_stock_cuff_m': .012,
                         'first_loop_radial_inset_fraction': .015,
                         'vertices': len(verts), 'faces': len(quads),
                         'stock_loop_weights_copied': True,
                         'all_wall_normals_outward': True,
                         'uv_source': 'stock atlas quiet grey cloth swatch; original donor maps retained'},
        'next_gate': 'Inspect front/side/back and stock walk/fire diagnostic pose.'
    })
    return {'blend': str(TARGET_B), 'removed_old_hem_faces': len(faces),
            'new_trouser_vertices': len(verts), 'new_trouser_faces': len(quads)}


def remap_v2c():
    """Map upper trousers to an actual quiet burgundy stock trouser swatch."""
    guard()
    owned(TARGET_C)
    owned(RECEIPT_C)
    if TARGET_C.exists() or RECEIPT_C.exists():
        raise FileExistsError('Preserve existing garment v2c target')
    if Path(bpy.data.filepath).resolve() != TARGET_B.resolve() or sha(TARGET_B) != TARGET_B_SHA:
        raise RuntimeError('Live scene must be the pinned garment v2b checkpoint')
    obj = bpy.data.objects[PANTS_NAME]
    mesh = obj.data
    if len(mesh.vertices) != 70 or len(mesh.polygons) != 56 or mesh.uv_layers.active is None:
        raise RuntimeError('Unexpected first-pass fitted upper trousers')
    uv = mesh.uv_layers.active
    for poly in mesh.polygons:
        local_face = poly.index % 28
        ring = local_face // 7
        segment = local_face % 7
        q0, q1 = segment / 7, (segment + 1) / 7
        v0, v1 = .70 + .13 * ring / 4, .70 + .13 * (ring + 1) / 4
        quad = ((.83 + .09 * q0, v0), (.83 + .09 * q1, v0),
                (.83 + .09 * q1, v1), (.83 + .09 * q0, v1))
        for loop_index, coord in zip(poly.loop_indices, quad):
            uv.data[loop_index].uv = coord
    mesh.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET_C), check_existing=False)
    write(RECEIPT_C, {
        'schema': 'ccp-060-archer-garment-v2c/v1',
        'status': 'authoring_first_step_material_adjustment_not_export_or_native_qualified',
        'parent_blend': str(TARGET_B), 'parent_sha256': TARGET_B_SHA,
        'blend': str(TARGET_C), 'blend_sha256': sha(TARGET_C),
        'changed': 'upper trouser UVs only, on the donor stock albedo atlas',
        'uv_region': {'u': [.83, .92], 'v': [.70, .83]},
        'pixel_probe': 'sampled actual source atlas: muted burgundy RGB about 82..121,40..70,41..68',
        'pattern_region': 'stock pattern PNG sampled zero in all channels over this UV region',
        'geometry_rig_weights': 'byte-identical in Blender file relative to v2b except serialization; no edit',
        'next_gate': 'Front/side/back material comparison and motion at cuff before next silhouette edit.'
    })
    return {'blend': str(TARGET_C), 'uv_region': [[.83, .92], [.70, .83]]}


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
