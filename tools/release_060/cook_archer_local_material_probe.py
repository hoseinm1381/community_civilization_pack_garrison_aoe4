"""One native cook with five verified stock texture top mips as local PNG sources.

The resulting model is diagnostic only. The stock normal/metal DDS images are
compiled resources, not proven equivalent to Essence authoring source maps.
"""
from __future__ import annotations

import hashlib
import json
import msvcrt
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from common import CFG, CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

DEST = OUT / "qualification/material-local-source-probe"
RECEIPT = DEST / "cook.json"
LIBRARY = STAGING / "p"
PROJECT = LIBRARY / "Mods/p60a"
PROJECT_FILE = PROJECT / "mod-project.json"
UNIT = "p60a_m"
BODY = PROJECT / f"project/source/art/scenario/garrison/p60a/units/{UNIT}/body"
MATERIAL = BODY / "model.material"
SOURCE = OUT / "qualification/archer-matched-control-export.json"
VALIDATED = OUT / "qualification/archer-matched-control-validate.json"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
PRIOR_FAILURE = OUT / "qualification/material-native-probe/outcome.json"
PRIOR_COOK = OUT / "qualification/material-native-probe/cook.json"
EDITOR = Path(CFG["art_editor"])
SLOT_FILES = {"albedoTexture": "stock_albedo.png", "normalMap": "stock_normal.png",
              "metalTex": "stock_metal.png", "patternTex": "stock_pattern.png",
              "skinTintLUT": "stock_skin_lut.png"}


