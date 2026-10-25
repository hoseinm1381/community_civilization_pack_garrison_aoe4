"""Pin male/female Age-I weighted donor and genuine prototype export contracts.

Read-only inputs; writes a task-owned qualification receipt. This is a source
preparation gate, never a palette-admission or runtime claim.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from common import ART, CORE, OUT, guard, read, sha, write

REPORT = OUT / "inventory/villager-rig-comparison.json"
DEST = OUT / "qualification/villager-geometry-route/contract-v2.json"
EXPECTED = {
    "male": ("male_villager1", "chi_villager_male_age01", ((836, 1188), (376, 434), (165, 148)),
             "b3dbe6bac2ca8c0f05a457cb06d15c6f433fae0b7424dab304a968c407ad41a6",
             "51c16bb1a686dad4a1f5adf6f65b9af0e0d7ef579d0602de26051e08d3bd4628",
             "32860a447721858bd20c5a7ce53e61e154b5cb7f346102ee59c6a3f795d735c1"),
    "female": ("female_villager1", "chi_villager_female_age01", ((897, 1312), (345, 406), (194, 188)),
               "621e7e5a3153153fa1074de06767ec8a0a33170115977901b33a6808fb2b480d",
               "820ce2d611fe675f50e6537e26c87dcacde5bc879f02512159ecf31b81e1ef4e",
               "affa75c260536a4d1ea02db3d25f2fd5cb1a53e281e42d1aa6831f8a3b4838e5"),
}


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def main():
    guard()
    if DEST.exists():
        raise FileExistsError(f"Preserve previous qualification: {DEST}")
    report = read(REPORT)
    if report["status"] != "hash_pinned_static_rig_and_palette_comparison_complete":
        raise RuntimeError("Villager comparison report is not qualified")
    proto = report["input_evidence"]["english_supported_prototype"]
    if proto["prototype_key"] != "english-villager-1" or proto["prototype_status"] != "Build supported":
        raise RuntimeError("Supported prototype changed")
    if sha(CORE) != proto["garrison_core_sha256"]:
        raise RuntimeError("Installed core changed since prototype probe")
    prototype_path = Path(proto["prototype_manifest_path"])
    if sha(prototype_path) != proto["prototype_manifest_sha256"]:
        raise RuntimeError("Prototype manifest changed")
    result = {"schema": "ccp-060-villager-geometry-route/v2",
              "status": "source_contract_prepared_native_palette_cook_unproved",
              "comparison": {"path": str(REPORT), "sha256": sha(REPORT)},
              "prototype": {"key": proto["prototype_key"], "fingerprint": proto["prototype_fingerprint"],
                            "manifest": str(prototype_path), "manifest_sha256": sha(prototype_path),
                            "core_sha256": sha(CORE), "animator_owner": proto["animator_owner"],
                            "bone_count": 73, "prototype_palette_bones": 45},
              "genders": {}, "boundary": {
                  "chinese_skin_palette_bones": 46,
                  "palette_mismatch": "Chinese adds active metarig_neck2; head parent and all LOD skin-index arrays differ from English prototype. No exact-palette admission.",
                  "normal_garrison_validation": "must run on genuine English prototype action/fingerprint; never forge or weaken validator",
                  "manual_geometry_source": "fresh blank private native project with three neutral diagnostic unit materials; preserve failed normal route separately",
                  "material_pair": "only after Chinese 73/46 bind, all three native geometry groups, topology, weights, direct UV and normal tolerances pass; stock RRMaterial/RGM/RGO unchanged",
                  "native_animator": "original Chinese base_civilian owner remains; playback/game client unproved",
                  "blender": "script prepared only; artist currently owns exclusive live Blender slot"}}
    for sex, (pilot, base, counts, receipt_sha, donor_sha, blend_sha) in EXPECTED.items():
        authoring = OUT / "pilots" / pilot / "authoring.json"
        if sha(authoring) != receipt_sha:
            raise RuntimeError(f"{sex} pilot receipt changed")
        row = read(authoring)
        donor_path = Path(row["donor_manifest"])
        blend_path = Path(row["blend"])
        if sha(donor_path) != donor_sha or row["donor_manifest_sha256"] != donor_sha:
            raise RuntimeError(f"{sex} donor manifest changed")
        if sha(blend_path) != blend_sha or row["blend_sha256"] != blend_sha:
            raise RuntimeError(f"{sex} pilot blend changed")
        donor = read(donor_path)
        previous = report["input_evidence"][f"chinese_{sex}_villager_i"]
        old = read(Path(previous["manifest_path"]))
        # The later verified pilot manifests have different cache provenance,
        # but the actual native model/geometry/skin records must remain equal.
        for key in ("bones", "rest_pose", "skin_palettes"):
            if canonical(donor["skeleton"][key]) != canonical(old["skeleton"][key]):
                raise RuntimeError(f"{sex} current-vs-compared {key} differs")
        if canonical(donor["geometry"]["groups"]) != canonical(old["geometry"]["groups"]):
            raise RuntimeError(f"{sex} current-vs-compared geometry differs")
        if sha(Path(donor["skeleton"]["source"])) != previous["model_source_sha256"]:
            raise RuntimeError(f"{sex} model source bytes drift")
        if sha(Path(donor["geometry"]["source"]["path"])) != previous["geometry_source_sha256"]:
            raise RuntimeError(f"{sex} geometry source bytes drift")
        groups = donor["geometry"]["groups"]
        if len(groups) != 3 or len(donor["skeleton"]["bones"]) != 73:
            raise RuntimeError(f"{sex} native LOD or skeleton count changed")
        palette = donor["skeleton"]["skin_palettes"]
        if len(palette) != 1 or palette[0]["bone_count"] != 46 or len(palette[0]["lod_palettes"]) != 3:
            raise RuntimeError(f"{sex} Chinese active palette contract changed")
        lods = []
        for idx, (group, (vertices, triangles)) in enumerate(zip(groups, counts), 1):
            if (group["name"] != base or group["material"] != f"lod{idx}"
                    or group["effect"] != "unit" or len(group["positions"]) != vertices
                    or len(group["triangles"]) != triangles):
                raise RuntimeError(f"{sex} LOD{idx} group/material/topology contract changed")
            lod_palette = palette[0]["lod_palettes"][idx-1]
            if lod_palette["name"] != f"{base}_lod{idx}" or lod_palette["material"] != f"lod{idx}" or lod_palette["effect"] != "unit":
                raise RuntimeError(f"{sex} LOD{idx} skin palette identity changed")
            lods.append({"lod": idx, "mesh_name": f"{base}_lod{idx}", "group_name": base,
                         "material_name": f"lod{idx}", "effect": "unit",
                         "vertices": vertices, "triangles": triangles,
                         "skin_palette_name": lod_palette["name"],
                         "skin_indices": lod_palette["skin_indices"]})
        materials = donor["material"]["materials"]
        if [m["name"] for m in materials] != ["lod1", "lod2", "lod3"]:
            raise RuntimeError(f"{sex} stock material LOD names changed")
        material_slots = []
        for number, material in enumerate(materials, 1):
            blocks = material["blocks"]
            if len(blocks) != 1 or blocks[0]["name"] != "UnitParams":
                raise RuntimeError(f"{sex} lod{number} material block changed")
            material_slots.append({"lod": number, "class": material["class"],
                                   "textures": [{"slot": t["name"],
                                                 "logical_path": t.get("logical_path")}
                                                for t in blocks[0]["textures"]]})
        source_model = donor["skeleton"]["source"]
        source_geom = donor["geometry"]["source"]["path"]
        result["genders"][sex] = {
            "pilot": pilot, "base": base,
            "authoring_receipt": str(authoring), "authoring_sha256": receipt_sha,
            "pilot_blend": str(blend_path), "pilot_blend_sha256": blend_sha,
            "donor_manifest": str(donor_path), "donor_manifest_sha256": donor_sha,
            "model_source": source_model, "model_sha256": sha(source_model),
            "geometry_source": source_geom, "geometry_sha256": sha(source_geom),
            "stock_rgm_source": source_model, "stock_rrmaterial_source": donor["material"]["source"],
            "skeleton_bones": 73, "chinese_palette_bones": 46,
            "palette_names": [b["name"] for b in palette[0]["bones"]],
            "lods": lods, "stock_unit_materials": material_slots,
            "uv_export_transform": "on cloned export meshes only: u unchanged, v := 1 - donor v; compare native direct UV after cook",
            "pilot_stock_collection": f"CCP060_{pilot}_exact_stock_mesh",
            "pilot_remodel_collection": f"CCP060_{pilot}_remodel",
            "next_gate": "live Garrison panel.create_unit from pinned English prototype then source rig matrix check and 3 native LOD export; fresh native 73/46 cook/readback required"}
    write(DEST, result)
    return {"contract": str(DEST), "genders": list(result["genders"]), "status": result["status"]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
