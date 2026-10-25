"""Read-only lifecycle/selector inventory; write one hash-qualified report under release_051."""
from __future__ import annotations
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(r"F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_051")
EXT = Path(r"C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com\garrison")
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_set(payload: bytes):
    name, at = rc.read_lp_string(payload, 0)
    count = struct.unpack_from("<I", payload, at)[0]
    at += 4
    members = []
    for _ in range(count):
        value, at = rc.read_lp_string(payload, at)
        members.append(value)
    assert at == len(payload)
    return {"name": name, "members": members}


def parse_predicate(payload: bytes):
    count = struct.unpack_from("<I", payload)[0]
    at, rows = 4, []
    for _ in range(count):
        op, flag, one = struct.unpack_from("<IBI", payload, at)
        at += 9
        prop, at = rc.read_lp_string(payload, at)
        value, at = rc.read_lp_string(payload, at)
        rows.append({"op": op, "flag": flag, "one": one, "property": prop, "value": value})
    assert at == len(payload)
    return rows


def rgm(path: Path):
    chunks = list(rc.walk(rc.load(path).roots))
    sets = [parse_set(c.payload) for c in chunks if c.tag == b"MSD " and len(c.payload) > 4]
    tests = [parse_predicate(c.payload) for c in chunks if c.tag == b"CNBP"]
    assert len(sets) in (len(tests), len(tests) + 1), (path, len(sets), len(tests))
    pairs = []
    for i, selector in enumerate(sets):
        pairs.append({"selector": selector, "conditions": tests[i] if i < len(tests) else []})
    mscl = next((c for c in chunks if c.tag == b"MSCL"), None)
    mscl_info = None
    if mscl:
        mscl_info = {"sha256": hashlib.sha256(mscl.payload).hexdigest(),
                     "children": [{"tag": x.tag.decode("ascii", "replace"), "bytes": len(x.payload),
                                   "sha256": hashlib.sha256(x.payload).hexdigest(),
                                   "prefix_hex": x.payload[:48].hex()} for x in mscl.children]}
        if len(mscl.children) == 1 and mscl.children[0].tag == b"DATA" and len(mscl.children[0].payload) >= 2:
            data = mscl.children[0].payload
            count = struct.unpack_from("<H", data)[0]
            mscl_info["source_object_count"] = count
            selector_names = {n for item in sets for n in item["members"]}
            offsets = {name: data.find(rc.lp_string(name)) for name in selector_names}
            mscl_info["source_object_name_offsets"] = offsets
            mscl_info["source_objects"] = sorted(offsets, key=offsets.get)
            mscl_info["selector_member_set_equals_source_objects"] = (
                len(selector_names) == count and all(offset >= 0 for offset in offsets.values())
                and len(set(offsets.values())) == count)
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size,
            "selector_count": len(sets), "predicate_count": len(tests),
            "selectors": pairs, "mscl": mscl_info}


def rgo(path: Path):
    chunks = list(rc.walk(rc.load(path).roots))
    rows = []
    for c in chunks:
        if c.tag in (b"BVBP", b"BBPD"):
            rows.append({"tag": c.tag.decode("ascii"), "name": c.decoded_name,
                         "payload_hex": c.payload[:128].hex(), "bytes": len(c.payload)})
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size,
            "behavior_chunks": rows}


def main():
    paths = {
        "castle_050_custom_citadel_rgm": OUT.parent / "castle_next/integration/payload/art/scenario/cccastle/imperial_citadel/model.rgm",
        "castle_050_custom_hq_rgm": OUT.parent / "castle_next/integration/payload/art/scenario/cccastle/resistance_hq/model.rgm",
        "castle_050_custom_citadel_rgo": OUT.parent / "castle_next/integration/payload/art/scenario/cccastle/imperial_citadel/model.rgo",
        "castle_050_custom_hq_rgo": OUT.parent / "castle_next/integration/payload/art/scenario/cccastle/resistance_hq/model.rgo",
        "stock_citadel_owner_rgm": OUT.parent / "castle_next/native-stock/official/art/civilizations/chinese/structures/wonder_greatwall_mp/wonder_greatwall_mp.rgm",
        "stock_citadel_owner_rgo": OUT.parent / "castle_next/native-stock/official/art/civilizations/chinese/structures/wonder_greatwall_mp/wonder_greatwall_mp.rgo",
        "stock_hq_owner_rgm": OUT.parent / "castle_next/native-stock/official/art/civilizations/chinese_ha_01/structures/landmark_2b/chi_ha_01_landmark_b_age02/chi_ha_01_landmark_b_age02.rgm",
        "stock_hq_owner_rgo": OUT.parent / "castle_next/native-stock/official/art/civilizations/chinese_ha_01/structures/landmark_2b/chi_ha_01_landmark_b_age02/chi_ha_01_landmark_b_age02.rgo",
        "release_051_frozen_citadel_rgm": OUT / "landmarks/baseline/art/scenario/cccastle/imperial_citadel/model.rgm",
        "release_051_frozen_hq_rgm": OUT / "landmarks/baseline/art/scenario/cccastle/resistance_hq/model.rgm",
        "release_040_pho_minh_rgm": OUT.parent / "release_040/integration/payload/art/scenario/cc040/pho_minh/model.rgm",
        "release_040_one_pillar_rgm": OUT.parent / "release_040/integration/payload/art/scenario/cc040/one_pillar/model.rgm",
        "release_040_pho_minh_rgo": OUT.parent / "release_040/integration/payload/art/scenario/cc040/pho_minh/model.rgo",
        "release_040_one_pillar_rgo": OUT.parent / "release_040/integration/payload/art/scenario/cc040/one_pillar/model.rgo",
        "stock_040_wood_fort_owner_rgo": OUT.parent / "release_040/integration/reference-stock/official/art/civilizations/english/structures/campaign_wood_fort/eng_campaign_wood_fort/eng_campaign_wood_fort.rgo",
    }
    report = {"schema": "ccp.release051.native-lifecycle-inventory/v1",
              "status": "read_only_static_inventory", "rgm": {}, "rgo": {},
              "native_runtime": "not tested"}
    for name, path in paths.items():
        if not path.is_file():
            continue
        if name.endswith("_rgm"):
            report["rgm"][name] = rgm(path)
        else:
            report["rgo"][name] = rgo(path)
    selector_file = OUT / "landmarks/selector-inspection.json"
    if selector_file.is_file():
        report["existing_selector_inspection"] = {"path": str(selector_file), "sha256": sha(selector_file)}
    target = OUT / "inventory/native-lifecycle.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(target),
                      "rgm": {k: v["sha256"] for k, v in report["rgm"].items()},
                      "rgo": {k: v["sha256"] for k, v in report["rgo"].items()}}, indent=2))


if __name__ == "__main__":
    main()
