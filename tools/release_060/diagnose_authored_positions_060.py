"""Read-only nearest-position diagnostics for a failed authored geometry attempt."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from common import OUT, guard, owned, read, sha, write


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--label", default="position-diagnostic")
    args = parser.parse_args()
    guard()
    folder = owned(OUT / "authored-geometry" / args.attempt)
    spec, readback = read(folder / "spec.json"), read(folder / "readback.json")
    source = read(Path(spec["authored_snapshot"]))
    compiled = read(Path(readback["decoded_manifest"]))
    rows = []
    for level, (authored, native) in enumerate(zip(source["geometry"]["groups"],
                                                 compiled["geometry"]["groups"]), 1):
        left = sorted({tuple(p) for p in authored["positions"]})
        right = sorted({tuple(p) for p in native["positions"]})
        distances = sorted((*(min((math.dist(p, q), q) for q in right)), p)
                           for p in left)
        over = [{"distance_m": distance, "source": p, "native": q,
                 "delta_xyz_m": [b - a for a, b in zip(p, q)]}
                for distance, q, p in distances if distance > .001]
        rows.append({"lod": level, "authored_unique_positions": len(left),
                     "native_unique_positions": len(right),
                     "outside_1mm_count": len(over),
                     "max_nearest_distance_m": distances[-1][0],
                     "outside_1mm_samples": over[:12],
                     "native_bounds": native.get("bounds"),
                     "authored_bounds": authored.get("bounds")})
    report = {"schema": "ccp-060-authored-position-diagnostic/v1",
              "attempt": args.attempt, "spec_sha256": sha(folder / "spec.json"),
              "readback_sha256": sha(folder / "readback.json"), "lods": rows}
    destination = owned(folder / (args.label + ".json"))
    if destination.exists():
        raise FileExistsError(destination)
    write(destination, report)
    print(json.dumps({"report": str(destination), "lods": rows}, indent=2))


if __name__ == "__main__":
    main()
