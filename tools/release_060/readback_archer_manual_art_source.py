"""Verify five native material slots, LUT pixels, and unchanged control geometry."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps

from common import ARCH, CFG, OUT, STAGING, guard, owned, read, sha, write

sys.path.insert(0, CFG["garrison_extension"])
from garrison_shared import model_variants as mv, rrtex_decoder  # noqa: E402

DEST = OUT / "qualification/manual-art-source-probe"
RECEIPT = DEST / "readback.json"
COOK = DEST / "cook.json"
PREPARE = DEST / "prepare.json"
ARCHIVE = STAGING / "m/Mods/m60a/dist/manual-cook/output/extension/m60a/m60a.sga"
READBACK = DEST / "readback"
TEXTURES = DEST / "decoded-textures"
BODY = READBACK / "art/scenario/garrison/m60a/body"
SOURCE_BODY = STAGING / "m/Mods/m60a/project/source/art/scenario/garrison/m60a/body"
CONTROL_GEOM = OUT / "qualification/archer-matched-control-readback/body-rrgeom.rrgeom"
BASE = "art/scenario/garrison/m60a/body/"
EXPECTED_NAMES = {"model.rgm", "model.rgo", "model.rrgeom", "model.rrmaterial",
                  "stock_albedo.rrtex", "stock_skin_lut.rrtex"}
SOURCE_PNG = {"albedoTexture": "stock_albedo.png", "normalMap": "stock_normal.png",
              "metalTex": "stock_metal.png", "patternTex": "stock_pattern.png",
              "skinTintLUT": "stock_skin_lut.png"}


def byte_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def colour_delta(source: Image.Image, compiled: Image.Image) -> dict:
    original = ImageOps.flip(source.convert("RGBA"))
    burned = compiled.convert("RGBA")
    if original.size != burned.size:
        raise RuntimeError(f"Native texture dimension drift: {original.size} != {burned.size}")
    count = original.width * original.height
    by_channel = {}
    for channel in "RGBA":
        left = original.getchannel(channel).tobytes()
        right = burned.getchannel(channel).tobytes()
        by_channel[channel] = {
            "mean_absolute_error": round(sum(abs(a-b) for a, b in zip(left, right)) / count, 6),
            "maximum_absolute_error": max(abs(a-b) for a, b in zip(left, right)),
        }
    return {"exact_after_native_vertical_flip": original.tobytes() == burned.tobytes(),
            "channels": by_channel, "source_flipped_rgba_sha256": byte_hash(original.tobytes()),
            "compiled_rgba_sha256": byte_hash(burned.tobytes())}


def main() -> None:
    guard()
    for path in (DEST, RECEIPT, TEXTURES):
        owned(path)
    if RECEIPT.exists() or TEXTURES.exists():
        raise FileExistsError("Preserve prior manual readback attempt")
    cook, prep = read(COOK), read(PREPARE)
    if (cook["status"] != "native_cook_completed_pending_readback"
            or cook["prepare_receipt_sha256"] != sha(PREPARE)
            or len(cook.get("archives", [])) != 1
            or Path(cook["archives"][0]["path"]) != ARCHIVE
            or cook["archives"][0]["sha256"] != sha(ARCHIVE)
            or not cook["source_bytes_preserved"]):
        raise RuntimeError("Native manual cook/archive input changed")
    proc = subprocess.run([str(ARCH), "list", "--verify", str(ARCHIVE)],
                          capture_output=True, text=True, encoding="utf-8", timeout=120)
    if proc.returncode:
        raise RuntimeError(f"Native archive verification failed: {proc.stderr[-1000:]}")
    listing = json.loads(proc.stdout)
    members = {row["path"] for row in listing["members"]}
    if not listing["archive"]["verification"]["verified"] or len(members) != 13:
        raise RuntimeError("Manual native archive CRC/SHA or member count invalid")
    if not {BASE + name for name in EXPECTED_NAMES}.issubset(members):
        raise RuntimeError("Compiled native model/material/LUT resources missing")
    if {p.name for p in BODY.glob("*") if p.is_file()} != {x.removeprefix(BASE) for x in members if x.startswith(BASE)}:
        raise RuntimeError("Archive and physical readback model resources differ")
    compiled = mv.material_slots((BODY / "model.rrmaterial").read_bytes())
    slots = {k: v.replace("\\", "/") for k, v in compiled["textures"].items() if k != "__default"}
    if set(slots) != set(SOURCE_PNG):
        raise RuntimeError(f"Five-slot native material contract differs: {slots}")
    if compiled["parameters"].get("g_emissiveFactor", {}).get("values") not in (["0"], ["0.0"]):
        raise RuntimeError("Native emissive parameter differs")
    if sha(BODY / "model.rrgeom") != sha(CONTROL_GEOM):
        raise RuntimeError("Manual material cook changed compiled control geometry/weights")
    TEXTURES.mkdir(parents=True)
    texture_rows = {}
    for slot, member in slots.items():
        if member not in members or not member.startswith(BASE):
            raise RuntimeError(f"Native material dependency unresolved: {slot} -> {member}")
        rrtex = BODY / Path(member).name
        if not rrtex.is_file():
            raise RuntimeError(f"Readback texture file missing: {slot}")
        decoded = rrtex_decoder.decode_rrtex(rrtex, TEXTURES / (rrtex.stem + ".dds"), validate_stream=True)
        source = SOURCE_BODY / SOURCE_PNG[slot]
        with Image.open(source) as source_image, Image.open(decoded["projection"]["path"]) as cooked_image:
            diff = colour_delta(source_image, cooked_image)
        texture_rows[slot] = {
            "resource": member, "rrtex_sha256": sha(rrtex),
            "source_png": str(source), "source_png_sha256": sha(source),
            "width": decoded["width"], "height": decoded["height"],
            "projection_format": decoded["projection"]["format"],
            "projection_dds_sha256": decoded["projection"]["sha256"],
            "mip_count": decoded["mip_count"], "native_stream_validation": decoded["stream_validation"],
            "pixel_comparison": diff,
        }
    lut = texture_rows["skinTintLUT"]
    if (lut["width"] != 20 or lut["height"] != 3
            or lut["projection_format"] != "RGBA8_UNORM"
            or not lut["pixel_comparison"]["exact_after_native_vertical_flip"]):
        raise RuntimeError("Compiled native skin tint LUT dimensions/format/pixels differ")
    receipt = {
        "schema": "ccp-060-manual-archer-native-readback/v1",
        "status": "native_manual_source_five_slots_lut_exact_and_control_geometry_exact_other_texture_semantics_unqualified",
        "prepare_receipt": str(PREPARE), "prepare_receipt_sha256": sha(PREPARE),
        "cook_receipt": str(COOK), "cook_receipt_sha256": sha(COOK),
        "archive": str(ARCHIVE), "archive_sha256": sha(ARCHIVE),
        "archive_crc_sha1_verified": True, "archive_member_allowlist": sorted(members),
        "material": str(BODY / "model.rrmaterial"),
        "material_sha256": sha(BODY / "model.rrmaterial"),
        "material_slots": slots, "material_parameters": compiled["parameters"],
        "all_five_texture_references_private_and_resolved": True,
        "textures": texture_rows,
        "lut_rgba8_20x3_source_pixels_exact_after_native_vertical_flip": True,
        "compiled_rrgeom": str(BODY / "model.rrgeom"),
        "compiled_rrgeom_sha256": sha(BODY / "model.rrgeom"),
        "normal_garrison_cooked_control_rrgeom": str(CONTROL_GEOM),
        "normal_garrison_cooked_control_rrgeom_sha256": sha(CONTROL_GEOM),
        "compiled_topology_weights_byte_identical_to_control": True,
        "control_far_lods_are_cloned_and_not_stock_compliant": True,
        "native_burn_is_distinct_from_garrison_build_unit": True,
        "full_stock_shader_and_visual_material_fidelity_unqualified": True,
        "no_active_gameplay_or_generated_prototype_actor_integrated": True,
        "client_import_and_native_match_unproved": True,
    }
    write(RECEIPT, receipt)
    print(json.dumps({"status": receipt["status"], "archive_sha256": sha(ARCHIVE),
                      "rrgeom_control_exact": True, "lut_exact_after_flip": True,
                      "receipt": str(RECEIPT)}, indent=2))


if __name__ == "__main__":
    main()
