"""One isolated normal Garrison unit-add/cook of the three-native-LOD control.

Generated actor/squad/material are diagnostic only. All native mutations use the
shared first-byte lock, exactly as tools/castle_next/cook.py. Never rerun in place.
"""
from __future__ import annotations

import json
import msvcrt
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common import CFG, CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

LIBRARY = STAGING / "l"
PROJECT = LIBRARY / "Mods/u60l"
PROJECT_FILE = PROJECT / "mod-project.json"
SOURCE = OUT / "qualification/archer-pairing-prep/export.json"
VALIDATION = OUT / "qualification/archer-pairing-prep/validation.json"
LOGS = OUT / "qualification/archer-pairing-prep/cook-logs"
RECEIPT = OUT / "qualification/archer-pairing-prep/cook.json"
EDITOR = Path(CFG["art_editor"])


def step(receipt: dict, label: str, command: list[object], timeout: int) -> None:
    log = owned(LOGS / (label + ".log"))
    if log.exists():
        raise FileExistsError(f"Preserve prior native diagnostic: {log}")
    result = subprocess.run([str(x) for x in command], capture_output=True, text=True,
                            errors="replace", timeout=timeout)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("COMMAND: " + " ".join(str(x) for x in command) + "\nEXIT: "
                   + str(result.returncode) + "\nSTDOUT:\n" + result.stdout
                   + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    receipt["steps"].append({"label": label, "returncode": result.returncode,
                             "log": str(log), "log_sha256": sha(log),
                             "at_utc": datetime.now(timezone.utc).isoformat()})
    write(RECEIPT, receipt)
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}); inspect {log}")


def main() -> None:
    guard()
    for path in (LIBRARY, RECEIPT):
        owned(path)
    if RECEIPT.exists() or PROJECT_FILE.exists():
        raise FileExistsError("Preserve previous u60l attempt")
    source, validation = read(SOURCE), read(VALIDATION)
    if (source["schema"] != "ccp-060-archer-paired-stock-lod-export/v1"
            or source["prototype"] != "english-spearman-2"
            or source["material_names"] != ["lod1", "lod2", "lod3"]
            or validation["status"] != "passed"
            or validation["source_receipt_sha256"] != sha(SOURCE)):
        raise RuntimeError("Paired source/validator drift")
    folder = Path(source["folder"])
    for name, item in source["files"].items():
        path = folder / name
        if not path.is_file() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise RuntimeError(f"Source export drift: {path}")
    if not EDITOR.is_file():
        raise FileNotFoundError(f"Configured Garrison editor missing: {EDITOR}")
    receipt = {"schema": "ccp-060-archer-paired-stock-lod-cook/v1",
               "status": "prepared_not_cooked", "source_receipt": str(SOURCE),
               "source_receipt_sha256": sha(SOURCE), "validation_receipt": str(VALIDATION),
               "validation_receipt_sha256": sha(VALIDATION), "project": str(PROJECT),
               "lock_protocol": "msvcrt.LK_NBLCK first byte; tools/castle_next/cook.py parity",
               "generated_actor_squad_material_diagnostic_only": True,
               "original_chinese_archer_animator_not_replaced": True, "steps": []}
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            receipt["status"] = "native_byte_lock_busy_no_mutation"
            receipt["error"] = str(error)
            write(RECEIPT, receipt)
            raise RuntimeError("Shared native byte lock busy; no mutation") from error
        try:
            receipt["status"] = "byte_lock_held"
            write(RECEIPT, receipt)
            step(receipt, "create", [CORE, "mod-project", "create", "--library", LIBRARY,
                                     "--name", "u60l"], 120)
            project = read(PROJECT_FILE)
            if project.get("key") != "u60l" or project.get("game_mode", {}).get("enabled"):
                raise RuntimeError("Unexpected isolated project")
            receipt["temporary_mod_id"] = project["mod_id"]
            step(receipt, "unit-add", [CORE, "mod-project", "unit-add", "--project", PROJECT,
                                       "--source", folder, "--name", "u60l_archer_3lod_control"], 600)
            project = read(PROJECT_FILE)
            if len(project.get("animated_units", [])) != 1:
                raise RuntimeError("Unexpected generated unit registration")
            step(receipt, "cook", [CORE, "mod-project", "cook", "--project", PROJECT,
                                   "--editor", EDITOR, "--timeout", "1200"], 1300)
            project = read(PROJECT_FILE)
            if len(project.get("cooks", [])) != 1:
                raise RuntimeError("Unexpected cook records")
            receipt["status"] = "isolated_cook_completed_pending_archive_readback"
            receipt["cook_record"] = project["cooks"][0]
            receipt["project_file_sha256"] = sha(PROJECT_FILE)
            write(RECEIPT, receipt)
            print(json.dumps({"status": receipt["status"], "cook_record": receipt["cook_record"]}, indent=2))
        except BaseException as error:
            receipt["status"] = "failed_under_byte_lock"
            receipt["error"] = f"{type(error).__name__}: {error}"
            write(RECEIPT, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
