"""Measure healthy native donor geometry in model-local Blender coordinates."""
from __future__ import annotations

import hashlib
import json
import math
import msvcrt
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
from garrison_shared import relic_chunky as rc

OUT = ROOT / "output/release_070/integration/native-measure"
OWNERS = ROOT / "output/release_070/integration/native-owner/owners.json"
UNIVERSITY = ROOT / "output/release_070/inventory/university/decoded"
INDEX = Path(r"C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.sqlite3")
CONFIG = Path(r"C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.local.json")
LOCK = Path(CFG["external_root"]) / "output/release_020/native-build.lock"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def parse_set(chunk):
    name, at = rc.read_lp_string(chunk.payload, 0)
    n = struct.unpack_from("<I", chunk.payload, at)[0]
    at += 4
    items = []
    for _ in range(n):
        item, at = rc.read_lp_string(chunk.payload, at)
        items.append(item)
    if at != len(chunk.payload):
        raise RuntimeError("Selector payload trailing bytes")
    return name, items


def states(chunk):
    n = struct.unpack_from("<I", chunk.payload)[0]
    at = 4
    values = []
    for _ in range(n):
        op, flag, one = struct.unpack_from("<IBI", chunk.payload, at)
        at += 9
        key, at = rc.read_lp_string(chunk.payload, at)
        val, at = rc.read_lp_string(chunk.payload, at)
        values.append((op, flag, one, key, val))
    if at != len(chunk.payload):
        raise RuntimeError("Predicate payload trailing bytes")
    return values


def healthy_names(raw: bytes):
    model = rc.parse(raw).roots[0]
    selector = next(c for c in model.children if c.tag == b"MSBP")
    sets = [parse_set(c) for c in selector.children if c.tag == b"MSD " and len(c.payload) > 4]
    predicates = [states(c) for c in selector.children if c.tag == b"CNBP"]
    if len(sets) not in (len(predicates), len(predicates) + 1):
        raise RuntimeError("Unknown native selector pairing")
    all_names = set().union(*(set(x[1]) for x in sets))
    healthy = set().union(*(set(pair[1]) for pair, cond in zip(sets, predicates)
                            if (2, 0, 1, "life_cycle_state", "healthy") in cond))
    if not healthy or not healthy <= all_names:
        raise RuntimeError("Healthy native selector unresolved")
    return model, all_names, healthy, {"selector_sets": len(sets),
                                      "predicate_tables": len(predicates),
                                      "all_object_names": len(all_names),
                                      "healthy_object_names": len(healthy)}


