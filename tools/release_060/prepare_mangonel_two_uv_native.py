"""Fresh short native source for real six-group/two-UV mangonel FBX."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, read, sha, write

KEY = "s60m"
LIBRARY = STAGING / "smu"
PROJECT = LIBRARY / "Mods/s60m"
BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-native"
PREP = BASE / "prepare.json"
EXPORT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-export.json"
PRIOR_PREP = OUT / "qualification/nonhumanoid-route-preflight/mangonel/partition-probe/prepare.json"
PRIOR_PROJECT = STAGING / "smp/Mods/s60m"
BODY_REL = "art/scenario/garrison/s60m/body"


def hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main():
    guard()
    body = PROJECT / "project/source" / BODY_REL
    for p in (PROJECT, PREP, BASE / "create.log", body): owned(p)
    if PROJECT.exists() or PREP.exists(): raise FileExistsError("Preserve two-UV manual source attempt")
    export = read(EXPORT)
    if (export["status"] != "source_export_only_native_cook_unproved" or
            export["stock_bones"] != 14 or len(export["uv_layers"]) != 6 or
            any(row["uv_layers"] != ["UVMap", "UV2"] for row in export["uv_layers"])):
        raise RuntimeError("Two-UV six-group export contract drift")
    fbx = Path(export["exported_fbx"])
    if sha(fbx) != export["exported_fbx_sha256"]: raise RuntimeError("Two-UV FBX drift")
    prior = read(PRIOR_PREP)
    if (prior["status"] != "six_group_structure_source_prepared_not_cooked" or
            Path(prior["project"]) != PRIOR_PROJECT):
        raise RuntimeError("Previous partition source drift")
    source_body = PRIOR_PROJECT / "project/source" / BODY_REL
    source_burn = PRIOR_PROJECT / "project/source/_default.burnproj"
    if sha(source_body / "model.rig") != prior["source_rig_sha256"] or sha(source_burn) != prior["project_file_sha256_after"]["project/source/_default.burnproj"]:
        raise RuntimeError("Partition and burn-rule source bytes changed")
    command = [str(CORE), "mod-project", "create", "--library", str(LIBRARY), "--name", KEY]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    BASE.mkdir(parents=True, exist_ok=True)
    log = BASE / "create.log"
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode) +
                   "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    if result.returncode: raise RuntimeError(f"Blank source create failed: {log}")
    config = read(PROJECT / "mod-project.json")
    if config.get("key") != KEY or config.get("animated_units") or config.get("assets") or config.get("cooks") or config.get("game_mode", {}).get("enabled"):
        raise RuntimeError("Fresh source project is not blank")
    before = hashes(PROJECT)
    shutil.copytree(source_body, body)
    shutil.copy2(fbx, body / "model.fbx")
    shutil.copy2(source_burn, PROJECT / "project/source/_default.burnproj")
    after = hashes(PROJECT)
    added = set(after) - set(before)
    expected = {"project/source/" + BODY_REL + "/" + p.name for p in body.iterdir() if p.is_file()}
    changed = {p for p in before if before[p] != after.get(p)}
    if added != expected or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError(f"Two-UV source allowlist drift: {added=} {changed=}")
    record = {"schema": "ccp-060-mangonel-two-uv-native-source/v1", "status": "six_group_two_uv_partition_source_prepared_not_cooked",
              "project": str(PROJECT), "project_key": KEY, "source_body": str(body),
              "source_fbx_sha256": sha(body / "model.fbx"), "source_rig_sha256": sha(body / "model.rig"),
              "two_uv_export_sha256": sha(EXPORT), "prior_partition_source_sha256": sha(PRIOR_PREP),
              "project_file_sha256_after": after, "only_added": sorted(added), "only_changed": sorted(changed),
              "stock_rgo_and_neutral_material_diagnostic_only": True,
              "no_generated_unit_or_animator": True, "create_log": str(log), "create_log_sha256": sha(log)}
    write(PREP, record)
    return {"status": record["status"], "project": str(PROJECT), "receipt": str(PREP)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
