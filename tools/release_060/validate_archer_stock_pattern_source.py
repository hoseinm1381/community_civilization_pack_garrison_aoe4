"""Installed source-only unit validation with the exact converted stock pattern."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, read, sha, write

ORIGINAL = OUT / "qualification/archer-matched-control-export.json"
MASK = OUT / "qualification/material-route-probe/stock-pattern-conversion.json"
INPUT = STAGING / "material-route-stock-input"
LOG = OUT / "qualification/material-route-probe/stock-pattern-validation.log"
RECEIPT = OUT / "qualification/material-route-probe/stock-pattern-validation.json"


def main() -> None:
    guard()
    for path in (INPUT, LOG, RECEIPT):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve previous stock-mask validation: {path}")
    original, mask = read(ORIGINAL), read(MASK)
    if mask["status"] != "verified_current_stock_mask_top_mip_png_pixel_exact" or sha(mask["png"]) != mask["png_sha256"]:
        raise RuntimeError("Stock mask conversion receipt drift")
    source = Path(original["folder"])
    for name, record in original["files"].items():
        if sha(source / name) != record["sha256"]:
            raise RuntimeError(f"Pinned control source drift: {name}")
    INPUT.mkdir(parents=True)
    for name in ("action.json", "albedo.png", "model.fbx"):
        shutil.copy2(source / name, INPUT / name)
    shutil.copy2(mask["png"], INPUT / "pattern.png")
    action = read(INPUT / "action.json")
    if action.get("textures") != ["albedo"]:
        raise RuntimeError("Unexpected original texture inputs")
    action["textures"] = ["albedo", "pattern"]
    write(INPUT / "action.json", action)
    cmd = [str(CORE), "mod-project", "unit-validate", "--source", str(INPUT / "action.json")]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("COMMAND: " + " ".join(cmd) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
                   encoding="utf-8")
    write(RECEIPT, {"schema": "ccp-060-stock-pattern-source-validation/v1",
                    "status": "source_validated_not_cooked" if result.returncode == 0 else "rejected",
                    "original_export_sha256": sha(ORIGINAL), "stock_mask_receipt_sha256": sha(MASK),
                    "input": str(INPUT), "input_sha256": {p.name: sha(p) for p in INPUT.iterdir()},
                    "exit_code": result.returncode, "log": str(LOG), "log_sha256": sha(LOG),
                    "no_native_cook_or_runtime_claim": True})
    print(json.dumps({"exit_code": result.returncode, "receipt": str(RECEIPT)}, indent=2))
    if result.returncode:
        raise RuntimeError(f"Installed unit validator rejected stock pattern source: {LOG}")


if __name__ == "__main__":
    main()
