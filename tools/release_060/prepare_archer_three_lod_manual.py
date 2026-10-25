"""Prepare a fresh short native art-source project for diagnostic three-LOD geometry.

No generated Build Unit entries. Materials are three neutral genuine source-input
`unit` records and are NEVER candidates for pairing with the stock RRMaterial.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, read, sha, write

KEY = "n60l"
LIBRARY = STAGING / "n"
PROJECT = LIBRARY / "Mods/n60l"
SCAFFOLD = PROJECT / "project/source"
BODY_REL = "art/scenario/garrison/n60l/body"
BODY = SCAFFOLD / BODY_REL
SOURCE_PROJECT = STAGING / "l/Mods/u60l"
SOURCE_BODY_REL = "art/scenario/garrison/u60l/units/u60l_archer_3lod_control/body"
SOURCE_BODY = SOURCE_PROJECT / "project/source" / SOURCE_BODY_REL
EXPORT = OUT / "qualification/archer-pairing-prep/export.json"
FAILED_COOK = OUT / "qualification/archer-pairing-prep/cook.json"
LOG = OUT / "qualification/archer-pairing-prep/manual/create.log"
RECEIPT = OUT / "qualification/archer-pairing-prep/manual/prepare.json"
COPY_NAMES = ("model.fbx", "model.rig", "model.rgo", "model.rgotemplate",
              "albedo.png", "normal.png", "metalness.png", "roughness.png")
RULE_BURNERS = ("RR Material Burner", "RGM", "RRGeometry", "RGO")


def files_under(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main() -> None:
    guard()
    for path in (PROJECT, BODY, LOG, RECEIPT):
        owned(path)
    if PROJECT.exists() or LOG.exists() or RECEIPT.exists():
        raise FileExistsError("Preserve prior n60l manual-source attempt")
    source = read(EXPORT)
    failure = read(FAILED_COOK)
    if (source["schema"] != "ccp-060-archer-paired-stock-lod-export/v1"
            or failure["status"] != "failed_under_byte_lock"
            or [step["label"] for step in failure["steps"]] != ["create", "unit-add", "cook"]
            or failure["steps"][-1]["returncode"] == 0):
        raise RuntimeError("Three-LOD source or normal-cook failure drift")
    for name in COPY_NAMES:
        file = SOURCE_BODY / name
        if not file.is_file():
            raise FileNotFoundError(f"Generated neutral source component missing: {file}")
    if sha(SOURCE_BODY / "model.fbx") != source["files"]["model.fbx"]["sha256"]:
        raise RuntimeError("Staged FBX differs from exported three-LOD control")
    original_material = ET.parse(SOURCE_BODY / "model.material").getroot().find("material")
    if (original_material is None or original_material.get("source") != "unit"
            or original_material.get("name") != "lod1"):
        raise RuntimeError("Generated neutral authoring material drift")
    slots = {param.get("name"): Path(param.get("value", "")).name
             for param in original_material.findall("param") if param.get("type") == "tex2D"}
    if slots != {"albedoTexture": "albedo.png", "normalMap": "normal.png",
                  "metalTex": "metalness.png", "roughnessTex": "roughness.png"}:
        raise RuntimeError("Generated source material slot semantics drift")
    command = [str(CORE), "mod-project", "create", "--library", str(LIBRARY), "--name", KEY]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
                   encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Fresh scaffold create failed; inspect {LOG}")
    config = read(PROJECT / "mod-project.json")
    if (config.get("key") != KEY or config.get("animated_units") or config.get("assets")
            or config.get("cooks") or config.get("game_mode", {}).get("enabled")
            or config.get("game_mode", {}).get("live_reload")):
        raise RuntimeError("Fresh manual art scaffold is not blank")
    before = files_under(PROJECT)
    burn = SCAFFOLD / "_default.burnproj"
    original = burn.read_text(encoding="utf-8")
    source_rules = (SOURCE_PROJECT / "project/source/_default.burnproj").read_text(encoding="utf-8")
    blocks = re.findall(r"<BurnRule>.*?</BurnRule>", source_rules, re.DOTALL)
    old_native = SOURCE_BODY_REL.replace("/", "\\")
    new_native = BODY_REL.replace("/", "\\")
    selected = [block for block in blocks if old_native in block]
    if (len(selected) != 4 or tuple(re.search(r"<Burner>(.*?)</Burner>", block).group(1)
                                     for block in selected) != RULE_BURNERS):
        raise RuntimeError("Installed generated four-art-burn-rule contract changed")
    revised = original.replace("</Rules>", "\n".join(block.replace(old_native, new_native)
                                                    for block in selected) + "\n\t</Rules>", 1)
    if revised == original or old_native in revised:
        raise RuntimeError("Art burn rule include replacement failed")
    ET.fromstring(revised)
    BODY.mkdir(parents=True)
    for name in COPY_NAMES:
        shutil.copy2(SOURCE_BODY / name, BODY / name)
    material_set = ET.Element("materialSet")
    for number in (1, 2, 3):
        material = ET.SubElement(material_set, "material", {
            "name": f"lod{number}", "type": "shader", "source": "unit"})
        for slot, filename in slots.items():
            ET.SubElement(material, "param", {"name": slot, "type": "tex2D",
                                              "value": BODY_REL + "/" + filename})
    ET.indent(material_set)
    (BODY / "model.material").write_bytes(ET.tostring(material_set, encoding="utf-8", xml_declaration=True))
    burn.write_text(revised, encoding="utf-8")
    after = files_under(PROJECT)
    added = set(after) - set(before)
    expected_added = {"project/source/" + BODY_REL + "/" + name
                      for name in (*COPY_NAMES, "model.material")}
    changed = {name for name in before if before[name] != after.get(name)}
    if added != expected_added or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError(f"Manual source allowlist drift: added={added}, changed={changed}")
    receipt = {"schema": "ccp-060-three-lod-manual-geometry-source/v1",
               "status": "manual_neutral_material_geometry_source_prepared_not_cooked",
               "project": str(PROJECT), "project_key": KEY,
               "temporary_mod_id": config["mod_id"],
               "source_body": str(BODY), "source_only_no_unit_add": True,
               "no_generated_unit_entries_or_actor": True,
               "garrison_build_unit_admission_not_claimed": True,
               "source_fbx_sha256": sha(BODY / "model.fbx"),
               "neutral_authoring_slots": slots, "neutral_authoring_material_names": ["lod1", "lod2", "lod3"],
               "diagnostic_compiled_material_must_not_enter_stock_pair": True,
               "qualified_burn_rule_burners": RULE_BURNERS,
               "scaffold_file_sha256_before": before,
               "project_file_sha256_after": after,
               "only_added": sorted(added), "only_changed": sorted(changed),
               "create_log": str(LOG), "create_log_sha256": sha(LOG)}
    write(RECEIPT, receipt)
    print(json.dumps({"status": receipt["status"], "project": str(PROJECT),
                      "fbx_sha256": receipt["source_fbx_sha256"], "receipt": str(RECEIPT)}, indent=2))


if __name__ == "__main__":
    main()
