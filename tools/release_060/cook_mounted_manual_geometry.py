"""Cook one verified mounted diagnostic source under the shared native byte lock."""
from __future__ import annotations

import json
import msvcrt
import subprocess
import sys
from pathlib import Path

from common import CFG, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write
from prepare_mangonel_manual_geometry import file_hashes

KINDS = {"horseman2": ("sh", "s60h"), "elephant": ("se", "s60e")}
EDITOR = Path(CFG["art_editor"])


def main(kind: str):
    guard()
    if kind not in KINDS:
        raise ValueError(kind)
    short, key = KINDS[kind]
    project = owned(STAGING / short / "Mods" / key)
    folder = owned(OUT / "qualification/nonhumanoid-route-preflight" / kind / "manual")
    prep_path, receipt_path = folder / "prepare.json", owned(folder / "cook.json")
    run = owned(project / "dist/manual-stock-rig-cook")
    if receipt_path.exists() or run.exists():
        raise FileExistsError("Preserve prior mounted cook attempt")
    prep = read(prep_path)
    if (prep["status"] != "prepared_not_cooked" or prep["kind"] != kind
            or Path(prep["project"]) != project or not NATIVE_LOCK.is_file() or not EDITOR.is_file()):
        raise RuntimeError("Mounted cook preconditions changed")
    before = file_hashes(project)
    if before != prep["source_hashes_after"]:
        raise RuntimeError("Prepared mounted source drift")
    config = read(project / "mod-project.json")
    if (config.get("animated_units") or config.get("assets") or config.get("cooks")
            or config.get("game_mode", {}).get("enabled")):
        raise RuntimeError("Unexpected actor, animation, or gameplay source in diagnostic project")
    command = [str(EDITOR), "-rtm", "--safe_settings", "--do_not_restore", "--quiet_crash_report",
               "--no_source_control", "--log_path", str(run / "logs"), "--build_mod",
               str(project / "project" / (key + ".aoe4mod")), "--no_burn_window",
               "--burn_verbose_log_level", "--burn_cache_type", "Local", "--burn_max_threads", "1",
               "--burn_log_path", str(run / "logs/burn.log"), "--build_path", str(run / "output"),
               "--intermediate_path", str(run / "intermediate")]
    receipt = {"schema": "ccp-060-mounted-manual-native-cook/v1", "status": "prepared_pending_shared_byte_lock",
               "kind": kind, "project": str(project), "prepare_sha256": sha(prep_path),
               "source_hashes_before": before, "command": command, "run_root": str(run),
               "lock_protocol": "msvcrt.LK_NBLCK first byte", "geometry_only_stock_owners_retained_for_pair": True}
    write(receipt_path, receipt)
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            receipt["status"] = "shared_native_byte_lock_busy_no_cook"
            receipt["error"] = str(error)
            write(receipt_path, receipt)
            raise RuntimeError("Shared native byte lock busy") from error
        try:
            run.mkdir(parents=True)
            receipt["status"] = "native_cook_running_under_shared_byte_lock"
            write(receipt_path, receipt)
            stdout, stderr = run / "stdout.log", run / "stderr.log"
            with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
                proc = subprocess.run(command, cwd=EDITOR.parent, stdout=out, stderr=err,
                                      text=True, timeout=1200)
            receipt.update({"exit_code": proc.returncode, "stdout_log": str(stdout),
                            "stdout_sha256": sha(stdout), "stderr_log": str(stderr),
                            "stderr_sha256": sha(stderr)})
            after = file_hashes(project)
            receipt["source_hashes_after"] = {name: after.get(name) for name in before}
            receipt["source_bytes_preserved"] = receipt["source_hashes_after"] == before
            receipt["created_project_files"] = sorted(set(after) - set(before))
            if not receipt["source_bytes_preserved"]:
                receipt["status"] = "native_cook_changed_source_refused"
            elif proc.returncode:
                receipt["status"] = "native_cook_failed_preserved"
            else:
                archives = sorted((run / "output").rglob("*.sga"))
                receipt["archives"] = [{"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size}
                                       for p in archives]
                receipt["status"] = "native_cook_completed_pending_readback" if archives else "native_build_no_archive_refused"
            write(receipt_path, receipt)
            if receipt["status"] != "native_cook_completed_pending_readback":
                raise RuntimeError("Mounted native cook did not qualify: " + receipt["status"])
            return {"status": receipt["status"], "archives": receipt["archives"], "receipt": str(receipt_path)}
        except BaseException as error:
            if receipt["status"] == "native_cook_running_under_shared_byte_lock":
                receipt["status"] = "native_cook_exception_preserved"
                receipt["error"] = f"{type(error).__name__}: {error}"
                write(receipt_path, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=2))
