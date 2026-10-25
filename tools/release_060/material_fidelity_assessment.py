"""Assess documented vs measured native texture transforms, read-only inputs."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageOps

from common import CFG, OUT, STAGING, guard, owned, read, sha, write

READBACK = OUT / "qualification/manual-art-source-probe/readback.json"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
PREPARE = OUT / "qualification/manual-art-source-probe/prepare.json"
COOK = OUT / "qualification/manual-art-source-probe/cook.json"
DEST = OUT / "qualification/material-fidelity-assessment.json"
REPORT = OUT / "qualification/material-fidelity-assessment.md"
BURN = STAGING / "m/Mods/m60a/project/source/_default.burnproj"
GUIDE = Path(CFG["garrison_extension"]) / "guide/rig-and-animation.html"
SLOTS = ("albedoTexture", "normalMap", "metalTex", "patternTex", "skinTintLUT")


def pixels(path: Path, *, flip: bool = False) -> tuple[tuple[int, int], list[bytes]]:
    with Image.open(path) as image:
        data = image.convert("RGBA")
        if flip:
            data = ImageOps.flip(data)
        return data.size, [data.getchannel(c).tobytes() for c in "RGBA"]


def channel_matrix(left: list[bytes], right: list[bytes]) -> dict:
    count = len(left[0])
    rows = {}
    for i, source in enumerate("RGBA"):
        rows[source] = {}
        for j, compiled in enumerate("RGBA"):
            a, b = left[i], right[j]
            rows[source][compiled] = {
                "mean_absolute_error": round(sum(abs(x-y) for x, y in zip(a, b)) / count, 6),
                "maximum_absolute_error": max(abs(x-y) for x, y in zip(a, b)),
                "exact_fraction": round(sum(x == y for x, y in zip(a, b)) / count, 6),
            }
    return rows


def channel_stats(rows: list[bytes]) -> dict:
    return {c: {"minimum": min(data), "maximum": max(data), "distinct_values": len(set(data)),
                "nonzero_pixels": sum(value != 0 for value in data)}
            for c, data in zip("RGBA", rows)}


def main() -> None:
    guard()
    for path in (DEST, REPORT):
        owned(path)
    if DEST.exists():
        prior = read(DEST)
        if (prior.get("schema") != "ccp-060-archer-material-fidelity-assessment/v1"
                or prior.get("status") != "five_native_slots_and_lut_exact_other_packed_source_semantics_unqualified"
                or prior.get("readback_sha256") != sha(READBACK)):
            raise RuntimeError("Refuse to revise an unrelated or drifted assessment")
    readback, stock, prep, cook = (read(p) for p in (READBACK, STOCK, PREPARE, COOK))
    if (readback["status"] != "native_manual_source_five_slots_lut_exact_and_control_geometry_exact_other_texture_semantics_unqualified"
            or readback["prepare_receipt_sha256"] != sha(PREPARE)
            or readback["cook_receipt_sha256"] != sha(COOK)
            or prep["project_file_sha256_after"]["project/source/_default.burnproj"] != sha(BURN)
            or cook["source_bytes_preserved"] is not True):
        raise RuntimeError("Manual material readback or source evidence drifted")
    guide_text = GUIDE.read_text(encoding="utf-8")
    if ("A decoded game’s packed normal/PBR PNG is not the corresponding" not in guide_text
            or "Red: owner-colour mask; green: skin mask; blue: hair mask" not in guide_text):
        raise RuntimeError("Installed guide's source-map/packed-map contract changed")
    burn_xml = ET.parse(BURN).getroot()
    material_params = [node for node in burn_xml.iter() if node.tag.endswith("NamedParameters")
                       and any(child.tag.endswith("Name") and child.text == "Static Material" for child in node)]
    if len(material_params) != 1:
        raise RuntimeError("Expected one native Static Material parameter block")
    flip = [elem.text for elem in material_params[0].iter() if elem.tag.endswith("FlipImage")]
    if flip != ["true"]:
        raise RuntimeError("Native material texture vertical-flip rule changed")
    lod1 = next(m for m in stock["material"]["materials"] if m["name"] == "lod1")
    stock_slots = {t["name"]: t for b in lod1["blocks"] for t in b["textures"] if t["name"] != "__default"}
    if set(stock_slots) != set(SLOTS):
        raise RuntimeError("Pinned official Archer II slot set changed")
    rows = {}
    for slot in SLOTS:
        compiled = readback["textures"][slot]
        source_path = Path(compiled["source_png"])
        official_path = Path(stock_slots[slot]["projection_path"])
        native_dds = OUT / "qualification/manual-art-source-probe/decoded-textures" / (Path(compiled["resource"]).stem + ".dds")
        if sha(source_path) != compiled["source_png_sha256"] or sha(native_dds) != compiled["projection_dds_sha256"]:
            raise RuntimeError(f"Material texture source/readback drift: {slot}")
        size_source, source = pixels(source_path)
        size_official, official = pixels(official_path)
        size_flipped, flipped = pixels(source_path, flip=True)
        size_native, native = pixels(native_dds)
        if size_source != size_official or source != official or size_flipped != size_native:
            raise RuntimeError(f"Official top mip or compiled dimensions changed: {slot}")
        rows[slot] = {
            "official_dds": str(official_path), "official_dds_sha256": sha(official_path),
            "official_projection_format": stock_slots[slot]["projection_format"],
            "source_png": str(source_path), "source_png_sha256": sha(source_path),
            "source_png_equals_official_top_mip_rgba": True,
            "compiled_dds": str(native_dds), "compiled_dds_sha256": sha(native_dds),
            "compiled_projection_format": compiled["projection_format"],
            "dimensions": list(size_source),
            "source_channels": channel_stats(flipped), "compiled_channels": channel_stats(native),
            "flipped_source_to_compiled_channel_matrix": channel_matrix(flipped, native),
            "pixel_exact_after_flip": flipped == native,
            "same_channel_error": compiled["pixel_comparison"]["channels"],
        }
    def mapping(slot: str, source: str, compiled: str) -> dict:
        return rows[slot]["flipped_source_to_compiled_channel_matrix"][source][compiled]
    observed = {
        "normalMap": {
            "source_R_to_compiled_A": mapping("normalMap", "R", "A"),
            "source_G_to_compiled_G": mapping("normalMap", "G", "G"),
            "source_B_to_compiled_B": mapping("normalMap", "B", "B"),
            "compiled_R_constant_zero": rows["normalMap"]["compiled_channels"]["R"]["nonzero_pixels"] == 0,
            "source_A_variable_not_preserved_in_same_compiled_channel": rows["normalMap"]["source_channels"]["A"]["distinct_values"] > 1 and rows["normalMap"]["compiled_channels"]["A"]["distinct_values"] > 1 and mapping("normalMap", "A", "A")["mean_absolute_error"] > 10,
        },
        "metalTex": {
            "source_R_to_compiled_R": mapping("metalTex", "R", "R"),
            "compiled_GBA_constant_zero": all(rows["metalTex"]["compiled_channels"][c]["nonzero_pixels"] == 0 for c in "GBA"),
            "source_GA_variable": all(rows["metalTex"]["source_channels"][c]["distinct_values"] > 1 for c in "GA"),
        },
        "patternTex": {
            "source_R_to_compiled_R": mapping("patternTex", "R", "R"),
            "compiled_GBA_constant_zero": all(rows["patternTex"]["compiled_channels"][c]["nonzero_pixels"] == 0 for c in "GBA"),
            "source_G_variable": rows["patternTex"]["source_channels"]["G"]["distinct_values"] > 1,
        },
    }
    if (observed["normalMap"]["source_R_to_compiled_A"]["maximum_absolute_error"] > 16
            or observed["normalMap"]["source_G_to_compiled_G"]["maximum_absolute_error"] > 2
            or observed["metalTex"]["source_R_to_compiled_R"]["maximum_absolute_error"] != 0
            or observed["patternTex"]["source_R_to_compiled_R"]["maximum_absolute_error"] > 1
            or not all(observed["normalMap"][key] for key in ("compiled_R_constant_zero", "source_A_variable_not_preserved_in_same_compiled_channel"))
            or not all(observed["metalTex"][key] for key in ("compiled_GBA_constant_zero", "source_GA_variable"))
            or not all(observed["patternTex"][key] for key in ("compiled_GBA_constant_zero", "source_G_variable"))):
        raise RuntimeError(f"Observed native channel transform changed: {observed}")
    status = "five_native_slots_and_lut_exact_other_packed_source_semantics_unqualified"
    assessment = {
        "schema": "ccp-060-archer-material-fidelity-assessment/v1", "status": status,
        "readback": str(READBACK), "readback_sha256": sha(READBACK),
        "stock_manifest": str(STOCK), "stock_manifest_sha256": sha(STOCK),
        "installed_guide": str(GUIDE), "installed_guide_sha256": sha(GUIDE),
        "manual_burn_project": str(BURN), "manual_burn_project_sha256": sha(BURN),
        "documented_contract": {
            "source_maps": "Guide rig-and-animation.html: normal is tangent-space RGB, roughness and metalness are grayscale, pattern RGB are owner/skin/hair masks.",
            "packed_warning": "Guide explicitly says decoded game packed normal/PBR PNG is not corresponding source map; Essence packs channels during cook.",
            "vertical_flip": "Manual native project's material TextureBurnParameters has FlipImage=true; compiled LUT pixels match flipped source exactly.",
            "exact_native_pack_mapping_for_official_normal_metal_pattern": "not documented by installed source reviewed; pairwise matrices below are observations, not semantic mapping proof",
        },
        "slots": rows,
        "observed_native_channel_transform_for_this_burn": observed,
        "fidelity_conclusion": {
            "five_slot_presence_and_private_resolution": True,
            "official_skin_lut_native_rgba8_20x3_pixel_exact_after_flip": rows["skinTintLUT"]["pixel_exact_after_flip"],
            "albedo_bc1_small_quantization_observed": True,
            "decoded_official_packed_normal_metal_pattern_reused_as_source": True,
            "guide_disallows_treating_those_as_source_maps": True,
            "normal_metal_pattern_appearance_matches_stock": "unproved and suspect; the source/compiled channel differences cannot be waved away as expected without a documented inverse pack transform or native render comparison",
            "native_archer_runtime_render": "not tested",
        },
    }
    write(DEST, assessment)
    lines = [
        "# Archer material fidelity assessment",
        "",
        "The manual native burn preserves all five named material slots, resolves their private RRtex resources, and compiles the Chinese skin LUT at 20×3 RGBA8. Its LUT pixels equal the official donor top mip after the burn project's declared vertical flip. The near-control RRGeom remains byte-identical, so material preparation did not change that control's geometry or weights.",
        "",
        "The installed Garrison guide explicitly distinguishes **authoring source maps** from decoded game packed normal/PBR textures: native Essence packing changes channels at cook. It defines source pattern RGB as owner-colour, skin and hair masks. The probe deliberately fed decoded official packed normal, metal and pattern projections back as source PNGs. That is a valid test of native five-slot acceptance, but the guide does not qualify it as appearance-preserving source preparation.",
        "",
        "| Slot | Official/compiled format | Measured flipped-source versus compiled result | Interpretation |",
        "|---|---|---|---|",
    ]
    descriptions = {
        "albedoTexture": "BC1 quantization only within 3 levels per RGB channel; visual comparison remains pending.",
        "normalMap": "Native packed channels differ materially; authoring-source semantics were violated, so a normal appearance claim is unsupported.",
        "metalTex": "Native packed channels differ materially; metal/PBR appearance is unsupported.",
        "patternTex": "R channel is close, but G differs materially; dynamic owner/skin presentation remains unsupported.",
        "skinTintLUT": "Exact 20×3 RGBA8 pixels after the declared flip; LUT source and compiled data are qualified at this gate.",
    }
    for slot in SLOTS:
        row = rows[slot]
        errors = row["same_channel_error"]
        diffs = ", ".join(f"{c} MAE {errors[c]['mean_absolute_error']:.3f}, max {errors[c]['maximum_absolute_error']}" for c in "RGBA")
        lines.append(f"| {slot} | {row['official_projection_format']} / {row['compiled_projection_format']} | {diffs} | {descriptions[slot]} |")
    lines += [
        "",
        "This burn's measured channel routing is specific: in `normalMap`, flipped source R appears in compiled A (quantized), G stays in G, B remains 255, compiled R is zero, and the varying source A is not preserved in compiled A. In `metalTex`, source R survives exactly in compiled R while compiled G/B/A are zero despite variable source G/A. In `patternTex`, source R survives within one level in compiled R while compiled G/B/A are zero despite a variable source G. These are observed mappings from decoded packed donor projections **re-fed as source**, not a documented general inverse packer or proof that the resulting shader appearance matches stock.",
        "",
        "The JSON records each source/compiled channel's range and a complete 4×4 pairwise error/exactness matrix with maxima. The next appearance-valid route must use legitimate normal/roughness/metalness/pattern **source** maps or a documented inverse packing conversion, then compare compiled resources and a native render before integration.",
        "",
        "Three native Archer LODs remain a separate geometry/material gate; the current control duplicates LOD1 into LOD2/3. No Garrison Build Unit or runtime proof follows from this manual native material burn.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": status, "receipt": str(DEST), "report": str(REPORT)}, indent=2))


if __name__ == "__main__":
    main()
