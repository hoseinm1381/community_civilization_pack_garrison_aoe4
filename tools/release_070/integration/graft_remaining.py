"""Build one private Foundry/University/Wonder art payload from a fresh cook."""
from __future__ import annotations

import argparse
import copy
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
from garrison_shared import building_project as bp, relic_chunky as rc, rgd
from integration_codec import intact_damage_conditions, copy_native_markers
from lifecycle_modes import install
from assemble_castle_object_061 import finish_selectors, rebase_model, rebase_material, selector_table
import integration as native

BASE = ROOT / "output/release_070/integration"
CONTRACT = BASE / "native-contract/contract.json"
OWNERS = BASE / "native-owner/owners.json"
DRAFT = Path(CFG["external_root"]) / "staging/release_070/integration/remaining-binding-draft/receipt.json"
REFERENCE = BASE / "remaining-reference-v1/receipt.json"
QUALIFIED = BASE / "remaining-binding-qualification-v1/receipt.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main(family: str, cook_label: str, payload_label: str) -> None:
    if family not in ("foundry", "university", "wonder"):
        raise ValueError("Unsupported private art family")
    if any(not x.replace("-", "").isalnum() for x in (cook_label, payload_label)):
        raise ValueError("Invalid immutable output label")
    cook_root = BASE / (family + "-" + cook_label)
    out = BASE / (family + "-" + payload_label)
    if out.exists():
        raise FileExistsError("Preserve earlier art payload")
    cook = json.loads((cook_root / "receipt.json").read_text())
    if cook["status"] != "fresh_native_cook_and_readback_complete_runtime_unverified":
        raise RuntimeError("Fresh model cook/readback required")
    frozen = json.loads((cook_root / "input-freeze.json").read_text())
    contract = json.loads(CONTRACT.read_text())
    owner = next(x for x in json.loads(OWNERS.read_text())["owners"] if x["family"] == family)
    actor = next(x for x in contract["actors"] if x["family"] == family)
    draft = json.loads(DRAFT.read_text())
    reference = json.loads(REFERENCE.read_text())
    qualified = json.loads(QUALIFIED.read_text())
    if (draft["status"] != "staged_not_active" or
            qualified["reference_archive_sha256"] != reference["archive_sha256"]):
        raise RuntimeError("Private binding compile proof missing")
    model_readback = Path(cook["model_readback"])
    donor_rgm = Path(owner["native_media"][".rgm"]["path"])
    donor_rgo = Path(owner["native_media"][".rgo"]["path"])
    if (file_sha(donor_rgm) != owner["native_media"][".rgm"]["sha256"] or
            file_sha(donor_rgo) != owner["native_media"][".rgo"]["sha256"]):
        raise RuntimeError("Native model owner drift")
    if any(file_sha(model_readback / name) != digest for name, digest in cook["media"].items()):
        raise RuntimeError("Fresh model readback drift")
    out.mkdir(parents=True)
    rows = []
    def put(member: str, raw: bytes, evidence: str):
        if any(x["member"] == member for x in rows):
            raise RuntimeError("Duplicate payload resource " + member)
        target = out / "payload" / member
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        rows.append({"member": member, "sha256": sha(raw), "bytes": len(raw),
                     "file": str(target), "evidence": evidence})
    stem = f"art/scenario/cc070/{family}/model"
    texture_folder = f"art/scenario/cc070/{family}"
    raw = bp.construction_model((model_readback / "model.rgm").read_bytes(),
                                donor_rgm.read_bytes(), frozen["building"]["parts"],
                                profile_id="english-house")
    raw, damage = intact_damage_conditions(raw)
    raw, ruins = install(raw)
    raw = finish_selectors(raw)
    # University main stock visual remains in the same stamp. Avoid copying its
    # functional marker set into the separate decorative overlay visual.
    marker_policy = "zero_addon_markers_stock_main_unchanged" if family == "university" else "exact_native_owner_markers_copied"
    markers = None
    if family != "university":
        raw, markers = copy_native_markers(raw, donor_rgm.read_bytes())
    else:
        marker_chunks = [c for c in rc.walk(rc.parse(raw).roots) if c.tag == b"MRKS"]
        if len(marker_chunks) != 1 or marker_chunks[0].payload != b"\0\0\0\0":
            raise RuntimeError("University add-on must carry no duplicate native markers")
        markers = {"addon_marker_count": 0, "stock_main_marker_owner": "unchanged stock visual"}
    raw = rebase_model(raw, stem)
    put(stem + ".rgm", raw, "fresh cook with typed lifecycle and scoped native owner")
    put(stem + ".rgo", donor_rgo.read_bytes(), "exact family-specific stock native RGO")
    put(stem + ".rrgeom", (model_readback / "model.rrgeom").read_bytes(), "fresh native object-PBR geometry")
    material, refs = rebase_material((model_readback / "model.rrmaterial").read_bytes(),
                                     f"art/scenario/garrison/cc070{family}/buildings/{family}", texture_folder)
    put(stem + ".rrmaterial", material, "fresh native object-PBR material")
    for leaf, member in sorted(refs.items()):
        put(member, (model_readback / leaf).read_bytes(), "fresh native texture")
    main_ref = actor["references"][0]
    stock_stamp = next(s for s in main_ref["stamps"] if s["member"] == owner["main_stamp"])
    source_stamp = BASE / "native-contract/official-cache/official" / stock_stamp["member"]
    assert file_sha(source_stamp) == stock_stamp["sha256"]
    original_visuals = native.active_visuals(native.NativeTree(source_stamp))
    if family == "university":
        target = next(v for v in original_visuals if v["id"] == "16329432728099511667")
        assert target["model"] == "art/civilizations/common/props/small_water_pot/small_water_pot"
    else:
        target = next(v for v in original_visuals if v["id"] == owner["body_id"])
        assert target["model"] == owner["stock_model"]
    private_stamp_member = f"art/stamps/cc070/{family}_main.bin"
    working_stamp = out / "working-stamp.bin"
    stamp_report = native.private_stamp(source_stamp, working_stamp, {target["model"]: stem})
    private_visuals = native.active_visuals(native.NativeTree(working_stamp))
    changed = [(old, new) for old, new in zip(original_visuals, private_visuals)
               if old["model"] != new["model"] or old["transform"] != new["transform"]]
    if (len(private_visuals) != len(original_visuals) or len(changed) != 1 or
            changed[0][0]["id"] != target["id"] or changed[0][1]["model"] != stem or
            changed[0][0]["transform"] != changed[0][1]["transform"]):
        raise RuntimeError("Private stamp altered outside one intended visual model")
    put(private_stamp_member, working_stamp.read_bytes(), "one scoped native visual path replacement")
    source_rows = [x for x in draft["identities"] if x["family"] == family]
    for index, row in enumerate(source_rows):
        member = f"attrib/attachments/attachment_lists/vietnam/release_070/{row['name']}.rgd"
        private = rgd.read(Path(row["compiled"]).read_bytes())
        if index == 0:
            original_stamp = owner["main_stamp"].removesuffix(".bin").replace("/", "\\")
            new_stamp = private_stamp_member.removesuffix(".bin").replace("/", "\\")
            changes = []
            for path, node in rgd.flatten(private.nodes):
                if node.key == "stamp" and node.value == original_stamp:
                    node.value = new_stamp
                    changes.append(path)
            if not changes:
                raise RuntimeError("No private main stamp fields changed")
        else:
            changes = []
        put(member, rgd.write(private), "private native PBG identity and scoped main stamp")
    actor_member = f"attrib/ebps/vietnam/{actor['actor']}.rgd"
    actor_readback = Path(reference["readback"][actor_member]["file"])
    put(actor_member, actor_readback.read_bytes(), "isolated Content Editor private default/campaign references")
    receipt = {"schema": "ccp-070-remaining-private-art-payload/v1",
               "status": "offline_native_cook_grafted_runtime_unverified", "family": family,
               "cook_receipt_sha256": file_sha(cook_root / "receipt.json"),
               "reference_receipt_sha256": file_sha(REFERENCE),
               "source_contract_sha256": file_sha(CONTRACT),
               "native_owner_rgm_sha256": owner["native_media"][".rgm"]["sha256"],
               "native_owner_rgo_sha256": owner["native_media"][".rgo"]["sha256"],
               "selector_table": selector_table(raw), "damage": damage, "ruins": ruins,
               "marker_policy": marker_policy, "marker_copy": markers,
               "stock_main_visual_preserved": family == "university",
               "university_displaced_prop": target if family == "university" else None,
               "stamp": stamp_report, "payloads": rows,
               "allowlist": sorted(x["member"] for x in rows),
               "native_import_appearance_lifecycle": "pending user match"}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(out / "receipt.json"), "members": len(rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("family", choices=("foundry", "university", "wonder"))
    parser.add_argument("--cook-label", default="cook-v1")
    parser.add_argument("--payload-label", default="payload-v1")
    args = parser.parse_args()
    main(args.family, args.cook_label, args.payload_label)
