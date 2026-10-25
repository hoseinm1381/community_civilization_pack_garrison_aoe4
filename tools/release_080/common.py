"""Shared constants and storage/hash helpers for 0.8.0."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage  # noqa: E402

CFG = json.loads((ROOT / "workspace.json").read_text(encoding="utf-8"))
EXT_ROOT = Path(CFG["external_root"])
OUT = ROOT / "output/release_080"
ART = ROOT / "art/authoring/release_080"
EXPORT = ROOT / "art/exports/release_080"
RECIPES = ROOT / "art/recipes/release_080"
STAGING = EXT_ROOT / "staging/r80"
NATIVE_LOCK = ROOT / "output/release_020/native-build.lock"

GUID = CFG["project_guid"]
GUID_HEX = GUID.replace("-", "")
CORE = Path(CFG["garrison_core"])
ARCH = Path(CFG["archive_tool"])
EDITOR = Path(CFG["content_editor"])
ART_EDITOR = Path(CFG["art_editor"])
EXTENSION = Path(CFG["garrison_extension"])

BASELINE_ZIP = ROOT / "output/release_074/delivery/community_civilization_pack-0.7.4.zip"
BASELINE_SGA = ROOT / "output/release_074/delivery/community_civilization_pack.sga"
EXPECTED_ZIP_SHA256 = "6d1bdfa52b8a440848f4b6dd0acc2a45822c9480f289dac63fa630d0ad5d82d4"
EXPECTED_SGA_SHA256 = "becbd1caa38d64a7f0cbb2b428d382da59cc8015ce8bf98578c31f742f664384"


def guard() -> dict:
    return check_storage(ROOT, CFG)


def owned(path: str | Path) -> Path:
    p = Path(path)
    resolved = p.resolve()
    allowed = (ROOT.resolve(), EXT_ROOT.resolve())
    if not any(resolved.is_relative_to(base) for base in allowed):
        raise ValueError(f"Path outside owned roots: {p}")
    return p


def sha(path: str | Path) -> str:
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path: str | Path) -> dict | list:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path: str | Path, data: dict | list) -> Path:
    target = owned(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target


def run_logged(label: str, args: list[str | Path], timeout: int = 1200, cwd: Path | None = None) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    cmd = [str(x) for x in args]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    log_path = OUT / "logs" / f"{label}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        f"COMMAND: {cmd!r}\nEXIT: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed with exit {proc.returncode}; see {log_path}")
    return proc.stdout
