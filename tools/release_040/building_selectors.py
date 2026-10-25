"""Inventory the official RGM lifecycle selector sets for 0.4.0 donors.

Run under Blender's bundled Python (the Garrison Chunky binary is cp313).
This is read-only and does not launch Blender or cook assets.
"""
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
spec = importlib.util.spec_from_file_location("garrison_shared", str(EXT / "garrison_shared.cp313-win_amd64.pyd"))
shared = importlib.util.module_from_spec(spec)
sys.modules["garrison_shared"] = shared
spec.loader.exec_module(shared)
from garrison_shared import relic_chunky as rc


def parse_state(payload):
    count = struct.unpack_from("<I", payload)[0]
    at, conditions = 4, []
    for _ in range(count):
        op, flag, one = struct.unpack_from("<IBI", payload, at)
        at += 9
        prop, at = rc.read_lp_string(payload, at)
        value, at = rc.read_lp_string(payload, at)
        conditions.append({"op": op, "flag": flag, "one": one, "property": prop, "value": value})
    assert at == len(payload)
    return conditions


def parse_set(payload):
    name, at = rc.read_lp_string(payload, 0)
    count = struct.unpack_from("<I", payload, at)[0]
    at += 4
    members = []
    for _ in range(count):
        member, at = rc.read_lp_string(payload, at)
        members.append(member)
    assert at == len(payload)
    return {"name": name, "members": members}


def run():
    donors = json.loads((ROOT / "art/recipes/release_040/buildings-donors.json").read_text())
    rows = []
    for donor in donors["models"]:
        source = donor["resources"]["model"]["cache_path"]
        chunks = list(rc.walk(rc.load(source).roots))
        sets = [parse_set(c.payload) for c in chunks if c.tag == b"MSD " and len(c.payload) > 4]
        states = [parse_state(c.payload) for c in chunks if c.tag == b"CNBP"]
        assert len(sets) in (len(states), len(states) + 1), (donor["family"], donor["age"], len(sets), len(states))
        pairs = [{"set": selector, "conditions": states[i] if i < len(states) else []}
                 for i, selector in enumerate(sets)]
        names = sorted({name for pair in pairs for name in pair["set"]["members"]})
        healthy = sorted({name for pair in pairs for name in pair["set"]["members"]
                          if any(c["property"] == "life_cycle_state" and c["value"] == "healthy"
                                 for c in pair["conditions"])})
        mscl = next((c for c in chunks if c.tag == b"MSCL"), None)
        mscl_count = struct.unpack_from("<H", mscl.children[0].payload)[0] if mscl and len(mscl.children) == 1 else None
        rows.append({"family": donor["family"], "age": donor["age"],
                     "rgm_logical_path": donor["logical_path"], "rgm_sha256": donor["resources"]["model"]["sha256"],
                     "selector_sets": pairs, "selector_name_count": len(names), "selector_names": names,
                     "healthy_selector_name_count": len(healthy), "healthy_selector_names": healthy,
                     "mscl_source_object_count": mscl_count,
                     "collection_contract": donor["has_collection_contract"]})
        print("BUILDING_SELECTOR", donor["family"], donor["age"], len(pairs), len(names), len(healthy), mscl_count)
    result = {"schema": "ccp.release040.building-selectors/v1", "status": "official_rgm_selector_inventory",
              "models": rows, "proof": "Static RGM selector parsing only; visible native runtime remains unverified"}
    dest = ROOT / "output/release_040/buildings/donor-selectors.json"
    dest.write_text(json.dumps(result, indent=2), encoding="utf8")
    print("BUILDING_SELECTORS_PINNED", dest)


if __name__ == "__main__":
    run()
