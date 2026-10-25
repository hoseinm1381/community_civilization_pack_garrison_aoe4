"""Prepare a stock Archer II weighted-body control for the exact-matched Spearman rig.

Run ONLY in the claimed live Blender session after the pilot worker releases it.
This creates a separate candidate and source FBX/action files; it does not cook,
integrate, or replace the Chinese Archer animator/actor. No prototype admission
flag or fingerprint is forged. A passed control is needed before redesigned art.
"""
from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/release_060'))
from common import OUT, EXPORT, guard, owned, read, sha, write  # noqa: E402

PROTOTYPE = OUT / 'donors/prototype-probe/2bd91fe1b0f69a897d468faecbeaeeb0fb624cc8a59069f5b29bf1cda3115770/prototype.json'
COMPARISON = OUT / 'qualification/archer-spearman-rig-comparison.json'
DONOR_MANIFEST = OUT / 'donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json'
ALBEDO = OUT / 'qualification/archer-stock-albedo-atlas.png'
BLEND = ROOT / 'art/authoring/release_060/archer/archer-base-rattan-prototype.blend'
BLEND_SHA = '19bfead45f5433820facacb855ad589491ebf025e693042c4354f0e9b4b22676'
ALBEDO_SHA = 'f231747e68cd39bd1c6edcc7ecfc074f79013e4644bf0debb98d46650f0dacdc'
FOLDER = EXPORT / 'archer-matched-control'
RECEIPT = OUT / 'qualification/archer-matched-control-export.json'
COLLECTION = 'CCP060_Archer_Matched_Control'


def addon_module(name):
    keys = [key for key in bpy.context.preferences.addons.keys() if key.endswith('.garrison') or key == 'garrison']
    if len(keys) != 1:
        raise RuntimeError(f'Expected one enabled Garrison add-on; found {keys}')
    return importlib.import_module(keys[0] + '.' + name)


def pick_donor():
    col = bpy.data.collections.get('CCP060_Archer_Reference')
    if col is None:
        raise ValueError('The exact Archer II reference collection is missing')
    matches = [o for o in col.all_objects if o.type == 'MESH'
               and 'lod1' in o.name.lower() and 'chi_ranged_bow_age02' in o.name.lower()]
    if len(matches) != 1:
        raise ValueError(f'Expected one stock LOD1 donor in reference, found {[o.name for o in matches]}')
    mesh = matches[0]
    armatures = [m.object for m in mesh.modifiers if m.type == 'ARMATURE']
    if len(armatures) != 1 or armatures[0] is None:
        raise ValueError('Stock donor must have exactly one armature modifier')
    if len(mesh.data.materials) != 1 or mesh.data.materials[0] is None or not mesh.data.uv_layers:
        raise ValueError('Control needs one material and a UV map; do not silently simplify donor')
    return mesh, armatures[0]


