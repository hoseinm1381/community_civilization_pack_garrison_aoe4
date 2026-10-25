"""Verify and decode a private villager native archive without promoting its actor."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import ARCH, CORE, OUT, guard, owned, read, sha, write
import decode_archer_three_lod_manual_uvfix as private_index


def run_archiver(*args):
    p = subprocess.run([str(ARCH), *map(str, args)], capture_output=True, text=True, errors="replace", timeout=120)
    if p.returncode: raise RuntimeError(f"Archiver failed: {p.stderr[-800:]}")
    return json.loads(p.stdout)


def main(gender: str) -> dict:
    guard()
    key = "s60v" if gender == "male" else "s60w"
    base = OUT / f"qualification/villager-geometry-route/20261018-resume/{gender}/manual"
    cook_file, prep_file = base / "cook.json", base / "prepare.json"
    receipt_file, dest = base / "readback.json", base / "readback"
    index, config, decoded = base / "private-index.sqlite3", base / "private-index-config.json", base / "decoded"
    for p in (receipt_file, dest, index, config, decoded):
        owned(p)
        if p.exists(): raise FileExistsError(f"Preserve prior villager readback: {p}")
    cook, prep = read(cook_file), read(prep_file)
    if cook["status"] != "native_cook_completed_pending_readback" or not cook["source_bytes_preserved"] or len(cook["archives"]) != 1:
        raise RuntimeError("Villager cook not eligible for readback")
    archive = Path(cook["archives"][0]["path"])
    if sha(archive) != cook["archives"][0]["sha256"]: raise RuntimeError("Villager archive drift")
    listing = run_archiver("list", "--verify", archive)
    if not listing["archive"]["verification"]["verified"]: raise RuntimeError("Archive verification failed")
    members = {item["path"]: item for item in listing["members"]}
    logical = f"art/scenario/garrison/{key}/body/model.rgm"
    resource_names = [logical[:-4] + suffix for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")]
    if not set(resource_names).issubset(members): raise RuntimeError("Native model members missing")
    dest.mkdir(parents=True)
    extracted = {}
    for member in resource_names:
        target = dest / Path(member).name
        run_archiver("extract-member", archive, member, target)
        extracted[member] = {"path": str(target), "sha256": sha(target), "bytes": target.stat().st_size}
    private_index.INDEX = index
    private_index.create_index(archive, listing["members"], prep["key"])
    original_config = json.loads(private_index.ORIGINAL_CONFIG.read_text(encoding="utf-8"))
    original_config["index_path"] = str(index)
    config.write_text(json.dumps(original_config, indent=2) + "\n", encoding="utf-8")
    command = [str(CORE), "convert", "decode-static", "--logical-path", logical,
               "--config", str(config), "--index", str(index), "--output-root", str(decoded)]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=300)
    log = base / "decode.log"
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    response = json.loads(result.stdout) if result.returncode == 0 else {}
    manifest = Path(response["manifest_path"]) if response.get("manifest_path") else None
    status = "decoded_pending_chinese_stock_comparison" if manifest and manifest.is_file() else "decode_failed_preserved"
    record = {"schema": "ccp-060-villager-manual-readback/v1", "status": status, "gender": gender,
              "archive": str(archive), "archive_sha256": sha(archive), "archive_verification": listing["archive"]["verification"],
              "members": sorted(members), "resources": extracted, "decode_exit_code": result.returncode,
              "decoded_manifest": str(manifest) if manifest else None,
              "decoded_manifest_sha256": sha(manifest) if manifest and manifest.is_file() else None,
              "decode_log": str(log), "decode_log_sha256": sha(log),
              "diagnostic_material_and_english_rgo_not_for_stock_pair": True}
    write(receipt_file, record)
    return {"status": status, "manifest": record["decoded_manifest"], "receipt": str(receipt_file)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gender", choices=("male", "female"))
    print(json.dumps(main(ap.parse_args().gender), indent=2))
