"""Verify and privately decode a mounted diagnostic native cook."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from common import ARCH, CORE, OUT, STAGING, guard, owned, read, sha, write
import decode_archer_three_lod_manual_uvfix as private_index

KINDS = {"horseman2": ("sh", "s60h"), "elephant": ("se", "s60e")}


def command(*args):
    result = subprocess.run([str(a) for a in args], capture_output=True,
                            text=True, errors="replace", timeout=120)
    if result.returncode:
        raise RuntimeError(f"{args[1]} failed: {result.stderr[-1000:]}")
    return json.loads(result.stdout)


def main(kind: str):
    guard()
    if kind not in KINDS:
        raise ValueError(kind)
    short, key = KINDS[kind]
    folder = owned(OUT / "qualification/nonhumanoid-route-preflight" / kind / "manual")
    prep_path, cook_path, receipt_path = [folder / name for name in
                                         ("prepare.json", "cook.json", "readback.json")]
    extract = owned(folder / "readback")
    decode = owned(folder / "decoded")
    index, config, log = [owned(folder / name) for name in
                          ("private-index.sqlite3", "private-index-config.json", "decode.log")]
    if any(p.exists() for p in (receipt_path, extract, decode, index, config, log)):
        raise FileExistsError("Preserve prior mounted readback")
    prep, cook = read(prep_path), read(cook_path)
    if (prep["kind"] != kind or cook["kind"] != kind
            or cook["status"] != "native_cook_completed_pending_readback"
            or cook["prepare_sha256"] != sha(prep_path)
            or not cook["source_bytes_preserved"] or len(cook["archives"]) != 1):
        raise RuntimeError("Mounted cook/source identity mismatch")
    archive = Path(cook["archives"][0]["path"])
    owned(archive)
    if sha(archive) != cook["archives"][0]["sha256"]:
        raise RuntimeError("Cooked archive drift")
    listing = command(ARCH, "list", "--verify", archive)
    if not listing["archive"]["verification"]["verified"]:
        raise RuntimeError("Cooked archive CRC failed")
    members = {m["path"]: m for m in listing["members"]}
    base = f"art/scenario/garrison/{key}/body/model"
    model = {suffix: base + suffix for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
    if len(members) != len(listing["members"]) or not set(model.values()).issubset(members):
        raise RuntimeError("Four unique compiled mounted model resources missing")
    extract.mkdir(parents=True)
    extracted = {}
    for suffix, member in model.items():
        target = owned(extract / ("model" + suffix))
        command(ARCH, "extract-member", archive, member, target)
        extracted[suffix] = {"member": member, "path": str(target), "sha256": sha(target)}
    private_index.INDEX = index
    private_index.create_index(archive, list(members.values()), key)
    private_root = owned(STAGING / short)
    (private_root / "cardinal/archives").mkdir(parents=True, exist_ok=True)
    cfg = json.loads(private_index.ORIGINAL_CONFIG.read_text(encoding="utf-8"))
    cfg["index_path"], cfg["game_root"] = str(index), str(private_root)
    config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    args = [str(CORE), "convert", "decode-static", "--logical-path", base + ".rgm",
            "--config", str(config), "--index", str(index), "--output-root", str(decode)]
    result = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=120)
    log.write_text("COMMAND: " + " ".join(args) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
                   encoding="utf-8")
    payload = json.loads(result.stdout) if result.returncode == 0 else {}
    manifest = Path(payload["manifest_path"]) if payload.get("manifest_path") else None
    status = "archive_verified_private_model_decoded_pending_geometry_comparison" if manifest and manifest.is_file() else "private_decode_failed_preserved"
    receipt = {"schema": "ccp-060-mounted-manual-native-readback/v1", "status": status,
               "kind": kind, "archive": str(archive), "archive_sha256": sha(archive),
               "archive_verification": listing["archive"]["verification"],
               "member_names": sorted(members), "extracted": extracted,
               "decoded_manifest": str(manifest) if manifest else None,
               "decoded_manifest_sha256": sha(manifest) if manifest and manifest.is_file() else None,
               "private_index_sha256": sha(index), "private_config_sha256": sha(config),
               "decode_exit_code": result.returncode, "decode_log_sha256": sha(log),
               "source_prepare_sha256": sha(prep_path), "native_cook_sha256": sha(cook_path),
               "diagnostic_material_and_rgm_rgo_not_for_final_pair": True,
               "stock_animation_owner_not_replaced": True}
    write(receipt_path, receipt)
    if status != "archive_verified_private_model_decoded_pending_geometry_comparison":
        raise RuntimeError("Mounted private decoder did not qualify")
    return {"status": status, "manifest": str(manifest), "receipt": str(receipt_path)}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=2))
