"""Verify the isolated Castle object-material payload without changing it."""
from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import configuration, check_storage

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
from garrison_shared import relic_chunky as rc, model_variants as mv

OUT = ROOT / "output/release_061/castle-object-payload-r1"
RECEIPT = json.loads((OUT / "receipt.json").read_text())
FINAL = json.loads((ROOT / "output/release_060/qualification/final-archive-r2/receipt.json").read_text())
ARCHIVE = Path(RECEIPT["native_cook_archive"])
ARCHIVER = Path(CFG["archive_tool"])
PRIOR = ROOT / "output/release_052/diagnostic-c/readback/art/scenario"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def chunks(path: Path, tag: bytes) -> list:
    return [c for c in rc.walk(rc.load(path).roots) if c.tag == tag]


def material(path: Path, texture_members: set[str]) -> list[dict]:
    roots = [x for x in rc.load(path).roots if x.tag == b"GMat"]
    descriptors = []
    for root in roots:
        label = next(x.payload[4:].decode("utf-8") for x in root.children if x.tag == b"MatD")
        one = rc.pack_document([rc.pack_chunk(root.kind, root.tag, root.payload,
                                              name=root.name, version=root.version)])
        slots = mv.material_slots(one)
        used = {v.replace("\\", "/").lower() for v in slots["textures"].values()
                if isinstance(v, str) and v.lower().startswith("art\\")}
        if not used <= texture_members:
            raise RuntimeError(f"Missing object texture: {sorted(used - texture_members)}")
        descriptors.append({"name": root.decoded_name, "class": label,
                            "texture_references": sorted(used),
                            "parameters": slots["parameters"]})
    if [x["class"] for x in descriptors] != ["object", "object_collection"]:
        raise RuntimeError("Material descriptor pair changed")
    return descriptors


def geom_compare(old: Path, new: Path) -> list[dict]:
    left, right = chunks(old, b"GEOB"), chunks(new, b"GEOB")
    if len(left) != len(right) or len(left) != 8:
        raise RuntimeError("Four native geometry groups required")
    report = []
    for j in range(0, len(left), 2):
        a, b = left[j].payload, right[j].payload
        na, _, sa, _ = struct.unpack_from("<4I", a)
        nb, _, sb, _ = struct.unpack_from("<4I", b)
        if (na, sa, nb, sb) != (na, 24, na, 20):
            raise RuntimeError("Expected structure to object vertex format change")
        if left[j + 1].payload != right[j + 1].payload:
            raise RuntimeError("Indexed triangles changed")
        if not all(a[16 + sa*i:32 + sa*i] == b[16 + sb*i:32 + sb*i] for i in range(na)):
            raise RuntimeError("Position, normal, tangent, or primary UV bytes changed")
        for i in range(na):
            if not all(math.isfinite(x) for x in struct.unpack_from("<4e", b, 16 + sb*i)):
                raise RuntimeError("Nonfinite position")
            if not all(math.isfinite(x) for x in struct.unpack_from("<2e", b, 28 + sb*i)):
                raise RuntimeError("Nonfinite primary UV")
        report.append({"group": j//2, "vertices": na,
                       "triangles": struct.unpack_from("<I", right[j + 1].payload)[0]//3,
                       "first_16_vertex_bytes_equal": True,
                       "all_triangle_index_bytes_equal": True,
                       "old_stride": sa, "new_stride": sb})
    return report


def main() -> None:
    result = subprocess.run([str(ARCHIVER), "list", str(ARCHIVE), "--verify"],
                            capture_output=True, text=True, check=True)
    listing = json.loads(result.stdout)
    if not listing["archive"]["verification"]["verified"]:
        raise RuntimeError("Native cook archive verification failed")
    if digest(ARCHIVE) != "c706c315ce8f208b57188278c4df5b4f8f73345675c6c36e55ad684dd7243807":
        raise RuntimeError("Fresh native cook archive drift")
    entries = RECEIPT["payloads"]
    if len(entries) != 15 or len({x["member"] for x in entries}) != 15:
        raise RuntimeError("Exact scoped Castle payload expected")
    payload = {x["member"]: x for x in entries}
    textures = {k for k in payload if k.endswith(".rrtex")}
    if len(textures) != 6 or not all(x.startswith("art/scenario/cc061/") for x in textures):
        raise RuntimeError("Expected six private 0.6.1 texture members")
    for item in entries:
        path = Path(item["path"])
        if not path.resolve().is_relative_to((OUT / "payload").resolve()):
            raise RuntimeError("Payload path escapes owned output")
        old = FINAL["members"].get(item["member"])
        if item["before_sha256"] != (old["sha256"] if old else None):
            raise RuntimeError("Baseline hash mismatch")
        if digest(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise RuntimeError("Payload hash/size drift")
    report = []
    for model in RECEIPT["models"]:
        stem = model["model"]
        private = OUT / "payload" / stem
        prior = PRIOR / stem.removeprefix("art/scenario/")
        old_model = prior.with_suffix(".rgm")
        new_model = private.with_suffix(".rgm")
        old_sel = [x.payload for x in rc.walk(rc.load(old_model).roots)
                   if x.tag in (b"MSD ", b"CNBP")]
        new_sel = [x.payload for x in rc.walk(rc.load(new_model).roots)
                   if x.tag in (b"MSD ", b"CNBP")]
        if old_sel != new_sel:
            raise RuntimeError(f"Lifecycle selectors changed: {stem}")
        old_markers = [x.payload for x in chunks(old_model, b"MRKS")]
        new_markers = [x.payload for x in chunks(new_model, b"MRKS")]
        if old_markers != new_markers:
            raise RuntimeError(f"Native markers changed: {stem}")
        old_rgo = prior.with_suffix(".rgo")
        if digest(old_rgo) != FINAL["members"][stem + ".rgo"]["sha256"]:
            raise RuntimeError(f"Native RGO changed: {stem}")
        geo = geom_compare(prior.with_suffix(".rrgeom"), private.with_suffix(".rrgeom"))
        mats = material(private.with_suffix(".rrmaterial"), textures)
        report.append({"stem": stem, "selectors_byte_identical_to_053": True,
                       "markers_byte_identical_to_053": True,
                       "native_rgo_sha256_retained": digest(old_rgo),
                       "geometry": geo, "materials": mats})
    result = {"schema": "ccp-061-castle-object-verification/v1",
              "status": "passed_offline_fresh_cook_readback_and_scoped_payload",
              "native_cook_archive_sha256": digest(ARCHIVE),
              "native_cook_archive_crc_sha1_verified": True,
              "baseline_060_sha256": FINAL["candidate_sha256"],
              "payload_count": len(entries), "model_count": len(report),
              "models": report,
              "native_render_selection_ruins_repair": "pending imported fresh match",
              "two_player_colours": "pending imported fresh match"}
    (OUT / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print("CASTLE_OBJECT_VERIFY_PASS", len(report), len(entries))


if __name__ == "__main__":
    main()
