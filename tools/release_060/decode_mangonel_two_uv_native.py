"""Decode the six-group native archive using only its own private provider."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import ARCH, CORE, OUT, STAGING, guard, owned, read, sha, write
import decode_archer_three_lod_manual_uvfix as private_index

BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-native"
PRIVATE_ROOT = STAGING / "smu"


def main():
    guard()
    receipt, index, config, dest, log = [BASE / n for n in
                                         ("decode.json", "private-index.sqlite3", "private-index-config.json",
                                          "decoded", "decode.log")]
    for p in (receipt, index, config, dest, log):
        owned(p)
        if p.exists(): raise FileExistsError(f"Preserve mangonel private decode: {p}")
    rb = read(BASE / "readback.json")
    prep = read(BASE / "prepare.json")
    if rb["status"] != "archive_verified_four_model_resources_extracted_pending_six_group_decode":
        raise RuntimeError("Native mangonel readback missing")
    archive = Path(rb["archive"])
    if sha(archive) != rb["archive_sha256"]: raise RuntimeError("Native archive drift")
    listed = subprocess.run([str(ARCH), "list", "--verify", str(archive)],
                            capture_output=True, text=True, errors="replace", timeout=120, check=True)
    data = json.loads(listed.stdout)
    if not data["archive"]["verification"]["verified"]: raise RuntimeError("Native CRC verification failed")
    unique_members = {}
    for item in data["members"]:
        unique_members.setdefault(item["path"], item)
    if len(unique_members) != rb["unique_member_count"]:
        raise RuntimeError("Private model index member count changed")
    private_index.INDEX = index
    private_index.create_index(archive, list(unique_members.values()), prep["project_key"])
    private_root = PRIVATE_ROOT
    owned(private_root)
    (private_root / "cardinal/archives").mkdir(parents=True, exist_ok=True)
    cfg = json.loads(private_index.ORIGINAL_CONFIG.read_text(encoding="utf-8"))
    cfg["index_path"], cfg["game_root"] = str(index), str(private_root)
    config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    command = [str(CORE), "convert", "decode-static", "--logical-path",
               "art/scenario/garrison/s60m/body/model.rgm", "--config", str(config),
               "--index", str(index), "--output-root", str(dest)]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode) +
                   "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    response = json.loads(result.stdout) if result.returncode == 0 else {}
    manifest = Path(response["manifest_path"]) if response.get("manifest_path") else None
    status = "decoded" if manifest and manifest.is_file() else "failed_diagnostic"
    record = {"schema": "ccp-060-mangonel-two-uv-private-decode/v1", "status": status,
              "archive_sha256": sha(archive), "readback_receipt_sha256": sha(BASE / "readback.json"),
              "manifest_path": str(manifest) if manifest else None,
              "manifest_sha256": sha(manifest) if manifest and manifest.is_file() else None,
              "private_index": str(index), "private_index_sha256": sha(index),
              "empty_game_archive_root": str(private_root / "cardinal/archives"),
              "exit_code": result.returncode, "log": str(log), "log_sha256": sha(log),
              "stock_animation_owner_discovery_not_claimed": True}
    write(receipt, record)
    return {"status": status, "manifest": record["manifest_path"], "receipt": str(receipt)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
