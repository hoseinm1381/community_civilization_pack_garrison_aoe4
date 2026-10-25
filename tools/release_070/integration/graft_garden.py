"""Build an isolated Garden model, private stamp/list and actor payload from a fresh cook."""
from __future__ import annotations

import copy
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
sys.path.insert(0, str(ROOT / "tools/release_010"))
sys.path.insert(0, str(ROOT / "tools/release_061"))
sys.path.insert(0, str(ROOT / "tools/castle_next"))
from garrison_shared import building_project as bp, rgd
from integration_codec import intact_damage_conditions, copy_native_markers
from lifecycle_modes import install
from assemble_castle_object_061 import finish_selectors, rebase_model, rebase_material, selector_table
import integration as native

BASE = ROOT / "output/release_070/integration"
COOK = BASE / "garden-cook-v1"
CONTRACT = BASE / "native-contract/contract.json"
OWNERS = BASE / "native-owner/owners.json"
DRAFT = ROOT / "staging/release_070/integration/garden-binding-draft"
OUT = BASE / "garden-payload-v2"
STEM = "art/scenario/cc070/garden/model"
TEXTURES = "art/scenario/cc070/garden"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def path_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def put(rows: list, member: str, raw: bytes, evidence: str) -> None:
    if any(r["member"] == member for r in rows):
        raise RuntimeError(f"Duplicate Garden payload {member}")
    target = OUT / "payload" / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({"member": member, "sha256": sha(raw), "bytes": len(raw),
                 "file": str(target), "evidence": evidence})


