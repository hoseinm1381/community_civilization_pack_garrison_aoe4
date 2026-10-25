#!/usr/bin/env python3
"""Run a dependency-free smoke test against the bundled SCAR skeleton."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    validator = skill_root / "scripts" / "validate_scar.py"
    skeleton = skill_root / "assets" / "game-mode-skeleton.scar"
    result = subprocess.run(
        [sys.executable, str(validator), str(skeleton)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    with tempfile.TemporaryDirectory(prefix="aoe4_scar_skill_") as directory:
        broken = Path(directory) / "broken_mode.scar"
        broken.write_text(
            """import("cardinal.scar")
Core_RegisterModule("BrokenMode")
_broken_mode = { options = {} }
function BrokenMode_Start()
    if _broken_mode.options.enabled then
        return
    end
end
""",
            encoding="utf-8",
        )
        negative = subprocess.run(
            [sys.executable, str(validator), str(broken)],
            capture_output=True,
            text=True,
        )
    if negative.returncode == 0 or "options-uninitialized" not in negative.stdout:
        print("SCAR negative fixture did not detect an uninitialized namespaced options table.")
        print(negative.stdout, end="")
        return 1
    print("SCAR skill self-test passed: game-mode skeleton validates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
