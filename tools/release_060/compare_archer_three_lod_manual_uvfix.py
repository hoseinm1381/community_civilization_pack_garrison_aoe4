"""PREPARED, NOT RUN: prove UV-corrected three-LOD geometry and weights."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from assemble_archer_geometry_pairing import rig_compatibility
from common import OUT, guard, owned, read, sha, write

DONOR = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
DECODE = OUT / "qualification/archer-pairing-prep/manual-uvfix/decode.json"
READBACK = OUT / "qualification/archer-pairing-prep/manual-uvfix/readback.json"
REPORT = OUT / "qualification/archer-pairing-prep/manual-uvfix/three-lod-comparison.json"
POSITION_TOLERANCE_M = 0.001
UV_TOLERANCE = 1.0 / 2048.0
NORMAL_VECTOR_TOLERANCE = 0.02


def normalized_weights(group: dict, index: int) -> tuple:
    return tuple(sorted((int(bone), round(weight * 255))
                        for bone, weight in zip(group["skin_indices"][index],
                                                group["skin_weights"][index])
                        if weight > 0))


def compare_lod(source: dict, output: dict, number: int) -> dict:
    positions_a = sorted({tuple(p) for p in source["positions"]})
    positions_b = sorted({tuple(p) for p in output["positions"]})
    if len(positions_a) != len(positions_b):
        raise RuntimeError(f"LOD{number} unique position count changed")
    output_ids = {position: index for index, position in enumerate(positions_b)}
    matching = {}
    distances = []
    for position in positions_a:
        nearest = min(range(len(positions_b)), key=lambda index:
                      sum((a-b) ** 2 for a, b in zip(position, positions_b[index])))
        matching[position] = nearest
        distances.append(math.dist(position, positions_b[nearest]))
    if len(set(matching.values())) != len(positions_a):
        raise RuntimeError(f"LOD{number} position matching not bijective")
    max_position = max(distances, default=0.0)

    def position_id(group: dict, index: int, donor: bool) -> int:
        position = tuple(group["positions"][index])
        return matching[position] if donor else output_ids[position]

    def topology(group: dict, donor: bool) -> Counter:
        return Counter(tuple(sorted(position_id(group, i, donor) for i in triangle))
                       for triangle in group["triangles"])

    def weighted_corners(group: dict, donor: bool) -> Counter:
        return Counter((position_id(group, i, donor), normalized_weights(group, i))
                       for triangle in group["triangles"] for i in triangle)

    topology_equal = topology(source, True) == topology(output, False)
    weights_equal = weighted_corners(source, True) == weighted_corners(output, False)

    def uv_by_corner(group: dict, donor: bool) -> dict[tuple, list[tuple[float, float]]]:
        uv = group["uv_layers"]["UVMap"]
        result = defaultdict(list)
        for triangle in group["triangles"]:
            tri_key = tuple(sorted(position_id(group, i, donor) for i in triangle))
            for index in triangle:
                key = (tri_key, position_id(group, index, donor), normalized_weights(group, index))
                result[key].append(tuple(uv[index]))
        return result

    old_uv, new_uv = uv_by_corner(source, True), uv_by_corner(output, False)
    uv_key_equal = old_uv.keys() == new_uv.keys() and all(
        len(old_uv[key]) == len(new_uv[key]) for key in old_uv.keys() & new_uv.keys())
    max_uv = None
    uv_corner_count = 0
    if uv_key_equal:
        max_uv = 0.0
        for key in old_uv:
            a, b = sorted(old_uv[key]), sorted(new_uv[key])
            for left, right in zip(a, b):
                max_uv = max(max_uv, *(abs(x-y) for x, y in zip(left, right)))
                uv_corner_count += 1

    def normals_by_corner(group: dict, donor: bool) -> dict[tuple, list[tuple[float, float, float]]]:
        result = defaultdict(list)
        for triangle in group["triangles"]:
            tri_key = tuple(sorted(position_id(group, i, donor) for i in triangle))
            for index in triangle:
                key = (tri_key, position_id(group, index, donor), normalized_weights(group, index))
                result[key].append(tuple(group["normals"][index]))
        return result

    old_normals, new_normals = normals_by_corner(source, True), normals_by_corner(output, False)
    normal_key_equal = old_normals.keys() == new_normals.keys() and all(
        len(old_normals[key]) == len(new_normals[key]) for key in old_normals.keys() & new_normals.keys())
    max_normal_vector_delta = None
    normal_corner_count = 0
    if normal_key_equal:
        max_normal_vector_delta = 0.0
        for key in old_normals:
            for left, right in zip(sorted(old_normals[key]), sorted(new_normals[key])):
                max_normal_vector_delta = max(max_normal_vector_delta, math.dist(left, right))
                normal_corner_count += 1
    return {
        "lod": number,
        "source_vertices": source["vertex_count"], "compiled_vertices": output["vertex_count"],
        "source_triangles": source["triangle_count"], "compiled_triangles": output["triangle_count"],
        "source_unique_positions": len(positions_a), "compiled_unique_positions": len(positions_b),
        "position_match_bijective": True, "maximum_position_distance_m": max_position,
        "position_tolerance_m": POSITION_TOLERANCE_M,
        "triangle_topology_multiset_exact": topology_equal,
        "weighted_corner_multiset_exact_after_influence_order_normalization": weights_equal,
        "uv_corner_identity_keys_and_counts_exact": uv_key_equal,
        "uv_corners_compared": uv_corner_count,
        "maximum_uv_scalar_delta": max_uv, "uv_tolerance": UV_TOLERANCE,
        "normal_corner_identity_keys_and_counts_exact": normal_key_equal,
        "normal_corners_compared": normal_corner_count,
        "maximum_normal_vector_delta": max_normal_vector_delta,
        "normal_vector_tolerance": NORMAL_VECTOR_TOLERANCE,
        "tangent_record_exposed_by_decoder": any("tangent" in key.lower() for key in source),
        "stock_and_compiled_skin_palette_lod_record_exact": (
            source["rig_projection"]["lod_palette"]["skin_indices"]
            == output["rig_projection"]["lod_palette"]["skin_indices"]),
        "stock_and_compiled_vertex_stride_exact": source["vertex_stride"] == output["vertex_stride"],
        "stock_and_compiled_index_stride_exact": source["index_stride"] == output["index_stride"],
        "passed": (max_position <= POSITION_TOLERANCE_M and topology_equal and weights_equal
                   and uv_key_equal and max_uv is not None and max_uv <= UV_TOLERANCE
                   and normal_key_equal and max_normal_vector_delta is not None
                   and max_normal_vector_delta <= NORMAL_VECTOR_TOLERANCE
                   and source["triangle_count"] == output["triangle_count"]),
    }


def main() -> None:
    guard()
    owned(REPORT)
    if REPORT.exists():
        raise FileExistsError("Preserve earlier all-LOD comparison")
    decode, readback = read(DECODE), read(READBACK)
    if (decode["status"] != "decoded" or decode["readback_receipt_sha256"] != sha(READBACK)
            or readback["archive_sha256"] != decode["archive_sha256"]):
        raise RuntimeError("Native readback/decode evidence drift")
    cooked_path = Path(decode["manifest_path"])
    owned(cooked_path)
    if sha(cooked_path) != decode["manifest_sha256"]:
        raise RuntimeError("Native decoded manifest drift")
    source, cooked = read(DONOR), read(cooked_path)
    if source["status"] != "decoded" or cooked["status"] != "decoded":
        raise RuntimeError("Source/cooked manifests are not decoded")
    rig = rig_compatibility(cooked, source)
    old_groups, new_groups = source["geometry"]["groups"], cooked["geometry"]["groups"]
    if len(old_groups) != len(new_groups) or len(old_groups) != 3:
        raise RuntimeError("Expected three genuine LOD groups")
    lods = [compare_lod(a, b, number) for number, (a, b) in enumerate(zip(old_groups, new_groups), 1)]
    names = [(g["name"], g["material"], g["effect"]) for g in new_groups]
    required = [("chi_ranged_bow_age02", f"lod{i}", "unit") for i in (1, 2, 3)]
    passed = all(row["passed"] and row["stock_and_compiled_skin_palette_lod_record_exact"]
                 and row["stock_and_compiled_vertex_stride_exact"]
                 and row["stock_and_compiled_index_stride_exact"] for row in lods) and names == required
    report = {"schema": "ccp-060-archer-three-native-lod-geometry-comparison/v1",
              "status": "three_native_lods_topology_weights_uv_bind_qualified" if passed else "three_lod_comparison_failed",
              "stock_manifest": str(DONOR), "stock_manifest_sha256": sha(DONOR),
              "compiled_manifest": str(cooked_path), "compiled_manifest_sha256": sha(cooked_path),
              "decode_receipt_sha256": sha(DECODE), "archive_sha256": readback["archive_sha256"],
              "compiled_rrgeom_sha256": readback["extracted"][".rrgeom"]["sha256"],
              "rig_compatibility": rig, "compiled_group_material_effect": names,
              "three_lods": lods,
              "native_manual_geometry_only_not_garrison_build_unit": True,
              "diagnostic_compiled_material_excluded_from_pair": True,
              "stock_rrmaterial_pair_not_yet_assembled_or_runtime_tested": True}
    write(REPORT, report)
    print(json.dumps({"status": report["status"], "lods": [{"lod": x["lod"],
                      "triangles": x["compiled_triangles"], "max_pos_m": x["maximum_position_distance_m"],
                      "topology": x["triangle_topology_multiset_exact"],
                      "weights": x["weighted_corner_multiset_exact_after_influence_order_normalization"],
                      "max_uv": x["maximum_uv_scalar_delta"],
                      "max_normal_vector": x["maximum_normal_vector_delta"]} for x in lods]}, indent=2))
    if not passed:
        raise RuntimeError("Full stock LOD geometry/UV comparison failed; report preserved")


if __name__ == "__main__":
    main()
