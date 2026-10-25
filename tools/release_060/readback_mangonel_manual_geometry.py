"""Verify isolated mangonel native cook and extract its four model resources."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import ARCH, OUT, guard, owned, read, sha, write

COOK = OUT / "qualification/nonhumanoid-route-preflight/mangonel/manual/cook.json"
PREPARE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/manual/prepare.json"
DEST = OUT / "qualification/nonhumanoid-route-preflight/mangonel/manual/readback"
RECEIPT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/manual/readback.json"
BASE = "art/scenario/garrison/s60m/body/model"
MODEL = {suffix: BASE + suffix for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
FIXED = {"attrib/s60m.rgd", "mod.bin", "mod.rrtex", "en/en.ucs", *MODEL.values()}


def archiver(*args):
    result = subprocess.run([str(ARCH), *map(str, args)], capture_output=True,
                            text=True, errors="replace", timeout=120)
    if result.returncode:
        raise RuntimeError(f"Archiver {args[0]} failed: {result.stderr[-1000:]}")
    return json.loads(result.stdout)


def main():
    guard()
    for path in (DEST, RECEIPT):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier mangonel readback: {path}")
    cook, prep = read(COOK), read(PREPARE)
    if (cook["status"] != "native_cook_completed_pending_six_group_readback"
            or cook["prepare_receipt_sha256"] != sha(PREPARE)
            or not cook["source_bytes_preserved"] or len(cook.get("archives", [])) != 1
            or prep["source_fbx_sha256"] != sha(Path(prep["source_body"]) / "model.fbx")
            or prep["source_rig_sha256"] != sha(Path(prep["source_body"]) / "model.rig")):
        raise RuntimeError("Native cook/source identity drift")
    archive = Path(cook["archives"][0]["path"])
    owned(archive)
    if sha(archive) != cook["archives"][0]["sha256"]:
        raise RuntimeError("Cooked archive bytes changed")
    listing = archiver("list", "--verify", archive)
    members = {row["path"]: row for row in listing["members"]}
    if (len(members) != len(listing["members"])
            or not listing["archive"]["verification"]["verified"]
            or not FIXED.issubset(members)):
        raise RuntimeError("Native archive verification or required model members failed")
    extras = set(members) - FIXED
    if not extras or any(not path.startswith("art/scenario/garrison/s60m/body/")
                         or not path.endswith(".rrtex") for path in extras):
        raise RuntimeError(f"Unexpected mangonel native archive members: {sorted(extras)}")
    DEST.mkdir(parents=True)
    extracted = {}
    for suffix, member in MODEL.items():
        target = owned(DEST / ("model" + suffix))
        archiver("extract-member", archive, member, target)
        extracted[suffix] = {"member": member, "path": str(target),
                             "sha256": sha(target), "bytes": target.stat().st_size}
    receipt = {"schema": "ccp-060-mangonel-minimal-rig-native-readback/v1",
               "status": "archive_verified_four_model_resources_extracted_pending_six_group_decode",
               "archive": str(archive), "archive_sha256": sha(archive),
               "archive_verification": listing["archive"]["verification"],
               "archive_member_allowlist": sorted(members),
               "prepare_receipt_sha256": sha(PREPARE), "cook_receipt_sha256": sha(COOK),
               "extracted": extracted,
               "neutral_material_and_temporary_rgm_rgo_excluded_from_stock_geometry_pair": True,
               "native_original_mangonel_animation_owner_unmodified": True}
    write(RECEIPT, receipt)
    return {"status": receipt["status"], "archive_sha256": sha(archive),
            "rrgeom_sha256": extracted[".rrgeom"]["sha256"], "receipt": str(RECEIPT)}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
