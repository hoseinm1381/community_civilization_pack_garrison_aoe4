"""Read-only skeleton comparison of official riderless worker and combined donor."""
from __future__ import annotations

import json
from pathlib import Path

from common import OUT, guard, owned, read, sha, write
from compare_mangonel_manual_geometry import delta

BASE = OUT / "qualification/nonhumanoid-route-preflight"


def main():
    guard()
    target = owned(BASE / "worker-elephant-stock/skeleton-compatibility.json")
    if target.exists(): raise FileExistsError("Preserve prior skeleton comparison")
    stock_receipt = read(BASE / "worker-elephant-stock/report.json")
    combined_row = read(BASE / "20261018-stock-rig-contract.json")["donors"]["elephant"]
    worker_path, combined_path = Path(stock_receipt["decoded_manifest"]), Path(combined_row["donor_manifest"])
    if (sha(worker_path) != stock_receipt["decoded_manifest_sha256"]
            or sha(combined_path) != combined_row["donor_manifest_sha256"]):
        raise RuntimeError("Pinned stock manifest drift")
    worker, combined = read(worker_path), read(combined_path)
    a, b = worker["skeleton"]["bones"], combined["skeleton"]["bones"]
    keys = ("index", "name", "parent_index", "parent_name")
    ordered = len(a) == len(b) == 140 and all(tuple(x[k] for k in keys) == tuple(y[k] for k in keys)
                                              for x, y in zip(a, b))
    maxima = {}
    if ordered:
        for key in ("local_reference_transform", "global_reference_transform"):
            maxima[key] = max(delta(x[key], y[key]) for x, y in zip(a, b))
    animal_groups = [g for g in worker["geometry"]["groups"] if g["material"].startswith("tug_elephant_lod")]
    wood_groups = [g for g in worker["geometry"]["groups"] if g["material"] == "res_wood_carry"]
    rider_groups = [g for g in worker["geometry"]["groups"] if "rider" in g["name"].lower()
                    or "rider" in g["material"].lower()]
    result = {"schema": "ccp-060-worker-elephant-stock-skeleton-comparison/v1",
              "status": "same_ordered_140_bone_skeleton_with_riderless_worker_geometry" if ordered and
                        len(animal_groups) == 3 and len(wood_groups) == 3 and not rider_groups else "compatibility_mismatch",
              "worker_manifest_sha256": sha(worker_path), "combined_manifest_sha256": sha(combined_path),
              "ordered_bone_index_name_parent_identity": ordered,
              "reference_transform_maximum_scalar_deltas": maxima,
              "worker_animal_lod_triangles": [g["triangle_count"] for g in animal_groups],
              "worker_wood_carry_lod_triangles": [g["triangle_count"] for g in wood_groups],
              "rider_groups": [(g["name"], g["material"]) for g in rider_groups],
              "worker_skin_palette_sizes": [len(p["bones"]) for p in worker["skeleton"]["skin_palettes"]],
              "combined_skin_palette_sizes": [len(p["bones"]) for p in combined["skeleton"]["skin_palettes"]],
              "owner_attachment_and_native_game_compatibility_unproved": True}
    write(target, result)
    return {"status": result["status"], "transform_maxima": maxima, "report": str(target)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
