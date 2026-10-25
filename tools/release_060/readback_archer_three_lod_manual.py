"""Verify one manual native archive and extract only four model resources."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import ARCH, OUT, guard, owned, read, sha, write

COOK = OUT / "qualification/archer-pairing-prep/manual/cook.json"
PREPARE = OUT / "qualification/archer-pairing-prep/manual/prepare.json"
DEST = OUT / "qualification/archer-pairing-prep/manual/readback"
RECEIPT = OUT / "qualification/archer-pairing-prep/manual/readback.json"
BASE = "art/scenario/garrison/n60l/body/model"
MODEL_MEMBERS = {suffix: BASE + suffix for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
EXPECTED = {
    "attrib/n60l.rgd", "mod.bin", "mod.rrtex", "en/en.ucs",
    *(BASE + suffix for suffix in MODEL_MEMBERS),
    "art/scenario/garrison/n60l/body/albedo.rrtex",
}


def archiver(*args: object) -> dict:
    result = subprocess.run([str(ARCH), *map(str, args)], capture_output=True,
                            text=True, errors="replace", timeout=120)
    if result.returncode:
        raise RuntimeError(f"Archiver {args[0]} failed: {result.stderr[-1000:]}")
    return json.loads(result.stdout)


def main() -> None:
    guard()
    for path in (DEST, RECEIPT):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier manual geometry readback: {path}")
    cook, prep = read(COOK), read(PREPARE)
    if (cook["status"] != "native_cook_completed_pending_readback"
            or cook["prepare_receipt_sha256"] != sha(PREPARE)
            or not cook["source_bytes_preserved"]
            or len(cook.get("archives", [])) != 1
            or prep["source_fbx_sha256"] != "a7dcf31bf808ffbdcfb42bce57776ceb9ba94327a65ccaca7870bd861249de8f"):
        raise RuntimeError("Manual native source/cook identity drift")
    archive = Path(cook["archives"][0]["path"])
    owned(archive)
    if sha(archive) != cook["archives"][0]["sha256"]:
        raise RuntimeError("Native archive bytes changed")
    listing = archiver("list", "--verify", archive)
    members = {row["path"]: row for row in listing["members"]}
    verify = listing["archive"]["verification"]
    if (not verify["verified"] or len(members) != 11 or not EXPECTED.issubset(members)
            or len(members) != len({item["path"] for item in listing["members"]})):
        raise RuntimeError("Native archive CRC/SHA or member allowlist drift")
    # Two packed neutral helper textures have hash-derived names; all other
    # members are fixed. They are diagnostic and never enter the final pair.
    extras = set(members) - EXPECTED
    if len(extras) != 2 or any(not x.startswith("art/scenario/garrison/n60l/body/")
                               or not x.endswith("_packed.rrtex") for x in extras):
        raise RuntimeError(f"Unexpected diagnostic archive members: {extras}")
    DEST.mkdir(parents=True)
    extracted = {}
    for suffix, member in MODEL_MEMBERS.items():
        target = owned(DEST / ("model" + suffix))
        archiver("extract-member", archive, member, target)
        extracted[suffix] = {"member": member, "path": str(target),
                             "sha256": sha(target), "bytes": target.stat().st_size}
    receipt = {"schema": "ccp-060-three-lod-manual-geometry-readback/v1",
               "status": "native_archive_verified_four_model_resources_extracted_pending_decode",
               "archive": str(archive), "archive_sha256": sha(archive),
               "archive_member_allowlist": sorted(members), "archive_verification": verify,
               "prepare_receipt": str(PREPARE), "prepare_receipt_sha256": sha(PREPARE),
               "cook_receipt": str(COOK), "cook_receipt_sha256": sha(COOK),
               "extracted": extracted, "diagnostic_compiled_material_excluded_from_stock_pair": True,
               "garrison_build_unit_admission_not_claimed": True,
               "original_chinese_animator_consumer_not_tested": True}
    write(RECEIPT, receipt)
    print(json.dumps({"status": receipt["status"], "archive_sha256": sha(archive),
                      "rrgeom_sha256": extracted[".rrgeom"]["sha256"],
                      "receipt": str(RECEIPT)}, indent=2))


if __name__ == "__main__":
    main()
