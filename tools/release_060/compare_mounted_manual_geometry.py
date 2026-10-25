"""Compare fresh mounted cook against its exact six-group native stock donor."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from common import OUT, guard, owned, read, sha, write
from compare_archer_three_lod_manual_uvfix import compare_lod
from compare_mangonel_manual_geometry import delta

CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
TOLERANCE = 0.0002


def rig_check(source: dict, cooked: dict, expected_bones: int, expected_palettes: list[int]):
    old, new = source["skeleton"], cooked["skeleton"]
    keys = ("index", "name", "parent_index", "parent_name")
    a, b = old["bones"], new["bones"]
    bone_identity = (len(a) == len(b) == expected_bones and
                     all(tuple(x[k] for k in keys) == tuple(y[k] for k in keys) for x, y in zip(a, b)))
    pa, pb = old["skin_palettes"], new["skin_palettes"]
    palette_keys = ("palette_index", "name", "parent_index", "parent_name", "skeleton_index")
    palette_identity = (len(pa) == len(pb) == len(expected_palettes)
                        and [len(p["bones"]) for p in pa] == expected_palettes
                        and [len(p["bones"]) for p in pb] == expected_palettes
                        and all(tuple(x[k] for k in palette_keys) == tuple(y[k] for k in palette_keys)
                                for ap, bp in zip(pa, pb) for x, y in zip(ap["bones"], bp["bones"])))
    maxima = {}
    if bone_identity:
        for key in ("local_reference_transform", "global_reference_transform"):
            maxima["skeleton_" + key] = max(delta(x[key], y[key]) for x, y in zip(a, b))
    if palette_identity:
        for key in ("global_reference_transform", "inverse_bind_transform"):
            maxima["palette_" + key] = max(delta(x[key], y[key])
                                             for ap, bp in zip(pa, pb) for x, y in zip(ap["bones"], bp["bones"]))
    lod_palettes_exact = palette_identity and all(x["lod_palettes"] == y["lod_palettes"]
                                                 for x, y in zip(pa, pb))
    passed = bone_identity and palette_identity and lod_palettes_exact and all(v <= TOLERANCE for v in maxima.values())
    return {"passed": passed, "ordered_full_skeleton_identity": bone_identity,
            "ordered_native_palette_identity": palette_identity,
            "three_lod_palette_records_exact": lod_palettes_exact,
            "maximum_scalar_deltas": maxima, "native_quantization_tolerance": TOLERANCE}


def main(kind: str):
    guard()
    if kind not in {"horseman2", "elephant"}:
        raise ValueError(kind)
    folder = owned(OUT / "qualification/nonhumanoid-route-preflight" / kind / "manual")
    result_path = owned(folder / "six-group-comparison.json")
    if result_path.exists():
        raise FileExistsError("Preserve prior mounted comparison")
    row = read(CONTRACT)["donors"][kind]
    rb = read(folder / "readback.json")
    if rb["status"] != "archive_verified_private_model_decoded_pending_geometry_comparison":
        raise RuntimeError("Mounted private readback missing")
    source_path, cooked_path = Path(row["donor_manifest"]), Path(rb["decoded_manifest"])
    if sha(source_path) != row["donor_manifest_sha256"] or sha(cooked_path) != rb["decoded_manifest_sha256"]:
        raise RuntimeError("Native source/candidate manifest drift")
    source, cooked = read(source_path), read(cooked_path)
    old_groups, new_groups = source["geometry"]["groups"], cooked["geometry"]["groups"]
    expected_palettes = [p["bone_count"] for p in row["palettes"]]
    rig = rig_check(source, cooked, row["full_skeleton_bones"], expected_palettes)
    group_rows = []
    if len(old_groups) == len(new_groups) == 6:
        for index, (x, y) in enumerate(zip(old_groups, new_groups), 1):
            try:
                group_rows.append(compare_lod(x, y, index))
            except (RuntimeError, ValueError) as error:
                group_rows.append({"lod": index, "passed": False,
                                   "source_triangles": x["triangle_count"],
                                   "compiled_triangles": y["triangle_count"],
                                   "source_vertices": x["vertex_count"],
                                   "compiled_vertices": y["vertex_count"],
                                   "source_first_position": x["positions"][0],
                                   "compiled_first_position": y["positions"][0],
                                   "geometry_comparison_error": f"{type(error).__name__}: {error}"})
    old_identity = [(g["name"], g["material"], g["effect"].lower()) for g in old_groups]
    new_identity = [(g["name"], g["material"], g["effect"].lower()) for g in new_groups]
    passed = (rig["passed"] and old_identity == new_identity and len(group_rows) == 6
              and all(group["passed"] and group["stock_and_compiled_skin_palette_lod_record_exact"]
                      and group["stock_and_compiled_vertex_stride_exact"]
                      and group["stock_and_compiled_index_stride_exact"] for group in group_rows))
    result = {"schema": "ccp-060-mounted-stock-rig-six-group-native-comparison/v1",
              "status": "six_groups_native_geometry_qualified" if passed else "native_geometry_mismatch_preserved",
              "kind": kind, "stock_manifest_sha256": sha(source_path), "cooked_manifest_sha256": sha(cooked_path),
              "native_archive_sha256": rb["archive_sha256"],
              "native_rrgeom_sha256": rb["extracted"][".rrgeom"]["sha256"],
              "rig": rig, "stock_group_identities": old_identity,
              "cooked_group_identities": new_identity, "groups": group_rows,
              "diagnostic_material_rgm_rgo_not_for_final_pair": True,
              "original_stock_rgm_rgo_rrmaterial_rhka_required_for_final_pair": True,
              "worker_elephant_riderless_geometry_is_later_distinct_art_gate": kind == "elephant",
              "native_game_and_client_import_unproved": True}
    write(result_path, result)
    if not passed:
        raise RuntimeError("Mounted native geometry mismatch preserved: " + str(result_path))
    return {"status": result["status"], "kind": kind, "report": str(result_path)}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=2))
