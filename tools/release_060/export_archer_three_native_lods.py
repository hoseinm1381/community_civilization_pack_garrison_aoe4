"""Prepare an exact-donor-three-LOD Archer control through installed generic unit export.

Run only after an exclusive live Blender handoff. This uses the existing genuine
English Spearman II prototype rig but exports three separate donor-derived LOD
meshes with unit_export.export_unit_model(..., three_lods=False). The standard
Build Unit panel's one-mesh/one-material path is intentionally not claimed;
subsequent installed unit-add/cook may refuse and must be left unchanged.
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
from common import ART, EXPORT, OUT, guard, owned, read, sha, write  # noqa: E402

BLEND = ART / 'archer/archer-matched-control.blend'
BLEND_SHA = '6ce72edfd57af484f84295f6c06b41ebc96ae34a99a73cc1434ef6f0fb3af58c'
DONOR_MANIFEST = OUT / 'donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json'
EXACT_MATCH = OUT / 'qualification/archer-spearman-rig-comparison.json'
CONTROL_EXPORT = OUT / 'qualification/archer-matched-control-export.json'
CONTROL_FOLDER = EXPORT / 'archer-matched-control'
FOLDER = EXPORT / 'archer-matched-three-lod-control'
RECEIPT = OUT / 'qualification/archer-matched-three-lod-export.json'
SAVED_BLEND = ART / 'archer/archer-matched-three-lod-control.blend'
COLLECTION = 'CCP060_Archer_Three_Native_LOD_Control'
EXPECTED_COUNTS = ((988,1236),(490,522),(187,155))


def addon_module(name):
    keys = [key for key in bpy.context.preferences.addons.keys()
            if key.endswith('.garrison') or key == 'garrison']
    if len(keys) != 1:
        raise RuntimeError(f'Expected one enabled Garrison add-on, got {keys}')
    return importlib.import_module(keys[0] + '.' + name)


def donor_lods():
    reference = bpy.data.collections.get('CCP060_Archer_Reference')
    if reference is None:
        raise ValueError('Pinned donor reference collection missing')
    result = []
    for number in (1,2,3):
        matches = [o for o in reference.all_objects if o.type == 'MESH'
                   and 'chi_ranged_bow_age02' in o.name.lower()
                   and f'lod{number}' in o.name.lower()]
        if len(matches) != 1:
            raise ValueError(f'Expected one stock lod{number}; found {[o.name for o in matches]}')
        mesh = matches[0]
        tris = sum(len(face.vertices)-2 for face in mesh.data.polygons)
        if (len(mesh.data.vertices),tris) != EXPECTED_COUNTS[number-1]:
            raise ValueError(f'Unexpected LOD{number} geometry count: {(len(mesh.data.vertices),tris)}')
        if len(mesh.data.materials) != 1 or not mesh.data.uv_layers:
            raise ValueError(f'LOD{number} needs one material and UVs')
        modifiers = [m.object for m in mesh.modifiers if m.type == 'ARMATURE']
        if len(modifiers) != 1 or modifiers[0] is None:
            raise ValueError(f'LOD{number} is not bound to one native armature')
        result.append((mesh,modifiers[0]))
    if len({rig.as_pointer() for _,rig in result}) != 1:
        raise ValueError('Donor LODs do not share one native armature')
    return result


def main():
    guard()
    for path in (FOLDER,RECEIPT,SAVED_BLEND):
        owned(path)
        if path.exists():
            raise FileExistsError(f'Preserve earlier three-LOD control: {path}')
    if bpy.data.collections.get(COLLECTION):
        raise FileExistsError('Three-LOD candidate collection already exists')
    if Path(bpy.data.filepath).resolve() != BLEND.resolve() or sha(BLEND) != BLEND_SHA:
        raise ValueError('Open the pinned saved matched-control .blend first')
    match = read(EXACT_MATCH)
    control = read(CONTROL_EXPORT)
    if (match['status'] != 'exact_bind_records_distinct_animation_owners'
            or sha(DONOR_MANIFEST) != match['archer_decoded_manifest']['sha256']
            or control['prototype_key'] != 'english-spearman-2'):
        raise ValueError('Pinned donor/prototype evidence drift')
    old_action = read(CONTROL_FOLDER / 'action.json')
    if sha(CONTROL_FOLDER / 'action.json') != control['files']['action.json']['sha256']:
        raise ValueError('Existing installed-validator action changed')
    rig = bpy.data.objects.get('CCP060 English Spearman II exact-match rig')
    if rig is None or rig.type != 'ARMATURE' or rig.get('garrison_prototype_key') != 'english-spearman-2':
        raise ValueError('Genuine matched prototype rig missing')
    lods = donor_lods()
    source_rig = lods[0][1]
    source_identity = [(b.name,b.parent.name if b.parent else None) for b in source_rig.data.bones]
    target_identity = [(b.name,b.parent.name if b.parent else None) for b in rig.data.bones]
    if source_identity != target_identity or len(source_identity) != 48:
        raise ValueError('Live source/target 48-bone hierarchy changed')
    matrix_delta = max(abs(source_rig.data.bones[name].matrix_local[i][j]
                           - rig.data.bones[name].matrix_local[i][j])
                       for name,_ in source_identity for i in range(4) for j in range(4))
    if matrix_delta > 1e-5:
        raise ValueError(f'Live bind rest matrices differ: {matrix_delta}')
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    candidate = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(candidate)
    material = lods[0][0].data.materials[0]
    meshes = []
    for number,(source,_) in enumerate(lods,1):
        if {g.name for g in source.vertex_groups} - {b.name for b in rig.data.bones}:
            raise ValueError(f'LOD{number} has unmapped weighted groups')
        clone = source.copy()
        clone.data = source.data.copy()
        candidate.objects.link(clone)
        clone.name = f'unit_mesh_lod{number}'
        clone.parent = rig
        clone.matrix_parent_inverse = Matrix.Identity(4)
        clone.matrix_world = rig.matrix_world @ source_rig.matrix_world.inverted() @ source.matrix_world
        for modifier in clone.modifiers:
            if modifier.type == 'ARMATURE':
                modifier.object = rig
        clone.data.materials.clear()
        clone.data.materials.append(material)
        meshes.append(clone)
    panel = addon_module('unit_prototype_panel')
    unit_export = addon_module('unit_export')
    action = panel.export_document(rig)
    action['material_name'] = material.name
    action['textures'] = ['albedo']
    if action != old_action or action['overrides'] or action['attachments']:
        raise ValueError('Control action/prototype changed; do not export altered clip owner')
    records = unit_export.skeleton_records(rig)
    FOLDER.mkdir(parents=True)
    unit_export.export_unit_model(rig, meshes, FOLDER / 'model.fbx', records,
                                  three_lods=False)
    shutil.copy2(CONTROL_FOLDER / 'albedo.png', FOLDER / 'albedo.png')
    (FOLDER / 'action.json').write_text(json.dumps(action, indent=2) + '\n', encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(SAVED_BLEND))
    write(RECEIPT, {
        'schema': 'ccp-060-archer-three-native-lod-export/v1',
        'status': 'source_export_only_installed_unit_add_not_yet_tested',
        'source_blend': str(BLEND), 'source_blend_sha256': sha(BLEND),
        'saved_blend': str(SAVED_BLEND), 'saved_blend_sha256': sha(SAVED_BLEND),
        'donor_manifest_sha256': sha(DONOR_MANIFEST),
        'prototype': 'english-spearman-2', 'fingerprint': control['prototype_fingerprint'],
        'matrix_max_delta': matrix_delta,
        'mesh_names': [obj.name for obj in meshes],
        'source_lods': [{'vertices':v,'triangles':t} for v,t in EXPECTED_COUNTS],
        'folder': str(FOLDER),
        'files': {p.name: {'sha256':sha(p),'bytes':p.stat().st_size} for p in FOLDER.iterdir() if p.is_file()},
        'no_clip_or_attachment_replacements': True,
        'generated_spearman_actor_prohibited_from_integration': True,
        'next_gate': 'Run installed unit-validate, then one isolated short-path unit-add/cook/readback; preserve any refusal. Do not infer far-LOD compliance from the source FBX.'
    })
    return {'folder':str(FOLDER),'receipt':str(RECEIPT),'blend':str(SAVED_BLEND)}


if __name__ == '__main__':
    print(json.dumps(main(),indent=2))
