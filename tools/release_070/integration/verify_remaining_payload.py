"""Verify an immutable 0.7.0 private art payload against native owners and refs."""
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
sys.path.insert(0, str(ROOT / "tools/release_061"))
sys.path.insert(0, str(ROOT / "tools/castle_next"))
from garrison_shared import rgd
from assemble_castle_object_061 import selector_table
import integration as native

BASE = ROOT / "output/release_070/integration"
OFFICIAL = BASE / "native-contract/official-cache/official"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def leaf_map(raw: bytes):
    return dict(rgd.flatten(rgd.read(raw).nodes))


def main(family: str, cook_label: str, payload_label: str, qualification_label: str) -> None:
    for label in (cook_label, payload_label, qualification_label):
        if not label.replace("-", "").isalnum():
            raise ValueError("Invalid immutable label")
    out = BASE / f"{family}-{qualification_label}"
    if out.exists():
        raise FileExistsError("Preserve earlier qualification")
    cook = json.loads((BASE / f"{family}-{cook_label}/receipt.json").read_text())
    payload = json.loads((BASE / f"{family}-{payload_label}/receipt.json").read_text())
    reference = json.loads((BASE / "remaining-reference-v1/receipt.json").read_text())
    preflight = json.loads((BASE / "remaining-binding-qualification-v1/receipt.json").read_text())
    contract = json.loads((BASE / "native-contract/contract.json").read_text())
    owner = next(x for x in json.loads((BASE / "native-owner/owners.json").read_text())["owners"] if x["family"] == family)
    actor = next(x for x in contract["actors"] if x["family"] == family)
    if payload["family"] != family or cook["family"] != family:
        raise RuntimeError("Cook/payload family mismatch")
    if payload["cook_receipt_sha256"] != digest(BASE / f"{family}-{cook_label}/receipt.json"):
        raise RuntimeError("Payload not tied to this fresh cook")
    if payload["reference_receipt_sha256"] != digest(BASE / "remaining-reference-v1/receipt.json"):
        raise RuntimeError("Payload not tied to compiled private references")
    assert preflight["reference_archive_sha256"] == reference["archive_sha256"]
    rows = {r["member"]: r for r in payload["payloads"]}
    assert len(rows) == len(payload["payloads"])
    assert set(rows) == set(payload["allowlist"])
    assert all(digest(Path(r["file"])) == r["sha256"] for r in rows.values())
    model = f"art/scenario/cc070/{family}/model"
    assert digest(Path(rows[model + ".rgo"]["file"])) == owner["native_media"][".rgo"]["sha256"]
    assert digest(Path(rows[model + ".rrgeom"]["file"])) == cook["media"]["model.rrgeom"]
    table = selector_table(Path(rows[model + ".rgm"]["file"]).read_bytes())
    assert json.loads(json.dumps(table)) == payload["selector_table"]
    def selected(state):
        return sorted({part for _, parts, predicates in table for part in parts
                       if (2, 0, 1, "life_cycle_state", state) in predicates})
    parts = lambda indices: [f"garrison_part_{i:04}" for i in indices]
    for state in ("healthy", "damage_1", "damage_2", "preview", "targeting"):
        assert selected(state) == parts([0, 1, 4, 5, 6]), state
    for state in ("damage_3", "damage_4", "damage_5"):
        assert selected(state) == parts([0, 3]), state
    assert selected("ruins") == parts([2])
    for index in range(0, 100, 5):
        assert selected(f"construct_{index:02}") == parts([0] if index < 20 else [0, 1, 4, 5, 6])
    stamp_member = f"art/stamps/cc070/{family}_main.bin"
    stock = OFFICIAL / owner["main_stamp"]
    original = native.active_visuals(native.NativeTree(stock))
    private = native.active_visuals(native.NativeTree(Path(rows[stamp_member]["file"])))
    assert len(private) == len(original)
    changed = [(a, b) for a, b in zip(original, private)
               if a["model"] != b["model"] or a["transform"] != b["transform"]]
    target_id = "16329432728099511667" if family == "university" else owner["body_id"]
    assert len(changed) == 1 and changed[0][0]["id"] == target_id
    assert changed[0][1]["model"] == model
    assert changed[0][0]["transform"] == changed[0][1]["transform"]
    if family == "university":
        assert changed[0][0]["model"] == "art/civilizations/common/props/small_water_pot/small_water_pot"
        assert any(a["id"] == owner["body_id"] and a["model"] == b["model"] == owner["stock_model"]
                   and a["transform"] == b["transform"] for a, b in zip(original, private))
        assert payload["marker_policy"] == "zero_addon_markers_stock_main_unchanged"
    else:
        assert changed[0][0]["model"] == owner["stock_model"]
        assert payload["marker_policy"] == "exact_native_owner_markers_copied"
    draft = json.loads((Path(CFG["external_root"]) / "staging/release_070/integration/remaining-binding-draft/receipt.json").read_text())
    identities = []
    for row in (x for x in draft["identities"] if x["family"] == family):
        member = f"attrib/attachments/attachment_lists/vietnam/release_070/{row['name']}.rgd"
        private_bytes = Path(rows[member]["file"]).read_bytes()
        native_bytes = Path(reference["readback"][member]["file"]).read_bytes()
        assert leaf_map(private_bytes)["default/pbgid"].value == leaf_map(native_bytes)["default/pbgid"].value == row["pbgid"]
        restored = copy.deepcopy(rgd.read(private_bytes))
        donor_bytes = (OFFICIAL / row["donor"]).read_bytes()
        rgd.find(restored.nodes, "default/pbgid").value = leaf_map(donor_bytes)["default/pbgid"].value
        if row["name"].endswith("_main"):
            old = owner["main_stamp"].removesuffix(".bin").replace("/", "\\")
            new = stamp_member.removesuffix(".bin").replace("/", "\\")
            rewrites = 0
            for _, node in rgd.flatten(restored.nodes):
                if node.key == "stamp" and node.value == new:
                    node.value = old
                    rewrites += 1
            assert rewrites > 0
        assert rgd.write(restored) == donor_bytes, row["name"]
        identities.append({"name": row["name"], "pbgid": row["pbgid"],
                           "full_official_donor_restoration_byte_identical": True})
    actor_member = f"attrib/ebps/vietnam/{actor['actor']}.rgd"
    assert digest(Path(rows[actor_member]["file"])) == reference["readback"][actor_member]["sha256"]
    result = {"schema": "ccp-070-remaining-private-art-qualification/v1",
              "status": "passed_static_native_cook_and_reference_runtime_unverified",
              "family": family, "cook_archive_sha256": cook["archive_sha256"],
              "reference_archive_sha256": reference["archive_sha256"],
              "one_stamp_visual_replaced": changed[0],
              "stock_main_visual_preserved": family == "university",
              "exact_owner_rgo": True, "selector_state_parts": True,
              "compiled_actor_equals_private_payload": True,
              "private_list_donor_restoration_byte_identical": True,
              "identities": identities, "changed_resource_allowlist": payload["allowlist"],
              "limits": "Static cook/readback and reference proof; imported match appearance, player colour, construction, persistent ruins and repair remain untested."}
    out.mkdir(parents=True)
    (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"receipt": str(out / "receipt.json"), "members": len(rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("family", choices=("foundry", "university", "wonder"))
    parser.add_argument("--cook-label", default="cook-v1")
    parser.add_argument("--payload-label", default="payload-v1")
    parser.add_argument("--qualification-label", default="qualification-v1")
    args = parser.parse_args()
    main(args.family, args.cook_label, args.payload_label, args.qualification_label)
