"""Try the installed, genuine Garrison unit route for a villager control.

This is diagnostic: generated English actors, animator and materials cannot enter
the 0.6.0 civilization. A native success still requires independent skin readback.
Run once per gender only after the claimed Blender exporter has completed.
"""
from __future__ import annotations

import argparse
import json
import msvcrt
import subprocess
from pathlib import Path

from common import CFG, CORE, EXPORT, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

EDITOR = Path(CFG["art_editor"])
CONTRACT = OUT / "qualification/villager-geometry-route/contract-v2.json"
PREFLIGHT = OUT / "qualification/villager-geometry-route/20261018-resume/preflight.json"
PARENT = OUT / "qualification/villager-geometry-route/20261018-resume"


def run(command: list[object], log: Path, timeout: int) -> int:
    owned(log)
    if log.exists():
        raise FileExistsError(f"Preserve existing diagnostic: {log}")
    result = subprocess.run([str(x) for x in command], capture_output=True, text=True,
                            errors="replace", timeout=timeout)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("COMMAND: " + " ".join(map(str, command)) + "\nEXIT: "
                   + str(result.returncode) + "\nSTDOUT:\n" + result.stdout
                   + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    return result.returncode


def main(gender: str) -> dict:
    guard()
    if gender not in {"male", "female"}:
        raise ValueError("gender must be male or female")
    dest = owned(PARENT / gender / "normal-route.json")
    if dest.exists():
        raise FileExistsError(f"Preserve existing normal-route receipt: {dest}")
    contract, preflight = read(CONTRACT), read(PREFLIGHT)
    if (preflight["status"] != "pinned_sources_verified_export_and_native_cook_not_run"
            or preflight["contract_sha256"] != sha(CONTRACT)
            or contract["prototype"]["key"] != "english-villager-1"):
        raise RuntimeError("Pinned villager source checkpoint drift")
    export_receipt = OUT / "qualification/villager-geometry-route" / gender / "export.json"
    exported = read(export_receipt)
    if (exported["status"] != "source_export_only_native_46_bone_palette_unproved"
            or exported["gender"] != gender
            or exported["contract_sha256"] != sha(CONTRACT)
            or exported["prototype_key"] != "english-villager-1"
            or exported["prototype_fingerprint"] != contract["prototype"]["fingerprint"]
            or exported["source_palette_bones"] != 46):
        raise RuntimeError("Villager export contract drift")
    folder = Path(exported["folder"])
    if not folder.resolve().is_relative_to(EXPORT.resolve()):
        raise RuntimeError("Export folder escaped owned 0.6.0 root")
    for name, entry in exported["files"].items():
        item = folder / name
        if not item.is_file() or item.stat().st_size != entry["bytes"] or sha(item) != entry["sha256"]:
            raise RuntimeError(f"Exported source changed: {item}")
    if sha(Path(exported["saved_blend"])) != exported["saved_blend_sha256"]:
        raise RuntimeError("Exported Blender review source changed")
    action = read(folder / "action.json")
    if (action.get("prototype") != "english-villager-1"
            or action.get("fingerprint") != contract["prototype"]["fingerprint"]
            or action.get("material_name") != "lod1"
            or action.get("overrides") or action.get("attachments")
            or len(action.get("bones", [])) != 73):
        raise RuntimeError("Generated action identity, no-overrides, or rest bones drift")
    if not EDITOR.is_file() or not NATIVE_LOCK.is_file():
        raise RuntimeError("Configured Garrison art editor or shared native lock absent")
    project_key = {"male": "v60m", "female": "v60f"}[gender]
    # Native burners have a measured short-path sensitivity in this workspace.
    library = owned(STAGING / {"male": "vm", "female": "vf"}[gender])
    project = owned(library / "Mods" / project_key)
    if project.exists():
        raise FileExistsError(f"Preserve existing private project: {project}")
    receipt = {"schema": "ccp-060-villager-normal-route/v1",
               "status": "validating_installed_garrison_unit_source",
               "gender": gender, "source_receipt": str(export_receipt),
               "source_receipt_sha256": sha(export_receipt),
               "source_action_sha256": sha(folder / "action.json"),
               "project": str(project), "project_key": project_key,
               "generated_english_unit_and_animator_diagnostic_only": True,
               "native_cook_does_not_prove_chinese_palette_or_original_animation_owner": True,
               "steps": []}
    write(dest, receipt)

    def step(label: str, command: list[object], timeout: int):
        log = owned(dest.parent / (label + ".log"))
        exit_code = run(command, log, timeout)
        receipt["steps"].append({"name": label, "exit_code": exit_code,
                                 "log": str(log), "log_sha256": sha(log)})
        write(dest, receipt)
        if exit_code:
            receipt["status"] = label + "_rejected_preserved"
            write(dest, receipt)
            raise RuntimeError(f"Installed Garrison {label} rejected; inspect {log}")

    step("unit-validate", [CORE, "mod-project", "unit-validate", "--source",
                           folder / "action.json"], 180)
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            receipt["status"] = "shared_native_byte_lock_busy_no_project"
            receipt["error"] = str(error)
            write(dest, receipt)
            raise RuntimeError("Shared native byte lock busy") from error
        try:
            receipt["status"] = "shared_native_byte_lock_held"
            write(dest, receipt)
            step("create", [CORE, "mod-project", "create", "--library", library,
                            "--name", project_key], 120)
            config = read(project / "mod-project.json")
            if (config.get("key") != project_key or config.get("animated_units")
                    or config.get("game_mode", {}).get("enabled")):
                raise RuntimeError("Blank private project contract changed")
            receipt["temporary_mod_id"] = config["mod_id"]
            write(dest, receipt)
            step("unit-add", [CORE, "mod-project", "unit-add", "--project", project,
                              "--source", folder, "--name",
                              project_key + "_villager_geometry_control"], 600)
            config = read(project / "mod-project.json")
            if len(config.get("animated_units", [])) != 1:
                raise RuntimeError("Generated diagnostic unit registration changed")
            step("cook", [CORE, "mod-project", "cook", "--project", project,
                          "--editor", EDITOR, "--timeout", "1200"], 1300)
            receipt["status"] = "normal_garrison_cook_completed_pending_native_readback"
            receipt["project_file_sha256"] = sha(project / "mod-project.json")
            write(dest, receipt)
        except BaseException as error:
            if not receipt["status"].endswith("_rejected_preserved"):
                receipt["status"] = "normal_route_exception_preserved"
                receipt["error"] = f"{type(error).__name__}: {error}"
                write(dest, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    return {"status": receipt["status"], "receipt": str(dest), "project": str(project)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("gender", choices=("male", "female"))
    args = parser.parse_args()
    print(json.dumps(main(args.gender), indent=2))
