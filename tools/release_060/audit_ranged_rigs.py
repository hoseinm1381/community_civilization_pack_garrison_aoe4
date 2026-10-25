"""Read-only stock ranged-tier donor trace and complete native-rig audit.

Only exact active EBP references are followed. Extracts/decodes are isolated in
output/release_060/qualification/ranged-rig-audit; no index or active source edits.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, CORE, OUT, ROOT, guard, owned, read, sha, write

INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
CONFIG = INDEX.with_name("game-assets.local.json")
DEST = OUT / "qualification/ranged-rig-audit"
NAMES = (
    "vn_unit_archer_2_vit", "vn_unit_archer_3_vit", "vn_unit_archer_4_vit",
    "vn_unit_crossbowman_3_chi", "vn_unit_crossbowman_4_chi",
    "vn_unit_handcannon_4_chi",
)
PROTOTYPE = (OUT / "donors/prototype-probe"
             / "2bd91fe1b0f69a897d468faecbeaeeb0fb624cc8a59069f5b29bf1cda3115770"
             / "prototype.json")
ARCHER2 = (OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json")
ARCHER2_TRACE = OUT / "donors/archer-trace.json"


def command(*args: object, timeout: int = 90) -> dict:
    proc = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"exit {proc.returncode}: {[str(x) for x in args]}; "
                           f"stdout={proc.stdout[-1200:]} stderr={proc.stderr[-1200:]}")
    return json.loads(proc.stdout)


def member_metadata(archive: Path, member: str) -> dict:
    listing = command(ARCH, "list", archive, "--filter", Path(member).name)
    found = [x for x in listing["members"] if x["path"].lower() == member.lower()]
    if len(found) != 1:
        raise RuntimeError(f"Exact official RGD member not found uniquely: {member}: {found}")
    return found[0]


def extract_rgd(archive: Path, archive_hash: str, member: str) -> tuple[ET.Element, dict]:
    meta = member_metadata(archive, member)
    key = f"{archive_hash[:20]}-{meta['crc']:08x}-{meta['size']}"
    directory = owned(DEST / "rgd" / Path(member).stem / key)
    binary, xml, receipt = directory / Path(member).name, directory / (Path(member).stem + ".xml"), directory / "receipt.json"
    identity = {"archive_sha256": archive_hash, "member": member,
                "member_crc": meta["crc"], "member_size": meta["size"],
                "member_stored_size": meta["stored_size"]}
    if directory.exists():
        if not all(x.is_file() for x in (binary, xml, receipt)):
            raise RuntimeError(f"Incomplete RGD cache: {directory}")
        old = read(receipt)
        if old["source"] != identity or old["rgd_sha256"] != sha(binary) or old["xml_sha256"] != sha(xml):
            raise RuntimeError(f"RGD cache drift: {directory}")
    else:
        directory.mkdir(parents=True)
        command(ARCH, "extract-member", archive, member, binary)
        command(ARCH, "decode-rgd", binary, xml)
        write(receipt, {"source": identity, "rgd_sha256": sha(binary), "xml_sha256": sha(xml)})
    return ET.parse(xml).getroot(), {"source": identity, "xml": str(xml),
                                     "xml_sha256": sha(xml), "rgd_sha256": sha(binary)}


def default_animators(root: ET.Element) -> list[dict]:
    default = next((x for x in root.findall("RGDNode") if x.get("Key") == "default"), None)
    if default is None:
        raise RuntimeError("RGD has no default branch")
    return [{"key": x.get("Key"), "value": x.get("Value")}
            for x in default.iter("RGDNode")
            if (x.get("Key", "").startswith("animator") or x.get("Key") == "parent_animator")
            and x.get("Value")]


def model_row(db: sqlite3.Connection, value: str) -> dict:
    logical = value.replace("\\", "/").lower()
    if not logical.endswith(".rgm"):
        logical += ".rgm"
    rows = db.execute("select logical_path,archive_path,archive,size from resolved_assets "
                      "where lower(logical_path)=?", (logical,)).fetchall()
    if len(rows) != 1 or not Path(rows[0][1]).is_file():
        raise RuntimeError(f"Exact indexed model unavailable: {logical}: {rows}")
    return dict(zip(("logical_path", "archive_path", "archive", "bytes"), rows[0]))


def trace() -> dict:
    guard()
    game = read(CONFIG)
    archive = Path(game["game_root"]) / "cardinal/archives/Attrib.sga"
    archive_hash = sha(archive)
    report = {"schema": "ccp-060-ranged-rig-audit/v1", "phase": "traced",
              "source_archive": str(archive), "source_archive_sha256": archive_hash,
              "index": str(INDEX), "config": str(CONFIG), "tiers": {}, "models": {}}
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        for name in NAMES:
            path = ROOT / "assets/attrib/instances/ebps/vietnam" / (name + ".xml")
            root = ET.parse(path).getroot()
            refs = [x.get("value") for x in root.iter("instance_reference")
                    if x.get("name") == "attachments" and x.get("value")]
            weapons = sorted({x.get("value") for x in root.iter("instance_reference")
                              if x.get("name") == "animator_attachments" and x.get("value")})
            if not refs:
                raise RuntimeError(f"No body attachment on active EBP: {path}")
            body_ref = refs[0]
            # First top-level/default tier is the active initial appearance.
            body_member = "attrib/" + body_ref.replace("\\", "/") + ".rgd"
            body_xml, body_source = extract_rgd(archive, archive_hash, body_member)
            body_animations = default_animators(body_xml)
            if not body_animations:
                raise RuntimeError(f"No native default body animator: {body_member}")
            body_models = [model_row(db, a["value"]) for a in body_animations]
            primary_weapon = next((x.get("value") for x in root.iter("instance_reference")
                                   if x.get("name") == "animator_attachments" and x.get("value")), None)
            weapon_source = None
            weapon_animations = []
            if primary_weapon:
                weapon_member = "attrib/" + primary_weapon.replace("\\", "/") + ".rgd"
                weapon_xml, weapon_source = extract_rgd(archive, archive_hash, weapon_member)
                weapon_animations = default_animators(weapon_xml)
            weapon_models = [model_row(db, a["value"]) for a in weapon_animations
                             if a["value"].lower().startswith("art\\")]
            report["tiers"][name] = {
                "active_ebp": str(path), "active_ebp_sha256": sha(path),
                "body_attachment": body_ref, "other_body_tier_refs": sorted(set(refs[1:])),
                "body_source": body_source, "body_animators": body_animations,
                "body_models": body_models, "primary_weapon_attachment": primary_weapon,
                "weapon_attachment_refs": weapons, "primary_weapon_source": weapon_source,
                "primary_weapon_animators": weapon_animations,
                "primary_weapon_models": weapon_models,
            }
            for item in body_models:
                report["models"][item["logical_path"]] = item
            write(DEST / "trace.json", report)
    if sha(archive) != archive_hash:
        raise RuntimeError("Official Attrib archive changed during trace")
    return report


def decode_model(model: dict, source_hash: str) -> Path:
    logical = model["logical_path"]
    if logical == "art/civilizations/chinese/humans/chi_ranged_bow_age02/chi_ranged_bow_age02.rgm":
        old = read(ARCHER2_TRACE)
        if old["source_archive_sha256"] != source_hash or not ARCHER2.is_file():
            raise RuntimeError("Pinned Archer II prior donor/archive drift")
        decoded = read(ARCHER2)
        if decoded["request"]["logical_path"] != logical:
            raise RuntimeError("Pinned Archer II manifest identity drift")
        return ARCHER2
    target = owned(DEST / "decoded" / Path(logical).stem)
    existing = list(target.glob("*/decoded-static.json")) if target.exists() else []
    if len(existing) > 1:
        raise RuntimeError(f"Ambiguous decoder outputs: {existing}")
    if existing:
        manifest = read(existing[0])
        if manifest["request"]["logical_path"] != logical or manifest["status"] != "decoded":
            raise RuntimeError(f"Decoder cache identity/status drift: {existing[0]}")
        return existing[0]
    result = command(CORE, "convert", "decode-static", "--logical-path", logical,
                     "--config", CONFIG, "--index", INDEX, "--output-root", target,
                     timeout=360)
    paths = list(target.glob("*/decoded-static.json"))
    if len(paths) != 1:
        raise RuntimeError(f"Decoder did not create exactly one manifest for {logical}: {result}")
    manifest = read(paths[0])
    if manifest["request"]["logical_path"] != logical or manifest["status"] != "decoded":
        raise RuntimeError(f"Decoder returned incomplete model: {paths[0]}")
    return paths[0]


def compare(a: dict, b: dict) -> dict:
    sa, sb = a.get("skeleton"), b.get("skeleton")
    if not isinstance(sa, dict) or not isinstance(sb, dict) or not sa.get("bones") or not sb.get("bones"):
        return {"status": "unsupported_missing_skeleton"}
    ba, bb = sa["bones"], sb["bones"]
    pa, pb = sa.get("skin_palettes", []), sb.get("skin_palettes", [])
    result = {"skeleton_bones": [len(ba), len(bb)], "skeleton_records_exact": ba == bb,
              "bone_name_mismatch_indices": [i for i in range(min(len(ba), len(bb)))
                                             if ba[i].get("name") != bb[i].get("name")],
              "palette_counts": [len(pa), len(pb)],
              "palette_bone_counts": [[len(x.get("bones", [])) for x in pa],
                                      [len(x.get("bones", [])) for x in pb]],
              "palette_container_records_exact": pa == pb,
              "palette_bone_records_exact": len(pa) == len(pb) and all(
                  left.get("bones") == right.get("bones") for left, right in zip(pa, pb)),
              "palette_container_names": [[x.get("name") for x in ps] for ps in (pa, pb)]}
    result["lod_skin_maps"] = [
        [[lod.get("skin_indices") for lod in p.get("lod_palettes", [])] for p in ps]
        for ps in (pa, pb)]
    result["lod_skin_maps_exact"] = result["lod_skin_maps"][0] == result["lod_skin_maps"][1]
    result["status"] = ("exact_bind_and_lod_skin_records"
                        if result["skeleton_records_exact"] and result["palette_bone_records_exact"]
                        and result["lod_skin_maps_exact"] else "different_native_records")
    return result


def summarize(path: Path, model: dict) -> dict:
    decoded = read(path)
    groups = decoded["geometry"]["groups"]
    return {"model": model, "manifest": str(path), "manifest_sha256": sha(path),
            "status": decoded["status"],
            "skeleton_bones": len(decoded["skeleton"].get("bones", [])),
            "skin_palette_bones": [len(x.get("bones", [])) for x in decoded["skeleton"].get("skin_palettes", [])],
            "geometry_groups": [{"name": g["name"], "lod_material": g["material"],
                                 "effect": g["effect"], "vertices": g["vertex_count"],
                                 "triangles": g["triangle_count"]} for g in groups],
            "total_triangles": sum(g["triangle_count"] for g in groups),
            "material_slots": decoded["material"].get("materials"),
            "texture_dependencies": decoded["material"].get("texture_dependencies"),
            "textures": [{"name": t.get("texture_name"), "source_sha256": t.get("source", {}).get("sha256")}
                         for t in decoded.get("textures", [])]}


def verify_current_source(decoded: dict, logical: str, db: sqlite3.Connection,
                          archive_hashes: dict[str, str]) -> list[dict]:
    """Re-extract only the three exact current compiled members; compare bytes."""
    checked = []
    expected = {".rgm": decoded["skeleton"]["source_sha256"],
                ".rrgeom": decoded["geometry"]["source"]["sha256"],
                ".rrmaterial": decoded["material"]["source"]["sha256"]}
    for suffix, expected_hash in expected.items():
        member = logical.removesuffix(".rgm") + suffix
        rows = db.execute("select archive_path,size from resolved_assets where lower(logical_path)=?",
                          (member.lower(),)).fetchall()
        if len(rows) != 1:
            raise RuntimeError(f"Current official compiled member unresolved: {member}: {rows}")
        archive = Path(rows[0][0])
        if str(archive) not in archive_hashes:
            archive_hashes[str(archive)] = sha(archive)
        archive_hash = archive_hashes[str(archive)]
        meta = member_metadata(archive, member)
        if meta["size"] != rows[0][1]:
            raise RuntimeError(f"Index/archive member size drift: {member}")
        folder = owned(DEST / "current-source" / Path(logical).stem / suffix[1:]
                       / f"{archive_hash[:20]}-{meta['crc']:08x}-{meta['size']}")
        binary, receipt = folder / Path(member).name, folder / "receipt.json"
        identity = {"archive": str(archive), "archive_sha256": archive_hash,
                    "member": member, "member_crc": meta["crc"], "member_size": meta["size"]}
        if folder.exists():
            if not binary.is_file() or not receipt.is_file() or read(receipt)["source"] != identity:
                raise RuntimeError(f"Current-source cache drift: {folder}")
            if sha(binary) != read(receipt)["sha256"]:
                raise RuntimeError(f"Current-source cached bytes drift: {binary}")
        else:
            folder.mkdir(parents=True)
            command(ARCH, "extract-member", archive, member, binary)
            write(receipt, {"source": identity, "sha256": sha(binary)})
        actual_hash = sha(binary)
        if actual_hash != expected_hash:
            raise RuntimeError(f"Decoded manifest is stale against current official {member}: "
                               f"decoded={expected_hash} current={actual_hash}")
        checked.append({"source": identity, "sha256": actual_hash,
                        "decoded_source_sha256": expected_hash, "exact": True})
    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-only", action="store_true")
    args = parser.parse_args()
    traced = trace()
    if args.trace_only:
        print(json.dumps({"phase": "traced", "path": str(DEST / "trace.json"),
                          "models": list(traced["models"])}, indent=2))
        return
    prototype = read(PROTOTYPE)
    manifests = {}
    for logical, model in traced["models"].items():
        path = decode_model(model, traced["source_archive_sha256"])
        manifests[logical] = path
        write(DEST / "decode-progress.json", {"decoded": {k: str(v) for k, v in manifests.items()},
                                                "pending": [k for k in traced["models"] if k not in manifests]})
    report = {"schema": "ccp-060-ranged-rig-comparison/v1", "phase": "decoded_compared",
              "source_trace": str(DEST / "trace.json"), "source_trace_sha256": sha(DEST / "trace.json"),
              "prototype": {"path": str(PROTOTYPE), "sha256": sha(PROTOTYPE),
                            "key": prototype["prototype"]["key"]},
              "models": {}, "tiers": {}, "limitations": [
                  "Matching bind records are an experimental model-only compatibility finding, not Build Unit admission.",
                  "No Blender export, native cook, animator remap, gameplay binding or match test is claimed."]}
    archive_hashes = {}
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        for logical, path in manifests.items():
            model = traced["models"][logical]
            decoded = read(path)
            item = summarize(path, model)
            item["current_official_source_checks"] = verify_current_source(
                decoded, logical, db, archive_hashes)
            item["vs_english_spearman_2"] = compare(decoded, prototype)
            item["vs_other_native_models"] = {other: compare(decoded, read(other_path))
                                               for other, other_path in manifests.items() if other != logical}
            report["models"][logical] = item
            write(DEST / "compare-progress.json", {"compared": list(report["models"]),
                                                     "pending": [k for k in manifests if k not in report["models"]]})
    report["official_art_archive_sha256"] = archive_hashes
    for name, tier in traced["tiers"].items():
        report["tiers"][name] = {"active_ebp": tier["active_ebp"],
                                 "body_attachment": tier["body_attachment"],
                                 "body_models": [x["logical_path"] for x in tier["body_models"]],
                                 "primary_weapon_attachment": tier["primary_weapon_attachment"],
                                 "primary_weapon_animators": tier["primary_weapon_animators"],
                                 "primary_weapon_models": tier["primary_weapon_models"],
                                 "weapon_attachment_refs": tier["weapon_attachment_refs"]}
    write(DEST / "report.json", report)
    short = {"schema": "ccp-060-ranged-rig-summary/v1", "source_report": str(DEST / "report.json"),
             "source_report_sha256": sha(DEST / "report.json"),
             "comparison_scope": "complete ordered skeleton bone records, complete ordered skin-palette bone bind records, and every LOD skin-index array; model-specific palette container names and chunk hashes are recorded separately",
             "tiers": {}, "native_pair_statuses": {}}
    for name, tier in report["tiers"].items():
        key = tier["body_models"][0]
        model = report["models"][key]
        short["tiers"][name] = {
            "model": key, "skeleton_bones": model["skeleton_bones"],
            "palette_bones": model["skin_palette_bones"],
            "lod_geometry": [{"lod": x["lod_material"], "vertices": x["vertices"],
                              "triangles": x["triangles"]} for x in model["geometry_groups"]],
            "material_texture_dependencies": model["texture_dependencies"],
            "primary_weapon_attachment": tier["primary_weapon_attachment"],
            "primary_weapon_models": [x["logical_path"] for x in tier["primary_weapon_models"]],
            "vs_english_spearman_2": model["vs_english_spearman_2"]["status"],
            "official_model_geometry_material_bytes_verified": all(
                x["exact"] for x in model["current_official_source_checks"]),
        }
        short["native_pair_statuses"][name] = {
            other_name: model["vs_other_native_models"][other_tier["body_models"][0]]["status"]
            for other_name, other_tier in report["tiers"].items() if other_name != name}
    write(DEST / "summary.json", short)
    print(json.dumps({"phase": report["phase"], "report": str(DEST / "report.json"),
                      "model_statuses": {k: v["vs_english_spearman_2"]["status"]
                                         for k, v in report["models"].items()}}, indent=2))


if __name__ == "__main__":
    main()
