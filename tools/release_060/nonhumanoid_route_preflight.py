"""Pin stock rig/group topology for mounted and siege source-route research.

This reads existing decoded donor evidence only. It does not create an FBX,
author a .rig file, run a native cook, or claim prototype admission.
"""
from __future__ import annotations

import json
from pathlib import Path

from common import CFG, OUT, guard, owned, read, sha, write

ROOT = OUT / "qualification/nonhumanoid-route-preflight"
RECEIPT = ROOT / "20261018-stock-rig-contract.json"
EXTENSION = Path(CFG["garrison_extension"])
EXPORTER = EXTENSION / "unit_export.py"
SAMPLE_RIG = OUT.parent.parent / "staging/release_060/l/Mods/u60l/project/source/art/scenario/garrison/u60l/units/u60l_archer_3lod_control/body/model.rig"
EXPECTED = {
    "horseman2": {"bones": 127, "palettes": [58, 46], "triangles": [1656, 576, 188, 1204, 498, 170],
                   "effects": ["unit"] * 6},
    "elephant": {"bones": 140, "palettes": [110], "triangles": [3349, 1272, 2713, 504, 1701, 166],
                 "effects": ["unit"] * 6},
    "siege_mangonel3": {"bones": 14, "palettes": [2, 12],
                         "triangles": [384, 96, 60, 4449, 1880, 1568],
                         "effects": ["Structure"] * 6},
}


def main() -> dict:
    guard()
    owned(RECEIPT)
    if RECEIPT.exists():
        raise FileExistsError(f"Preserve prior nonhumanoid contract: {RECEIPT}")
    exporter_text = EXPORTER.read_text(encoding="utf-8")
    for token in ("def skeleton_records(", "def export_unit_model(", "three_lods=False",
                  "require_valid(meshes", "for obj in meshes", "_prepare_mesh_copy"):
        if token not in exporter_text:
            raise RuntimeError(f"Installed generic exporter contract changed: {token}")
    rig_text = SAMPLE_RIG.read_text(encoding="utf-8")
    if (not rig_text.startswith("[HAVOK SKELETON DEFINITION FILE]")
            or "[BONES START]" not in rig_text or "[PARTITION START]" not in rig_text):
        raise RuntimeError("Installed generated .rig source example changed")
    results = {}
    for pilot, expected in EXPECTED.items():
        authoring = OUT / "pilots" / pilot / "authoring.json"
        receipt = read(authoring)
        if receipt["pilot"] != pilot or receipt["export_cook_native"] != "not run":
            raise RuntimeError(f"{pilot} pilot status changed")
        donor_path = Path(receipt["donor_manifest"])
        if sha(donor_path) != receipt["donor_manifest_sha256"]:
            raise RuntimeError(f"{pilot} verified donor changed")
        if sha(Path(receipt["blend"])) != receipt["blend_sha256"]:
            raise RuntimeError(f"{pilot} pilot blend changed")
        donor = read(donor_path)
        skeleton, geometry = donor["skeleton"], donor["geometry"]
        groups, palettes = geometry["groups"], skeleton["skin_palettes"]
        if (donor["status"] != "decoded" or skeleton["bone_count"] != expected["bones"]
                or [p["bone_count"] for p in palettes] != expected["palettes"]
                or [g["triangle_count"] for g in groups] != expected["triangles"]
                or [g["effect"].lower() for g in groups] != [x.lower() for x in expected["effects"]]
                or len(groups) != 6 or donor["rig_projection"]["unresolved_group_count"] != 0):
            raise RuntimeError(f"{pilot} native decoded group/palette contract changed")
        model = Path(skeleton["source"])
        geom = Path(geometry["source"]["path"])
        if sha(model) != skeleton["source_sha256"] or sha(geom) != geometry["source"]["sha256"]:
            raise RuntimeError(f"{pilot} native donor model/geometry changed")
        material_source = donor["material"]["source"]
        if sha(Path(material_source["path"])) != material_source["sha256"]:
            raise RuntimeError(f"{pilot} compiled stock material changed")
        rows = []
        for palette in palettes:
            rows.append({"name": palette["name"], "bone_count": palette["bone_count"],
                         "bone_names": [b["name"] for b in palette["bones"]],
                         "lods": [{"name": lod["name"], "material": lod["material"],
                                   "effect": lod["effect"], "skin_indices": lod["skin_indices"]}
                                  for lod in palette["lod_palettes"]]})
        results[pilot] = {
            "status": "verified_stock_multigroup_source_only",
            "authoring_receipt": str(authoring), "authoring_sha256": sha(authoring),
            "pilot_blend": receipt["blend"], "pilot_blend_sha256": receipt["blend_sha256"],
            "donor_manifest": str(donor_path), "donor_manifest_sha256": sha(donor_path),
            "native_model_sha256": sha(model), "native_geometry_sha256": sha(geom),
            "native_stock_rrmaterial_sha256": material_source["sha256"],
            "full_skeleton_bones": skeleton["bone_count"], "palette_count": len(palettes),
            "palettes": rows,
            "geometry_groups_in_native_order": [
                {"name": g["name"], "material": g["material"], "effect": g["effect"],
                 "vertices": g["vertex_count"], "triangles": g["triangle_count"]}
                for g in groups],
            "stock_material_names": [m["name"] for m in donor["material"]["materials"]],
            "prototype_build_admission": "none of these exact native rigs is an installed qualified Garrison prototype",
            "next_source_control": "claim Blender; inspect imported stock armature records and all six meshes; generic export_unit_model with three_lods=False only after group, material, UV and weight preflight",
            "next_native_gate": "derive and verify exact donor-specific .rig partitions and neutral source materials; fresh manual art-source cook/readback; preserve native stock RGO/RGM/RRMaterial if geometry pairing is later qualified",
        }
    report = {
        "schema": "ccp-060-nonhumanoid-stock-rig-route-preflight/v1",
        "status": "three_donors_pinned_generic_export_possible_manual_native_source_unproved",
        "installed_generic_exporter": str(EXPORTER), "installed_generic_exporter_sha256": sha(EXPORTER),
        "generic_exporter_scope": "stock-record-bearing imported rig and multiple bound meshes with three_lods=False; no prototype fingerprint or supported Build Unit claim",
        "generated_rig_format_example": str(SAMPLE_RIG), "generated_rig_format_example_sha256": sha(SAMPLE_RIG),
        "rig_format_observation": "HAVOK bone list plus named contiguous start/end partitions; sample is English spearman only and cannot be transplanted",
        "donors": results,
        "shared_blockers": [
            "No installed Build Unit prototype or fingerprint for these exact 127/140/14-bone rigs.",
            "No donor-specific editable .rig partition source has been identified; compiled skin LOD index arrays alone do not prove valid native authoring partitions.",
            "No fresh six-group FBX export/native cook/readback exists; topology, weighted corners, UV, material linkage, and original animator ownership remain unqualified."
        ],
        "mangonel_special_case": "Six groups use Structure/page rather than Unit material semantics; the neutral unit-material archer cook recipe is not transferable without a separate native structure-material source contract.",
        "blender_or_native_cook_run": False, "active_gameplay_or_prior_release_changed": False,
    }
    write(RECEIPT, report)
    return {"status": report["status"], "receipt": str(RECEIPT),
            "donors": {key: {"bones": row["full_skeleton_bones"],
                             "palettes": [p["bone_count"] for p in row["palettes"]],
                             "groups": len(row["geometry_groups_in_native_order"])}
                       for key, row in results.items()}}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
