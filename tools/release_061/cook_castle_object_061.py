"""Fresh isolated Garrison object-material cook for retained Castle FBX sources."""
from __future__ import annotations

import hashlib
import json
import msvcrt
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import configuration, check_storage

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
EXT = Path(CFG["external_root"])
OUT = ROOT / "output/release_061/castle-object-cook-r1"
WORK = EXT / "staging/release_061/castle-object-r1"
CORE = Path(CFG["garrison_core"])
EDITOR = Path(CFG["art_editor"])
LOCK = EXT / "output/release_020/native-build.lock"
PROJECT_NAME = "cc061castle"
LIBRARY = WORK / "library"
PROJECT = LIBRARY / "Mods" / PROJECT_NAME


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(label: str, *args: object, timeout: int = 1800) -> str:
    command = [str(x) for x in args]
    proc = subprocess.run(command, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    log = OUT / f"{label}.log"
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(proc.returncode)
                   + "\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr,
                   encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"{label} failed: {log}; exit {proc.returncode}")
    return proc.stdout


def main() -> None:
    if OUT.exists() or WORK.exists():
        raise FileExistsError("Preserve existing object-cook attempt")
    OUT.mkdir(parents=True)
    WORK.mkdir(parents=True)
    frozen = []
    for name in ("imperial_citadel", "resistance_hq"):
        original = ROOT / "art/exports/castle_next/landmarks" / name
        handoff = json.loads((ROOT / "output/castle_next/landmarks" / name / "handoff.json").read_text())
        expected = handoff["export_sha256"]
        actual = {p.name: digest(p) for p in original.iterdir() if p.is_file()}
        if actual != expected:
            raise RuntimeError(f"Retained source drift: {name}")
        target = WORK / "inputs" / name
        shutil.copytree(original, target)
        copied = {p.name: digest(p) for p in target.iterdir() if p.is_file()}
        if copied != expected:
            raise RuntimeError(f"Staged source drift: {name}")
        frozen.append({"name": name, "source": str(original), "staged": str(target),
                       "hashes": actual, "parts": handoff["building"]["parts"]})
    (OUT / "input-freeze.json").write_text(json.dumps(frozen, indent=2) + "\n")

    with LOCK.open("r+b") as stream:
        msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        try:
            run("create", CORE, "mod-project", "create", "--library", LIBRARY,
                "--name", PROJECT_NAME, timeout=120)
            run("settings", CORE, "mod-project", "settings", "--project", PROJECT,
                "--live-reload", "off", timeout=120)
            for row in frozen:
                run("register-" + row["name"], CORE, "mod-project", "building",
                    "--project", PROJECT, "--source", row["staged"],
                    "--name", row["name"], "--profile", "english-house",
                    "--integration", "script", timeout=300)
            config = json.loads((PROJECT / "mod-project.json").read_text())
            if config["game_mode"]["enabled"] or config["game_mode"]["live_reload"]:
                raise RuntimeError("Unexpected Garrison game mode or live reload")
            (OUT / "project-freeze.json").write_text(json.dumps({
                "project": str(PROJECT), "config_sha256": digest(PROJECT / "mod-project.json"),
                "garrison_mod_id": config["mod_id"], "source": frozen,
                "route": "native object-PBR Garrison building; no owner-colour structure material conversion",
            }, indent=2) + "\n")
            result = run("native-cook", CORE, "mod-project", "cook", "--project", PROJECT,
                         "--editor", EDITOR, "--timeout", "1800", timeout=2000)
            (OUT / "native-cook-result.txt").write_text(result, encoding="utf-8")
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

    after = []
    for row in frozen:
        original = Path(row["source"])
        staged = Path(row["staged"])
        for folder in (original, staged):
            hashes = {p.name: digest(p) for p in folder.iterdir() if p.is_file()}
            if hashes != row["hashes"]:
                raise RuntimeError(f"Source changed during cook: {folder}")
        after.append({"name": row["name"], "source_and_staging_unchanged": True})
    (OUT / "post-cook-source.json").write_text(json.dumps(after, indent=2) + "\n")
    print("OBJECT_COOK_COMPLETED", OUT)


if __name__ == "__main__":
    main()
