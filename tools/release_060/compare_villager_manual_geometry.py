"""Compare both real Chinese villager donors to fresh private native geometry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from assemble_archer_geometry_pairing import _scalar_delta
from compare_archer_three_lod_manual_uvfix import compare_lod
from common import OUT, guard, owned, read, sha, write


def main(gender: str):
    guard()
    contract_file = OUT / "qualification/villager-geometry-route/contract-v2.json"
    contract = read(contract_file)["genders"][gender]
    donor_file = Path(contract["donor_manifest"])
    base = OUT / f"qualification/villager-geometry-route/20261018-resume/{gender}/manual"
    decode_file, extract_file = base / "decode-local.json", base / "archive-extract.json"
    report_file = base / "stock-geometry-comparison-v2.json"
    owned(report_file)
    if report_file.exists(): raise FileExistsError("Preserve prior villager geometry comparison")
    decoded = read(decode_file)
    if decoded["status"] != "decoded_private_model_no_stock_owner_scan":
        raise RuntimeError("Private villager decoder not successful")
    compiled_file = Path(decoded["decoded_manifest"])
    if sha(compiled_file) != decoded["decoded_manifest_sha256"] or sha(donor_file) != contract["donor_manifest_sha256"]:
        raise RuntimeError("Pinned native model input drift")
    stock, cooked = read(donor_file), read(compiled_file)
    groups_a, groups_b = stock["geometry"]["groups"], cooked["geometry"]["groups"]
    result = {"schema": "ccp-060-villager-three-lod-native-geometry-comparison/v1",
              "status": "comparison_started", "gender": gender,
              "stock_manifest": str(donor_file), "stock_manifest_sha256": sha(donor_file),
              "compiled_manifest": str(compiled_file), "compiled_manifest_sha256": sha(compiled_file),
              "archive_sha256": read(extract_file)["archive_sha256"],
              "compiled_rrgeom_sha256": read(extract_file)["extracted"][".rrgeom"]["sha256"],
              "diagnostic_material_and_generated_english_rgo_excluded_from_pair": True,
              "original_chinese_animation_owner_preserved_in_later_pair": True,
              "native_game_not_tested": True}
    try:
        if stock["status"] != "decoded" or cooked["status"] != "decoded":
            raise RuntimeError("Stock or cooked manifest not decoded")
        if len(groups_a) != len(groups_b) or len(groups_a) != 3:
            raise RuntimeError("Expected exactly three native LOD groups")
        result["skeleton_bone_counts"] = [len(stock["skeleton"]["bones"]), len(cooked["skeleton"]["bones"])]
        result["skin_palette_bone_counts"] = [len(stock["skeleton"]["skin_palettes"][0]["bones"]),
                                               len(cooked["skeleton"]["skin_palettes"][0]["bones"])]
        a, b = cooked["skeleton"], stock["skeleton"]
        keys = ("index", "name", "parent_index", "parent_name")
        pkeys = ("palette_index", "name", "parent_index", "parent_name", "skeleton_index")
        ab, bb = a["skin_palettes"][0]["bones"], b["skin_palettes"][0]["bones"]
        skeleton_identity = (len(a["bones"]) == len(b["bones"]) == 73 and
                             all(tuple(x[k] for k in keys) == tuple(y[k] for k in keys)
                                 for x, y in zip(a["bones"], b["bones"])))
        palette_identity = (len(ab) == len(bb) == 46 and
                            all(tuple(x[k] for k in pkeys) == tuple(y[k] for k in pkeys)
                                for x, y in zip(ab, bb)))
        bind = {
            "skeleton_identity_exact": skeleton_identity,
            "palette_identity_exact": palette_identity,
            "lod_palette_records_exact": a["skin_palettes"][0]["lod_palettes"] == b["skin_palettes"][0]["lod_palettes"],
            "max_local_reference_scalar_delta": max(_scalar_delta(x["local_reference_transform"], y["local_reference_transform"])
                                                    for x, y in zip(a["bones"], b["bones"])),
            "max_global_reference_scalar_delta": max(_scalar_delta(x["global_reference_transform"], y["global_reference_transform"])
                                                     for x, y in zip(a["bones"], b["bones"])),
            "max_palette_global_scalar_delta": max(_scalar_delta(x["global_reference_transform"], y["global_reference_transform"])
                                                 for x, y in zip(ab, bb)),
            "max_inverse_bind_scalar_delta": max(_scalar_delta(x["inverse_bind_transform"], y["inverse_bind_transform"])
                                             for x, y in zip(ab, bb)),
            "numeric_tolerance": 0.0002,
        }
        result["rig_compatibility"] = bind
        result["three_lods"] = [compare_lod(a, b, n) for n, (a, b) in enumerate(zip(groups_a, groups_b), 1)]
        names = [(g["name"], g["material"], g["effect"]) for g in groups_b]
        required = [(contract["base"], f"lod{n}", "unit") for n in (1, 2, 3)]
        result["group_material_effect"] = names
        passed = (all((bind["skeleton_identity_exact"], bind["palette_identity_exact"],
                          bind["lod_palette_records_exact"]))
                  and max(bind[k] for k in ("max_local_reference_scalar_delta",
                                                 "max_global_reference_scalar_delta",
                                                 "max_palette_global_scalar_delta",
                                                 "max_inverse_bind_scalar_delta")) <= bind["numeric_tolerance"]
                  and result["skeleton_bone_counts"] == [73, 73]
                  and result["skin_palette_bone_counts"] == [46, 46]
                  and names == required
                  and all(row["passed"] and row["stock_and_compiled_skin_palette_lod_record_exact"]
                          and row["stock_and_compiled_vertex_stride_exact"]
                          and row["stock_and_compiled_index_stride_exact"] for row in result["three_lods"]))
        result["status"] = "three_native_lods_topology_weights_uv_bind_qualified" if passed else "three_lod_comparison_failed"
    except Exception as error:
        result["status"] = "three_lod_comparison_error_preserved"
        result["error"] = f"{type(error).__name__}: {error}"
    write(report_file, result)
    return {"status": result["status"], "gender": gender, "report": str(report_file),
            "lods": [{"triangles": x["compiled_triangles"], "topology": x["triangle_topology_multiset_exact"],
                      "weights": x["weighted_corner_multiset_exact_after_influence_order_normalization"],
                      "uv_max": x["maximum_uv_scalar_delta"]} for x in result.get("three_lods", [])],
            "error": result.get("error")}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gender", choices=("male", "female"))
    print(json.dumps(main(ap.parse_args().gender), indent=2))
