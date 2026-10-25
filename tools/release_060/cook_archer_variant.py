"""Isolated stock Archer II material-variant cook probe; never activates an actor.

The shared native byte lock is held across every mutating CLI and overlay step.
The prior unlocked project creation is retained as diagnostic history.
"""
from __future__ import annotations

import argparse
import json
import msvcrt
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import CFG, CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

PROJECT = STAGING / "archer-variant-library/Mods/ccp_060_archer_stock_variant_probe"
PROJECT_FILE = PROJECT / "mod-project.json"
RECEIPT = OUT / "qualification/archer-variant-cook.json"
LOG_DIR = OUT / "qualification/archer-variant-cook-logs"
MODEL = "art/civilizations/chinese/humans/chi_ranged_bow_age02/chi_ranged_bow_age02"
STOCK_ALBEDO = "art/civilizations/chinese/humans/chi_ranged_bow_age02/15644768145151564932_packed.rrtex"
VARIANT = "vn_060_archer_stock_probe"
ADDON = Path(CFG["garrison_extension"])
EDITOR = Path(CFG["art_editor"])
GAME_ROOT = Path(CFG["content_editor"]).parent


def stamp():
    return datetime.now(timezone.utc).isoformat()


def run_step(receipt, label, argv, timeout=900):
    log = owned(LOG_DIR / f"{label}.log")
    if log.exists():
        raise FileExistsError(f"Preserving earlier step log: {log}")
    result = subprocess.run([str(x) for x in argv], capture_output=True, text=True,
                            errors="replace", timeout=timeout, check=False)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("COMMAND: " + " ".join(str(x) for x in argv) + "\n"
                   + "EXIT: " + str(result.returncode) + "\nSTDOUT:\n" + result.stdout
                   + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    receipt["steps"].append({"label": label, "at_utc": stamp(),
                             "returncode": result.returncode, "log": str(log),
                             "log_sha256": sha(log)})
    write(RECEIPT, receipt)
    if result.returncode:
        raise RuntimeError(f"{label} failed with {result.returncode}; inspect {log}")
    return result.stdout


def overlay_command():
    code = (
        "import json,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "from garrison_shared import editor_overlay as e;"
        "p=sys.argv[2];"
        "before=e.inspect_overlay(None,p);"
        "print('BEFORE='+json.dumps(before,default=str));"
        "status=before.get('status');"
        "assert status in ('ready','missing','stale'),status;"
        "e.ensure_overlay(p) if status != 'ready' else None;"
        "after=e.inspect_overlay(None,p);"
        "print('AFTER='+json.dumps(after,default=str));"
        "assert after.get('status') == 'ready',after"
    )
    return ["py", "-3.13", "-c", code, str(ADDON), str(GAME_ROOT)]


def main():
    global PROJECT, PROJECT_FILE, RECEIPT, LOG_DIR, VARIANT
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("variant", "overlay", "cook", "all"), default="all")
    parser.add_argument("--short", action="store_true", help="Use the fresh short-path isolated project")
    args = parser.parse_args()
    if args.short:
        PROJECT = STAGING / "v/Mods/v60av"
        PROJECT_FILE = PROJECT / "mod-project.json"
        RECEIPT = OUT / "qualification/archer-variant-short-cook.json"
        LOG_DIR = OUT / "qualification/archer-variant-short-cook-logs"
        VARIANT = "v60av_stock"
    guard()
    owned(PROJECT)
    owned(RECEIPT)
    if not PROJECT_FILE.is_file() or not CORE.is_file() or not ADDON.is_dir():
        raise FileNotFoundError("Pinned isolated project/core/add-on input is missing")
    project = read(PROJECT_FILE)
    expected_key = "v60av" if args.short else "ccp_060_archer_stock_variant_probe"
    if project.get("schema") != "garrison.mod-project/v1" or project.get("key") != expected_key:
        raise ValueError("Unexpected isolated project identity")
    if project.get("game_mode", {}).get("enabled") or project.get("runtime_modules", {}).get("files"):
        raise ValueError("Project unexpectedly contains a game mode or runtime module")
    receipt = read(RECEIPT) if RECEIPT.exists() else {
        "schema": "ccp-060-archer-variant-cook-probe/v1",
        "status": "not_started",
        "historical_lock_error": "An earlier FileShare.None open failed, but a PowerShell non-terminating error allowed the first isolated mod-project create to run without the byte lock. That created a task-owned empty project only. Its later variant cook failed at an output path of 265 characters. All earlier diagnostics are retained.",
        "isolation": {"project": str(PROJECT), "project_key": project["key"],
                      "project_mod_id": project["mod_id"], "project_file_sha256_before": sha(PROJECT_FILE),
                      "model_source": MODEL, "stock_albedo": STOCK_ALBEDO,
                      "no_actor_integration": True},
        "steps": [],
    }
    completed = {entry["label"] for entry in receipt["steps"] if entry["returncode"] == 0}
    # This exact lock protocol is shared with tools/castle_next/cook.py.
    # A shareable open handle does not mean the byte range is locked.
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            receipt["status"] = "native_byte_lock_busy_no_mutation"
            receipt["last_error"] = str(error)
            write(RECEIPT, receipt)
            raise RuntimeError("Shared native byte lock busy; no cook step run") from error
        try:
            receipt["status"] = "byte_lock_held"
            receipt["lock_protocol"] = "msvcrt.LK_NBLCK first byte; same as tools/castle_next/cook.py"
            write(RECEIPT, receipt)
            if args.phase in ("variant", "all"):
                if "variant" not in completed:
                    run_step(receipt, "variant", [CORE, "mod-project", "variant", "--project", PROJECT,
                                                  "--source", MODEL, "--name", VARIANT])
                if "variant-set-stock-albedo" not in completed:
                    run_step(receipt, "variant-set-stock-albedo", [CORE, "mod-project", "variant-set",
                              "--project", PROJECT, "--name", VARIANT,
                              "--slot", "albedoTexture", "--image", STOCK_ALBEDO])
            if args.phase in ("overlay", "all") and "overlay" not in completed:
                run_step(receipt, "overlay", overlay_command(), timeout=1800)
            if args.phase in ("cook", "all"):
                if not EDITOR.is_file():
                    raise FileNotFoundError(f"Garrison art editor not prepared: {EDITOR}")
                if "cook" not in completed:
                    run_step(receipt, "cook", [CORE, "mod-project", "cook", "--project", PROJECT,
                                              "--editor", EDITOR, "--timeout", "1200"], timeout=1300)
            receipt["status"] = "phase_completed"
            receipt["phase"] = args.phase
            receipt["project_file_sha256_after"] = sha(PROJECT_FILE)
            write(RECEIPT, receipt)
        except BaseException as error:
            receipt["status"] = "failed_under_byte_lock"
            receipt["last_error"] = f"{type(error).__name__}: {error}"
            write(RECEIPT, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
