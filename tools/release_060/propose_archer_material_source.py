"""Draft a faithful stock-slot material source for review; do not stage/cook it."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from common import OUT, guard, owned, read, sha, write

DEST = OUT / "qualification/material-route-probe"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
PATTERN_PROBE = DEST / "receipt.json"
MASK = DEST / "stock-pattern-conversion.json"
VALIDATED = DEST / "stock-pattern-validation.json"
PROPOSAL = DEST / "proposed-control-stock-lod1.model.material"
RECEIPT = DEST / "proposal.json"


def main() -> None:
    guard()
    for path in (PROPOSAL, RECEIPT):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve previous material proposal: {path}")
    stock, pattern, mask, validated = (read(p) for p in (STOCK, PATTERN_PROBE, MASK, VALIDATED))
    if pattern["status"] != "pattern_source_recognized_skin_lut_absent" \
            or mask["status"] != "verified_current_stock_mask_top_mip_png_pixel_exact" \
            or validated["status"] != "source_validated_not_cooked":
        raise RuntimeError("Material route inputs are not in the expected state")
    material_name, baseline = next(iter(pattern["baseline_params"].items()))
    stock_lods = {}
    for item in stock["material"]["materials"]:
        stock_lods[item["name"]] = {
            "textures": {t["name"]: t["logical_path"] for block in item["blocks"]
                         for t in block["textures"] if t["name"] != "__default"},
            "parameters": {p["name"]: {"type": p["type"], "values": p["values"]}
                           for p in item["parameters"]},
        }
    if set(stock_lods) != {"lod1", "lod2", "lod3"}:
        raise RuntimeError("Expected three decoded stock material LODs")
    common = {slot for slot in ("albedoTexture", "metalTex", "patternTex", "skinTintLUT")
              if len({stock_lods[lod]["textures"].get(slot) for lod in stock_lods}) == 1}
    if common != {"albedoTexture", "metalTex", "patternTex", "skinTintLUT"}:
        raise RuntimeError("Expected common stock texture slots drifted")
    root = ET.Element("materialSet")
    material = ET.SubElement(root, "material", {"name": material_name, "type": "shader", "source": "unit"})
    # Only this control's single LOD1 material name is known. Stock LOD2/3 use
    # different normal maps and need their own geometry/material name contract.
    for name, value in stock_lods["lod1"]["textures"].items():
        ET.SubElement(material, "param", {"name": name, "type": "tex2D", "value": value})
    emissive = stock_lods["lod1"]["parameters"].get("g_emissiveFactor")
    if emissive:
        ET.SubElement(material, "param", {"name": "g_emissiveFactor", "type": emissive["type"],
                                          "value": str(emissive["values"][0])})
    ET.indent(root)
    PROPOSAL.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    parsed = ET.parse(PROPOSAL).getroot()
    actual = {p.get("name"): p.get("value") for p in parsed.find("material").findall("param")}
    for name, value in stock_lods["lod1"]["textures"].items():
        if actual.get(name) != value:
            raise RuntimeError(f"Proposal slot mismatch: {name}")
    write(RECEIPT, {
        "schema": "ccp-060-archer-material-source-proposal/v1",
        "status": "review_only_not_staged_not_cooked",
        "stock_manifest": str(STOCK), "stock_manifest_sha256": sha(STOCK),
        "source_only_pattern_probe": str(PATTERN_PROBE), "source_only_pattern_probe_sha256": sha(PATTERN_PROBE),
        "exact_stock_pattern_conversion": str(MASK), "exact_stock_pattern_conversion_sha256": sha(MASK),
        "stock_pattern_validator": str(VALIDATED), "stock_pattern_validator_sha256": sha(VALIDATED),
        "proposed_material": str(PROPOSAL), "proposed_material_sha256": sha(PROPOSAL),
        "control_generated_material_name": material_name,
        "control_generated_baseline_params": baseline,
        "stock_lod_material_slots": stock_lods,
        "stock_common_texture_slots": sorted(common),
        "supported_route": "Build Unit source action textures includes pattern; installed unit-validate accepted exact converted stock pattern PNG; generated source emitted patternTex. This route does not expose skinTintLUT.",
        "unsupported_candidate": "A native .material source with the exact stock lod1 texture paths and generated control material name is drafted, but Garrison exposes no supported unit-add option for skinTintLUT or material source replacement. Do not stage/cook it without an isolated native source experiment and readback.",
        "far_lod_material_gap": "Stock lod1/lod2/lod3 normalMap paths differ. Current single-material control and three-LOD export recipe collapse them; separate name/material contracts and native readback are required.",
        "uv_gap": "Stock mask is exact for donor UVs only. New clothing UV islands must receive authored albedo and RGB pattern coverage before material acceptance.",
        "release_gate": "Neither control material nor proposal qualifies dynamic player colour or Chinese skin tint in game; no gameplay model binding or package use is permitted.",
    })
    print(json.dumps({"status": "review_only_not_staged_not_cooked", "proposal": str(PROPOSAL),
                      "receipt": str(RECEIPT), "stock_slots": list(stock_lods["lod1"]["textures"])}, indent=2))


if __name__ == "__main__":
    main()
