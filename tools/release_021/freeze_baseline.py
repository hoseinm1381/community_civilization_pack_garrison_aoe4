"""Freeze accepted 0.2.0 outputs and hash the inherited source/art inputs."""
from __future__ import annotations

import hashlib
import json
import shutil
import argparse
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = Path(r"F:\aoe_4_temp\Community_civilization_pack_garrison_temp")
OUTPUT = EXTERNAL / "output" / "release_021"
DEST = EXTERNAL / "archives" / "release_020_user_accepted"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_files(directory: Path):
    if not directory.exists():
        return []
    if directory.is_symlink() or directory.is_junction():
        raise RuntimeError(f"Refusing to recurse through a junction: {directory}")
    found = []
    for path in directory.rglob("*"):
        if path.is_symlink() or path.is_junction():
            raise RuntimeError(f"Unexpected link within frozen tree: {path}")
        if path.is_file():
            found.append(path)
    return sorted(found)


def manifest(paths: list[Path], base: Path) -> dict:
    result = {}
    for path in paths:
        result[path.relative_to(base).as_posix()] = {
            "sha256": sha(path),
            "bytes": path.stat().st_size,
        }
    return result


def copy_frozen(source: Path, target: Path, expected: str) -> dict:
    if not source.is_file():
        raise FileNotFoundError(source)
    actual = sha(source)
    if actual != expected:
        raise RuntimeError(f"Hash mismatch for {source}: expected {expected}, got {actual}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha(target) != expected:
            raise RuntimeError(f"Refusing to replace different frozen file: {target}")
    else:
        shutil.copy2(source, target)
    return {"source": str(source), "archive_copy": str(target), "sha256": sha(target), "bytes": target.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Verify existing immutable freeze and do not write it")
    args = parser.parse_args()
    # Recheck exact junction targets before doing any copy/hash work.
    import subprocess
    workspace = json.loads((ROOT / "workspace.json").read_text(encoding="utf-8"))
    python = Path(workspace["python"])
    subprocess.run([str(python), str(ROOT / "tools" / "verify_workspace.py"), "--storage-only"], check=True)
    if EXTERNAL.resolve() != Path(workspace["external_root"]).resolve():
        raise RuntimeError("Configured external root differs from the expected owned root")

    rel020 = OUTPUT.parent / "release_020"
    normal_snapshot = ROOT / "docs" / "preparation" / "normal-before.json"
    normal_root = Path(workspace["source_root"])
    normal_baseline = json.loads(normal_snapshot.read_text(encoding="utf-8"))
    if len(normal_baseline) != 484:
        raise RuntimeError(f"Unexpected preserved normal-edition baseline size: {len(normal_baseline)}")
    for relative, record in normal_baseline.items():
        path = normal_root / Path(relative)
        if not path.is_file() or sha(path) != record["sha256"]:
            raise RuntimeError(f"Preserved normal-edition hash mismatch: {relative}")
    package_receipt = json.loads((rel020 / "package-verification.json").read_text(encoding="utf-8"))
    expected_zip = package_receipt["zip_sha256"]
    expected_sga = package_receipt["sga_sha256"]
    zip_path = rel020 / "community_civilization_pack-0.2.0.zip"
    sga_path = rel020 / "package" / "community_civilization_pack.sga"
    if sha(zip_path) != expected_zip or sha(sga_path) != expected_sga:
        raise RuntimeError("Accepted 0.2.0 ZIP/SGA no longer match package-verification.json")
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"0.2.0 ZIP CRC failure: {bad}")
        sga_members = [name for name in archive.namelist() if name.lower().endswith(".sga")]
        embedded = [name for name in sga_members if hashlib.sha256(archive.read(name)).hexdigest() == expected_sga]
        if not embedded:
            raise RuntimeError("The ZIP does not contain the packaged SGA recorded by its receipt")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    copies = {
        "zip": copy_frozen(zip_path, DEST / zip_path.name, expected_zip),
        "sga": copy_frozen(sga_path, DEST / "community_civilization_pack.sga", expected_sga),
    }
    receipt_names = [
        "package-verification.json", "archive-verification.json", "release-checks.json",
        "source-preservation.json", "baseline-freeze.json", "baseline-tests.json",
        "cleanup-verification.json",
    ]
    receipt_copies = {}
    for name in receipt_names:
        source = rel020 / name
        if source.is_file():
            receipt_copies[name] = copy_frozen(source, DEST / "receipts" / name, sha(source))

    # Full hash inventory for the live active source assets and preserved 0.1/0.2 art.
    assets = ROOT / "assets"
    asset_files = safe_files(assets)
    art_roots = [
        ROOT / "art" / "authoring" / "houses_010", ROOT / "art" / "authoring" / "traps_010",
        ROOT / "art" / "authoring" / "buildings_020", ROOT / "art" / "exports" / "houses_010",
        ROOT / "art" / "exports" / "traps_010", ROOT / "art" / "exports" / "buildings_020",
        ROOT / "art" / "recipes" / "release_010", ROOT / "art" / "recipes" / "release_020",
    ]
    art_manifest = {}
    for base in art_roots:
        if base.exists():
            art_manifest[str(base.relative_to(ROOT)).replace("\\", "/")] = manifest(safe_files(base), base)
    art_manifest["output/release_020/accepted-art-baseline.json"] = {
        "sha256": sha(rel020 / "accepted-art-baseline.json"),
        "bytes": (rel020 / "accepted-art-baseline.json").stat().st_size,
    }
    project_path = ROOT / workspace["project_file"]
    active_assets_manifest = manifest(asset_files, assets)
    frozen_art_receipt = OUTPUT / "baseline-freeze.json"
    if frozen_art_receipt.exists():
        prior = json.loads(frozen_art_receipt.read_text(encoding="utf-8"))
        # Verify every field already recorded before adding the project and normal-source
        # verification fields. This permits a one-time schema completion of this script's
        # just-created receipt without refreshing any frozen input hashes or its timestamp.
        if prior.get("schema") != "community-civilization-pack.release-021-baseline-freeze/v1":
            raise RuntimeError("Existing baseline-freeze.json has an unexpected schema")
        if prior.get("zip_sha256") != expected_zip or prior.get("sga_sha256") != expected_sga:
            raise RuntimeError("Existing freeze does not match accepted 0.2.0 package hashes")
        prior_assets = prior.get("active_source_assets", {}).get("files", {})
        current_asset_keys = {path.relative_to(assets).as_posix() for path in asset_files}
        if set(prior_assets) != current_asset_keys:
            raise RuntimeError("Frozen active source asset file inventory changed")
        for relative, record in prior_assets.items():
            path = assets / Path(relative)
            if not path.is_file() or sha(path) != record["sha256"]:
                raise RuntimeError(f"Frozen asset changed: {relative}")
        for base_relative, entries in prior.get("preserved_art_manifests", {}).items():
            if base_relative == "output/release_020/accepted-art-baseline.json":
                path = rel020 / "accepted-art-baseline.json"
                if sha(path) != entries["sha256"]:
                    raise RuntimeError("Accepted art baseline receipt changed")
                continue
            base = ROOT / Path(base_relative)
            current_art_keys = {path.relative_to(base).as_posix() for path in safe_files(base)}
            if set(entries) != current_art_keys:
                raise RuntimeError(f"Frozen art file inventory changed: {base_relative}")
            for relative, record in entries.items():
                path = base / Path(relative)
                if not path.is_file() or sha(path) != record["sha256"]:
                    raise RuntimeError(f"Frozen art input changed: {base_relative}/{relative}")
        for descriptor in list(prior.get("rollback_copies", {}).values()) + list(prior.get("receipt_copies", {}).values()):
            path = Path(descriptor["archive_copy"])
            if not path.is_file() or sha(path) != descriptor["sha256"]:
                raise RuntimeError(f"Frozen rollback copy changed: {path}")
        if "active_project_file" in prior:
            project_record = prior["active_project_file"]
            project_actual = Path(project_record["path"])
            if not project_actual.is_file() or sha(project_actual) != project_record["sha256"]:
                raise RuntimeError("Active Content Editor project file changed since baseline freeze")
        if args.verify_only and ("active_project_file" not in prior or "normal_source_verification" not in prior):
            raise RuntimeError("Existing freeze needs one-time metadata completion; rerun without --verify-only")
        active_assets_manifest = prior["active_source_assets"]["files"]
        art_manifest = prior["preserved_art_manifests"]
    freeze = {
        "schema": "community-civilization-pack.release-021-baseline-freeze/v1",
        "frozen_at_utc": (prior.get("frozen_at_utc") if frozen_art_receipt.exists() else datetime.now(timezone.utc).isoformat()),
        "accepted_prior_release": "0.2.0",
        "user_acceptance": "User reports 0.2.0 tested and good; individual test coverage was not specified.",
        "acceptance_scope_limit": "This records the user report and package hashes; it does not assert which scenarios, ages, or runtime paths were tested.",
        "acceptance_receipt": str(rel020 / "package-verification.json"),
        "zip_sha256": expected_zip,
        "sga_sha256": expected_sga,
        "zip_integrity": "passed",
        "embedded_sga_member": embedded[0],
        "rollback_archive": str(DEST),
        "rollback_copies": copies,
        "receipt_copies": receipt_copies,
        "active_source_assets": {
            "root": str(assets), "count": len(asset_files),
            "files": active_assets_manifest,
        },
        "active_project_file": {"path": str(project_path), "sha256": sha(project_path), "bytes": project_path.stat().st_size},
        "preserved_art_manifests": art_manifest,
        "normal_source_verification": {
            "status": "passed",
            "method": "SHA-256 checked each of 484 paths from docs/preparation/normal-before.json against the untouched normal source root",
            "baseline_receipt": str(normal_snapshot),
            "baseline_receipt_sha256": sha(normal_snapshot),
            "files_checked": len(normal_baseline),
            "source_root": workspace["source_root"],
            "result": "Every recorded normal-edition file matched its original hash.",
        },
    }
    target = frozen_art_receipt

    # Compact consumer map: use frozen package receipts for identities and hashes,
    # and live source XML only to document the preserved relationship.
    old_cleanup = json.loads((ROOT / "output" / "release_010" / "cleanup-verification.json").read_text(encoding="utf-8"))
    old_map = {}
    for entry in old_cleanup.get("targets", []):
        if "verification-readback" in entry.get("path", ""):
            for member, value in entry.get("files", {}).items():
                if member.startswith("final-c04280a8b2293e7e/"):
                    old_map[member.removeprefix("final-c04280a8b2293e7e/")] = value
    run = json.loads((rel020 / "integration" / "runs" / "c020r020proof2" / "candidate.json").read_text(encoding="utf-8"))
    payload_map = {p["member"]: p for p in run.get("payloads", [])}
    def old_hash(member: str) -> dict:
        return old_map.get(member, {"evidence": "member hash absent from compact 0.1.0 readback receipt"})
    def model(path: str, hashes: dict) -> dict:
        return {
            "member_prefix": path,
            "replace_scope": [path + "/model.rgm", path + "/model.rrgeom", path + "/model.rrmaterial"],
            "preserve_byte_identical": [path + "/model.rgo"],
            "original_rgo": hashes,
        }
    def stamp(member: str) -> dict:
        record = old_hash(member)
        return {"member": member, **record}
    trap_t1 = model("art/scenario/cc010/t1", old_hash("art/scenario/cc010/t1/model.rgo"))
    trap_t2 = model("art/scenario/cc010/t2", old_hash("art/scenario/cc010/t2/model.rgo"))
    ministry_path = "art/scenario/cc020/economy_ministry"
    ministry = model(ministry_path, payload_map[ministry_path + "/model.rgo"])
    ministry_stamp = payload_map["art/stamps/cc020/economy_ministry.bin"]
    inventory = {
        "schema": "community-civilization-pack.release-021-consumer-inventory/v1",
        "basis": [
            str(ROOT / "output" / "release_010" / "package" / "EVIDENCE.json"),
            str(ROOT / "output" / "release_010" / "archive-verification.json"),
            str(rel020 / "archive-verification.json"),
            str(rel020 / "release-checks.json"),
            str(rel020 / "integration" / "runs" / "c020r020proof2" / "candidate.json"),
        ],
        "authorized_replacement_allowlist": [
            "art/scenario/cc010/t1/model.rgm", "art/scenario/cc010/t1/model.rrgeom", "art/scenario/cc010/t1/model.rrmaterial",
            "art/scenario/cc010/t2/model.rgm", "art/scenario/cc010/t2/model.rrgeom", "art/scenario/cc010/t2/model.rrmaterial",
            ministry_path + "/model.rgm", ministry_path + "/model.rrgeom", ministry_path + "/model.rrmaterial",
        ],
        "trap_consumers": {
            "t1": {**trap_t1, "asset": "native English tent A / stake thicket", "consumer_chain": "Vietnam vn_building_bambo_outpost_chi -> vn_trap_thicket_visual -> art/stamps/cc010/stake_thicket.bin; default and campaign actor copies are present in the 0.1.0 source-preservation receipt.", "stamp": stamp("art/stamps/cc010/stake_thicket.bin")},
            "t2": {**trap_t2, "asset": "native English tent B / stake fan", "consumer_chain": "Vietnam vn_building_defense_outpost_bambo_chi -> vn_trap_parent_visual and vn_trap_palisade_visual -> art/stamps/cc010/stake_fan.bin; default and campaign actor copies are present in the 0.1.0 source-preservation receipt.", "stamp": stamp("art/stamps/cc010/stake_fan.bin")},
            "bindings_to_preserve": [
                "attrib/instances/attachments/attachment_lists/vietnam/vn_trap_parent_visual.xml",
                "attrib/instances/attachments/attachment_lists/vietnam/vn_trap_palisade_visual.xml",
                "attrib/instances/attachments/attachment_lists/vietnam/vn_trap_thicket_visual.xml",
                "art/stamps/cc010/stake_fan.bin", "art/stamps/cc010/stake_thicket.bin",
            ],
            "binding_identities": [
                {"name": "vn_trap_thicket_visual", "pbgid": 35919088, "parent": "attachments\\attachment_lists\\civilizations\\english\\buildings\\campaign\\military_tent_a", "consumer": "vn_building_bambo_outpost_chi"},
                {"name": "vn_trap_parent_visual", "pbgid": 34266860, "parent": "attachments\\attachment_lists\\races\\core\\substructs\\props\\substruct_firewood", "consumer": "vn_building_defense_outpost_bambo_chi"},
                {"name": "vn_trap_palisade_visual", "pbgid": 34217400, "parent": "attachments\\attachment_lists\\civilizations\\english\\buildings\\campaign\\military_tent_b", "consumer": "vn_building_defense_outpost_bambo_chi"},
            ],
            "gameplay_coupling": "Trap tier/range/roller upgrades and trap SCAR remain in the source; this allowlist does not admit actor, attachment-list, SCAR, weapon, effect, or upgrade edits. Existing receipts retain these campaign/default and upgrade references.",
        },
        "ministry_consumer": {
            **ministry,
            "consumer_chain": "Vietnam vn_building_econ_food_control_chi -> default and campaign tier_ext attachment -> private vn_020_economy_ministry_visual -> art/stamps/cc020/economy_ministry.bin -> model/material/texture resources.",
            "private_binding_to_preserve": "attrib/instances/attachments/attachment_lists/vietnam/release_020/vn_020_economy_ministry_visual.xml",
            "private_binding_identity": {"name": "vn_020_economy_ministry_visual", "pbgid": 37539755, "parent": "attachments\\attachment_lists\\civilizations\\chinese\\buildings\\dynasty_pagoda_chi\\tier1_pagoda_chi"},
            "stamp_to_preserve": {"member": ministry_stamp["member"], "sha256": ministry_stamp["sha256"], "bytes": ministry_stamp["bytes"]},
            "blueprint_and_binding_preservation": "Keep source bindings, PBGIDs, production, upgrades, state trees, actor references, and stamp bytes unchanged.",
        },
        "preserve_byte_identical": [
            "all three trap attachment-list bindings and their compiled private RGD members",
            "both trap stamps, model.rgo files, and all authored/exported 0.1.0 source assets",
            "Ministry source actor and private attachment-list binding; only its named model quartet and approved private textures may change",
            "all unrelated 0.1.0 and 0.2.0 archive members, subject to independent archive comparison before integration",
        ],
        "limitations": "Static consumer/integration inventory only. It does not prove client import, lobby activation, visual appearance, trap event behavior, or native match acceptance.",
    }
    inv_target = OUTPUT / "inventory.json"
    if inv_target.exists():
        existing_inventory = json.loads(inv_target.read_text(encoding="utf-8"))
        if existing_inventory != inventory:
            # Correct only the earlier inventory authored by this task, which had the
            # trap family mapping reversed and incorrectly admitted RGO replacement.
            old_allowlist = existing_inventory.get("authorized_replacement_allowlist", [])
            was_our_reversed_draft = (
                existing_inventory.get("schema") == inventory["schema"]
                and (
                    "stake_fan.bin" in existing_inventory.get("trap_consumers", {}).get("t1", {}).get("consumer_chain", "")
                    or isinstance(existing_inventory.get("trap_consumers", {}).get("t1", {}).get("stamp", {}).get("sha256"), dict)
                    or any(path.endswith("/model.rgo") for path in old_allowlist)
                    or "binding_identities" not in existing_inventory.get("trap_consumers", {})
                )
            )
            if not was_our_reversed_draft:
                raise RuntimeError("Existing consumer inventory differs from current receipt-backed evidence")
            inv_target.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    else:
        if args.verify_only:
            raise RuntimeError("Consumer inventory is missing; verify-only will not create it")
        inv_target.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    if frozen_art_receipt.exists():
        # Preserve the existing freeze snapshot fields while completing only the requested
        # project-file and normal-source verification metadata once.
        prior = json.loads(frozen_art_receipt.read_text(encoding="utf-8"))
        if "active_project_file" in prior and "normal_source_verification" in prior:
            if args.verify_only:
                print(json.dumps({"status": "passed", "verify_only": True, "receipt": str(frozen_art_receipt),
                                  "inventory": str(inv_target), "assets": len(active_assets_manifest),
                                  "zip_sha256": expected_zip, "sga_sha256": expected_sga}, indent=2))
                return
            # The immutable receipt is complete; regular invocations verify, never rewrite.
            return
        # This branch is only reachable for the receipt created by this script before
        # metadata completion. Keep its exact timestamp and frozen manifests.
        freeze["frozen_at_utc"] = prior["frozen_at_utc"]
        freeze["active_source_assets"] = prior["active_source_assets"]
        freeze["preserved_art_manifests"] = prior["preserved_art_manifests"]
        if args.verify_only:
            raise RuntimeError("Existing freeze needs one-time metadata completion; rerun without --verify-only")
        target.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    else:
        if args.verify_only:
            raise RuntimeError("No existing freeze to verify")
        target.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "receipt": str(target), "zip_sha256": expected_zip,
                      "sga_sha256": expected_sga, "asset_files": len(asset_files),
                      "inventory": str(inv_target), "rollback_archive": str(DEST)}, indent=2))


if __name__ == "__main__":
    main()
