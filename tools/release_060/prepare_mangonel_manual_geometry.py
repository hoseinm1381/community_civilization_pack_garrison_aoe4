"""Prepare a fresh minimal 14-bone, six-group native geometry-only cook source.

Run after a real stock-rig FBX export. Compiled material is diagnostic only;
the later geometry pair must retain the original stock RGM/RGO/RRMaterial/RHKA.
"""
from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, read, sha, write

KEY = "s60m"
LIBRARY = STAGING / "sm"
PROJECT = LIBRARY / "Mods" / KEY
SCAFFOLD = PROJECT / "project/source"
BODY_REL = f"art/scenario/garrison/{KEY}/body"
BODY = SCAFFOLD / BODY_REL
EXPORT = OUT / "qualification/nonhumanoid-route-preflight/siege_mangonel3/source-export.json"
CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
RIG_PROBE = OUT / "qualification/nonhumanoid-route-preflight/20261018-rig-text-probe.json"
RIG = OUT / "qualification/nonhumanoid-route-preflight/minimal-mangonel-14bone-diagnostic.rig"
STOCK_RGO = OUT / "qualification/nonhumanoid-route-preflight/stock-eng-mangonel.rgo"
STOCK_RGO_SHA256 = "6035179342bf4a93b8c58ea3e4f2ad3f80556b8a712b657522f195e24f35a84f"
SOURCE_PROJECT = STAGING / "l/Mods/u60l"
SOURCE_BODY_REL = "art/scenario/garrison/u60l/units/u60l_archer_3lod_control/body"
LOG = OUT / "qualification/nonhumanoid-route-preflight/mangonel/manual/create.log"
RECEIPT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/manual/prepare.json"
RULE_BURNERS = ("RR Material Burner", "RGM", "RRGeometry", "RGO")