def main(cook_label: str, payload_label: str) -> None:
    global COOK, OUT
    if not cook_label.replace("-", "").isalnum() or not payload_label.replace("-", "").isalnum():
        raise ValueError("Invalid immutable output label")
    COOK = BASE / ("garden-" + cook_label)
    OUT = BASE / ("garden-" + payload_label)
    if OUT.exists():
        raise FileExistsError("Preserve existing Garden payload")
    cook = json.loads((COOK / "receipt.json").read_text())
    if cook["status"] != "fresh_native_cook_and_readback_complete_runtime_unverified":
        raise RuntimeError("Fresh Garden cook required")
    contract = json.loads(CONTRACT.read_text())
    owner = next(x for x in json.loads(OWNERS.read_text())["owners"] if x["family"] == "garden")
    garden = next(x for x in contract["actors"] if x["family"] == "garden")
    draft = json.loads((DRAFT / "receipt.json").read_text())
    if draft["status"] != "staged_not_active":
        raise RuntimeError("Garden private binding draft missing")
    frozen = json.loads((COOK / "input-freeze.json").read_text())
    parts = frozen["building"]["parts"]
    cooked = Path(cook["model_readback"])
    donor = Path(owner["native_media"][".rgm"]["path"])
    donor_rgo = Path(owner["native_media"][".rgo"]["path"])
    if path_sha(donor) != owner["native_media"][".rgm"]["sha256"]:
        raise RuntimeError("Native Garden RGM donor drift")
    if path_sha(donor_rgo) != owner["native_media"][".rgo"]["sha256"]:
        raise RuntimeError("Native Garden RGO donor drift")
    for name, expected in cook["media"].items():
        if path_sha(cooked / name) != expected:
            raise RuntimeError(f"Cooked Garden readback drift: {name}")
    OUT.mkdir(parents=True)
    rows = []
    raw = bp.construction_model((cooked / "model.rgm").read_bytes(), donor.read_bytes(),
                                parts, profile_id="english-house")
    raw, damage = intact_damage_conditions(raw)
    raw, ruins = install(raw)
    raw = finish_selectors(raw)
    raw, markers = copy_native_markers(raw, donor.read_bytes())
    raw = rebase_model(raw, STEM)
    put(rows, STEM + ".rgm", raw, "fresh cook + exact native construction/marker graft")
    put(rows, STEM + ".rgo", donor_rgo.read_bytes(), "exact stock native RGO")
    put(rows, STEM + ".rrgeom", (cooked / "model.rrgeom").read_bytes(), "fresh native cook")
    material, refs = rebase_material((cooked / "model.rrmaterial").read_bytes(),
                                    "art/scenario/garrison/cc070garden/buildings/garden", TEXTURES)
    put(rows, STEM + ".rrmaterial", material, "fresh native object-PBR cook")
    for leaf, member in sorted(refs.items()):
        put(rows, member, (cooked / leaf).read_bytes(), "fresh native texture cook")

    # Clone the exact Chinese Garden visual stamp and replace its one structure model.
    main_ref = next(r for r in garden["references"] if "/outskirts/" not in r["member"])
    stock_stamp = main_ref["stamps"][0]
    source_stamp = BASE / "native-contract/official-cache/official" / stock_stamp["member"]
    if path_sha(source_stamp) != stock_stamp["sha256"]:
        raise RuntimeError("Native Garden stamp drift")
    private_stamp = "art/stamps/cc070/garden_main"
    stamp_file = OUT / "working-stamp.bin"
    stamp_report = native.private_stamp(source_stamp, stamp_file,
                                         {owner["stock_model"]: STEM})
    visuals = native.active_visuals(native.NativeTree(stamp_file))
    original_visuals = native.active_visuals(native.NativeTree(source_stamp))
    changed = [(a, b) for a, b in zip(original_visuals, visuals)
               if a["model"] != b["model"] or a["transform"] != b["transform"]]
    if (len(visuals) != len(original_visuals) or len(changed) != 1 or
            changed[0][0]["id"] != owner["body_id"] or
            changed[0][1]["model"] != STEM or
            changed[0][0]["transform"] != changed[0][1]["transform"]):
        raise RuntimeError("Private stamp changed outside one visual model path")
    put(rows, private_stamp + ".bin", stamp_file.read_bytes(), "one native visual path replacement")

    # The only compiled list differences are its generated private PBG ID and stamp path.
    main_identity = next(x for x in draft["identities"] if x["name"] == "vn070_garden_main")
    old_list = Path(main_identity["compiled"]).read_bytes()
    selected = rgd.read(old_list)
    copied = copy.deepcopy(selected)
    old_stamp_value = stock_stamp["member"].removesuffix(".bin").replace("/", "\\")
    new_stamp_value = private_stamp.replace("/", "\\")
    edited = []
    for field, node in rgd.flatten(copied.nodes):
        if node.key == "stamp" and node.value == old_stamp_value:
            node.value = new_stamp_value
            edited.append(field)
    if not edited:
        raise RuntimeError("No Garden visual stamp references changed")
    check = copy.deepcopy(copied)
    for _, node in rgd.flatten(check.nodes):
        if node.key == "stamp" and node.value == new_stamp_value:
            node.value = old_stamp_value
    if rgd.write(check) != old_list:
        raise RuntimeError("Private list nonvisual fields changed")
    member = "attrib/attachments/attachment_lists/vietnam/release_070/vn070_garden_main.rgd"
    put(rows, member, rgd.write(copied), "private visual stamp reference only")
    outskirts = next(x for x in draft["identities"] if x["name"] == "vn070_garden_outskirts")
    put(rows, "attrib/attachments/attachment_lists/vietnam/release_070/vn070_garden_outskirts.rgd",
        Path(outskirts["compiled"]).read_bytes(), "private outskirts identity, stock markers retained")

    # Patch exactly the two compiled Vietnamese attachment references; no other actor field.
    actor_member = "attrib/ebps/vietnam/vn_building_landmark_age3_imperial_garden_vit.rgd"
    actor_baseline = (ROOT / "output/release_070/monk/readback/after" / actor_member).read_bytes()
    actor = rgd.read(actor_baseline)
    edited_actor = copy.deepcopy(actor)
    paths = []
    substitutions = {
        "building_wonder_age2_pagoda_control_chi": "vn070_garden_main",
        "byz_lan_03": "vn070_garden_outskirts",
    }
    for path, node in rgd.flatten(edited_actor.nodes):
        if node.key == "$PBGNAME" and "/attachments/" in path and node.value in substitutions:
            before = node.value
            node.value = CFG["project_guid"].replace("-", "") + ":" + substitutions[before]
            paths.append({"path": path, "before": before, "after": node.value})
    if len(paths) != 2:
        raise RuntimeError(f"Expected two Garden compiled actor refs, got {len(paths)}")
    restored = copy.deepcopy(edited_actor)
    reverse_names = {p["path"]: p["before"] for p in paths}
    for path, node in rgd.flatten(restored.nodes):
        if path in reverse_names:
            node.value = reverse_names[path]
    if rgd.write(restored) != actor_baseline:
        raise RuntimeError("Garden actor changed outside two visual attachment references")
    put(rows, actor_member, rgd.write(edited_actor), "two Vietnamese visual attachment references")
    receipt = {"schema": "ccp-070-garden-private-visual-payload/v1",
               "status": "offline_native_cook_grafted_runtime_unverified",
               "cook_receipt_sha256": path_sha(COOK / "receipt.json"),
               "identity_receipt_sha256": path_sha(DRAFT / "receipt.json"),
               "baseline_sga_sha256": contract["baseline_sga_sha256"],
               "native_owner_rgm_sha256": owner["native_media"][".rgm"]["sha256"],
               "native_owner_rgo_sha256": owner["native_media"][".rgo"]["sha256"],
               "selector_table": selector_table(raw), "damage": damage, "ruins": ruins,
               "markers": markers, "stamp": stamp_report,
               "list_stamp_fields": edited, "actor_attachment_fields": paths,
               "actor_attachment_map_policy": "unchanged native attachments\\attachment_lists",
               "payloads": rows, "allowlist": sorted(r["member"] for r in rows),
               "native_import_appearance_repair": "pending user test"}
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"), "members": len(rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cook-label", default="cook-v1")
    parser.add_argument("--payload-label", default="payload-v2")
    options = parser.parse_args()
    main(options.cook_label, options.payload_label)
