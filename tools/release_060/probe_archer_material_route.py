"""Source-only Build Unit pattern-slot diagnostic; never cook or integrate it.

The pattern input is deliberately a byte copy of albedo. It proves only that the
supported builder emits a patternTex slot; it is INVALID as a player-colour mask.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, read, sha, write

SOURCE_RECEIPT = OUT / "qualification/archer-matched-control-export.json"
STOCK_DECODE = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
BASE_PROJECT = STAGING / "u/Mods/u60a/project/source/art/scenario/garrison/u60a/units/u60a_archer_control/body/model.material"
LIBRARY = STAGING / "m"
PROJECT = LIBRARY / "Mods/m60p"
INPUT = owned(STAGING / "material-route-probe/input")
RECEIPT = OUT / "qualification/material-route-probe/receipt.json"
LOGS = OUT / "qualification/material-route-probe/logs"


def step(name: str, args: list[object], timeout: int) -> dict:
    proc = subprocess.run([str(x) for x in args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    log = owned(LOGS / (name + ".log"))
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("COMMAND: " + " ".join(str(x) for x in args) + "\nEXIT: "
                   + str(proc.returncode) + "\nSTDOUT:\n" + proc.stdout
                   + "\nSTDERR:\n" + proc.stderr, encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"{name} failed exit {proc.returncode}; {log}")
    return {"log": str(log), "log_sha256": sha(log), "exit_code": proc.returncode}


def parameters(path: Path) -> dict:
    root = ET.parse(path).getroot()
    return {mat.get("name"): {p.get("name"): {"type": p.get("type"), "value": p.get("value")}
                                    for p in mat.findall("param")}
            for mat in root.findall("material")}


def main() -> None:
    guard()
    if INPUT.exists() or PROJECT.exists() or RECEIPT.exists():
        raise FileExistsError("Preserve existing isolated material-route diagnostic")
    source = read(SOURCE_RECEIPT)
    original = Path(source["folder"])
    if source["prototype_key"] != "english-spearman-2":
        raise RuntimeError("Unexpected prototype source")
    for name, identity in source["files"].items():
        if sha(original / name) != identity["sha256"]:
            raise RuntimeError(f"Control source drift: {name}")
    stock = read(STOCK_DECODE)
    stock_slots = {mat["name"]: {tex["name"]: tex.get("logical_path")
                    for block in mat["blocks"] for tex in block.get("textures", [])}
                   for mat in stock["material"]["materials"]}
    INPUT.mkdir(parents=True)
    for name in ("action.json", "albedo.png", "model.fbx"):
        shutil.copy2(original / name, INPUT / name)
    shutil.copy2(original / "albedo.png", INPUT / "pattern.png")
    action = read(INPUT / "action.json")
    if action.get("textures") != ["albedo"]:
        raise RuntimeError("Original action texture contract changed")
    action["textures"] = ["albedo", "pattern"]
    write(INPUT / "action.json", action)
    receipt = {"schema": "ccp-060-archer-material-route-probe/v1", "status": "started",
               "source_receipt": str(SOURCE_RECEIPT), "source_receipt_sha256": sha(SOURCE_RECEIPT),
               "stock_manifest": str(STOCK_DECODE), "stock_manifest_sha256": sha(STOCK_DECODE),
               "stock_slots": stock_slots, "baseline_generated_material": str(BASE_PROJECT),
               "baseline_generated_material_sha256": sha(BASE_PROJECT),
               "baseline_params": parameters(BASE_PROJECT),
               "probe_input": str(INPUT),
               "probe_files_sha256": {p.name: sha(p) for p in INPUT.iterdir()},
               "pattern_input_is_invalid_duplicate_albedo": True,
               "source_only_no_cook_or_gameplay_integration": True, "steps": {}}
    write(RECEIPT, receipt)
    try:
        receipt["steps"]["validate"] = step("validate", [CORE, "mod-project", "unit-validate",
                                                        "--source", INPUT / "action.json"], 180)
        write(RECEIPT, receipt)
        receipt["steps"]["create"] = step("create", [CORE, "mod-project", "create",
                                                    "--library", LIBRARY, "--name", "m60p"], 120)
        write(RECEIPT, receipt)
        receipt["steps"]["unit_add"] = step("unit-add", [CORE, "mod-project", "unit-add",
                                                          "--project", PROJECT, "--source", INPUT,
                                                          "--name", "m60p_pattern_source"], 600)
        write(RECEIPT, receipt)
        generated = (PROJECT / "project/source/art/scenario/garrison/m60p/units"
                     / "m60p_pattern_source/body/model.material")
        if not generated.is_file():
            raise FileNotFoundError(f"Expected generated material source: {generated}")
        receipt["generated_material"] = str(generated)
        receipt["generated_material_sha256"] = sha(generated)
        receipt["generated_params"] = parameters(generated)
        params = next(iter(receipt["generated_params"].values()))
        receipt["status"] = ("pattern_source_recognized_skin_lut_absent"
                             if "patternTex" in params and "skinTintLUT" not in params
                             else "inspect_generated_material")
        write(RECEIPT, receipt)
        print(json.dumps({"status": receipt["status"], "receipt": str(RECEIPT),
                          "generated_slots": list(params)}, indent=2))
    except BaseException as error:
        receipt["status"] = "failed_preserved"
        receipt["error"] = f"{type(error).__name__}: {error}"
        write(RECEIPT, receipt)
        raise


if __name__ == "__main__":
    main()