def main():
    guard()
    owned(FOLDER); owned(RECEIPT)
    if RECEIPT.exists() or FOLDER.exists() or bpy.data.collections.get(COLLECTION):
        raise FileExistsError('Matched control already exists; preserve it before a new attempt')
    comparison = read(COMPARISON)
    if comparison['status'] != 'exact_bind_records_distinct_animation_owners':
        raise ValueError('Pinned full-record rig comparison is not exact')
    if sha(DONOR_MANIFEST) != comparison['archer_decoded_manifest']['sha256']:
        raise ValueError('Pinned Archer II donor manifest drift')
    if Path(bpy.data.filepath).resolve() != BLEND.resolve() or sha(BLEND) != BLEND_SHA:
        raise ValueError('Open the pinned Archer sample blend; do not export from another scene or changed file')
    doc = read(PROTOTYPE)
    if doc['prototype']['key'] != 'english-spearman-2' or doc['fingerprint'] != comparison['admitted_prototype_manifest']['fingerprint']:
        raise ValueError('Unexpected prototype identity/fingerprint')
    if sha(PROTOTYPE) != comparison['admitted_prototype_manifest']['sha256']:
        raise ValueError('Prototype manifest drift')
    if not ALBEDO.is_file() or sha(ALBEDO) != ALBEDO_SHA:
        raise ValueError('Pinned unmodified stock atlas PNG is missing or changed')
    donor, source_rig = pick_donor()
    panel = addon_module('unit_prototype_panel')
    unit_export = addon_module('unit_export')
    addon_common = addon_module('addon_common')
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # The installed Garrison creator stores the genuine prototype fingerprint,
    # stock skeleton records, and inherited clips on this NEW rig.
    rig = panel.create_unit(doc, bpy.context)
    candidate = rig.users_collection[0]
    candidate.name = COLLECTION
    root = rig.parent
    root.name = 'CCP060 matched control root'
    rig.name = 'CCP060 English Spearman II exact-match rig'
    source_names = [(b.name, b.parent.name if b.parent else None) for b in source_rig.data.bones]
    target_names = [(b.name, b.parent.name if b.parent else None) for b in rig.data.bones]
    if source_names != target_names or len(source_names) != 48:
        raise ValueError('Live armature hierarchy differs despite offline record match')
    matrix_delta = max(abs(source_rig.data.bones[name].matrix_local[i][j]
                           - rig.data.bones[name].matrix_local[i][j])
                       for name, _ in source_names for i in range(4) for j in range(4))
    if matrix_delta > 1e-5:
        raise ValueError(f'Live rest matrices differ; maximum delta {matrix_delta}')
    unmapped = sorted({group.name for group in donor.vertex_groups} - {bone.name for bone in rig.data.bones})
    if unmapped:
        raise ValueError(f'Donor has non-prototype weighted groups: {unmapped}')
    # Exact matching rest records permit direct rebinding, preserving every
    # vertex group and native weight rather than humanoid role-map folding.
    clone = donor.copy()
    clone.data = donor.data.copy()
    candidate.objects.link(clone)
    clone.name = 'CCP060 Archer donor weighted control'
    target_world = rig.matrix_world @ source_rig.matrix_world.inverted() @ donor.matrix_world
    clone.parent = rig
    clone.matrix_parent_inverse = Matrix.Identity(4)
    clone.matrix_world = target_world
    for modifier in clone.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.object = rig
    if len(clone.data.vertices) != len(donor.data.vertices) or len(clone.vertex_groups) != len(donor.vertex_groups):
        raise ValueError('Control duplicate changed geometry or weight group count')
    state = rig.garrison_unit
    state.mesh = clone
    state.build_name = 'ccp060_archer_matched_control'
    state.albedo = str(ALBEDO)
    # The built-in operator's exact source document/FBX route is used; action
    # overrides remain empty, so the generated prototype only inherits clips.
    action = panel.export_document(rig)
    if action['overrides'] or action['attachments']:
        raise ValueError('Control unexpectedly changes animation/equipment')
    core_unit = addon_common.core_module('unit_prototypes')
    unit_material = addon_common.core_module('unit_project')
    spec = core_unit.get(action['prototype'])
    textures = unit_material.texture_sources({'albedo': str(ALBEDO)})
    action['material_name'] = clone.data.materials[0].name
    action['textures'] = list(textures)
    FOLDER.mkdir(parents=True)
    records = unit_export.skeleton_records(rig)
    unit_export.export_unit_model(rig, [clone], FOLDER / 'model.fbx', records,
                                  three_lods=True, lod_counts=spec['lod_counts'])
    for role, path in textures.items():
        shutil.copy2(path, FOLDER / (role + '.png'))
    (FOLDER / 'action.json').write_text(json.dumps(action, indent=2) + '\n', encoding='utf-8')
    write(RECEIPT, {
        'schema': 'ccp-060-archer-matched-control-export/v1',
        'status': 'source_export_only_not_unit_validated_or_cooked',
        'prototype_key': doc['prototype']['key'], 'prototype_fingerprint': doc['fingerprint'],
        'original_archer_animator_preserved_for_eventual_integration': True,
        'generated_spearman_actor_must_not_be_integrated': True,
        'donor_mesh': donor.name, 'donor_vertex_count': len(donor.data.vertices),
        'live_rest_matrix_max_delta': matrix_delta,
        'donor_manifest_sha256': sha(DONOR_MANIFEST), 'source_blend_sha256': sha(BLEND),
        'stock_albedo_png_sha256': sha(ALBEDO),
        'prototype_rig': rig.name, 'candidate_collection': candidate.name,
        'folder': str(FOLDER),
        'files': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in FOLDER.iterdir() if p.is_file()},
        'next_gate': 'Run mod-project unit-validate on action.json, then unit-add/cook only in an isolated short-path project under shared native byte lock.'
    })
    return {'collection': candidate.name, 'folder': str(FOLDER), 'receipt': str(RECEIPT)}


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
