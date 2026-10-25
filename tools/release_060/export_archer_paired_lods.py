"""PREPARED, NOT RUN: exact-name three-LOD Archer geometry pairing control.

Requires exclusive Blender handoff. Preserves the genuine prototype rig/action
and stock weighted LODs. Per-LOD material names follow the native RGM contract;
installed unit-add/cook may refuse this multi-material FBX and must not be bypassed.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/release_060"))
from common import ART, EXPORT, OUT, guard, owned, read, sha, write  # noqa: E402
from export_archer_three_native_lods import addon_module, donor_lods  # noqa: E402

BLEND = ART / "archer/archer-matched-control.blend"
BLEND_SHA = "6ce72edfd57af484f84295f6c06b41ebc96ae34a99a73cc1434ef6f0fb3af58c"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
STATIC = OUT / "qualification/archer-pairing-prep/static-contract.json"
CONTROL = OUT / "qualification/archer-matched-control-export.json"
CONTROL_FOLDER = EXPORT / "archer-matched-control"
FOLDER = EXPORT / "archer-paired-stock-lods"
RECEIPT = OUT / "qualification/archer-pairing-prep/export.json"
SAVED_BLEND = ART / "archer/archer-paired-stock-lods.blend"
COLLECTION = "CCP060_Archer_Paired_Stock_LODs"
BASE = "chi_ranged_bow_age02"
EXPECTED = ((988, 1236), (490, 522), (187, 155))


def main() -> dict:
    guard()
    for path in (FOLDER, RECEIPT, SAVED_BLEND):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier pairing export: {path}")
    if bpy.data.collections.get(COLLECTION):
        raise FileExistsError(f"Pairing candidate collection exists: {COLLECTION}")
    if Path(bpy.data.filepath).resolve() != BLEND.resolve() or sha(BLEND) != BLEND_SHA:
        raise RuntimeError("Open the pinned matched-control Blender file")
    static, donor, control = read(STATIC), read(STOCK), read(CONTROL)
    if (static["status"] != "stock_variant_contract_pinned_new_geometry_unproved"
            or sha(STOCK) != static["stock_manifest_sha256"]
            or control["prototype_key"] != "english-spearman-2"):
        raise RuntimeError("Static donor/prototype pairing inputs changed")
    prior_action = read(CONTROL_FOLDER / "action.json")
    if sha(CONTROL_FOLDER / "action.json") != control["files"]["action.json"]["sha256"]:
        raise RuntimeError("Pinned prototype action changed")
    rig = bpy.data.objects.get("CCP060 English Spearman II exact-match rig")
    if rig is None or rig.type != "ARMATURE" or rig.get("garrison_prototype_key") != "english-spearman-2":
        raise RuntimeError("Genuine exact-match prototype rig missing")
    lods = donor_lods()
    if len(lods) != 3 or any((len(mesh.data.vertices), sum(len(face.vertices)-2 for face in mesh.data.polygons))
                                != EXPECTED[n-1] for n, (mesh, _) in enumerate(lods, 1)):
        raise RuntimeError("Pinned donor LOD counts changed")
    source_rig = lods[0][1]
    source_bones = [(b.name, b.parent.name if b.parent else None) for b in source_rig.data.bones]
    target_bones = [(b.name, b.parent.name if b.parent else None) for b in rig.data.bones]
    if source_bones != target_bones or len(source_bones) != 48:
        raise RuntimeError("Native/prototype bone hierarchy changed")
    matrix_delta = max(abs(source_rig.data.bones[name].matrix_local[i][j]
                           - rig.data.bones[name].matrix_local[i][j])
                       for name, _ in source_bones for i in range(4) for j in range(4))
    if matrix_delta > 1e-5:
        raise RuntimeError(f"Rest bind matrices differ: {matrix_delta}")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    if any(bpy.data.materials.get(f"lod{n}") for n in (1, 2, 3)):
        raise RuntimeError("Exact stock material names already occupied in scene")
    candidate = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(candidate)
    meshes, material_copies = [], []
    for number, (source, _) in enumerate(lods, 1):
        expected_group = static["required_geometry_and_palette_lods"][number-1]
        if (expected_group["geometry_group"]["name"] != BASE
                or expected_group["geometry_group"]["material"] != f"lod{number}"
                or expected_group["skin_palette_name"] != f"{BASE}_lod{number}"):
            raise RuntimeError(f"Stock RGM group/material contract changed at LOD{number}")
        if {group.name for group in source.vertex_groups} - {bone.name for bone in rig.data.bones}:
            raise RuntimeError(f"Unmapped weighted groups in LOD{number}")
        clone = source.copy()
        clone.data = source.data.copy()
        candidate.objects.link(clone)
        clone.name = f"{BASE}_lod{number}"
        clone.data.name = f"{BASE}_lod{number}_mesh"
        clone.parent = rig
        clone.matrix_parent_inverse = Matrix.Identity(4)
        clone.matrix_world = rig.matrix_world @ source_rig.matrix_world.inverted() @ source.matrix_world
        for modifier in clone.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = rig
        material = source.data.materials[0].copy()
        material.name = f"lod{number}"
        if material.name != f"lod{number}":
            raise RuntimeError("Blender renamed an exact stock material")
        material_copies.append(material)
        clone.data.materials.clear()
        clone.data.materials.append(material)
        meshes.append(clone)
    panel = addon_module("unit_prototype_panel")
    unit_export = addon_module("unit_export")
    action = panel.export_document(rig)
    action["material_name"] = "lod1"
    action["textures"] = ["albedo"]
    expected_action = dict(prior_action)
    expected_action["material_name"] = "lod1"
    if action != expected_action or action["overrides"] or action["attachments"]:
        raise RuntimeError("Prototype fingerprint/action/bones or animation ownership changed")
    FOLDER.mkdir(parents=True)
    records = unit_export.skeleton_records(rig)
    unit_export.export_unit_model(rig, meshes, FOLDER / "model.fbx", records, three_lods=False)
    shutil.copy2(CONTROL_FOLDER / "albedo.png", FOLDER / "albedo.png")
    (FOLDER / "action.json").write_text(json.dumps(action, indent=2) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(SAVED_BLEND))
    write(RECEIPT, {
        "schema": "ccp-060-archer-paired-stock-lod-export/v1",
        "status": "source_export_only_not_validated_or_cooked",
        "source_blend": str(BLEND), "source_blend_sha256": BLEND_SHA,
        "saved_blend": str(SAVED_BLEND), "saved_blend_sha256": sha(SAVED_BLEND),
        "stock_manifest_sha256": sha(STOCK), "static_contract_sha256": sha(STATIC),
        "prototype": "english-spearman-2", "fingerprint": control["prototype_fingerprint"],
        "rest_matrix_max_delta": matrix_delta,
        "geometry_group_basename_required": BASE,
        "mesh_names": [obj.name for obj in meshes],
        "material_names": [mat.name for mat in material_copies],
        "action_primary_material": action["material_name"],
        "source_lods": [{"vertices": v, "triangles": t} for v, t in EXPECTED],
        "folder": str(FOLDER),
        "files": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                  for p in FOLDER.iterdir() if p.is_file()},
        "no_clip_or_attachment_replacements": True,
        "generated_spearman_actor_rgo_rhka_prohibited_from_integration": True,
        "next_gate": "Installed unit-validate, then one isolated unit-add/cook/readback. Require compiled RRGeom groups and per-LOD material names to exactly match stock RGM/RRMaterial before any selective eight-member test archive.",
    })
    return {"folder": str(FOLDER), "receipt": str(RECEIPT), "blend": str(SAVED_BLEND)}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
