"""PREPARED, NOT RUN: UV-corrected native geometry burn with neutral materials.

No Garrison Build Unit admission or generated actor/animation ownership claim.
"""
from __future__ import annotations

import json
import msvcrt
import subprocess
from pathlib import Path

from common import CFG, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

PROJECT = STAGING / "n2/Mods/n60v"
PREPARE = OUT / "qualification/archer-pairing-prep/manual-uvfix/prepare.json"
RECEIPT = OUT / "qualification/archer-pairing-prep/manual-uvfix/cook.json"
RUN = PROJECT / "dist/manual-geometry-uvfix-cook"
EDITOR = Path(CFG["art_editor"])


def files_under(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main() -> None:
    guard()
    for path in (PROJECT, RECEIPT, RUN):
        owned(path)
    if RECEIPT.exists() or RUN.exists():
        raise FileExistsError("Preserve prior manual UV-fix native attempt")
    prep = read(PREPARE)
    if (prep["status"] != "manual_neutral_material_geometry_source_prepared_not_cooked"
            or Path(prep["project"]) != PROJECT
            or not prep["diagnostic_compiled_material_must_not_enter_stock_pair"]
            or not NATIVE_LOCK.is_file() or not EDITOR.is_file()):
        raise RuntimeError("Manual source/editor/lock preconditions changed")
    before = files_under(PROJECT)
    if before != prep["project_file_sha256_after"]:
        raise RuntimeError("Manual source changed since preparation")
    config = read(PROJECT / "mod-project.json")
    if (config.get("animated_units") or config.get("assets") or config.get("cooks")
            or config.get("game_mode", {}).get("enabled")):
        raise RuntimeError("Manual scaffold registered unit/gameplay source")
    command = [str(EDITOR), "-rtm", "--safe_settings", "--do_not_restore",
               "--quiet_crash_report", "--no_source_control", "--log_path", str(RUN / "logs"),
               "--build_mod", str(PROJECT / "project/n60v.aoe4mod"), "--no_burn_window",
               "--burn_verbose_log_level", "--burn_cache_type", "Local",
               "--burn_max_threads", "1", "--burn_log_path", str(RUN / "logs/burn.log"),
               "--build_path", str(RUN / "output"),
               "--intermediate_path", str(RUN / "intermediate")]
    receipt = {"schema": "ccp-060-three-lod-manual-geometry-uvfix-cook/v1",
               "status": "prepared_pending_shared_byte_lock", "project": str(PROJECT),
               "prepare_receipt": str(PREPARE), "prepare_receipt_sha256": sha(PREPARE),
               "source_hashes_before": before, "run_root": str(RUN), "command": command,
               "source_only_no_unit_add": True, "no_generated_unit_entries_or_actor": True,
               "native_cook_is_not_garrison_build_unit_qualification": True,
               "diagnostic_compiled_material_excluded_from_stock_pair": True,
               "lock_protocol": "msvcrt.LK_NBLCK first byte; tools/castle_next/cook.py parity"}
    write(RECEIPT, receipt)
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            receipt["status"] = "shared_native_byte_lock_busy_no_cook"
            receipt["error"] = str(error)
            write(RECEIPT, receipt)
            raise RuntimeError("Shared native byte lock busy; no cook launched") from error
        try:
            RUN.mkdir(parents=True)
            receipt["status"] = "native_cook_running_under_shared_byte_lock"
            write(RECEIPT, receipt)
            stdout, stderr = RUN / "stdout.log", RUN / "stderr.log"
            with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
                proc = subprocess.run(command, cwd=EDITOR.parent, stdout=out, stderr=err,
                                      text=True, timeout=1200)
            receipt["exit_code"] = proc.returncode
            receipt["stdout_log"] = str(stdout)
            receipt["stdout_sha256"] = sha(stdout)
            receipt["stderr_log"] = str(stderr)
            receipt["stderr_sha256"] = sha(stderr)
            after = files_under(PROJECT)
            receipt["source_hashes_after"] = {key: after.get(key) for key in before}
            receipt["source_bytes_preserved"] = receipt["source_hashes_after"] == before
            receipt["created_project_files"] = sorted(set(after) - set(before))
            if not receipt["source_bytes_preserved"]:
                receipt["status"] = "native_cook_changed_manual_source_refused"
            elif proc.returncode:
                receipt["status"] = "native_cook_failed_preserved"
            else:
                archives = sorted((RUN / "output").rglob("*.sga"))
                receipt["archives"] = [{"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size}
                                       for p in archives]
                receipt["status"] = ("native_cook_completed_pending_readback" if archives
                                     else "native_build_no_archive_refused")
            write(RECEIPT, receipt)
            print(json.dumps({"status": receipt["status"], "exit_code": proc.returncode,
                              "archives": receipt.get("archives", []), "receipt": str(RECEIPT)}, indent=2))
        except BaseException as error:
            receipt["status"] = "native_cook_exception_preserved"
            receipt["error"] = f"{type(error).__name__}: {error}"
            write(RECEIPT, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