def decode(family: str, logical: str) -> Path:
    if family == "university":
        manifests = list(UNIVERSITY.rglob("decoded-static.json"))
        if len(manifests) != 1:
            raise RuntimeError("University exact decode manifest missing/ambiguous")
        return manifests[0]
    folder = OUT / "decoded" / family
    if folder.exists():
        raise FileExistsError("Preserve existing native decode attempt")
    folder.mkdir(parents=True)
    cmd = [str(CFG["garrison_core"]), "convert", "decode-static",
           "--logical-path", logical, "--config", str(CONFIG),
           "--index", str(INDEX), "--output-root", str(folder)]
    with LOCK.open("r+b") as stream:
        msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=600)
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    (OUT / f"decode-{family}.log").write_text("COMMAND: " + " ".join(cmd) +
          f"\nEXIT: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    if proc.returncode:
        raise RuntimeError(f"Native {family} decode failed")
    manifests = list(folder.rglob("decoded-static.json"))
    if len(manifests) != 1:
        raise RuntimeError(f"Native {family} decode manifest missing/ambiguous")
    return manifests[0]


def measure(owner, manifest: Path):
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data["status"] != "decoded" or data["warnings"] or data["completeness"]["status"] != "complete":
        raise RuntimeError("Native decode not complete")
    donor = Path(owner["native_media"][".rgm"]["path"])
    if sha(donor) != owner["native_media"][".rgm"]["sha256"]:
        raise RuntimeError("Native owner drift")
    model, all_names, healthy, selectors = healthy_names(donor.read_bytes())
    groups = data["geometry"]["groups"]
    contract = data["structure_collection_contract"]
    bounds = [[math.inf, math.inf, math.inf], [-math.inf, -math.inf, -math.inf]]
    triangles = 0
    used_vertices = 0
    slots = []

    def include(group, tri):
        nonlocal triangles, used_vertices
        triangles += 1
        for vertex_index in tri:
            point = group["positions"][vertex_index]
            if len(point) != 3 or not all(math.isfinite(x) for x in point):
                raise RuntimeError("Invalid decoded position")
            used_vertices += 1
            for axis in range(3):
                bounds[0][axis] = min(bounds[0][axis], point[axis])
                bounds[1][axis] = max(bounds[1][axis], point[axis])

    if contract is None:
        for group in groups:
            if group["name"] not in healthy:
                continue
            before = triangles
            for tri in group["triangles"]:
                include(group, tri)
            slots.append({"group": group["name"], "healthy_triangles": triangles - before})
    else:
        mscl = next(c for c in model.children if c.tag == b"MSCL")
        payload = mscl.children[0].payload
        source_count = struct.unpack_from("<H", payload)[0]
        if source_count != len(all_names):
            raise RuntimeError("MSCL object count mismatch")
        offsets = {name: payload.find(rc.lp_string(name)) for name in all_names}
        if any(x < 2 for x in offsets.values()) or len(set(offsets.values())) != source_count:
            raise RuntimeError("MSCL object ordering unresolved")
        ordered = sorted(all_names, key=offsets.get)
        gi = 0
        for mapping, span in zip(contract["maps"], contract["geometry_group_spans"]):
            inverse = {bone: ordered[i] for i, bone in enumerate(mapping["source_to_local_bone"])
                       if bone >= 0}
            before = triangles
            for group in groups[gi:gi + span]:
                bones = group["collection_bone_indices"]
                for tri in group["triangles"]:
                    a, b, c = (bones[i] for i in tri)
                    if a != b or a != c or a not in inverse:
                        raise RuntimeError("Triangle crosses or misses native collection bone")
                    if inverse[a] in healthy:
                        include(group, tri)
            slots.append({"slot": mapping["slot"], "group_span": span,
                          "healthy_triangles": triangles - before})
            gi += span
        if gi != len(groups):
            raise RuntimeError("Unmapped geometry groups")
    if triangles <= 0:
        raise RuntimeError("No healthy triangles")
    minimum, maximum = bounds
    return {"family": owner["family"], "stock_model": owner["stock_model"],
            "stock_model_sha256": sha(donor), "decode_manifest": str(manifest),
            "decode_manifest_sha256": sha(manifest), "coordinate_projection":
            data["geometry"]["coordinate_projection"],
            "selection": "official CNBP healthy selector union joined through MSCL source-object names and decoded collection bones",
            "selectors": selectors, "healthy_lod0_triangles": triangles,
            "sampled_triangle_vertices": used_vertices,
            "model_local_bounds_min": minimum, "model_local_bounds_max": maximum,
            "model_local_dimensions": [maximum[i] - minimum[i] for i in range(3)],
            "model_local_center": [(maximum[i] + minimum[i]) / 2 for i in range(3)],
            "stock_main_stamp_transform": owner["stock_transform"],
            "slots": slots, "native_appearance": "unverified"}


def main() -> None:
    target = OUT / "targets.json"
    if target.exists():
        raise FileExistsError("Preserve native target measurement")
    OUT.mkdir(parents=True, exist_ok=True)
    owners = json.loads(OWNERS.read_text())["owners"]
    rows = []
    for owner in owners:
        manifest = decode(owner["family"], owner["stock_model"] + ".rgm")
        row = measure(owner, manifest)
        rows.append(row)
        (OUT / (owner["family"] + ".json")).write_text(json.dumps(row, indent=2) + "\n")
        print(json.dumps({"family": row["family"], "dimensions": row["model_local_dimensions"],
                          "center": row["model_local_center"],
                          "healthy_triangles": row["healthy_lod0_triangles"]}), flush=True)
    result = {"schema": "ccp-070-native-healthy-geometry-targets/v1",
              "status": "offline_healthy_selector_geometry_measured",
              "owner_freeze_sha256": sha(OWNERS), "targets": rows,
              "caution": "Model-local render bounds; placement cells, pathing and functional marker reach require separate native verification. Do not equate footprint_scale 8/12 with FBX metre width."}
    target.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
