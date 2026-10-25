"""Cook a short, private villager geometry source under the shared native lock."""
from __future__ import annotations

import argparse
import json
import msvcrt
import subprocess
from pathlib import Path

from common import CFG, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write


def hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main(gender: str) -> dict:
    guard()
    key = "s60v" if gender == "male" else "s60w"
    project = STAGING / ("svm" if gender == "male" else "svf") / "Mods" / key
    base = OUT / f"qualification/villager-geometry-route/20261018-resume/{gender}/manual"
    prep_file, receipt_file = base / "prepare.json", base / "cook.json"
    run = project / "dist/manual-geometry-cook"
    editor = Path(CFG["art_editor"])
    for p in (project, receipt_file, run): owned(p)
    if receipt_file.exists() or run.exists(): raise FileExistsError("Preserve prior villager manual cook")
    prep = read(prep_file)
    if prep["status"] != "prepared_not_cooked" or prep["gender"] != gender or Path(prep["project"]) != project:
        raise RuntimeError("Villager manual source contract drift")
    before = hashes(project)
    if before != prep["source_hashes_after"] or not NATIVE_LOCK.is_file() or not editor.is_file():
        raise RuntimeError("Villager source, lock, or editor changed")
    command = [str(editor), "-rtm", "--safe_settings", "--do_not_restore", "--quiet_crash_report",
               "--no_source_control", "--log_path", str(run / "logs"), "--build_mod",
               str(project / f"project/{key}.aoe4mod"), "--no_burn_window", "--burn_verbose_log_level",
               "--burn_cache_type", "Local", "--burn_max_threads", "1",
               "--burn_log_path", str(run / "logs/burn.log"), "--build_path", str(run / "output"),
               "--intermediate_path", str(run / "intermediate")]
    record = {"schema": "ccp-060-villager-short-manual-cook/v1", "status": "pending_lock",
              "gender": gender, "project": str(project), "prepare_sha256": sha(prep_file),
              "source_hashes_before": before, "run_root": str(run), "command": command,
              "diagnostic_material_and_english_rgo_not_for_stock_pair": True}
    write(receipt_file, record)
    with NATIVE_LOCK.open("r+b") as stream:
        try: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            record["status"] = "lock_busy_no_cook"; record["error"] = str(error)
            write(receipt_file, record); raise
        try:
            run.mkdir(parents=True)
            stdout, stderr = run / "stdout.log", run / "stderr.log"
            record["status"] = "running_under_shared_lock"; write(receipt_file, record)
            with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
                proc = subprocess.run(command, cwd=editor.parent, stdout=out, stderr=err, text=True, timeout=1200)
            record.update(exit_code=proc.returncode, stdout_log=str(stdout), stdout_sha256=sha(stdout),
                          stderr_log=str(stderr), stderr_sha256=sha(stderr))
            after = hashes(project)
            record["source_hashes_after"] = {k: after.get(k) for k in before}
            record["source_bytes_preserved"] = record["source_hashes_after"] == before
            record["created_project_files"] = sorted(set(after) - set(before))
            archives = sorted((run / "output").rglob("*.sga"))
            record["archives"] = [{"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size} for p in archives]
            record["status"] = ("native_cook_failed_preserved" if proc.returncode else
                                "native_cook_completed_pending_readback" if archives else "native_build_no_archive")
            if not record["source_bytes_preserved"]: record["status"] = "source_changed_refused"
            write(receipt_file, record)
            return {"status": record["status"], "exit_code": proc.returncode,
                    "archives": record["archives"], "receipt": str(receipt_file)}
        finally:
            stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gender", choices=("male", "female"))
    print(json.dumps(main(ap.parse_args().gender), indent=2))
