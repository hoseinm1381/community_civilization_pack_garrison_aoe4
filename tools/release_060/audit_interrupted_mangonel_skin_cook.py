"""Record the interrupted native cook without modifying its diagnostic source."""
from __future__ import annotations

import json
import msvcrt
import subprocess
from pathlib import Path

from common import NATIVE_LOCK, OUT, guard, owned, read, sha, write

BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native"
RECEIPT = BASE / "interrupted-cook-audit.json"


def main():
    guard()
    owned(RECEIPT)
    if RECEIPT.exists(): raise FileExistsError("Preserve prior interruption audit")
    cook = read(BASE / "cook.json")
    if cook["status"] != "native_cook_running_under_shared_byte_lock":
        raise RuntimeError("Cook already resolved; no interruption audit needed")
    run = Path(cook["run_root"])
    stdout, stderr = run / "stdout.log", run / "stderr.log"
    final = run / "output/extension/s60m/s60m.sga"
    process = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'EssenceEditor.exe' -and $_.CommandLine -like '*manual-two-uv-skin-native-cook*' } | Select-Object -ExpandProperty ProcessId"],
                             capture_output=True, text=True, errors="replace", timeout=20)
    if process.returncode: raise RuntimeError("Could not inspect native cook process")
    pids = [int(x) for x in process.stdout.split() if x.isdigit()]
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            free = False
        else:
            free = True
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    source_after = {key: sha(Path(cook["project"]) / key) for key in cook["source_hashes_before"]}
    unchanged = source_after == cook["source_hashes_before"]
    report = {"schema": "ccp-060-interrupted-mangonel-skin-cook-audit/v1",
              "status": "interrupted_no_final_archive_source_preserved" if not pids and not final.exists() and free and unchanged else "state_requires_manual_review",
              "stale_cook_receipt": str(BASE / "cook.json"), "stale_cook_receipt_sha256": sha(BASE / "cook.json"),
              "matching_active_essence_editor_pids": pids,
              "shared_native_byte_lock_free": free,
              "final_archive_present": final.is_file(),
              "intermediate_archive_present": (run / "intermediate/archives/s60m.sga").is_file(),
              "stdout_log": str(stdout), "stdout_sha256": sha(stdout) if stdout.is_file() else None,
              "stdout_tail": stdout.read_text(encoding="utf-8", errors="replace")[-1800:] if stdout.is_file() else None,
              "stderr_log": str(stderr), "stderr_sha256": sha(stderr) if stderr.is_file() else None,
              "source_bytes_preserved": unchanged,
              "no_cook_or_cleanup_performed_by_audit": True}
    write(RECEIPT, report)
    return {"status": report["status"], "lock_free": free, "source_preserved": unchanged,
            "final_archive_present": final.is_file(), "receipt": str(RECEIPT)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
