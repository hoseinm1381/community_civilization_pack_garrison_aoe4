"""Compare the second stock UV channel for all six native mangonel groups."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from compare_archer_three_lod_manual_uvfix import normalized_weights
from common import OUT, guard, owned, read, sha, write

BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-native"
CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
REPORT = BASE / "six-group-uv2-comparison.json"


def group_uv(group: dict) -> dict:
    layers = group["uv_layers"]
    if set(layers) != {"UVMap", "UV2"}: raise RuntimeError("Both exact native UV layers missing")
    result = defaultdict(list)
    for tri in group["triangles"]:
        tri_position = tuple(sorted(tuple(group["positions"][i]) for i in tri))
        for i in tri:
            key = (tri_position, tuple(group["positions"][i]), normalized_weights(group, i))
            result[key].append(tuple(layers["UV2"][i]))
    return result


def main():
    guard()
    owned(REPORT)
    if REPORT.exists(): raise FileExistsError("Preserve prior Mangonel UV2 comparison")
    contract, decode = read(CONTRACT), read(BASE / "decode.json")
    donor_file = Path(contract["donors"]["siege_mangonel3"]["donor_manifest"])
    cooked_file = Path(decode["manifest_path"])
    if (sha(donor_file) != contract["donors"]["siege_mangonel3"]["donor_manifest_sha256"] or
            sha(cooked_file) != decode["manifest_sha256"]):
        raise RuntimeError("Mangonel decoded input drift")
    stock, cooked = read(donor_file), read(cooked_file)
    a, b = stock["geometry"]["groups"], cooked["geometry"]["groups"]
    if len(a) != len(b) or len(a) != 6: raise RuntimeError("Six native groups absent")
    rows = []
    for number, (left, right) in enumerate(zip(a, b), 1):
        old, new = group_uv(left), group_uv(right)
        keys_equal = old.keys() == new.keys() and all(len(old[k]) == len(new[k]) for k in old.keys() & new.keys())
        maximum = None
        count = 0
        if keys_equal:
            maximum = 0.0
            for key in old:
                for u, v in zip(sorted(old[key]), sorted(new[key])):
                    maximum = max(maximum, abs(u[0] - v[0]), abs(u[1] - v[1]))
                    count += 1
        rows.append({"group_number": number, "name": left["name"],
                     "stock_triangle_count": left["triangle_count"],
                     "cooked_triangle_count": right["triangle_count"],
                     "uv2_corner_identity_and_count_exact": keys_equal,
                     "uv2_corners_compared": count, "maximum_uv2_scalar_delta": maximum,
                     "uv2_tolerance": 1 / 2048,
                     "passed": keys_equal and maximum is not None and maximum <= 1 / 2048})
    passed = all(x["passed"] for x in rows)
    report = {"schema": "ccp-060-mangonel-six-group-direct-uv2-comparison/v1",
              "status": "six_group_uv2_qualified" if passed else "six_group_uv2_mismatch_preserved",
              "stock_manifest_sha256": sha(donor_file), "cooked_manifest_sha256": sha(cooked_file),
              "archive_sha256": decode["archive_sha256"], "groups": rows,
              "native_game_not_tested": True}
    write(REPORT, report)
    return {"status": report["status"], "groups": rows, "report": str(REPORT)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
