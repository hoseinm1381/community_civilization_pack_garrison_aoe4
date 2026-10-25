"""Demand six direct-UV native groups and both stock mangonel skin palettes."""
from __future__ import annotations

import json
from pathlib import Path

from compare_archer_three_lod_manual_uvfix import compare_lod
from common import OUT, guard, owned, read, sha, write

BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/manual"
CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
DECODE = BASE / "decode.json"
READBACK = BASE / "readback.json"
REPORT = BASE / "six-group-comparison.json"
RIG_TOLERANCE = 0.0002


def delta(left, right):
    if isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys():
        return max((delta(left[k], right[k]) for k in left), default=0.0)
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return max((delta(a, b) for a, b in zip(left, right)), default=0.0)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right))
    raise ValueError("Rest/bind transform shape changed")


def rig_check(source: dict, cooked: dict) -> dict:
    original, candidate = source["skeleton"], cooked["skeleton"]
    bone_keys = ("index", "name", "parent_index", "parent_name")
    palette_keys = ("palette_index", "name", "parent_index", "parent_name", "skeleton_index")
    bones_a, bones_b = original["bones"], candidate["bones"]
    identity = (len(bones_a) == len(bones_b) == 14
                and all(tuple(a[k] for k in bone_keys) == tuple(b[k] for k in bone_keys)
                        for a, b in zip(bones_a, bones_b)))
    palette_a, palette_b = original["skin_palettes"], candidate["skin_palettes"]
    palette_identity = (len(palette_a) == len(palette_b) == 2
                        and [len(p["bones"]) for p in palette_a] == [2, 12]
                        and [len(p["bones"]) for p in palette_b] == [2, 12]
                        and all(tuple(a[k] for k in palette_keys) == tuple(b[k] for k in palette_keys)
                                for pa, pb in zip(palette_a, palette_b)
                                for a, b in zip(pa["bones"], pb["bones"])))
    maxima = {}
    if identity:
        for key in ("local_reference_transform", "global_reference_transform"):
            maxima["skeleton_" + key] = max(delta(a[key], b[key])
                                               for a, b in zip(bones_a, bones_b))
    if palette_identity:
        for key in ("global_reference_transform", "inverse_bind_transform"):
            maxima["palette_" + key] = max(delta(a[key], b[key])
                                              for pa, pb in zip(palette_a, palette_b)
                                              for a, b in zip(pa["bones"], pb["bones"]))
    lod_palettes_exact = palette_identity and all(pa["lod_palettes"] == pb["lod_palettes"]
                                                  for pa, pb in zip(palette_a, palette_b))
    passed = identity and palette_identity and lod_palettes_exact and all(v <= RIG_TOLERANCE for v in maxima.values())
    return {"passed": passed, "ordered_14_bone_identity": identity,
            "ordered_2_and_12_bone_palette_identity": palette_identity,
            "both_three_lod_palette_records_exact": lod_palettes_exact,
            "transform_maximum_scalar_deltas": maxima,
            "native_quantization_tolerance": RIG_TOLERANCE}


def main():
    guard()
    owned(REPORT)
    if REPORT.exists():
        raise FileExistsError("Preserve earlier mangonel six-group comparison")
    contract, decode, readback = read(CONTRACT), read(DECODE), read(READBACK)
    if (decode["status"] != "decoded" or decode["readback_receipt_sha256"] != sha(READBACK)
            or readback["archive_sha256"] != decode["archive_sha256"]):
        raise RuntimeError("Mangonel native readback/decode evidence drift")
    donor_path = Path(contract["donors"]["siege_mangonel3"]["donor_manifest"])
    cooked_path = Path(decode["manifest_path"])
    owned(cooked_path)
    if (sha(donor_path) != contract["donors"]["siege_mangonel3"]["donor_manifest_sha256"]
            or sha(cooked_path) != decode["manifest_sha256"]):
        raise RuntimeError("Decoded stock/candidate manifest drift")
    stock, cooked = read(donor_path), read(cooked_path)
    if stock["status"] != "decoded" or cooked["status"] != "decoded":
        raise RuntimeError("Stock or candidate native manifest undecoded")
    groups_a, groups_b = stock["geometry"]["groups"], cooked["geometry"]["groups"]
    rig = rig_check(stock, cooked)
    if len(groups_a) != 6:
        raise RuntimeError("Original stock mangonel group count changed")
    if len(groups_b) == 6:
        groups = [compare_lod(a, b, number) for number, (a, b) in enumerate(zip(groups_a, groups_b), 1)]
    else:
        groups = []
    identities_a = [(g["name"], g["material"], g["effect"].lower()) for g in groups_a]
    identities_b = [(g["name"], g["material"], g["effect"].lower()) for g in groups_b]
    passed = (rig["passed"] and identities_a == identities_b
              and len(groups) == 6
              and all(g["passed"] and g["stock_and_compiled_skin_palette_lod_record_exact"]
                      and g["stock_and_compiled_vertex_stride_exact"]
                      and g["stock_and_compiled_index_stride_exact"] for g in groups))
    report = {"schema": "ccp-060-mangonel-six-group-native-geometry-comparison/v1",
              "status": "six_groups_two_palettes_geometry_qualified" if passed else "six_group_native_geometry_mismatch_preserved",
              "stock_manifest_sha256": sha(donor_path), "compiled_manifest_sha256": sha(cooked_path),
              "native_archive_sha256": readback["archive_sha256"],
              "native_rrgeom_sha256": readback["extracted"][".rrgeom"]["sha256"],
              "rig": rig, "stock_group_identities": identities_a,
              "cooked_group_identities": identities_b, "groups": groups,
              "temporary_rgm_rgo_rrmaterial_not_for_integration": True,
              "original_stock_rgm_rgo_rrmaterial_rhka_must_remain_byte_identical_in_pair": True,
              "native_game_animation_and_client_import_unproved": True}
    write(REPORT, report)
    if not passed:
        raise RuntimeError(f"Mangonel native six-group geometry did not qualify; preserved {REPORT}")
    return {"status": report["status"], "report": str(REPORT),
            "triangles": [g["compiled_triangles"] for g in groups]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
