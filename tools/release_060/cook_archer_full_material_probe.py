"""One isolated native cook of a proposed full-slot Archer source material.

No generated actor is integrated. A shared msvcrt first-byte lock serializes
all project/native mutations. Earlier control/variant projects remain untouched.
"""
from __future__ import annotations

import json
import msvcrt
import shutil
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, CFG, CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

ROOT = OUT / "qualification/material-native-probe"
RECEIPT = ROOT / "cook.json"
LIBRARY = STAGING / "n"
PROJECT = LIBRARY / "Mods/n60a"
PROJECT_FILE = PROJECT / "mod-project.json"
SOURCE = OUT / "qualification/archer-matched-control-export.json"
VALIDATED = OUT / "qualification/archer-matched-control-validate.json"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
PROPOSAL = OUT / "qualification/material-route-probe/proposal.json"
INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
EDITOR = Path(CFG["art_editor"])
UNIT = "n60a_m"
GENERATED = PROJECT / f"project/source/art/scenario/garrison/n60a/units/{UNIT}/body/model.material"


def command(receipt: dict, label: str, argv: list[object], timeout: int) -> bool:
    log = owned(ROOT / "logs" / (label + ".log"))
    if log.exists():
        raise FileExistsError(f"Preserve earlier native diagnostic: {log}")
    result = subprocess.run([str(x) for x in argv], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("COMMAND: " + " ".join(str(x) for x in argv) + "\nEXIT: "
                   + str(result.returncode) + "\nSTDOUT:\n" + result.stdout
                   + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    receipt["steps"].append({"name": label, "exit_code": result.returncode,
                             "log": str(log), "log_sha256": sha(log)})
    write(RECEIPT, receipt)
    return result.returncode == 0


def slots(path: Path) -> tuple[str, dict[str, str]]:
    tree = ET.parse(path).getroot()
    materials = tree.findall("material")
    if len(materials) != 1 or materials[0].get("source") != "unit":
        raise RuntimeError(f"Expected one unit material: {path}")
    return materials[0].get("name"), {x.get("name"): x.get("value")
                                      for x in materials[0].findall("param")}


def verify_stock_refs(receipt: dict, proposal: dict) -> None:
    stock = read(STOCK)
    if proposal["stock_manifest_sha256"] != sha(STOCK):
        raise RuntimeError("Pinned stock manifest drift")
    lod1 = proposal["stock_lod_material_slots"]["lod1"]["textures"]
    expected = {"albedoTexture", "normalMap", "metalTex", "patternTex", "skinTintLUT"}
    if set(lod1) != expected:
        raise RuntimeError(f"Unexpected stock texture slots: {lod1}")
    decoder_sources = {Path(x["source"]["path"]).name: x["source"]["sha256"]
                       for x in stock["textures"]}
    archive_hashes = {}
    checks = {}
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        for slot, logical in lod1.items():
            rows = db.execute("select archive_path,size from resolved_assets where lower(logical_path)=?",
                              (logical.lower(),)).fetchall()
            if len(rows) != 1:
                raise RuntimeError(f"Stock texture unresolved: {slot} {logical}: {rows}")
            archive = Path(rows[0][0])
            if str(archive) not in archive_hashes:
                archive_hashes[str(archive)] = sha(archive)
            target = owned(ROOT / "stock-refs" / (slot + ".rrtex"))
            if target.exists():
                raise FileExistsError(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not command(receipt, "extract-" + slot,
                           [ARCH, "extract-member", archive, logical, target], 90):
                raise RuntimeError(f"Official texture extract failed: {slot}")
            expected_hash = decoder_sources.get(Path(logical).name)
            if not expected_hash or sha(target) != expected_hash or target.stat().st_size != rows[0][1]:
                raise RuntimeError(f"Official texture content changed: {slot}")
            checks[slot] = {"logical_path": logical, "archive": str(archive),
                            "sha256": sha(target), "bytes": target.stat().st_size}
    receipt["stock_texture_refs"] = checks
    receipt["stock_texture_archive_sha256"] = archive_hashes
    write(RECEIPT, receipt)


def main() -> None:
    guard()
    for path in (ROOT, PROJECT):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier isolated material probe: {path}")
    if not EDITOR.is_file() or not NATIVE_LOCK.is_file():
        raise FileNotFoundError("Installed Garrison art editor or native byte lock missing")
    source, validated, proposal = read(SOURCE), read(VALIDATED), read(PROPOSAL)
    if validated["status"] != "passed" or validated["source_receipt_sha256"] != sha(SOURCE):
        raise RuntimeError("Pinned control source has not passed installed unit-validate")
    if proposal["status"] != "review_only_not_staged_not_cooked":
        raise RuntimeError("Full-slot material proposal status changed")
    source_dir = Path(source["folder"])
    for name, record in source["files"].items():
        if sha(source_dir / name) != record["sha256"]:
            raise RuntimeError(f"Pinned source changed: {name}")
    proposal_file = Path(proposal["proposed_material"])
    if sha(proposal_file) != proposal["proposed_material_sha256"]:
        raise RuntimeError("Proposed material source changed")
    material_name, expected_slots = slots(proposal_file)
    if material_name != proposal["control_generated_material_name"]:
        raise RuntimeError("Proposal uses wrong generated material name")
    receipt = {"schema": "ccp-060-archer-full-material-native-probe/v1",
               "status": "prepared_pending_byte_lock", "project": str(PROJECT),
               "source_export": str(SOURCE), "source_export_sha256": sha(SOURCE),
               "proposal": str(PROPOSAL), "proposal_sha256": sha(PROPOSAL),
               "material_source": str(proposal_file), "material_source_sha256": sha(proposal_file),
               "intended_slots": expected_slots, "generated_spearman_actor_never_integrated": True,
               "no_animation_owner_or_active_gameplay_changes": True,
               "lock_protocol": "msvcrt.LK_NBLCK first byte, tools/castle_next/cook.py parity",
               "steps": []}
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            # Nothing task-owned has been written or mutated on a busy lock.
            raise RuntimeError("Shared native byte lock busy; no mutation") from error
        try:
            receipt["status"] = "byte_lock_held"
            write(RECEIPT, receipt)
            verify_stock_refs(receipt, proposal)
            if not command(receipt, "create", [CORE, "mod-project", "create",
                                                "--library", LIBRARY, "--name", "n60a"], 120):
                raise RuntimeError("Isolated create failed")
            project = read(PROJECT_FILE)
            if project.get("key") != "n60a" or project.get("game_mode", {}).get("enabled"):
                raise RuntimeError("Unexpected isolated project identity")
            receipt["temporary_mod_id"] = project["mod_id"]
            write(RECEIPT, receipt)
            if not command(receipt, "unit-add", [CORE, "mod-project", "unit-add",
                                                  "--project", PROJECT, "--source", source_dir,
                                                  "--name", UNIT], 600):
                raise RuntimeError("Isolated unit-add failed")
            if not GENERATED.is_file():
                raise FileNotFoundError(f"Generated material source missing: {GENERATED}")
            generated_name, generated_slots = slots(GENERATED)
            if generated_name != material_name or set(generated_slots) != {
                    "albedoTexture", "normalMap", "metalTex", "roughnessTex"}:
                raise RuntimeError("Generated material name or baseline slots changed")
            receipt["generated_material_sha256_before_edit"] = sha(GENERATED)
            receipt["generated_material_baseline_slots"] = generated_slots
            shutil.copy2(proposal_file, GENERATED)
            if sha(GENERATED) != proposal["proposed_material_sha256"] or slots(GENERATED) != (material_name, expected_slots):
                raise RuntimeError("Exact material source replacement failed")
            receipt["generated_material_sha256_after_edit_before_cook"] = sha(GENERATED)
            receipt["status"] = "full_slot_material_staged_before_cook"
            write(RECEIPT, receipt)
            ok = command(receipt, "cook", [CORE, "mod-project", "cook", "--project", PROJECT,
                                           "--editor", EDITOR, "--timeout", "1200"], 1300)
            receipt["generated_material_sha256_after_cook"] = sha(GENERATED) if GENERATED.is_file() else None
            receipt["material_source_survived_cook"] = (receipt["generated_material_sha256_after_cook"]
                                                         == proposal["proposed_material_sha256"])
            if not ok:
                receipt["status"] = "native_cook_rejected_full_material_preserved"
            elif not receipt["material_source_survived_cook"]:
                receipt["status"] = "normal_cook_regenerated_material_route_unavailable"
            else:
                cooked = read(PROJECT_FILE).get("cooks", [])
                if len(cooked) != 1:
                    raise RuntimeError("Unexpected isolated cook count")
                receipt["cook_record"] = cooked[0]
                receipt["archive_sha256"] = sha(cooked[0]["archive"])
                if receipt["archive_sha256"] != cooked[0]["sha256"]:
                    raise RuntimeError("Cook archive hash mismatch")
                receipt["status"] = "cook_succeeded_source_preserved_pending_readback"
            write(RECEIPT, receipt)
            print(json.dumps({"status": receipt["status"], "receipt": str(RECEIPT),
                              "material_source_survived_cook": receipt["material_source_survived_cook"]}, indent=2))
        except BaseException as error:
            receipt["status"] = "failed_under_byte_lock"
            receipt["error"] = f"{type(error).__name__}: {error}"
            if GENERATED.is_file():
                receipt["generated_material_sha256_at_failure"] = sha(GENERATED)
            write(RECEIPT, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
