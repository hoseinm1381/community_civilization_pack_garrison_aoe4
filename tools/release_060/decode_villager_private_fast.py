"""Decode verified private SGA with an empty game root to bound owner search."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import ARCH, CORE, OUT, STAGING, guard, owned, read, sha, write
import decode_archer_three_lod_manual_uvfix as private_index


def main(gender: str):
    guard()
    key = "s60v" if gender == "male" else "s60w"
    base = OUT / f"qualification/villager-geometry-route/20261018-resume/{gender}/manual"
    extract_file = base / "archive-extract.json"
    index, config, dest, receipt, log = [base / n for n in
                                        ("private-index.sqlite3", "private-index-config-local.json",
                                         "decoded-local", "decode-local.json", "decode-local.log")]
    for p in (index, config, dest, receipt, log): owned(p)
    if receipt.exists() or log.exists(): raise FileExistsError("Preserve private decode report")
    extracted = read(extract_file)
    if extracted["status"] != "archive_verified_four_model_resources_extracted_decode_pending":
        raise RuntimeError("Private archive not verified")
    archive = Path(extracted["archive"])
    if sha(archive) != extracted["archive_sha256"]: raise RuntimeError("Private archive drift")
    result = subprocess.run([str(ARCH), "list", "--verify", str(archive)],
                            capture_output=True, text=True, errors="replace", timeout=120, check=True)
    listing = json.loads(result.stdout)
    if not listing["archive"]["verification"]["verified"]: raise RuntimeError("Archive verify drift")
    private_root = STAGING / ("svm" if gender == "male" else "svf")
    owned(private_root)
    (private_root / "cardinal/archives").mkdir(parents=True, exist_ok=True)
    if not index.exists():
        private_index.INDEX = index
        private_index.create_index(archive, listing["members"], key)
    else:
        # The earlier full-root attempt created this exact private archive index.
        if gender != "male": raise FileExistsError(f"Unexpected private index: {index}")
    if not config.exists():
        cfg = json.loads(private_index.ORIGINAL_CONFIG.read_text(encoding="utf-8"))
        cfg["index_path"] = str(index)
        cfg["game_root"] = str(private_root)
        config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    else:
        cfg = json.loads(config.read_text(encoding="utf-8-sig"))
        if cfg["index_path"] != str(index) or cfg["game_root"] != str(private_root):
            raise RuntimeError("Private decoder config drift")
    command = [str(CORE), "convert", "decode-static", "--logical-path",
               f"art/scenario/garrison/{key}/body/model.rgm", "--config", str(config),
               "--index", str(index), "--output-root", str(dest)]
    if gender == "male" and dest.exists():
        # Confirm the prior command's completed output without overwriting it.
        manifests = list(dest.rglob("decoded-static.json"))
        if len(manifests) != 1: raise RuntimeError("Prior male private decode result ambiguous")
        output = {"manifest_path": str(manifests[0])}
        exit_code = 0
        stdout, stderr = "existing private-root decoder output verified", ""
    else:
        run = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
        exit_code, stdout, stderr = run.returncode, run.stdout, run.stderr
        output = json.loads(stdout) if exit_code == 0 else {}
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(exit_code) +
                   "\nSTDOUT:\n" + stdout + "\nSTDERR:\n" + stderr, encoding="utf-8")
    manifest = Path(output["manifest_path"]) if output.get("manifest_path") else None
    status = "decoded_private_model_no_stock_owner_scan" if manifest and manifest.is_file() else "decode_failed_preserved"
    report = {"schema": "ccp-060-villager-private-model-decode/v1", "status": status,
              "gender": gender, "archive_sha256": sha(archive), "extraction_sha256": sha(extract_file),
              "private_index": str(index), "private_index_sha256": sha(index),
              "private_config": str(config), "private_config_sha256": sha(config),
              "empty_private_game_archive_root": str(private_root / "cardinal/archives"),
              "decoded_manifest": str(manifest) if manifest else None,
              "decoded_manifest_sha256": sha(manifest) if manifest and manifest.is_file() else None,
              "exit_code": exit_code, "log": str(log), "log_sha256": sha(log),
              "stock_animation_owner_resolution_not_claimed": True}
    write(receipt, report)
    return {"status": status, "manifest": report["decoded_manifest"], "receipt": str(receipt)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gender", choices=("male", "female"))
    print(json.dumps(main(ap.parse_args().gender), indent=2))
