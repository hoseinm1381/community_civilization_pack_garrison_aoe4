"""Verify native object-PBR UVs match the FBX after Essence's V conversion."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
from garrison_shared import relic_chunky as rc

BASE = ROOT / "output/release_070/integration"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fbx_uv(path: Path) -> list[tuple[float, float]]:
    raw = path.read_bytes()
    if not raw.startswith(b"Kaydara FBX Binary"):
        raise RuntimeError("Expected binary Blender FBX")
    pairs = []
    at = 0
    while (at := raw.find(b"\x02UVd", at)) >= 0:
        count, encoding, size = struct.unpack_from("<3I", raw, at + 4)
        blob = raw[at + 16:at + 16 + size]
        blob = zlib.decompress(blob) if encoding else blob
        if count % 2 or len(blob) != count * 8:
            raise RuntimeError("Malformed FBX UV direct array")
        values = struct.unpack("<" + str(count) + "d", blob)
        pairs.extend(zip(values[::2], values[1::2]))
        at += 16 + size
    if not pairs:
        raise RuntimeError("FBX contains no primary UV arrays")
    return pairs


def native_uv(path: Path) -> list[tuple[float, float]]:
    pairs = []
    for chunk in rc.walk(rc.load(path).roots):
        if chunk.tag != b"GEOB":
            continue
        count, _, stride, _ = struct.unpack_from("<4I", chunk.payload)
        if stride == 20:
            pairs.extend(struct.unpack_from("<2e", chunk.payload, 16 + i * stride + 12)
                         for i in range(count))
    if not pairs:
        raise RuntimeError("Native RRGeom has no object-PBR UV vertices")
    return pairs


def coverage(source: list[tuple[float, float]], cooked: list[tuple[float, float]], flip: bool) -> float:
    # Native half-floats quantize against FBX doubles; allow <=~0.0015 per axis.
    grid = {(round(u * 1000), round((1-v if flip else v) * 1000)) for u, v in source}
    matches = 0
    for u, v in cooked:
        a, b = round(u * 1000), round(v * 1000)
        matches += any((a + du, b + dv) in grid
                       for du in (-1, 0, 1) for dv in (-1, 0, 1))
    return matches / len(cooked)


def main(family: str, cook_label: str, out_label: str) -> None:
    if family not in ("garden", "foundry", "university", "wonder"):
        raise ValueError("Unknown family")
    if any(not value.replace("-", "").isalnum() for value in (cook_label, out_label)):
        raise ValueError("Invalid immutable label")
    out = BASE / f"{family}-uv-{out_label}"
    if out.exists():
        raise FileExistsError("Preserve prior UV proof")
    cook_root = BASE / f"{family}-{cook_label}"
    frozen = json.loads((cook_root / "input-freeze.json").read_text())
    cooked = json.loads((cook_root / "receipt.json").read_text())
    fb = Path(frozen["staged"]) / "model.fbx"
    geom = Path(cooked["model_readback"]) / "model.rrgeom"
    assert digest(fb) == frozen["hashes"]["model.fbx"]
    assert digest(geom) == cooked["media"]["model.rrgeom"]
    source_uv = fbx_uv(fb)
    native = native_uv(geom)
    identity = coverage(source_uv, native, False)
    vflip = coverage(source_uv, native, True)
    if vflip < 0.999 or identity >= vflip:
        raise RuntimeError(f"Cooked UV orientation did not match Essence V projection: {identity}, {vflip}")
    result = {"schema": "ccp-070-native-uv-orientation/v1",
              "status": "passed_readback_uv_projection_runtime_unverified",
              "family": family, "fbx_sha256": digest(fb), "rrgeom_sha256": digest(geom),
              "fbx_uv_pairs": len(source_uv), "native_uv_vertices": len(native),
              "native_coverage_vs_fbx_identity": identity,
              "native_coverage_vs_fbx_v_flipped": vflip,
              "tolerance": "FBX double to native half, 0.0015 per UV axis",
              "limit": "Numerical readback of V projection only; textured native appearance remains a user gate."}
    out.mkdir(parents=True)
    (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"receipt": str(out / "receipt.json"), "vflip_coverage": vflip}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("family", choices=("garden", "foundry", "university", "wonder"))
    parser.add_argument("--cook-label", required=True)
    parser.add_argument("--out-label", default="v1")
    args = parser.parse_args()
    main(args.family, args.cook_label, args.out_label)
