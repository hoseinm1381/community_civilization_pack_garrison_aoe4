"""Bounded diagnostic source contract for the exact 24-group riderless worker elephant."""
from __future__ import annotations

import argparse
import json
import msvcrt
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, CFG, CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write
from prepare_mangonel_manual_geometry import png, file_hashes
import decode_archer_three_lod_manual_uvfix as private_index

BASE = OUT / "qualification/remaining_roster/tug_worker"
V8 = BASE / "v8-tug24-native-names/export.json"
V9 = BASE / "v9-native-names-snapshot/snapshot.json"
KEY = "t24g"
PROJECT = STAGING / "ag/tug-worker-v8/Mods" / KEY
BODY_REL = f"art/scenario/garrison/{KEY}/body"
BODY = PROJECT / "project/source" / BODY_REL
EVIDENCE = OUT / "authored-geometry/tug-worker-v8"


def source_contract() -> dict:
    guard()
    export, receipt = read(V8), read(V9)
    if (receipt["source_v8_receipt_sha256"] != sha(V8)
            or receipt["source_v8_fbx_sha256"] != export["files"]["model.fbx"]["sha256"]
            or receipt["snapshot_sha256"] != sha(receipt["snapshot"])):
        raise RuntimeError("Pinned tug worker export/snapshot drift")
    snapshot = read(receipt["snapshot"])
    donor_path = Path(snapshot["donor_manifest"])
    donor = read(donor_path)
    if snapshot["donor_manifest_sha256"] != sha(donor_path):
        raise RuntimeError("Exact tug donor drift")
    if (len(snapshot["skeleton"]["bones"]) != len(donor["skeleton"]["bones"]) != 140
            or len(snapshot["geometry"]["groups"]) != len(donor["geometry"]["groups"]) != 24
            or snapshot["skeleton"] != donor["skeleton"]):
        raise RuntimeError("Tug worker skeleton/group count changed")
    a, b = snapshot["geometry"]["groups"], donor["geometry"]["groups"]
    if any(a[i] != b[i] for i in range(3, 24)):
        raise RuntimeError("Tug worker conditional cargo/body group changed")
    for i in range(24):
        if (a[i]["name"], a[i]["material"], a[i]["effect"]) != (b[i]["name"], b[i]["material"], b[i]["effect"]):
            raise RuntimeError("Tug worker native group/material order changed")
    if [a[i]["triangle_count"] for i in range(3)] != [96, 96, 96]:
        raise RuntimeError("Approved basket crate triangle counts changed")
    palettes = [len(item["bones"]) for item in snapshot["skeleton"]["skin_palettes"]]
    if palettes != [2, 2, 2, 2, 2, 52, 2, 2]:
        raise RuntimeError("Exact tug worker palette arrangement changed")
    fbx = Path(export["folder"]) / "model.fbx"
    raw = fbx.read_bytes()
    skin = raw.count(b"DeformerS\x04\x00\x00\x00Skin")
    cluster = raw.count(b"DeformerS\x07\x00\x00\x00Cluster")
    if sha(fbx) != export["files"]["model.fbx"]["sha256"] or (skin, cluster) != (24, 3360):
        raise RuntimeError("Tug worker actual FBX Skin/Cluster contract changed")
    return {"group_count": 24, "full_skeleton_bones": 140,
            "palette_bones": palettes, "changed_group_indices": [0, 1, 2],
            "unchanged_conditional_groups": 21,
            "fbx_skin_nodes": skin, "fbx_cluster_nodes": cluster,
            "fbx": str(fbx), "fbx_sha256": sha(fbx),
            "snapshot": receipt["snapshot"], "snapshot_sha256": sha(receipt["snapshot"]),
            "donor": str(donor_path), "donor_sha256": sha(donor_path)}


def worker_rig_text(donor: dict) -> str:
    bones = donor["skeleton"]["bones"]
    names = [bone["name"] for bone in bones]
    if len(names) != 140 or len(set(names)) != 140 or [bone["index"] for bone in bones] != list(range(140)):
        raise RuntimeError("Exact tug worker ordered skeleton changed")
    return ("[HAVOK SKELETON DEFINITION FILE]\n\n[BONES START]\n"
            + "\n".join(names) + "\n[END]\n\n[PARTITION START]\n"
            + f"fullbody_lod3 {names[0]} {names[-1]}\n[END]\n")