def png(rgb: tuple[int, int, int]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    raw = (b"\x00" + bytes(rgb) * 4) * 4
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def file_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main():
    guard()
    for path in (PROJECT, BODY, LOG, RECEIPT):
        owned(path)
    if any(path.exists() for path in (PROJECT, LOG, RECEIPT)):
        raise FileExistsError("Preserve prior mangonel manual source attempt")
    export, contract, probe = read(EXPORT), read(CONTRACT), read(RIG_PROBE)
    donor_row = contract["donors"]["siege_mangonel3"]
    if (export["status"] != "raw_stock_rig_fbx_export_only_native_cook_unproved"
            or export["pilot"] != "siege_mangonel3"
            or export["contract_sha256"] != sha(CONTRACT)
            or export["source_lod_triangles"] != [384, 96, 60, 4449, 1880, 1568]
            or export["stock_palette_bone_counts"] != [2, 12]
            or probe["minimal_candidate_sha256"] != sha(RIG)
            or not STOCK_RGO.is_file() or sha(STOCK_RGO) != STOCK_RGO_SHA256):
        raise RuntimeError("Stock source export or 14-bone rig candidate drift")
    fbx = Path(export["exported_fbx"])
    if sha(fbx) != export["exported_fbx_sha256"]:
        raise RuntimeError("Six-group source FBX drift")
    donor = read(Path(donor_row["donor_manifest"]))
    material = donor["material"]["materials"]
    if len(material) != 1 or material[0]["name"] != "page" or material[0]["class"] != "structure":
        raise RuntimeError("Stock structure/page material contract drift")
    textures = [t["name"] for block in material[0]["blocks"] for t in block["textures"]
                if t["name"] != "__default"]
    if len(textures) != len(set(textures)) or not {"albedoTex", "normalMap", "metalTex", "maskTex5"}.issubset(textures):
        raise RuntimeError("Native structure slot inventory drift")
    command = [str(CORE), "mod-project", "create", "--library", str(LIBRARY), "--name", KEY]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
                   encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Blank mangonel scaffold create failed: {LOG}")
    config = read(PROJECT / "mod-project.json")
    if (config.get("key") != KEY or config.get("animated_units") or config.get("assets")
            or config.get("cooks") or config.get("game_mode", {}).get("enabled")):
        raise RuntimeError("Fresh scaffold is not blank")
    before = file_hashes(PROJECT)
    burn = SCAFFOLD / "_default.burnproj"
    original = burn.read_text(encoding="utf-8")
    source_rules = (SOURCE_PROJECT / "project/source/_default.burnproj").read_text(encoding="utf-8")
    old = SOURCE_BODY_REL.replace("/", "\\")
    new = BODY_REL.replace("/", "\\")
    selected = [block for block in re.findall(r"<BurnRule>.*?</BurnRule>", source_rules, re.DOTALL) if old in block]
    if (len(selected) != 4 or tuple(re.search(r"<Burner>(.*?)</Burner>", b).group(1)
                                     for b in selected) != RULE_BURNERS):
        raise RuntimeError("Installed four native art rules changed")
    revised = original.replace("</Rules>", "\n".join(b.replace(old, new) for b in selected)
                               + "\n\t</Rules>", 1)
    if revised == original or old in revised:
        raise RuntimeError("Native burn rule injection failed")
    ET.fromstring(revised)
    BODY.mkdir(parents=True)
    shutil.copy2(fbx, BODY / "model.fbx")
    shutil.copy2(RIG, BODY / "model.rig")
    shutil.copy2(STOCK_RGO, BODY / "model.rgo")
    (BODY / "model.rgotemplate").write_text("<ObjectTemplate><LodDistances/></ObjectTemplate>\n", encoding="utf-8")
    colours = {"albedo.png": (150, 145, 135), "normal.png": (128, 128, 255),
               "metalness.png": (0, 0, 0), "white.png": (255, 255, 255),
               "black.png": (0, 0, 0)}
    for name, colour in colours.items():
        (BODY / name).write_bytes(png(colour))
    material_set = ET.Element("materialSet")
    item = ET.SubElement(material_set, "material", {"name": "page", "type": "shader", "source": "structure"})
    ET.SubElement(item, "param", {"name": "g_emissiveFactor", "type": "float", "value": "1"})
    slots = {}
    for slot in textures:
        if slot.startswith("normalMap"):
            file = "normal.png"
        elif slot.startswith("metalTex"):
            file = "metalness.png"
        elif slot == "maskAlpha":
            file = "white.png"
        elif "mask" in slot.lower():
            file = "black.png"
        else:
            file = "albedo.png"
        slots[slot] = file
        ET.SubElement(item, "param", {"name": slot, "type": "tex2D", "value": BODY_REL + "/" + file})
    ET.indent(material_set)
    (BODY / "model.material").write_bytes(ET.tostring(material_set, encoding="utf-8", xml_declaration=True))
    burn.write_text(revised, encoding="utf-8")
    after = file_hashes(PROJECT)
    added = set(after) - set(before)
    expected_added = {"project/source/" + BODY_REL + "/" + name
                      for name in ("model.fbx", "model.rig", "model.rgo", "model.rgotemplate",
                                   "model.material", *colours)}
    changed = {name for name in before if before[name] != after.get(name)}
    if added != expected_added or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError(f"Manual source allowlist drift: {added=} {changed=}")
    receipt = {"schema": "ccp-060-mangonel-minimal-rig-manual-source/v1",
               "status": "six_group_structure_source_prepared_not_cooked",
               "project": str(PROJECT), "project_key": KEY, "temporary_mod_id": config["mod_id"],
               "source_body": str(BODY), "source_fbx_sha256": sha(BODY / "model.fbx"),
               "source_rig_sha256": sha(BODY / "model.rig"),
               "stock_rgo_sha256": sha(BODY / "model.rgo"),
               "neutral_structure_material_name": "page", "neutral_structure_texture_slots": slots,
               "stock_rgo_and_diagnostic_material_not_for_final_pair": True,
               "no_generated_unit_or_animator": True,
               "source_export_receipt": str(EXPORT), "source_export_receipt_sha256": sha(EXPORT),
               "project_file_sha256_after": after,
               "only_added": sorted(added), "only_changed": sorted(changed),
               "create_log": str(LOG), "create_log_sha256": sha(LOG)}
    write(RECEIPT, receipt)
    return {"status": receipt["status"], "project": str(PROJECT), "receipt": str(RECEIPT)}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