def command(receipt: dict, label: str, args: list[object], timeout: int) -> bool:
    log = owned(DEST / "logs" / (label + ".log"))
    if log.exists():
        raise FileExistsError(log)
    proc = subprocess.run([str(x) for x in args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("COMMAND: " + " ".join(str(x) for x in args) + "\nEXIT: " + str(proc.returncode)
                   + "\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr,
                   encoding="utf-8")
    receipt["steps"].append({"name": label, "exit_code": proc.returncode,
                             "log": str(log), "log_sha256": sha(log)})
    write(RECEIPT, receipt)
    return proc.returncode == 0


def material(path: Path) -> tuple[str, dict[str, str]]:
    root = ET.parse(path).getroot()
    materials = root.findall("material")
    if len(materials) != 1 or materials[0].get("source") != "unit":
        raise RuntimeError(f"Expected one unit material: {path}")
    return materials[0].get("name"), {p.get("name"): p.get("value")
                                      for p in materials[0].findall("param")}


def pixel_digest(image: Image.Image) -> str:
    return hashlib.sha256(image.tobytes()).hexdigest()


def prepare_textures(receipt: dict, stock: dict, prior: dict) -> dict[str, str]:
    lod1 = next(x for x in stock["material"]["materials"] if x["name"] == "lod1")
    slots = {t["name"]: t for block in lod1["blocks"] for t in block["textures"]
             if t["name"] != "__default"}
    if set(slots) != set(SLOT_FILES):
        raise RuntimeError("Stock LOD1 texture slot set changed")
    results = {}
    for slot, filename in SLOT_FILES.items():
        source = slots[slot]
        official = prior["stock_texture_refs"][slot]
        if source["logical_path"] != official["logical_path"]:
            raise RuntimeError(f"Prior official source reference changed: {slot}")
        checked_rrtex = OUT / "qualification/material-native-probe/stock-refs" / (slot + ".rrtex")
        if sha(checked_rrtex) != official["sha256"]:
            raise RuntimeError(f"Prior official RRtex bytes changed: {slot}")
        dds = Path(source["projection_path"])
        image = Image.open(dds)
        image.load()
        if image.mode != "RGBA":
            raise RuntimeError(f"Expected RGBA stock projection for {slot}: {image.mode}")
        png = BODY / filename
        if png.exists():
            raise FileExistsError(png)
        image.save(png, format="PNG", optimize=False)
        reopened = Image.open(png)
        reopened.load()
        if reopened.mode != "RGBA" or reopened.size != image.size or reopened.tobytes() != image.tobytes():
            raise RuntimeError(f"Lossless top-mip PNG conversion failed: {slot}")
        results[slot] = {"stock_logical_rrtex": source["logical_path"],
                         "stock_official_rrtex_sha256": official["sha256"],
                         "decoder_dds": str(dds), "decoder_dds_sha256": sha(dds),
                         "png": str(png), "png_sha256": sha(png),
                         "rgba_pixel_sha256": pixel_digest(image), "dimensions": list(image.size),
                         "channel_extrema": image.getextrema(),
                         "dds_to_png_top_mip_rgba_exact": True}
    receipt["texture_sources"] = results
    write(RECEIPT, receipt)
    return {slot: f"art/scenario/garrison/p60a/units/{UNIT}/body/{filename}"
            for slot, filename in SLOT_FILES.items()}


def main() -> None:
    guard()
    for path in (DEST, PROJECT):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier local-texture candidate: {path}")
    if not EDITOR.is_file() or not NATIVE_LOCK.is_file():
        raise FileNotFoundError("Garrison art editor or shared native byte lock missing")
    source, validated, stock, prior_failure, prior_cook = (
        read(p) for p in (SOURCE, VALIDATED, STOCK, PRIOR_FAILURE, PRIOR_COOK))
    if (validated["status"] != "passed" or validated["source_receipt_sha256"] != sha(SOURCE)
            or prior_failure["status"] != "normal_native_cook_rejected_stock_rrtex_source_reference"
            or prior_cook["material_source_survived_cook"] is not True):
        raise RuntimeError("Pinned earlier source/failure evidence changed")
    source_dir = Path(source["folder"])
    for name, record in source["files"].items():
        if sha(source_dir / name) != record["sha256"]:
            raise RuntimeError(f"Pinned control source drift: {name}")
    receipt = {"schema": "ccp-060-archer-local-texture-native-probe/v1",
               "status": "prepared_pending_byte_lock", "project": str(PROJECT),
               "source_export_sha256": sha(SOURCE), "stock_manifest_sha256": sha(STOCK),
               "previous_failure_outcome_sha256": sha(PRIOR_FAILURE),
               "previous_failure_cook_sha256": sha(PRIOR_COOK),
               "generated_spearman_actor_never_integrated": True,
               "stock_compiled_normal_metal_images_are_not_proven_authoring_source_semantics": True,
               "lock_protocol": "msvcrt.LK_NBLCK first byte; tools/castle_next/cook.py parity",
               "steps": []}
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError("Shared native byte lock busy; no mutation") from error
        try:
            receipt["status"] = "byte_lock_held"
            write(RECEIPT, receipt)
            if not command(receipt, "create", [CORE, "mod-project", "create", "--library", LIBRARY,
                                                "--name", "p60a"], 120):
                raise RuntimeError("Isolated project creation failed")
            project = read(PROJECT_FILE)
            if project.get("key") != "p60a" or project.get("game_mode", {}).get("enabled"):
                raise RuntimeError("Unexpected isolated project identity")
            receipt["temporary_mod_id"] = project["mod_id"]
            write(RECEIPT, receipt)
            if not command(receipt, "unit-add", [CORE, "mod-project", "unit-add",
                                                  "--project", PROJECT, "--source", source_dir,
                                                  "--name", UNIT], 600):
                raise RuntimeError("Isolated unit-add failed")
            if not MATERIAL.is_file():
                raise FileNotFoundError(MATERIAL)
            name, baseline = material(MATERIAL)
            if name != read(source_dir / "action.json")["material_name"]:
                # Preserve the exact generated material name, including FBX association.
                raise RuntimeError("Generated material name differs from source action")
            if set(baseline) != {"albedoTexture", "normalMap", "metalTex", "roughnessTex"}:
                raise RuntimeError("Generated baseline material changed")
            receipt["generated_material_sha256_before_edit"] = sha(MATERIAL)
            receipt["generated_material_name"] = name
            receipt["generated_baseline_slots"] = baseline
            local = prepare_textures(receipt, stock, prior_cook)
            root = ET.Element("materialSet")
            mat = ET.SubElement(root, "material", {"name": name, "type": "shader", "source": "unit"})
            for slot, path in local.items():
                ET.SubElement(mat, "param", {"name": slot, "type": "tex2D", "value": path})
            ET.SubElement(mat, "param", {"name": "g_emissiveFactor", "type": "Float", "value": "0.0"})
            ET.indent(root)
            candidate = owned(DEST / "local-five-slot.model.material")
            candidate.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
            if material(candidate) != (name, {**local, "g_emissiveFactor": "0.0"}):
                raise RuntimeError("Candidate material slot synthesis failed")
            receipt["candidate_material_source"] = str(candidate)
            receipt["candidate_material_sha256"] = sha(candidate)
            shutil.copy2(candidate, MATERIAL)
            if sha(MATERIAL) != sha(candidate):
                raise RuntimeError("Generated material replacement bytes changed")
            receipt["material_source_sha256_before_cook"] = sha(MATERIAL)
            receipt["intended_local_texture_slots"] = local
            receipt["status"] = "local_five_slot_source_staged_before_cook"
            write(RECEIPT, receipt)
            ok = command(receipt, "cook", [CORE, "mod-project", "cook", "--project", PROJECT,
                                           "--editor", EDITOR, "--timeout", "1200"], 1300)
            receipt["material_source_sha256_after_cook"] = sha(MATERIAL) if MATERIAL.is_file() else None
            receipt["material_source_survived_cook"] = (
                receipt["material_source_sha256_after_cook"] == receipt["material_source_sha256_before_cook"])
            if not ok:
                receipt["status"] = "native_cook_rejected_local_source_preserved"
            elif not receipt["material_source_survived_cook"]:
                receipt["status"] = "cook_regenerated_material_source_unavailable"
            else:
                cooks = read(PROJECT_FILE).get("cooks", [])
                if len(cooks) != 1:
                    raise RuntimeError("Unexpected isolated cook count")
                receipt["cook_record"] = cooks[0]
                receipt["archive_sha256"] = sha(cooks[0]["archive"])
                if receipt["archive_sha256"] != cooks[0]["sha256"]:
                    raise RuntimeError("Cook archive hash mismatch")
                receipt["status"] = "cook_succeeded_local_source_preserved_pending_readback"
            write(RECEIPT, receipt)
            print(json.dumps({"status": receipt["status"], "receipt": str(RECEIPT),
                              "source_survived": receipt["material_source_survived_cook"]}, indent=2))
        except BaseException as error:
            receipt["status"] = "failed_under_byte_lock"
            receipt["error"] = f"{type(error).__name__}: {error}"
            if MATERIAL.is_file():
                receipt["material_source_sha256_at_failure"] = sha(MATERIAL)
            write(RECEIPT, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
