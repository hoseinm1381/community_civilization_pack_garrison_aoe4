"""Read-only RRGeom LOD container count in exact native owners and Garden cook."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
from garrison_shared import relic_chunky as rc

BASE = ROOT / "output/release_070/integration"
OUT = BASE / "lod-audit"


def sha(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect(path: Path):
    doc = rc.load(path)
    mesh = [c for c in rc.walk(doc.roots) if c.tag == b"MESH"]
    rows = []
    for i, node in enumerate(mesh):
        count = [c for c in node.children if c.tag == b"NBLO"]
        lod = [c for c in node.children if c.tag == b"LOD "]
        if len(count) != 1 or len(count[0].payload) != 4:
            raise RuntimeError(f"Unsupported LOD metadata in {path}")
        declared = struct.unpack("<I", count[0].payload)[0]
        if declared != len(lod):
            raise RuntimeError(f"LOD count mismatch in {path}")
        rows.append({"mesh_index": i, "declared_nb_lod": declared,
                     "lod_containers": len(lod),
                     "geometry_containers": sum(sum(c.tag == b"GEOM" for c in x.children) for x in lod)})
    return {"path": str(path), "sha256": sha(path), "mesh_container_count": len(mesh),
            "mesh_lod_counts": rows, "multi_lod_meshes": sum(x["declared_nb_lod"] > 1 for x in rows)}


def main() -> None:
    rows = []
    for family in ("garden", "foundry", "university", "wonder"):
        measure = json.loads((BASE / f"native-measure/{family}.json").read_text())
        decoded = json.loads(Path(measure["decode_manifest"]).read_text())
        path = Path(decoded["resources"]["geometry"]["cache_path"])
        rows.append({"family": family, "official": inspect(path)})
    cooked = BASE / "garden-cook-v1/readback/art/scenario/garrison/cc070garden/buildings/garden/model.rrgeom"
    rows[0]["garrison_cooked_r2"] = inspect(cooked)
    result = {"schema": "ccp-070-static-lod-inventory/v1", "rows": rows,
              "interpretation": "Each inspected stock mesh and the cooked Garden model declares exactly one LOD container. Multiple native stock mesh containers are not themselves demonstrated camera-distance LODs. The installed building-source/v1 handoff has no qualified distance thresholds or extra building LOD authoring contract. Lower-detail editable sources alone are not native LOD activation proof.",
              "native_distance_switch": "unverified"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"),
                      "stock_meshes": {x["family"]: x["official"]["mesh_container_count"] for x in rows},
                      "cooked_garden_meshes": rows[0]["garrison_cooked_r2"]["mesh_container_count"]}))


if __name__ == "__main__":
    main()
