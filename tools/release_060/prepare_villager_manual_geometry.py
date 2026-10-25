"""Short, private native geometry source from the two real villager exports."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, read, sha, write


def hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main(gender: str) -> dict:
    guard()
    key = "s60v" if gender == "male" else "s60w"
    project = STAGING / ("svm" if gender == "male" else "svf") / "Mods" / key
    source = project / "project/source"
    rel = f"art/scenario/garrison/{key}/body"
    body = source / rel
    prior = STAGING / ("vm" if gender == "male" else "vf") / "Mods" / ("v60m" if gender == "male" else "v60f") / "project/source"
    old_key = "v60m" if gender == "male" else "v60f"
    old_rel = f"art/scenario/garrison/{old_key}/units/{old_key}_villager_geometry_control/body"
    old_body = prior / old_rel
    export_file = OUT / f"qualification/villager-geometry-route/{gender}/export.json"
    folder = OUT / f"qualification/villager-geometry-route/20261018-resume/{gender}/manual"
    receipt = folder / "prepare.json"
    create_log = folder / "create.log"
    for p in (project, body, receipt, create_log): owned(p)
    if project.exists() or receipt.exists() or create_log.exists():
        raise FileExistsError("Preserve previous villager manual attempt")
    export = read(export_file)
    if export["gender"] != gender or export["status"] != "source_export_only_native_46_bone_palette_unproved":
        raise RuntimeError("Villager export contract drift")
    fbx = Path(export["folder"]) / "model.fbx"
    if sha(fbx) != export["files"]["model.fbx"]["sha256"]:
        raise RuntimeError("Villager FBX drift")
    names = ("model.fbx", "model.rig", "model.rgo", "model.rgotemplate",
             "albedo.png", "normal.png", "metalness.png", "roughness.png")
    if any(not (old_body / n).is_file() for n in names):
        raise FileNotFoundError("Installed generated source incomplete")
    command = [str(CORE), "mod-project", "create", "--library", str(project.parent.parent), "--name", key]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    folder.mkdir(parents=True)
    create_log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                          + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
                          encoding="utf-8")
    if result.returncode: raise RuntimeError(f"Fresh private project create failed: {create_log}")
    config = read(project / "mod-project.json")
    if config.get("key") != key or config.get("animated_units") or config.get("assets") or config.get("cooks") or config.get("game_mode", {}).get("enabled"):
        raise RuntimeError("Private geometry project is not blank")
    before = hashes(project)
    burn = source / "_default.burnproj"
    original = burn.read_text(encoding="utf-8")
    prior_rules = (prior / "_default.burnproj").read_text(encoding="utf-8")
    old = old_rel.replace("/", "\\")
    new = rel.replace("/", "\\")
    rules = [b for b in re.findall(r"<BurnRule>.*?</BurnRule>", prior_rules, re.DOTALL) if old in b]
    burners = [re.search(r"<Burner>(.*?)</Burner>", b).group(1) for b in rules]
    if burners != ["RR Material Burner", "RGM", "RRGeometry", "RGO"]:
        raise RuntimeError("Installed native body burn rules changed")
    revised = original.replace("</Rules>", "\n".join(b.replace(old, new) for b in rules) + "\n\t</Rules>", 1)
    ET.fromstring(revised)
    body.mkdir(parents=True)
    for name in names:
        shutil.copy2(fbx if name == "model.fbx" else old_body / name, body / name)
    old_mat = ET.parse(old_body / "model.material").getroot().find("material")
    if old_mat is None or old_mat.get("source") != "unit":
        raise RuntimeError("Generated diagnostic material is not unit")
    slots = {p.get("name"): Path(p.get("value", "")).name for p in old_mat.findall("param") if p.get("type") == "tex2D"}
    if slots != {"albedoTexture": "albedo.png", "normalMap": "normal.png", "metalTex": "metalness.png", "roughnessTex": "roughness.png"}:
        raise RuntimeError("Generated diagnostic material slots changed")
    matset = ET.Element("materialSet")
    for lod in (1, 2, 3):
        item = ET.SubElement(matset, "material", {"name": f"lod{lod}", "type": "shader", "source": "unit"})
        for slot, file in slots.items():
            ET.SubElement(item, "param", {"name": slot, "type": "tex2D", "value": rel + "/" + file})
    ET.indent(matset)
    (body / "model.material").write_bytes(ET.tostring(matset, encoding="utf-8", xml_declaration=True))
    burn.write_text(revised, encoding="utf-8")
    after = hashes(project)
    added = set(after) - set(before)
    expected = {"project/source/" + rel + "/" + n for n in (*names, "model.material")}
    changed = {n for n in before if before[n] != after.get(n)}
    if added != expected or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError(f"Private manual source allowlist drift: {added=} {changed=}")
    record = {"schema": "ccp-060-villager-short-manual-source/v1", "status": "prepared_not_cooked",
              "gender": gender, "project": str(project), "key": key, "body": str(body),
              "source_export_sha256": sha(export_file), "generated_source_rig_sha256": sha(body / "model.rig"),
              "generated_english_rgo_diagnostic_only": True,
              "neutral_material_not_for_stock_pair": True, "no_actor_or_animation_owner": True,
              "source_hashes_after": after, "only_added": sorted(added), "only_changed": sorted(changed),
              "create_log": str(create_log), "create_log_sha256": sha(create_log)}
    write(receipt, record)
    return {"status": record["status"], "project": str(project), "receipt": str(receipt)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gender", choices=("male", "female"))
    print(json.dumps(main(ap.parse_args().gender), indent=2))
