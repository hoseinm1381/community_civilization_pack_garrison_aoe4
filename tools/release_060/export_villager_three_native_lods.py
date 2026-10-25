"""PREPARED ONLY: export genuine-prototype male/female villager 3-LOD controls.

Run only with an exclusive Blender handoff and the pinned pilot review .blend
open. This preserves native Chinese donor vertex groups/weights and source scene,
but a Chinese 46-bone skin palette cook remains an explicit experiment; English
prototype palette has only 45. No generated actor/animator is for integration.

In claimed live Blender: import this script and call main('male') or main('female').
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
from export_archer_matched_control import addon_module  # noqa: E402

CONTRACT = OUT / "qualification/villager-geometry-route/contract-v2.json"
DIAGNOSTIC_ALBEDO = OUT / "qualification/archer-stock-albedo-atlas.png"
PROTOTYPE_KEY = "english-villager-1"


def donor_lods(pilot: str, base: str, expected: list[dict]):
    # LOD1 moved to exact_stock_mesh during pilot authoring; LOD2/3 stayed in
    # the Garrison projection collection. Never select the dyed or draft copy.
    names = (f"CCP060_{pilot}_exact_stock_mesh",
             f"CCP060_{pilot}_body_stock_reference")
    cols = [bpy.data.collections.get(name) for name in names]
    if any(col is None for col in cols):
        raise RuntimeError(f"Expected both pinned stock collections: {names}")
    pool = set(obj for col in cols for obj in col.all_objects if obj.type == "MESH")
    result = []
    for row in expected:
        number = row["lod"]
        matches = [obj for obj in pool if base.lower() in obj.name.lower()
                   and f"lod{number}" in obj.name.lower()
                   and len(obj.data.vertices) == row["vertices"]
                   and sum(len(face.vertices)-2 for face in obj.data.polygons) == row["triangles"]]
        if len(matches) != 1:
            raise RuntimeError(f"LOD{number} donor ambiguity: {[obj.name for obj in matches]}")
        mesh = matches[0]
        if len(mesh.data.materials) != 1 or not mesh.data.uv_layers:
            raise RuntimeError(f"LOD{number} lacks exact donor material/UV")
        rigs = [modifier.object for modifier in mesh.modifiers
                if modifier.type == "ARMATURE" and modifier.object is not None]
        if len(rigs) != 1:
            raise RuntimeError(f"LOD{number} expected exactly one native armature")
        result.append((mesh, rigs[0]))
    if len({rig.as_pointer() for _, rig in result}) != 1:
        raise RuntimeError("Donor LOD armatures do not match")
    return result


def main(gender: str):
    guard()
    contract = read(CONTRACT)
    if contract["status"] != "source_contract_prepared_native_palette_cook_unproved":
        raise RuntimeError("Villager source contract is not in prepared state")
    if gender not in contract["genders"]:
        raise ValueError("gender must be male or female")
    row = contract["genders"][gender]
    prototype = contract["prototype"]
    donor = read(Path(row["donor_manifest"]))
    if (sha(Path(row["donor_manifest"])) != row["donor_manifest_sha256"]
            or sha(Path(prototype["manifest"])) != prototype["manifest_sha256"]
            or sha(DIAGNOSTIC_ALBEDO) != "f231747e68cd39bd1c6edcc7ecfc074f79013e4644bf0debb98d46650f0dacdc"):
        raise RuntimeError("Pinned donor/prototype/diagnostic texture changed")
    blend = Path(row["pilot_blend"])
    if Path(bpy.data.filepath).resolve() != blend.resolve() or sha(blend) != row["pilot_blend_sha256"]:
        raise RuntimeError("Open the pinned gender pilot blend before export")
    pilot, base = row["pilot"], row["base"]
    folder = owned(EXPORT / "villager-geometry-route" / gender / "stock-three-lod-control")
    saved = owned(ART / "villager-geometry-route" / gender / "stock-three-lod-control.blend")
    receipt = owned(OUT / "qualification/villager-geometry-route" / gender / "export.json")
    collection_name = f"CCP060_{gender}_Villager_3LOD_Geometry_Control"
    if any(p.exists() for p in (folder, saved, receipt)) or bpy.data.collections.get(collection_name):
        raise FileExistsError("Preserve earlier villager geometry export candidate")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    source_lods = donor_lods(pilot, base, row["lods"])
    source_rig = source_lods[0][1]
    panel = addon_module("unit_prototype_panel")
    unit_export = addon_module("unit_export")
    document = read(Path(prototype["manifest"]))
    if document["prototype"]["key"] != PROTOTYPE_KEY or document["fingerprint"] != prototype["fingerprint"]:
        raise RuntimeError("Genuine installed prototype identity changed")
    rig = panel.create_unit(document, bpy.context)
    if rig.get("garrison_prototype_key") != PROTOTYPE_KEY:
        raise RuntimeError("Garrison did not create the expected prototype rig")
    candidate = rig.users_collection[0]
    candidate.name = collection_name
    rig.name = f"CCP060 {gender} English Villager I source rig"
    names = [(b.name, b.parent.name if b.parent else None) for b in source_rig.data.bones]
    target = [(b.name, b.parent.name if b.parent else None) for b in rig.data.bones]
    if len(names) != 73 or names != target:
        raise RuntimeError("Live Chinese donor and English prototype hierarchy differ")
    max_matrix_delta = max(abs(source_rig.data.bones[name].matrix_local[i][j]
                               - rig.data.bones[name].matrix_local[i][j])
                           for name, _ in names for i in range(4) for j in range(4))
    if max_matrix_delta > 1e-5:
        raise RuntimeError(f"Live donor/prototype rest bind matrix differs: {max_matrix_delta}")
    meshes, uv_rows = [], []
    for number, (source, _) in enumerate(source_lods, 1):
        unknown = {g.name for g in source.vertex_groups} - {bone.name for bone in rig.data.bones}
        if unknown:
            raise RuntimeError(f"LOD{number} has unmapped Chinese weights: {sorted(unknown)}")
        clone = source.copy()
        clone.data = source.data.copy()
        candidate.objects.link(clone)
        clone.name = f"{base}_lod{number}"
        clone.data.name = f"{base}_lod{number}_mesh"
        clone.parent = rig
        clone.matrix_parent_inverse = Matrix.Identity(4)
        clone.matrix_world = rig.matrix_world @ source_rig.matrix_world.inverted() @ source.matrix_world
        for modifier in clone.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = rig
        material = source.data.materials[0].copy()
        material.name = f"lod{number}"
        if material.name != f"lod{number}":
            raise RuntimeError("Blender material rename collision; cannot preserve native LOD ID")
        clone.data.materials.clear()
        clone.data.materials.append(material)
        old_uv = source.data.uv_layers.active.data
        new_uv = clone.data.uv_layers.active.data
        if len(old_uv) != len(new_uv) or len(new_uv) != len(clone.data.loops):
            raise RuntimeError(f"LOD{number} UV corner count changed")
        for before, after in zip(old_uv, new_uv):
            after.uv.x, after.uv.y = before.uv.x, 1.0 - before.uv.y
        uv_rows.append({"lod": number, "corners": len(new_uv), "transform": "u unchanged; v := 1 - donor v"})
        meshes.append(clone)
    if len(donor["skeleton"]["skin_palettes"][0]["bones"]) != 46:
        raise RuntimeError("Chinese 46-bone palette changed; never silently remap to English 45")
    rig.garrison_unit.mesh = meshes[0]
    rig.garrison_unit.build_name = f"ccp060_{gender}_villager_native_geometry_probe"
    rig.garrison_unit.albedo = str(DIAGNOSTIC_ALBEDO)
    action = panel.export_document(rig)
    if action["prototype"] != PROTOTYPE_KEY or action["fingerprint"] != prototype["fingerprint"]:
        raise RuntimeError("Genuine prototype action identity changed")
    if action["overrides"] or action["attachments"]:
        raise RuntimeError("Control must not replace clips/equipment")
    action["material_name"] = "lod1"
    action["textures"] = ["albedo"]
    folder.mkdir(parents=True)
    records = unit_export.skeleton_records(rig)
    unit_export.export_unit_model(rig, meshes, folder / "model.fbx", records, three_lods=False)
    shutil.copy2(DIAGNOSTIC_ALBEDO, folder / "albedo.png")
    (folder / "action.json").write_text(json.dumps(action, indent=2) + "\n", encoding="utf-8")
    saved.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(saved))
    write(receipt, {"schema": "ccp-060-villager-three-native-lod-export/v1",
                    "status": "source_export_only_native_46_bone_palette_unproved",
                    "gender": gender, "source_blend": str(blend), "source_blend_sha256": row["pilot_blend_sha256"],
                    "saved_blend": str(saved), "saved_blend_sha256": sha(saved),
                    "contract_sha256": sha(CONTRACT), "donor_manifest_sha256": sha(Path(row["donor_manifest"])),
                    "prototype_key": PROTOTYPE_KEY, "prototype_fingerprint": prototype["fingerprint"],
                    "live_rest_matrix_max_delta": max_matrix_delta,
                    "source_palette_bones": 46, "english_prototype_palette_bones": 45,
                    "mesh_names": [obj.name for obj in meshes], "materials": [f"lod{x}" for x in (1, 2, 3)],
                    "lods": row["lods"], "uv_preexport": uv_rows,
                    "diagnostic_texture_only": True,
                    "original_chinese_animation_owner_preserved_for_later_pair": True,
                    "generated_english_actor_rgo_rhka_prohibited_from_integration": True,
                    "folder": str(folder),
                    "files": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                              for p in folder.iterdir() if p.is_file()},
                    "next_gate": "Installed unit-validate, then independent fresh native geometry-only cook/readback. Demand original Chinese 73/46 skin palette and three direct-UV/native topology/weight equivalences before stock-material pairing."})
    return {"folder": str(folder), "receipt": str(receipt), "blend": str(saved)}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"male", "female"}:
        raise SystemExit("Use main('male') or main('female') in a claimed Blender session")
    print(json.dumps(main(sys.argv[1]), indent=2))