def prepare() -> dict:
    contract = source_contract()
    donor = read(contract["donor"])
    target = owned(EVIDENCE / "prepare.json")
    if target.exists() or PROJECT.exists():
        raise FileExistsError("Preserve prior tug worker diagnostic source")
    template = STAGING / "l/Mods/u60l/project/source"
    old_rel = "art/scenario/garrison/u60l/units/u60l_archer_3lod_control/body"
    text = (template / "_default.burnproj").read_text(encoding="utf-8")
    old, new = old_rel.replace("/", "\\"), BODY_REL.replace("/", "\\")
    blocks = [block for block in re.findall(r"<BurnRule>.*?</BurnRule>", text, re.DOTALL) if old in block]
    burners = [re.search(r"<Burner>(.*?)</Burner>", block).group(1) for block in blocks]
    if burners != ["RR Material Burner", "RGM", "RRGeometry", "RGO"]:
        raise RuntimeError("Installed native model burner rules changed")
    rgo_member = donor["resources"]["model"]["logical_path"].removesuffix(".rgm") + ".rgo"
    archive = Path(donor["resources"]["model"]["archive_path"]).with_name("ArtSultanateHA.sga")
    if not archive.is_file(): raise FileNotFoundError(archive)
    listing = subprocess.run([str(ARCH), "list", str(archive), "--filter", Path(rgo_member).name],
                             capture_output=True, text=True, errors="replace", timeout=120, check=True)
    if [row["path"] for row in json.loads(listing.stdout)["members"] if row["path"] == rgo_member] != [rgo_member]:
        raise RuntimeError("Exact worker RGO member missing")
    command = [str(CORE), "mod-project", "create", "--library", str(PROJECT.parent.parent), "--name", KEY]
    run = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    log = EVIDENCE / "create.log"
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(run.returncode)
                   + "\nSTDOUT:\n" + run.stdout + "\nSTDERR:\n" + run.stderr, encoding="utf-8")
    if run.returncode: raise RuntimeError("Blank worker project create failed")
    config = read(PROJECT / "mod-project.json")
    if (config.get("key") != KEY or config.get("animated_units") or config.get("assets")
            or config.get("cooks") or config.get("game_mode", {}).get("enabled")):
        raise RuntimeError("Worker diagnostic project not blank")
    before = file_hashes(PROJECT)
    burn = PROJECT / "project/source/_default.burnproj"
    revised = burn.read_text(encoding="utf-8").replace("</Rules>",
        "\n".join(block.replace(old, new) for block in blocks) + "\n\t</Rules>", 1)
    ET.fromstring(revised)
    BODY.mkdir(parents=True)
    shutil.copy2(contract["fbx"], BODY / "model.fbx")
    (BODY / "model.rig").write_text(worker_rig_text(donor), encoding="utf-8")
    extract = subprocess.run([str(ARCH), "extract-member", str(archive), rgo_member,
                              str(BODY / "model.rgo")], capture_output=True, text=True,
                             errors="replace", timeout=120)
    if extract.returncode: raise RuntimeError("Exact worker RGO extraction failed: " + extract.stderr[-500:])
    (BODY / "model.rgotemplate").write_text("<ObjectTemplate><LodDistances/></ObjectTemplate>\n",
                                              encoding="utf-8")
    colours = {"albedo.png": (150, 145, 135), "normal.png": (128, 128, 255),
               "metalness.png": (0, 0, 0), "roughness.png": (200, 200, 200),
               "pattern.png": (255, 255, 255)}
    for name, colour in colours.items(): (BODY / name).write_bytes(png(colour))
    slot_files = {"albedoTexture": "albedo.png", "normalMap": "normal.png",
                  "metalTex": "metalness.png", "roughnessTex": "roughness.png",
                  "patternTex": "pattern.png"}
    matset = ET.Element("materialSet")
    for material in donor["material"]["materials"]:
        if material["class"] != "unit": raise RuntimeError("Unexpected worker material class")
        item = ET.SubElement(matset, "material", {"name": material["name"], "type": "shader", "source": "unit"})
        slots = {texture["name"] for block in material["blocks"]
                 for texture in block["textures"] if texture["name"] != "__default"}
        slots.add("roughnessTex")
        if slots - slot_files.keys(): raise RuntimeError("Unexpected worker material texture slot")
        for slot in sorted(slots):
            ET.SubElement(item, "param", {"name": slot, "type": "tex2D",
                                          "value": BODY_REL + "/" + slot_files[slot]})
    ET.indent(matset)
    (BODY / "model.material").write_bytes(ET.tostring(matset, encoding="utf-8", xml_declaration=True))
    burn.write_text(revised, encoding="utf-8")
    after = file_hashes(PROJECT)
    added = set(after) - set(before)
    expected = {"project/source/" + BODY_REL + "/" + name for name in
                ("model.fbx", "model.rig", "model.rgo", "model.rgotemplate", "model.material", *colours)}
    changed = {name for name in before if before[name] != after.get(name)}
    if added != expected or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError("Worker diagnostic source allowlist mismatch")
    record = {"schema": "ccp-060-tug24-native-diagnostic-preparation/1", "status": "prepared_not_cooked",
              "project": str(PROJECT), "body": str(BODY), "source_contract": contract,
              "source_hashes_after": after, "stock_rgo_member": rgo_member,
              "stock_rgo_sha256": sha(BODY / "model.rgo"), "diagnostic_material_not_final": True,
              "native_rig_palettes_and_group_identity_unproved": True,
              "original_worker_animation_owner_must_remain": True}
    write(target, record)
    return {"status": record["status"], "receipt": str(target)}


