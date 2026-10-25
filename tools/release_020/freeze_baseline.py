"""Freeze the 0.2.0 starting source and preserve the accepted 0.1.0 rollback."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CONFIG = configuration(ROOT)
EXTERNAL = Path(CONFIG["external_root"]).resolve()
OUT = EXTERNAL / "output/release_020/baseline-freeze.json"
STAGE = EXTERNAL / "staging/release_020/baseline_source"
ROLLBACK = EXTERNAL / "archives/release_010_user_accepted"
EXPECTED_ZIP = "bd37ac9b79a9f07c127abd1c32abcb4f4f8cb450f0bda22ab10988c9ef0e2f93"
EXPECTED_SGA = "c04280a8b2293e7e9c92832b3608d7033cba0a8ed1c807b8e37a457180482546"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inventory(path: Path) -> dict:
    path = path.resolve(strict=True)
    if not path.is_relative_to(ROOT.resolve()) and not path.is_relative_to(EXTERNAL):
        raise ValueError(f"Inventory path escapes owned roots: {path}")
    if path.is_file():
        return {path.name: {"sha256": sha(path), "bytes": path.stat().st_size}}
    result = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink() or item.is_junction():
            raise ValueError(f"Refusing recursive inventory through link: {item}")
        if item.is_file():
            result[item.relative_to(path).as_posix()] = {"sha256": sha(item), "bytes": item.stat().st_size}
    return result


def verify_storage_and_preservation() -> dict:
    links = check_storage(ROOT, CONFIG)
    # Validate the untouched normal source against the immutable pre-copy manifest.
    provenance = json.loads((ROOT / "docs/migration-provenance.json").read_text(encoding="utf-8"))
    if provenance.get("source_snapshot") != "docs/preparation/normal-before.json":
        raise ValueError("Migration provenance points at an unexpected normal snapshot")
    normal_path = Path(CONFIG["source_root"]).resolve(strict=True)
    if not normal_path.is_relative_to(ROOT.parent.resolve()):
        raise ValueError(f"Normal baseline escaped its expected parent: {normal_path}")
    manifest_path = ROOT / provenance["source_snapshot"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current = {p.relative_to(normal_path).as_posix() for p in normal_path.rglob("*") if p.is_file()}
    if current != set(manifest):
        raise ValueError("Normal source file inventory differs from migration snapshot")
    for relative, expected in manifest.items():
        if sha(normal_path / relative) != expected["sha256"]:
            raise ValueError(f"Normal source changed since migration snapshot: {relative}")
    if provenance.get("source_project_guid") != CONFIG["source_project_guid"] or provenance.get("project_guid") != CONFIG["project_guid"]:
        raise ValueError("Migration provenance GUIDs differ from active workspace configuration")
    normal_check = {"manifest": str(manifest_path), "files_unchanged": len(manifest),
                    "source_project_guid": provenance["source_project_guid"],
                    "destination_project_guid": provenance["project_guid"]}
    return {"storage_links": links, "normal_preservation": normal_check,
            "normal_manifest": str(manifest_path),
            "source_project_guid": provenance["source_project_guid"],
            "destination_project_guid": provenance["project_guid"]}


def copy_verified(src: Path, dest: Path, expected: str, name: str) -> dict:
    src = src.resolve(strict=True)
    dest = dest.resolve() if dest.exists() else dest
    if not src.is_file() or not src.is_relative_to(EXTERNAL):
        raise ValueError(f"Expected owned release file missing/outside F: {src}")
    actual = sha(src)
    if actual != expected:
        raise ValueError(f"Accepted {name} hash mismatch: {actual}")
    if not dest.parent.resolve().is_relative_to(EXTERNAL):
        raise ValueError(f"Rollback target escapes owned F: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if sha(dest) != expected:
            raise ValueError(f"Existing rollback copy has mismatched hash: {dest}")
    else:
        shutil.copy2(src, dest)
    return {"path": str(dest), "sha256": sha(dest), "bytes": dest.stat().st_size}


def freeze() -> dict:
    proof = verify_storage_and_preservation()
    if OUT.exists():
        record = json.loads(OUT.read_text(encoding="utf-8"))
        current = {
            "assets": inventory(ROOT / "assets"),
            "project": inventory(ROOT / CONFIG["project_file"]),
            "configuration": inventory(ROOT / "workspace.json"),
            "release_010_tools": inventory(ROOT / "tools/release_010"),
            "authoring_recipes": inventory(ROOT / "art/recipes/release_010"),
        }
        if current != record["source_hashes"]:
            raise ValueError("Current source/config/tools/recipes differ from the recorded baseline freeze")
        if not STAGE.is_dir() or inventory(STAGE / "assets") != record["source_hashes"]["assets"]:
            raise ValueError("Existing 0.2.0 source freeze no longer matches its receipt")
        if sha(STAGE / CONFIG["project_file"]) != record["source_hashes"]["project"][CONFIG["project_file"]]["sha256"]:
            raise ValueError("Existing 0.2.0 frozen project no longer matches its receipt")
        for name, frozen in record["accepted_release_010"]["rollback"].items():
            target = Path(frozen["path"]).resolve(strict=True)
            if not target.is_relative_to(ROLLBACK.resolve()) or sha(target) != frozen["sha256"]:
                raise ValueError(f"Accepted 0.1.0 rollback copy changed: {name}")
        if proof["normal_preservation"] != record["normal_preservation"]:
            raise ValueError("Normal preservation proof differs from existing freeze")
        return record
    if STAGE.exists() or ROLLBACK.exists():
        raise ValueError("Unreceipted staging or rollback folder exists; inspect before continuing")

    rel010 = EXTERNAL / "output/release_010"
    package = json.loads((rel010 / "package-verification.json").read_text(encoding="utf-8"))
    candidate_pointer = json.loads((rel010 / "current-candidate.json").read_text(encoding="utf-8"))
    candidate = Path(candidate_pointer["candidate"]).resolve(strict=True)
    if candidate_pointer.get("status") != "passed":
        raise ValueError("Current 0.1.0 candidate pointer is not accepted")
    candidate_record = json.loads(candidate.read_text(encoding="utf-8"))
    if package.get("zip_sha256") != EXPECTED_ZIP or package.get("sga_sha256") != EXPECTED_SGA:
        raise ValueError("0.1.0 package receipt does not match authorized accepted hashes")
    if candidate_record.get("sha256") != EXPECTED_SGA or candidate_record.get("status") != "passed":
        raise ValueError("Current candidate receipt does not match accepted SGA")

    zip_src = rel010 / "community_civilization_pack-0.1.0.zip"
    sga_src = Path(package["sga"])
    rollback_payload = {
        "community_civilization_pack-0.1.0.zip": copy_verified(zip_src, ROLLBACK / "community_civilization_pack-0.1.0.zip", EXPECTED_ZIP, "ZIP"),
        "community_civilization_pack.sga": copy_verified(sga_src, ROLLBACK / "community_civilization_pack.sga", EXPECTED_SGA, "SGA"),
    }
    receipt_names = ["current-candidate.json", "package-verification.json", "release-checks.json",
                     "source-preservation.json", "archive-verification.json"]
    for name in receipt_names:
        source = rel010 / name
        if source.is_file():
            target = ROLLBACK / "receipts" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha(source) != sha(target):
                raise ValueError(f"Receipt copy mismatch: {name}")
            rollback_payload[name] = {"path": str(target), "sha256": sha(target), "bytes": target.stat().st_size}
    candidate_target = ROLLBACK / "receipts" / "accepted-candidate.json"
    candidate_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate, candidate_target)
    rollback_payload["accepted-candidate.json"] = {"path": str(candidate_target), "sha256": sha(candidate_target), "bytes": candidate_target.stat().st_size}

    STAGE.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", STAGE / "assets")
    shutil.copy2(ROOT / CONFIG["project_file"], STAGE / CONFIG["project_file"])
    source_hashes = {
        "assets": inventory(STAGE / "assets"),
        "project": inventory(STAGE / CONFIG["project_file"]),
        "configuration": inventory(ROOT / "workspace.json"),
        "release_010_tools": inventory(ROOT / "tools/release_010"),
        "authoring_recipes": inventory(ROOT / "art/recipes/release_010"),
    }
    record = {
        "schema": "community-civilization-pack.release-020-baseline/v1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "starting source freeze for 0.2.0; preserves gameplay and 0.1.0 houses/traps",
        "source_stage": str(STAGE), "source_hashes": source_hashes,
        "config_and_tool_hashes": {k: v for k, v in source_hashes.items() if k != "assets" and k != "project"},
        "normal_preservation": proof["normal_preservation"],
        "normal_manifest_check": {k: v for k, v in proof.items() if k != "storage_links" and k != "normal_preservation"},
        "storage_links": proof["storage_links"],
        "accepted_release_010": {"zip_sha256": EXPECTED_ZIP, "sga_sha256": EXPECTED_SGA,
                                  "current_candidate": str(candidate), "rollback": rollback_payload},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2))
