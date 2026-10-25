"""Prepare private stock-rig mounted geometry controls; no gameplay or animation cook."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, CORE, OUT, STAGING, guard, owned, read, sha, write
from prepare_mangonel_manual_geometry import png, file_hashes

CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
ARCHER = STAGING / "l/Mods/u60l/project/source"
ARCHER_REL = "art/scenario/garrison/u60l/units/u60l_archer_3lod_control/body"
KINDS = {"horseman2": ("sh", "s60h", "ArtChinese.sga"),
         "elephant": ("se", "s60e", "ArtSultanate.sga")}


def main(kind: str):
    guard()
    if kind not in KINDS:
        raise ValueError(kind)
    short, key, rgo_archive_name = KINDS[kind]
    project = owned(STAGING / short / "Mods" / key)
    rel = f"art/scenario/garrison/{key}/body"
    body = owned(project / "project/source" / rel)
    folder = owned(OUT / "qualification/nonhumanoid-route-preflight" / kind / "manual")
    receipt, log = owned(folder / "prepare.json"), owned(folder / "create.log")
    if project.exists() or receipt.exists() or log.exists():
        raise FileExistsError("Preserve prior mounted control")
    row = read(CONTRACT)["donors"][kind]
    export_path = OUT / "qualification/nonhumanoid-route-preflight" / kind / "source-export.json"
    export = read(export_path)
    if (export["pilot"] != kind or export["status"] != "raw_stock_rig_fbx_export_only_native_cook_unproved"
            or export["contract_sha256"] != sha(CONTRACT)
            or export["stock_skeleton_bones"] != row["full_skeleton_bones"]
            or export["fbx_skin_nodes"] < 6 or export["fbx_cluster_nodes"] < 6):
        raise RuntimeError("Real six-group stock-rig export missing or drifted")
    fbx = Path(export["exported_fbx"])
    data = fbx.read_bytes()
    if sha(fbx) != export["exported_fbx_sha256"] or data.count(b"DeformerS\x04\x00\x00\x00Skin") < 6:
        raise RuntimeError("FBX lacks verified six-group skin")
    donor_path = Path(row["donor_manifest"])
    if sha(donor_path) != row["donor_manifest_sha256"]:
        raise RuntimeError("Native donor manifest drift")
    donor = read(donor_path)
    bones = [b["name"] for b in donor["skeleton"]["bones"]]
    if len(bones) != row["full_skeleton_bones"]:
        raise RuntimeError("Native skeleton/material contract drift")
    if len(set(bones)) != len(bones):
        raise RuntimeError("Duplicate native bone name")
    rig = ("[HAVOK SKELETON DEFINITION FILE]\n\n[BONES START]\n" + "\n".join(bones)
           + "\n[END]\n\n[PARTITION START]\nfullbody_lod3 " + bones[0] + " " + bones[-1] + "\n[END]\n")
    model = donor["resources"]["model"]
    rgo_member = model["logical_path"].removesuffix(".rgm") + ".rgo"
    archive = Path(model["archive_path"]).with_name(rgo_archive_name)
    listing = subprocess.run([str(ARCH), "list", str(archive), "--filter", Path(rgo_member).name],
                             capture_output=True, text=True, errors="replace", timeout=120, check=True)
    exact = [m for m in json.loads(listing.stdout)["members"] if m["path"] == rgo_member]
    if len(exact) != 1:
        raise RuntimeError("Exact donor RGO missing")
    command = [str(CORE), "mod-project", "create", "--library", str(project.parent.parent), "--name", key]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    folder.mkdir(parents=True)
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Blank mounted project creation failed: {log}")
    config = read(project / "mod-project.json")
    if (config.get("key") != key or config.get("animated_units") or config.get("assets")
            or config.get("cooks") or config.get("game_mode", {}).get("enabled")):
        raise RuntimeError("Mounted diagnostic project is not blank")
    before = file_hashes(project)
    burn = project / "project/source/_default.burnproj"
    source_rules = (ARCHER / "_default.burnproj").read_text(encoding="utf-8")
    old, new = ARCHER_REL.replace("/", "\\"), rel.replace("/", "\\")
    rules = [b for b in re.findall(r"<BurnRule>.*?</BurnRule>", source_rules, re.DOTALL) if old in b]
    if [re.search(r"<Burner>(.*?)</Burner>", b).group(1) for b in rules] != ["RR Material Burner", "RGM", "RRGeometry", "RGO"]:
        raise RuntimeError("Four installed native art rules changed")
    original = burn.read_text(encoding="utf-8")
    revised = original.replace("</Rules>", "\n".join(b.replace(old, new) for b in rules) + "\n\t</Rules>", 1)
    ET.fromstring(revised)
    body.mkdir(parents=True)
    shutil.copy2(fbx, body / "model.fbx")
    (body / "model.rig").write_text(rig, encoding="utf-8")
    rgo_run = subprocess.run([str(ARCH), "extract-member", str(archive), rgo_member, str(body / "model.rgo")],
                             capture_output=True, text=True, errors="replace", timeout=120)
    if rgo_run.returncode:
        raise RuntimeError("Exact donor RGO extraction failed: " + rgo_run.stderr[-500:])
    (body / "model.rgotemplate").write_text("<ObjectTemplate><LodDistances/></ObjectTemplate>\n", encoding="utf-8")
    colours = {"albedo.png": (150, 145, 135), "normal.png": (128, 128, 255),
               "metalness.png": (0, 0, 0), "roughness.png": (200, 200, 200),
               "pattern.png": (255, 255, 255), "skinlut.png": (255, 255, 255)}
    for name, colour in colours.items():
        (body / name).write_bytes(png(colour))
    slot_files = {"albedoTexture": "albedo.png", "normalMap": "normal.png",
                  "metalTex": "metalness.png", "roughnessTex": "roughness.png",
                  "patternTex": "pattern.png", "skinTintLUT": "skinlut.png"}
    matset = ET.Element("materialSet")
    native_materials = donor["material"]["materials"]
    if set(export["native_group_material_order"][i][1] for i in range(6)) != {m["name"] for m in native_materials}:
        raise RuntimeError("Export/native material set mismatch")
    for material in native_materials:
        if material["class"] != "unit":
            raise RuntimeError("Non-unit stock material")
        item = ET.SubElement(matset, "material", {"name": material["name"], "type": "shader", "source": "unit"})
        slots = {t["name"] for block in material["blocks"] for t in block["textures"] if t["name"] != "__default"}
        slots |= {"roughnessTex"}
        if slots - slot_files.keys():
            raise RuntimeError("Unknown native material texture slots: " + str(slots - slot_files.keys()))
        for slot in sorted(slots):
            ET.SubElement(item, "param", {"name": slot, "type": "tex2D", "value": rel + "/" + slot_files[slot]})
    ET.indent(matset)
    (body / "model.material").write_bytes(ET.tostring(matset, encoding="utf-8", xml_declaration=True))
    burn.write_text(revised, encoding="utf-8")
    after = file_hashes(project)
    added = set(after) - set(before)
    expected = {"project/source/" + rel + "/" + n for n in
                ("model.fbx", "model.rig", "model.rgo", "model.rgotemplate", "model.material", *colours)}
    changed = {name for name in before if after.get(name) != before[name]}
    if added != expected or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError(f"Mounted source allowlist mismatch: {added=} {changed=}")
    record = {"schema": "ccp-060-mounted-manual-geometry-source/v1", "status": "prepared_not_cooked",
              "kind": kind, "key": key, "project": str(project), "body": str(body),
              "export_receipt_sha256": sha(export_path), "donor_manifest_sha256": sha(donor_path),
              "source_fbx_sha256": sha(body / "model.fbx"), "source_rig_sha256": sha(body / "model.rig"),
              "exact_stock_rgo_sha256": sha(body / "model.rgo"), "stock_rgo_member": rgo_member,
              "source_hashes_after": after, "only_added": sorted(added), "only_changed": sorted(changed),
              "diagnostic_material_and_rgm_rgo_not_for_final_pair": True,
              "original_stock_animation_owner_must_be_retained": True, "create_log_sha256": sha(log)}
    write(receipt, record)
    return {"status": record["status"], "receipt": str(receipt), "project": str(project)}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=2))