def cook() -> dict:
    guard()
    prep_path, receipt = EVIDENCE / "prepare.json", owned(EVIDENCE / "cook.json")
    prep = read(prep_path)
    run = owned(PROJECT / "dist/tug24-native-diagnostic")
    if receipt.exists() or run.exists(): raise FileExistsError("Preserve prior tug diagnostic cook")
    if prep["status"] != "prepared_not_cooked" or prep["source_hashes_after"] != file_hashes(PROJECT):
        raise RuntimeError("Prepared tug source changed")
    editor = Path(CFG["art_editor"])
    if not editor.is_file() or not NATIVE_LOCK.is_file(): raise FileNotFoundError("Native editor/byte lock")
    command = [str(editor), "-rtm", "--safe_settings", "--do_not_restore", "--quiet_crash_report",
               "--no_source_control", "--log_path", str(run / "logs"), "--build_mod",
               str(PROJECT / f"project/{KEY}.aoe4mod"), "--no_burn_window",
               "--burn_verbose_log_level", "--burn_cache_type", "Local", "--burn_max_threads", "1",
               "--burn_log_path", str(run / "logs/burn.log"), "--build_path", str(run / "output"),
               "--intermediate_path", str(run / "intermediate")]
    record = {"schema": "ccp-060-tug24-native-diagnostic-cook/1", "status": "pending_lock",
              "prepare_sha256": sha(prep_path), "source_hashes_before": prep["source_hashes_after"],
              "command": command, "run_root": str(run), "shared_lock": str(NATIVE_LOCK)}
    with NATIVE_LOCK.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError("Shared native cook lock busy") from error
        try:
            write(receipt, record)
            run.mkdir(parents=True)
            record["status"] = "running_under_shared_native_lock"
            write(receipt, record)
            stdout, stderr = run / "stdout.log", run / "stderr.log"
            with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
                result = subprocess.run(command, cwd=editor.parent, stdout=out, stderr=err,
                                        text=True, timeout=1200)
            record.update({"exit_code": result.returncode, "stdout_log": str(stdout),
                           "stdout_sha256": sha(stdout), "stderr_log": str(stderr),
                           "stderr_sha256": sha(stderr)})
            after = file_hashes(PROJECT)
            record["source_bytes_preserved"] = all(after.get(k) == v for k, v in prep["source_hashes_after"].items())
            archives = sorted((run / "output").rglob("*.sga"))
            record["archives"] = [{"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size} for p in archives]
            record["status"] = ("native_cook_completed_pending_readback" if
                                result.returncode == 0 and record["source_bytes_preserved"] and len(archives) == 1
                                else "native_cook_failed_preserved")
            write(receipt, record)
            if record["status"] != "native_cook_completed_pending_readback":
                raise RuntimeError("Tug worker native diagnostic cook failed; preserved receipt/logs")
            return {"status": record["status"], "receipt": str(receipt)}
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def _json_command(*args: object) -> dict:
    result = subprocess.run([str(value) for value in args], capture_output=True,
                            text=True, errors="replace", timeout=120)
    if result.returncode:
        raise RuntimeError(f"{args[1]} failed: {result.stderr[-1000:]}")
    return json.loads(result.stdout)


def readback() -> dict:
    guard()
    prep_path, cook_path, receipt_path = [EVIDENCE / name for name in
                                          ("prepare.json", "cook.json", "readback.json")]
    extract, decode = owned(EVIDENCE / "readback"), owned(EVIDENCE / "decoded")
    index, config, log = [owned(EVIDENCE / name) for name in
                          ("private-index.sqlite3", "private-index-config.json", "decode.log")]
    if any(p.exists() for p in (receipt_path, extract, decode, index, config, log)):
        raise FileExistsError("Preserve prior tug worker readback")
    cook_receipt = read(cook_path)
    if (cook_receipt["status"] != "native_cook_completed_pending_readback"
            or cook_receipt["prepare_sha256"] != sha(prep_path)
            or not cook_receipt["source_bytes_preserved"] or len(cook_receipt["archives"]) != 1):
        raise RuntimeError("Worker cook/source identity mismatch")
    archive = Path(cook_receipt["archives"][0]["path"])
    owned(archive)
    if sha(archive) != cook_receipt["archives"][0]["sha256"]: raise RuntimeError("Worker archive drift")
    listing = _json_command(ARCH, "list", "--verify", archive)
    if not listing["archive"]["verification"]["verified"]: raise RuntimeError("Worker archive CRC failed")
    members = {item["path"]: item for item in listing["members"]}
    base = f"art/scenario/garrison/{KEY}/body/model"
    expected = {suffix: base + suffix for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
    if len(members) != len(listing["members"]) or not set(expected.values()) <= set(members):
        raise RuntimeError("Four worker model resources absent or archive duplicate")
    if any(path.startswith("attrib/") and path != f"attrib/{KEY}.rgd" for path in members):
        raise RuntimeError("Unexpected worker actor source compiled")
    extract.mkdir(parents=True)
    extracted = {}
    for suffix, member in expected.items():
        target = owned(extract / ("model" + suffix))
        _json_command(ARCH, "extract-member", archive, member, target)
        extracted[suffix] = {"member": member, "path": str(target), "sha256": sha(target)}
    private_index.INDEX = index
    private_index.create_index(archive, list(members.values()), KEY)
    private_root = owned(STAGING / "ag/tug-worker-v8")
    (private_root / "cardinal/archives").mkdir(parents=True, exist_ok=True)
    cfg = json.loads(private_index.ORIGINAL_CONFIG.read_text(encoding="utf-8"))
    cfg["index_path"], cfg["game_root"] = str(index), str(private_root)
    config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    command = [str(CORE), "convert", "decode-static", "--logical-path", base + ".rgm",
               "--config", str(config), "--index", str(index), "--output-root", str(decode)]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    payload = json.loads(result.stdout) if result.returncode == 0 else {}
    manifest = Path(payload["manifest_path"]) if payload.get("manifest_path") else None
    status = ("native_worker_decoded_pending_comparison" if manifest and manifest.is_file()
              else "worker_native_decode_failed_preserved")
    record = {"schema": "ccp-060-tug24-native-diagnostic-readback/1", "status": status,
              "archive": str(archive), "archive_sha256": sha(archive),
              "archive_verification": listing["archive"]["verification"],
              "member_names": sorted(members), "extracted": extracted,
              "decoded_manifest": str(manifest) if manifest else None,
              "decoded_manifest_sha256": sha(manifest) if manifest and manifest.is_file() else None,
              "private_index_sha256": sha(index), "decode_log_sha256": sha(log),
              "diagnostic_model_material_rgo_not_final": True,
              "stock_worker_animation_owner_not_replaced": True}
    write(receipt_path, record)
    if status != "native_worker_decoded_pending_comparison": raise RuntimeError(status)
    return {"status": status, "receipt": str(receipt_path)}


def worker_structure(source: dict, cooked: dict) -> dict:
    """Gate the worker's carry-state groups and eight palettes before corners."""
    a, b = source["geometry"]["groups"], cooked["geometry"]["groups"]
    sa, sb = source["skeleton"], cooked["skeleton"]
    fields = ("name", "material", "effect", "triangle_count")
    source_rows = [tuple(group[key] for key in fields) for group in a]
    compiled_rows = [tuple(group[key] for key in fields) for group in b]
    bone_fields = ("index", "name", "parent_index", "parent_name")
    source_bones = [tuple(bone[key] for key in bone_fields) for bone in sa["bones"]]
    compiled_bones = [tuple(bone[key] for key in bone_fields) for bone in sb["bones"]]
    source_palettes = sa["skin_palettes"]
    compiled_palettes = sb["skin_palettes"]
    record = {"source_groups": len(a), "compiled_groups": len(b),
              "source_palette_bones": [len(p["bones"]) for p in source_palettes],
              "compiled_palette_bones": [len(p["bones"]) for p in compiled_palettes],
              "source_skeleton_bones": len(source_bones),
              "compiled_skeleton_bones": len(compiled_bones),
              "ordered_bone_hierarchy_exact": source_bones == compiled_bones,
              "ordered_group_name_material_effect_triangles_exact": source_rows == compiled_rows,
              "ordered_skin_palettes_exact": source_palettes == compiled_palettes,
              "source_groups_summary": [dict(zip(fields, row)) for row in source_rows],
              "compiled_groups_summary": [dict(zip(fields, row)) for row in compiled_rows]}
    record["passed"] = (record["source_skeleton_bones"] ==
                        record["compiled_skeleton_bones"] == 140
                        and record["source_groups"] == record["compiled_groups"] == 24
                        and record["source_palette_bones"] ==
                        record["compiled_palette_bones"] == [2, 2, 2, 2, 2, 52, 2, 2]
                        and record["ordered_bone_hierarchy_exact"]
                        and record["ordered_group_name_material_effect_triangles_exact"]
                        and record["ordered_skin_palettes_exact"])
    return record


def compare() -> dict:
    """Record native readback, refusing to qualify merged carry groups."""
    guard()
    target = owned(EVIDENCE / "comparison.json")
    if target.exists(): raise FileExistsError("Preserve worker comparison")
    contract = source_contract()
    readback_path = EVIDENCE / "readback.json"
    receipt = read(readback_path)
    if receipt["status"] != "native_worker_decoded_pending_comparison":
        raise RuntimeError("Worker readback is not comparison-ready")
    decoded = Path(receipt["decoded_manifest"])
    owned(decoded)
    if sha(decoded) != receipt["decoded_manifest_sha256"]:
        raise RuntimeError("Worker native decoded manifest drift")
    source, cooked = read(Path(contract["snapshot"])), read(decoded)
    structure = worker_structure(source, cooked)
    record = {"schema": "ccp-060-tug24-native-diagnostic-comparison/1",
              "status": "native_worker_control_incompatible" if not structure["passed"]
                        else "native_worker_structure_only_pending_corner_comparison",
              "source_snapshot": contract["snapshot"],
              "source_snapshot_sha256": contract["snapshot_sha256"],
              "native_manifest": str(decoded), "native_manifest_sha256": sha(decoded),
              "readback_receipt_sha256": sha(readback_path),
              "structure": structure,
              "native_geometry_qualified": False,
              "diagnostic_material_not_final": True,
              "reason": "Native burner merged distinct conditional carry groups and eight palettes"
                        if not structure["passed"] else
                        "Full weighted-corner geometry comparison not yet run"}
    write(target, record)
    return {"status": record["status"], "receipt": str(target),
            "source_groups": structure["source_groups"],
            "compiled_groups": structure["compiled_groups"],
            "source_palettes": structure["source_palette_bones"],
            "compiled_palettes": structure["compiled_palette_bones"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("source", "prepare", "cook", "readback", "compare"))
    args = parser.parse_args()
    print(json.dumps(globals()[args.stage]() if args.stage != "source" else source_contract(), indent=2))


if __name__ == "__main__": main()
