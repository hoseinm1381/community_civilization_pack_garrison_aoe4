"""Read-only weighted corner differences for one cooked authored LOD."""
from __future__ import annotations

import argparse
from collections import Counter
from collections import defaultdict
import json
import math
from pathlib import Path

from authored_geometry_060 import expanded_corner_group
from compare_archer_three_lod_manual_uvfix import normalized_weights
from common import OUT, guard, owned, read, sha, write


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--lod", type=int, default=1, choices=(1, 2, 3))
    parser.add_argument("--label", default="weight-corner-diagnostic")
    args = parser.parse_args()
    guard()
    base = owned(OUT / "authored-geometry" / args.attempt)
    spec, rb = read(base / "spec.json"), read(base / "readback.json")
    a = expanded_corner_group(read(Path(spec["authored_snapshot"]))["geometry"]["groups"][args.lod - 1])
    b = read(Path(rb["decoded_manifest"]))["geometry"]["groups"][args.lod - 1]
    pa, pb = sorted({tuple(p) for p in a["positions"]}), sorted({tuple(p) for p in b["positions"]})
    if len(pa) != len(pb): raise RuntimeError("Position count differs")
    candidates = [[j for _, j in sorted((math.dist(p, q), j) for j, q in enumerate(pb)
                                  if math.dist(p, q) <= .00105)] for p in pa]
    owner = [-1] * len(pb)

    def assign(i: int, seen: set[int]) -> bool:
        for j in candidates[i]:
            if j in seen: continue
            seen.add(j)
            if owner[j] < 0 or assign(owner[j], seen):
                owner[j] = i
                return True
        return False

    for i in sorted(range(len(pa)), key=lambda i: len(candidates[i])):
        if not assign(i, set()): raise RuntimeError("Position matching not bijective")
    mapping = {pa[i]: pb[j] for j, i in enumerate(owner)}

    def corners(group: dict, source: bool) -> Counter:
        out = Counter()
        for tri in group["triangles"]:
            for index in tri:
                raw = tuple(group["positions"][index])
                position = mapping[raw] if source else raw
                out[(position, normalized_weights(group, index))] += 1
        return out

    left, right = corners(a, True), corners(b, False)
    missing, added = left - right, right - left
    trailing_panel_positions = {mapping[tuple(a["positions"][i])]
                                for tri in a["triangles"][-24:] for i in tri}
    mismatch_positions = {key[0] for key in missing}
    def panel_vectors(group: dict, source: bool) -> dict:
        result = defaultdict(set)
        for index, raw in enumerate(group["positions"]):
            position = mapping[tuple(raw)] if source else tuple(raw)
            if position in trailing_panel_positions:
                result[position].add(tuple(normalized_weights(group, index)))
        return result
    panel_a, panel_b = panel_vectors(a, True), panel_vectors(b, False)
    def raw_panel_bones(group: dict, source: bool) -> dict:
        found = defaultdict(set)
        for index, raw in enumerate(group["positions"]):
            position = mapping[tuple(raw)] if source else tuple(raw)
            if position in trailing_panel_positions:
                found[position].add(tuple(sorted(int(x) for x in group["skin_indices"][index])))
        return found
    raw_bones_a, raw_bones_b = raw_panel_bones(a, True), raw_panel_bones(b, False)
    panel_weight_deltas = []
    for position in trailing_panel_positions:
        if len(panel_a[position]) == len(panel_b[position]) == 1:
            aa, bb = dict(next(iter(panel_a[position]))), dict(next(iter(panel_b[position])))
            panel_weight_deltas.append(max(abs(aa.get(i, 0) - bb.get(i, 0))
                                           for i in aa.keys() | bb.keys()))
    def by_identity(group: dict, source: bool) -> dict:
        found = defaultdict(list)
        for tri in group["triangles"]:
            for index in tri:
                raw = tuple(group["positions"][index])
                position = mapping[raw] if source else raw
                weights = tuple((bone, value) for bone, value in normalized_weights(group, index) if value > 0)
                found[(position, tuple(bone for bone, _ in weights))].append(tuple(value for _, value in weights))
        return found
    identities_a, identities_b = by_identity(a, True), by_identity(b, False)
    same_identity_counts = (identities_a.keys() == identities_b.keys()
                            and all(len(identities_a[k]) == len(identities_b[k]) for k in identities_a))
    scalar_deltas = []
    if same_identity_counts:
        for key in identities_a:
            for wa, wb in zip(sorted(identities_a[key]), sorted(identities_b[key])):
                scalar_deltas.extend(abs(x - y) for x, y in zip(wa, wb))
    record = {"schema": "ccp-060-authored-weight-corner-diagnostic/v1",
              "attempt": args.attempt, "lod": args.lod,
              "spec_sha256": sha(base / "spec.json"), "readback_sha256": sha(base / "readback.json"),
              "source_corner_count": sum(left.values()), "native_corner_count": sum(right.values()),
              "missing_corners": sum(missing.values()), "added_corners": sum(added.values()),
              "mismatch_positions": len(mismatch_positions),
              "trailing_24_triangle_positions": len(trailing_panel_positions),
              "mismatch_positions_within_trailing_24": mismatch_positions <= trailing_panel_positions,
              "panel_positions_with_single_weight_vector": len(panel_weight_deltas),
              "panel_raw_bone_slots_exact": raw_bones_a == raw_bones_b,
              "maximum_panel_8bit_weight_scalar_delta": max(panel_weight_deltas, default=None),
              "mismatched_source_8bit_weight_sums": dict(Counter(sum(value for _, value in key[1])
                                                              for key in missing).most_common()),
              "mismatched_native_8bit_weight_sums": dict(Counter(sum(value for _, value in key[1])
                                                              for key in added).most_common()),
              "same_bone_identity_and_counts": same_identity_counts,
              "source_only_bone_identity_samples": [str(k) for k in list(identities_a.keys() - identities_b.keys())[:12]],
              "native_only_bone_identity_samples": [str(k) for k in list(identities_b.keys() - identities_a.keys())[:12]],
              "maximum_8bit_weight_scalar_delta": max(scalar_deltas, default=None),
              "missing_samples": [{"position": k[0], "weights": k[1], "count": v}
                                  for k, v in missing.most_common(20)],
              "added_samples": [{"position": k[0], "weights": k[1], "count": v}
                                for k, v in added.most_common(20)]}
    dest = owned(base / f"{args.label}-lod{args.lod}.json")
    if dest.exists(): raise FileExistsError(dest)
    write(dest, record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__": main()
