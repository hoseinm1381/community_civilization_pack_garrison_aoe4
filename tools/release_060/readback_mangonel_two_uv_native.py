"""Verify model members; disclose duplicated diagnostic texture records."""
from __future__ import annotations

import collections
import json
import subprocess
from pathlib import Path

from common import ARCH, OUT, guard, owned, read, sha, write

BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-native"


def archiver(*args):
    p = subprocess.run([str(ARCH), *map(str, args)], capture_output=True, text=True,
                       errors="replace", timeout=120)
    if p.returncode: raise RuntimeError(f"Archive {args[0]} rejected: {p.stderr[-900:]}")
    return json.loads(p.stdout)


def main():
    guard()
    receipt, dest = BASE / "readback.json", BASE / "readback"
    for p in (receipt, dest):
        owned(p)
        if p.exists(): raise FileExistsError("Preserve prior two-UV readback")
    cook, prep = read(BASE / "cook.json"), read(BASE / "prepare.json")
    if (cook["status"] != "native_cook_completed_pending_six_group_readback" or
            not cook["source_bytes_preserved"] or
            cook["prepare_receipt_sha256"] != sha(BASE / "prepare.json") or
            len(cook["archives"]) != 1 or
            prep["source_fbx_sha256"] != sha(Path(prep["source_body"]) / "model.fbx")):
        raise RuntimeError("Native cook/source identity drift")
    archive = Path(cook["archives"][0]["path"])
    if sha(archive) != cook["archives"][0]["sha256"]: raise RuntimeError("Native archive drift")
    listing = archiver("list", "--verify", archive)
    if not listing["archive"]["verification"]["verified"]: raise RuntimeError("Native archive verification failed")
    groups = collections.defaultdict(list)
    for item in listing["members"]: groups[item["path"]].append(item)
    stem = "art/scenario/garrison/s60m/body/model"
    model = {suffix: stem + suffix for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
    if any(len(groups[path]) != 1 for path in model.values()):
        raise RuntimeError("Native model resources missing or duplicated")
    duplicates = {path: len(rows) for path, rows in groups.items() if len(rows) > 1}
    if any(not path.endswith(".rrtex") for path in duplicates):
        raise RuntimeError("Nontexture resource duplicate in diagnostic archive")
    dest.mkdir(parents=True)
    extracted = {}
    for suffix, path in model.items():
        target = dest / ("model" + suffix)
        archiver("extract-member", archive, path, target)
        extracted[suffix] = {"member": path, "path": str(target),
                             "sha256": sha(target), "bytes": target.stat().st_size}
    record = {"schema": "ccp-060-mangonel-two-uv-native-readback/v1",
              "status": "archive_verified_four_model_resources_extracted_pending_six_group_decode",
              "archive": str(archive), "archive_sha256": sha(archive),
              "archive_verification": listing["archive"]["verification"],
              "archive_member_count": len(listing["members"]), "unique_member_count": len(groups),
              "duplicated_diagnostic_texture_members": duplicates,
              "duplicated_texture_records_are_not_for_final_pair": True,
              "extracted": extracted, "prepare_receipt_sha256": sha(BASE / "prepare.json"),
              "cook_receipt_sha256": sha(BASE / "cook.json"),
              "stock_rgm_rgo_rrmaterial_rhka_required_for_final_pair": True}
    write(receipt, record)
    return {"status": record["status"], "rrgeom_sha256": extracted[".rrgeom"]["sha256"],
            "duplicate_texture_names": len(duplicates), "receipt": str(receipt)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
