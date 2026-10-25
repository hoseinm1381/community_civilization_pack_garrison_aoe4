"""Run one direct Essence native burn of the isolated manual Archer art source.

This deliberately does not invoke Garrison Build Unit or modify generated unit
sources. It preserves all source hashes and failed native diagnostics.
"""
from __future__ import annotations

import json
import msvcrt
import subprocess
from pathlib import Path

from common import CFG, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

PROJECT = STAGING / "m/Mods/m60a"
PREPARE = OUT / "qualification/manual-art-source-probe/prepare.json"
DEST = OUT / "qualification/manual-art-source-probe"
RECEIPT = DEST / "cook.json"
RUN = PROJECT / "dist/manual-cook"
EDITOR = Path(CFG["art_editor"])
EDITOR_SHA = "2ff1278eed5b1a6e163e6d78e04ad768dc38e4c198f6354069c99bed9e8f84e8"


def files_under(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main() -> None:
    guard()
    for path in (PROJECT, DEST, RECEIPT, RUN):
        owned(path)
    if RECEIPT.exists() or RUN.exists():
        raise FileExistsError("Preserve earlier manual native attempt")
    prep = read(PREPARE)
    if (prep["status"] != "manual_source_prepared_not_cooked" or Path(prep["project"]) != PROJECT
            or sha(EDITOR) != EDITOR_SHA or not NATIVE_LOCK.is_file()):
        raise RuntimeError("Prepared manual source, editor, or shared native lock drifted")
    before = files_under(PROJECT)
    expected = prep["project_file_sha256_after"]
    if before != expected:
        raise RuntimeError("Manual project source changed since the preparation receipt")
    config = read(PROJECT / "mod-project.json")
    if (config.get("animated_units") or config.get("assets") or config.get("cooks")
            or config.get("game_mode", {}).get("enabled") or config.get("game_mode", {}).get("live_reload")):
        raise RuntimeError("Manual project acquired registered units/assets/gameplay")
    argv = [str(EDITOR), "-rtm", "--safe_settings", "--do_not_restore", "--quiet_crash_report",
            "--no_source_control", "--log_path", str(RUN / "logs"), "--build_mod",
            str(PROJECT / "project/m60a.aoe4mod"), "--no_burn_window", "--burn_verbose_log_level",
            "--burn_cache_type", "Local", "--burn_max_threads", "1", "--burn_log_path",
            str(RUN / "logs/burn.log"), "--build_path", str(RUN / "output"),
            "--intermediate_path", str(RUN / "intermediate")]
    receipt = {
        "schema": "ccp-060-manual-archer-native-cook/v1",
        "status": "prepared_pending_shared_byte_lock", "project": str(PROJECT),
        "prepare_receipt": str(PREPARE), "prepare_receipt_sha256": sha(PREPARE),
        "editor": str(EDITOR), "editor_sha256": EDITOR_SHA,
        "run_root": str(RUN), "command": argv,
        "source_hashes_before": before,
        "source_only_no_unit_add": True, "no_generated_unit_entries_or_actor": True,
        "lock_protocol": "msvcrt.LK_NBLCK first byte; tools/castle_next/cook.py parity",
        "native_cook_is_not_garrison_build_unit_qualification": True,
    }
    write(RECEIPT, receipt)
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            receipt["status"] = "shared_native_byte_lock_busy_no_cook"
            write(RECEIPT, receipt)
            raise RuntimeError("Shared native byte lock busy; no cook launched") from error
        try:
            RUN.mkdir(parents=True)
            receipt["status"] = "native_cook_running_under_shared_byte_lock"
            write(RECEIPT, receipt)
            stdout, stderr = RUN / "stdout.log", RUN / "stderr.log"
            with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
                proc = subprocess.run(argv, cwd=EDITOR.parent, stdout=out, stderr=err,
                                      text=True, timeout=1200)
            receipt["exit_code"] = proc.returncode
            receipt["stdout_log"] = str(stdout)
            receipt["stdout_sha256"] = sha(stdout)
            receipt["stderr_log"] = str(stderr)
            receipt["stderr_sha256"] = sha(stderr)
            after = files_under(PROJECT)
            source_after = {key: after.get(key) for key in before}
            receipt["source_hashes_after"] = source_after
            receipt["source_bytes_preserved"] = source_after == before
            created = sorted(set(after) - set(before))
            receipt["created_project_files"] = created
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
