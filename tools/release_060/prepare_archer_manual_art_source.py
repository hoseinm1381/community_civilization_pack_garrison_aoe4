"""Prepare an isolated, manually maintained native art source; no unit-add or cook.

The four art burn rules are copied from a verified successful unit source's
_default.burnproj into a fresh *blank* scaffold, with only their include path
changed. This project never registers a Garrison Build Unit action or actor.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from common import OUT, STAGING, guard, owned, read, sha, write

KEY = "m60a"
PROJECT = STAGING / "m/Mods/m60a"
SCAFFOLD = PROJECT / "project/source"
BODY_REL = "art/scenario/garrison/m60a/body"
BODY = SCAFFOLD / BODY_REL
RECEIPT = OUT / "qualification/manual-art-source-probe/prepare.json"
CONTROL = STAGING / "u/Mods/u60a/project/source"
CONTROL_BODY_REL = "art/scenario/garrison/u60a/units/u60a_archer_control/body"
CONTROL_BODY = CONTROL / CONTROL_BODY_REL
PNG_BODY = STAGING / "p/Mods/p60a/project/source/art/scenario/garrison/p60a/units/p60a_m/body"
PIXEL_RECEIPT = OUT / "qualification/material-local-source-probe/outcome.json"
CONTROL_COOK = OUT / "qualification/archer-matched-control-cook.json"
SOURCE_HASHES = {
    "model.fbx": "8d6bea5bbb999b4170cbfb5508b71d21ba8aabf2e729345c3624d5ca98e6e6eb",
    "model.rig": "ab0f07170392a78e81c41abc5ddacd3fd18dd0f67ce018f42cb0c0829e02a6f9",
    "model.rgo": "bb41b0bf48275e2b625767eadba2cafbad864b8ab76289cb7942fe8e7813290b",
    "model.rgotemplate": "de4ef1e0f56292ddb8f66ec799e45241be500d01f19657e2dea6d64a36891dc3",
}
PNGS = {
    "albedoTexture": ("stock_albedo.png", "f231747e68cd39bd1c6edcc7ecfc074f79013e4644bf0debb98d46650f0dacdc"),
    "normalMap": ("stock_normal.png", "a4cd30ac95408053bb7e9e24a7acc90c9bf560402465da371a3d6a68c78a80b6"),
    "metalTex": ("stock_metal.png", "c20611a6642dda2b8ff693c30c011c0431b5f9fd338fa6f13e03522447fb8e8f"),
    "patternTex": ("stock_pattern.png", "828a19f33c783faf6d9f58888b2760939968cd5ca9deef661716c3b24a327675"),
    "skinTintLUT": ("stock_skin_lut.png", "8d9722887ccf297b7ebc0ab9b954f4bf5179ce51e23ee5cb2db7fc9f056e29aa"),
}
RULE_BURNERS = ["RR Material Burner", "RGM", "RRGeometry", "RGO"]


def files_under(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main() -> None:
    guard()
    for path in (PROJECT, BODY, RECEIPT):
        owned(path)
    if RECEIPT.exists() or BODY.exists():
        raise FileExistsError("Preserve any earlier manual art-source preparation")
    config = read(PROJECT / "mod-project.json")
    if (config.get("key") != KEY or config.get("mod_id") != "8863ce05-88cd-4432-8567-2dd9f5bfa342"
            or config.get("game_mode", {}).get("enabled") or config.get("game_mode", {}).get("live_reload")
            or config.get("animated_units") or config.get("assets") or config.get("cooks")):
        raise RuntimeError("Fresh blank scaffold identity or empty-source contract changed")
    if read(CONTROL_COOK)["status"] != "isolated_cook_completed_pending_archive_readback":
        raise RuntimeError("Pinned control native cook receipt changed")
    pixels = read(PIXEL_RECEIPT)["five_converted_textures"]
    if set(pixels) != set(PNGS) or not all(row["exact_top_mip"] for row in pixels.values()):
        raise RuntimeError("Prior pixel-verified PNG source receipt changed")
    for name, expected in SOURCE_HASHES.items():
        if sha(CONTROL_BODY / name) != expected:
            raise RuntimeError(f"Pinned control source changed: {name}")
    for slot, (name, expected) in PNGS.items():
        source = PNG_BODY / name
        if sha(source) != expected:
            raise RuntimeError(f"Pinned pixel source changed: {slot}")
        image = Image.open(source)
        image.load()
        if (list(image.size) != pixels[slot]["dimensions"] or image.mode != "RGBA"
                or hashlib.sha256(image.tobytes()).hexdigest() != pixels[slot]["rgba_pixel_sha256"]):
            raise RuntimeError(f"PNG top-mip pixel digest changed: {slot}")
    before = files_under(PROJECT)
    burn = SCAFFOLD / "_default.burnproj"
    original = burn.read_text(encoding="utf-8")
    if ("</Rules>" not in original or "art\\scenario\\garrison\\m60a" in original
            or "<Burner>RR Material Burner</Burner>" in original):
        raise RuntimeError("Blank scaffold already contains art rules")
    qualified = (CONTROL / "_default.burnproj").read_text(encoding="utf-8")
    blocks = re.findall(r"<BurnRule>.*?</BurnRule>", qualified, re.DOTALL)
    old_native = CONTROL_BODY_REL.replace("/", "\\")
    new_native = BODY_REL.replace("/", "\\")
    selected = [block for block in blocks if old_native in block]
    if (len(selected) != 4 or [re.search(r"<Burner>(.*?)</Burner>", block).group(1)
                               for block in selected] != RULE_BURNERS):
        raise RuntimeError("Qualified native art burn rule set changed")
    inserted = "\n".join(block.replace(old_native, new_native) for block in selected)
    if old_native in inserted or inserted.count(new_native) != 5:
        raise RuntimeError("Manual native burn rule include-path rewrite failed")
    revised = original.replace("</Rules>", inserted + "\n\t</Rules>", 1)
    ET.fromstring(revised)
    BODY.mkdir(parents=True)
    for name in SOURCE_HASHES:
        shutil.copy2(CONTROL_BODY / name, BODY / name)
    for name, _ in PNGS.values():
        shutil.copy2(PNG_BODY / name, BODY / name)
    original_material = ET.parse(CONTROL_BODY / "model.material").getroot().find("material")
    if original_material is None or original_material.get("source") != "unit":
        raise RuntimeError("Qualified unit material source identity changed")
    material_name = original_material.get("name")
    root = ET.Element("materialSet")
    material = ET.SubElement(root, "material", {"name": material_name, "type": "shader", "source": "unit"})
    for slot, (name, _) in PNGS.items():
        ET.SubElement(material, "param", {"name": slot, "type": "tex2D", "value": BODY_REL + "/" + name})
    ET.SubElement(material, "param", {"name": "g_emissiveFactor", "type": "Float", "value": "0.0"})
    ET.indent(root)
    (BODY / "model.material").write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    burn.write_text(revised, encoding="utf-8")
    after = files_under(PROJECT)
    added = set(after) - set(before)
    expected_added = {BODY_REL + "/" + name for name in [*SOURCE_HASHES, *(name for name, _ in PNGS.values()), "model.material"]}
    # files_under(PROJECT) includes project/source in each relative key.
    expected_added = {"project/source/" + item for item in expected_added}
    changed = {name for name in before if before[name] != after.get(name)}
    if added != expected_added or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError(f"Manual source allowlist mismatch: added={added}, changed={changed}")
    receipt = {
        "schema": "ccp-060-manual-archer-art-source/v1",
        "status": "manual_source_prepared_not_cooked",
        "project": str(PROJECT), "project_key": KEY, "temporary_mod_id": config["mod_id"],
        "project_file": str(PROJECT / "project/m60a.aoe4mod"),
        "source_body": str(BODY), "source_only_no_unit_add": True,
        "no_generated_unit_entries_or_actor": True, "game_mode_and_live_reload_off": True,
        "qualified_control_body": str(CONTROL_BODY),
        "qualified_burn_rules_source": str(CONTROL / "_default.burnproj"),
        "qualified_burn_rule_burners": RULE_BURNERS,
        "pixel_receipt": str(PIXEL_RECEIPT), "pixel_receipt_sha256": sha(PIXEL_RECEIPT),
        "material_name": material_name,
        "material_slots": {slot: BODY_REL + "/" + name for slot, (name, _) in PNGS.items()},
        "scaffold_file_sha256_before": before,
        "project_file_sha256_after": after,
        "only_added": sorted(added), "only_changed": sorted(changed),
        "next_gate": "Under shared native byte lock invoke documented Essence --build_mod once; stop at first native failure; no Garrison Build Unit claim.",
    }
    write(RECEIPT, receipt)
    print(json.dumps({"status": receipt["status"], "project": str(PROJECT), "receipt": str(RECEIPT),
                      "only_added": sorted(added), "only_changed": sorted(changed)}, indent=2))


if __name__ == "__main__":
    main()
