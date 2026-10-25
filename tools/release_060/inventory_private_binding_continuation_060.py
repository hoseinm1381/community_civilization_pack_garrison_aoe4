"""Build a read-only private consumer plan from pinned 0.6.0 inventories."""
from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from common import OUT, guard, owned, sha, write

ROOT = Path(__file__).resolve().parents[2]
EXT = Path(r"F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_060")
CONT = EXT / "inventory/continuation"
BASE = EXT / "baseline/final053"
VISUAL = EXT / "inventory/visual-bindings.json"
SIEGE = CONT / "continuation-ledger-v3.json"
PLANS = [
    EXT / "qualification/material-batch-continuation/plan.json",
    EXT / "qualification/material-batch-remaining-humanoids/plan.json",
]
EXPECTED_INPUTS = {
    str(VISUAL): "9ba07a2bb420366ec662e850c84a0bee1fe36a744938592391be5a093e0a791a",
    str(SIEGE): "8b5b4912fa85d6ef7fd03aa358ad879e6c35b2aab5205463f55f0019f12bd2df",
    str(PLANS[0]): "ed5d10ac675c9926ef68824b081fc05d885151a137d5823baf5a0c442d2972aa",
    str(PLANS[1]): "da45f4c7b1e165cc12fc2958a640db9503e749f0a5b1f037905431296494196e",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def model_key(value: str) -> str:
    return value.replace("\\", "/").removesuffix(".rgm").lower()


def render_leaves(xml_path: Path) -> list[dict]:
    root = ET.parse(xml_path).getroot()
    result = []
    def walk(node, chain, sibling_index=0):
        key = node.attrib.get("Key", node.tag)
        part = f"{node.tag}[@Key='{key}'][{sibling_index}]"
        here = chain + [part]
        if key in {"alternate_sua", "parent_animator", "animator", "animator0"} and node.attrib.get("Value"):
            result.append({"leaf": "/" + "/".join(here), "field": key,
                           "before_value": node.attrib["Value"]})
        for index, child in enumerate(list(node)):
            walk(child, here, index)
    walk(root, [])
    return result


def main() -> None:
    guard()
    for path, expected in EXPECTED_INPUTS.items():
        if sha(path) != expected:
            raise ValueError(f"Pinned inventory input changed: {path}")
    v = load(VISUAL)
    siege = load(SIEGE)
    archive_members = {}
    for p in (BASE / "archive-members/attrib").rglob("*.rgd"):
        rel = p.relative_to(BASE / "archive-members").as_posix()
        archive_members[rel] = {"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size}

    native_visual_leaves = {}
    for member, record in siege["attributed_consumer_paths"].items():
        xml = Path(record.get("decoded_xml", ""))
        if xml.is_file():
            native_visual_leaves[member] = {
                "raw_archive_member_sha256": record["sha256"],
                "decoded_xml_sha256": record["decoded_xml_sha256"],
                "decoded_xml_path": str(xml), "leaves": render_leaves(xml),
            }
    cart_member = "attrib/attachments/attachment_lists/civilizations/english/units/tier3_siege_cart_eng.rgd"
    cart_xml = CONT / "archive-readback/official-archive-readback-001/attrib__attachments__attachment_lists__civilizations__english__units__tier3_siege_cart_eng.xml"
    cart_raw = cart_xml.with_suffix(".rgd")
    if cart_xml.is_file() and cart_raw.is_file():
        native_visual_leaves[cart_member] = {
            "raw_archive_member_sha256": sha(cart_raw), "decoded_xml_sha256": sha(cart_xml),
            "decoded_xml_path": str(cart_xml), "leaves": render_leaves(cart_xml),
        }

    jobs = []
    for plan_path in PLANS:
        for j in load(plan_path)["jobs"]:
            wanted = model_key(j["model"])
            lists = []
            for member, record in v["native_attachment_resources"].items():
                slots = [s for s in record["slots"]
                         if s.get("role") == "render_model_slot"
                         and model_key(s.get("before_value", "")) == wanted]
                if slots:
                    raw_hash = slots[0].get("raw_archive_member_sha256")
                    lists.append({"member": member,
                                  "raw_archive_member_sha256": raw_hash,
                                  "decoded_xml_sha256": slots[0].get("sha256_of_decoded_xml"),
                                  "slots": slots})
            consumer_rows = []
            for family in v["families"]:
                for actor in family.get("actor_bindings", []):
                    for node in actor.get("visual_and_owner_references", []):
                        normalized = node.get("before_value", "").replace("\\", "/").lower()
                        if any(x["member"].removeprefix("attrib/").removesuffix(".rgd").replace("/", "\\").lower()
                               == node.get("before_value", "").lower() for x in lists):
                            src = node["source"]
                            compiled = "attrib/" + actor["actor"].replace("\\", "/") + ".rgd"
                            consumer_rows.append({
                                "source": src["asset_relative_path"],
                                "source_sha256": src["sha256"],
                                "compiled_member": compiled,
                                "compiled_baseline": archive_members.get(compiled),
                                "leaf": node["node_path"],
                                "field": node["field"],
                                "before_value": node["before_value"],
                                "variant_context": node.get("variant_context", []),
                                "list_item_id_context": node.get("list_item_id_context", []),
                            })
            jobs.append({"source_plan": str(plan_path), "geometry_slug": j["geometry_slug"],
                         "material_key": j["key"], "stock_model": j["model"],
                         "native_attachment_lists": lists, "vietnamese_actor_consumers": consumer_rows,
                         "private_action": "Clone every shared non-Vietnamese list to Vietnam, replace only the matching render_model_slot leaves, and redirect only the listed Vietnamese actor attachment leaves; preserve parent_animator, tool/cargo slots, gender variants, and all nonvisual fields."})

    planned_lists = {x["member"] for j in jobs for x in j["native_attachment_lists"]}
    reachable_lists = {}
    for family in v["families"]:
        for actor in family.get("actor_bindings", []):
            for node in actor.get("visual_and_owner_references", []):
                if node.get("field") != "attachments" or not node.get("before_value", "").startswith("attachments\\attachment_lists\\"):
                    continue
                member = "attrib/" + node["before_value"].replace("\\", "/") + ".rgd"
                record = v["native_attachment_resources"].get(member)
                if not record:
                    continue
                body_slots = [s for s in record["slots"] if s.get("role") == "render_model_slot"]
                if not body_slots:
                    continue
                source = node["source"]
                compiled = "attrib/" + actor["actor"].replace("\\", "/") + ".rgd"
                row = reachable_lists.setdefault(member, {"member": member,
                    "raw_archive_member_sha256": body_slots[0].get("raw_archive_member_sha256"),
                    "slots": body_slots, "vietnamese_consumers": []})
                row["vietnamese_consumers"].append({
                    "family": family["family"], "actor": actor["actor"],
                    "source": source["asset_relative_path"], "source_sha256": source["sha256"],
                    "compiled_member": compiled, "compiled_baseline": archive_members.get(compiled),
                    "leaf": node["node_path"], "before_value": node["before_value"],
                    "variant_context": node.get("variant_context", []),
                    "list_item_id_context": node.get("list_item_id_context", []),
                })

    consumers = {}
    source_root = ROOT / "assets/attrib/instances"
    needles = {
        "ram": "unit_ram_3_chi",
        "springald": "unit_springald_3_chi",
        "trebuchet_counterweight": "unit_trebuchet_4_cw_chi",
        "trebuchet_traction": "unit_trebuchet_4_tr_chi",
        "siege_cart": "unit_siege_cart",
    }
    for fam, needle in needles.items():
        rows = []
        for src in sorted(source_root.rglob("*.xml")):
            if "vietnam" not in src.parts:
                continue
            lines = src.read_text(encoding="utf-8-sig").splitlines()
            for no, line in enumerate(lines, 1):
                if needle not in line:
                    continue
                rel = src.relative_to(source_root).as_posix()
                rgd = "attrib/" + rel.removesuffix(".xml") + ".rgd"
                rows.append({"source": "assets/attrib/instances/" + rel,
                             "source_sha256": sha(src), "line": no,
                             "before_value": line.strip(), "compiled_member": rgd,
                             "compiled_baseline": archive_members.get(rgd)})
        consumers[fam] = rows

    result = {
        "schema": "ccp-060-private-consumer-binding-plan/v1",
        "status": "inventory_only_no_source_or_archive_changes",
        "inputs": {str(VISUAL): sha(VISUAL), str(SIEGE): sha(SIEGE),
                   **{str(p): sha(p) for p in PLANS}},
        "material_jobs": jobs,
        "additional_reachable_body_lists": [x for m, x in sorted(reachable_lists.items()) if m not in planned_lists],
        "siege_consumers": consumers,
        "siege_native_members": siege["attributed_consumer_paths"],
        "siege_native_visual_leaves": native_visual_leaves,
        "required_boundaries": [
            "Never edit shared English/Chinese/Mongol donor actors or lists.",
            "Use private Vietnamese actor/list identities; root assigns IDs in its single batch.",
            "Keep base/campaign/xp3 and discounted/free consumers where reachable.",
            "Preserve native animation owners, weapons, sockets/mounts, tools, cargo, and gameplay fields.",
            "Do not treat missing consumer proof as unreachable; keep it unresolved until source/compiled selector evidence exists.",
        ],
    }
    out = owned(CONT / "private-consumer-binding-plan-v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    write(out, result)
    print(json.dumps({"output": str(out), "material_jobs": len(jobs),
                      "siege_consumers": {k: len(v) for k, v in consumers.items()},
                      "sha256": sha(out)}, indent=2))


if __name__ == "__main__":
    main()
