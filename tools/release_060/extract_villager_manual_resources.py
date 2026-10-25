"""Bounded archive and four-resource readback without slow animation discovery."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import ARCH, OUT, guard, owned, read, sha, write


def archiver(*args):
    result = subprocess.run([str(ARCH), *map(str, args)], capture_output=True, text=True, errors="replace", timeout=120)
    if result.returncode: raise RuntimeError(f"Archive tool failed: {result.stderr[-1000:]}")
    return json.loads(result.stdout)


def main(gender: str):
    guard()
    key = "s60v" if gender == "male" else "s60w"
    base = OUT / f"qualification/villager-geometry-route/20261018-resume/{gender}/manual"
    receipt, dest = base / "archive-extract.json", base / "resources"
    for p in (receipt, dest):
        owned(p)
        if p.exists(): raise FileExistsError("Preserve existing villager archive extraction")
    cook = read(base / "cook.json")
    if cook["status"] != "native_cook_completed_pending_readback" or not cook["source_bytes_preserved"]:
        raise RuntimeError("Native villager cook not eligible")
    archive = Path(cook["archives"][0]["path"])
    if sha(archive) != cook["archives"][0]["sha256"]: raise RuntimeError("Native archive drift")
    listing = archiver("list", "--verify", archive)
    if not listing["archive"]["verification"]["verified"]: raise RuntimeError("Archive verification failed")
    members = {item["path"] for item in listing["members"]}
    stem = f"art/scenario/garrison/{key}/body/model"
    expected = {suffix: stem + suffix for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
    if not set(expected.values()).issubset(members): raise RuntimeError("Native model resources absent")
    dest.mkdir(parents=True)
    extracted = {}
    for suffix, member in expected.items():
        file = dest / ("model" + suffix)
        archiver("extract-member", archive, member, file)
        extracted[suffix] = {"member": member, "path": str(file), "sha256": sha(file), "bytes": file.stat().st_size}
    record = {"schema": "ccp-060-villager-native-resource-extract/v1",
              "status": "archive_verified_four_model_resources_extracted_decode_pending",
              "gender": gender, "archive": str(archive), "archive_sha256": sha(archive),
              "archive_verification": listing["archive"]["verification"], "members": sorted(members),
              "extracted": extracted, "diagnostic_material_and_english_rgo_not_for_stock_pair": True}
    write(receipt, record)
    return {"status": record["status"], "rrgeom_sha256": extracted[".rrgeom"]["sha256"], "receipt": str(receipt)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gender", choices=("male", "female"))
    print(json.dumps(main(ap.parse_args().gender), indent=2))
