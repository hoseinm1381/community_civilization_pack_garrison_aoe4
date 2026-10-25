"""Rebase freshly cooked object-PBR Castle visuals onto existing native owners.

Only writes new 0.6.1 payload and evidence. Does not alter the active archive.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import configuration, check_storage

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
from garrison_shared import building_project as bp, model_variants as mv, relic_chunky as rc

sys.path.insert(0, str(ROOT / "tools/release_010"))
from integration_codec import intact_damage_conditions, copy_native_markers

sys.path.insert(0, str(ROOT / "tools/release_040"))
import lifecycle

OUT = ROOT / "output/release_061/castle-object-payload-r1"
COOK = ROOT / "output/release_061/castle-object-cook-r1"
BACK = COOK / "readback/art/scenario/garrison/cc061castle/buildings"
OLD = ROOT / "output/release_052/diagnostic-c/readback/art/scenario"
STOCK = ROOT / "output/castle_next/native-stock/official/art"
FINAL = json.loads((ROOT / "output/release_060/qualification/final-archive-r2/receipt.json").read_text())
FROZEN = json.loads((COOK / "input-freeze.json").read_text())
PARTS = {row["name"]: row["parts"] for row in FROZEN}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def selector_table(raw: bytes) -> list[tuple[str, list[str], list[tuple]]]:
    _, pairs = lifecycle._pairs(raw)
    return [(lifecycle._selector(s)[0], lifecycle._selector(s)[1],
             lifecycle._conditions(c)) for s, c in pairs]


def finish_selectors(raw: bytes) -> bytes:
    """Match the final 0.5.1 six-selector native lifecycle contract exactly."""
    doc, pairs = lifecycle._pairs(raw)
    current = selector_table(raw)
    expected_names = ["sel_construct_00", "sel_construct_20", "sel_construct_40",
                      "sel_construct_60", "sel_heavy_damage", "sel_ruins"]
    if [r[0] for r in current] != expected_names:
        raise RuntimeError(f"Cooked selector names changed: {[r[0] for r in current]}")
    main = ["garrison_part_0001", "garrison_part_0004",
            "garrison_part_0005", "garrison_part_0006"]
    prefix = "garrison_part_"
    if {p for _, members, _ in current for p in members} != {prefix + f"{i:04}" for i in range(7)}:
        raise RuntimeError("Seven source parts are not all present")
    stages = [f"construct_{i:02}" for i in range(0, 100, 5)]
    wanted = [
        ("sel_construct_00", [prefix + "0000"], stages + ["preview", "targeting"]),
        ("sel_construct_20", main, stages[4:] + ["preview", "targeting"]),
        ("sel_healthy", [prefix + "0000", *main], ["healthy", "damage_1", "damage_2"]),
        ("sel_construct_60", [], [row[-1] for row in current[3][2]]),
        ("sel_damaged", [prefix + "0000", prefix + "0003"],
         ["damage_3", "damage_4", "damage_5"]),
        ("sel_ruins", [prefix + "0002"], ["ruins"]),
    ]
    edits = {}
    for (name, members, states), (s, c) in zip(wanted, pairs):
        edits[s.offset] = lifecycle._pack_selector(name, members)
        edits[c.offset] = lifecycle._pack_conditions(states)
    result = rc.rebuild(doc, lambda c: edits.get(c.offset))
    rows = selector_table(result)
    for state in [*stages, "preview", "targeting", "healthy", "ruins",
                  *(f"damage_{i}" for i in range(1, 6))]:
        selected = sorted({p for _, members, conditions in rows for p in members
                           if (2, 0, 1, "life_cycle_state", state) in conditions})
        if state == "ruins":
            target = [prefix + "0002"]
        elif state in ("damage_3", "damage_4", "damage_5"):
            target = [prefix + "0000", prefix + "0003"]
        elif state.startswith("construct_") and int(state[-2:]) < 20:
            target = [prefix + "0000"]
        else:
            target = [prefix + "0000", *main]
        if selected != sorted(target):
            raise RuntimeError(f"Lifecycle mismatch {state}: {selected} != {target}")
    return result


def rebase_model(raw: bytes, stem: str) -> bytes:
    doc = rc.parse(raw)
    nodes = [c for c in rc.walk(doc.roots) if c.tag == b"BANA"]
    if len(nodes) != 1:
        raise RuntimeError("Expected one BANA model path")
    return rc.rebuild(doc, lambda c: rc.lp_string(stem.replace("/", "\\"))
                      if c.offset == nodes[0].offset else None)


def rebase_material(raw: bytes, source_folder: str, destination_folder: str) -> tuple[bytes, dict[str, str]]:
    doc = rc.parse(raw)
    changes = {}
    references = {}
    for material in doc.roots:
        if material.tag != b"GMat":
            continue
        one = rc.pack_document([rc.pack_chunk(material.kind, material.tag, material.payload,
                                              name=material.name, version=material.version)])
        mapping = {}
        for slot, value in mv.material_slots(one)["textures"].items():
            if not isinstance(value, str) or not value.startswith("art\\"):
                continue
            normalized = value.replace("\\", "/").lower()
            if not normalized.startswith(source_folder + "/") or not normalized.endswith(".rrtex"):
                raise RuntimeError(f"Foreign material dependency: {value}")
            leaf = normalized.rsplit("/", 1)[1]
            mapped = destination_folder + "/" + leaf
            mapping[slot] = mapped.replace("/", "\\")
            references[leaf] = mapped
        updated = mv.rewrite_material(one, mapping, {})
        changes[material.offset] = rc.parse(updated).roots[0].payload
    result = rc.rebuild(doc, lambda c: changes.get(c.offset))
    roots = [x for x in rc.parse(result).roots if x.tag == b"GMat"]
    descriptors = [next(y.payload[4:].decode("utf-8") for y in x.children if y.tag == b"MatD")
                   for x in roots]
    if descriptors != ["object", "object_collection"]:
        raise RuntimeError(f"Wrong native material route: {descriptors}")
    return result, references


def add(rows: list[dict], member: str, raw: bytes) -> None:
    target = OUT / "payload" / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    expected = FINAL["members"].get(member)
    rows.append({"member": member, "path": str(target), "sha256": sha(raw),
                 "bytes": len(raw), "before_sha256": expected["sha256"] if expected else None})


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"Preserve existing payload run: {OUT}")
    OUT.mkdir(parents=True)
    rows = []
    model_proofs = []
    models = [
        ("imperial_citadel", "art/scenario/cccastle/imperial_citadel/model",
         STOCK / "civilizations/chinese/structures/wonder_greatwall_mp/wonder_greatwall_mp.rgm",
         OLD / "cccastle/imperial_citadel/model.rgm"),
        ("resistance_hq", "art/scenario/cccastle/resistance_hq/model",
         STOCK / "civilizations/chinese_ha_01/structures/landmark_2b/chi_ha_01_landmark_b_age02/chi_ha_01_landmark_b_age02.rgm",
         OLD / "cccastle/resistance_hq/model.rgm"),
        ("imperial_citadel", "art/scenario/cc050/imperial_citadel_campaign/model",
         STOCK / "civilizations/chinese/structures/wonder_greatwall_mp/wonder_greatwall_mp.rgm",
         OLD / "cc050/imperial_citadel_campaign/model.rgm"),
    ]
    first_geometry = {}
    first_material = {}
    first_texture = {}
    for name, stem, donor_path, old_path in models:
        cooked = BACK / name
        source_folder = f"art/scenario/garrison/cc061castle/buildings/{name}"
        destination_folder = f"art/scenario/cc061/{name}"
        raw = bp.construction_model((cooked / "model.rgm").read_bytes(),
                                    donor_path.read_bytes(), PARTS[name], profile_id="english-house")
        raw, damage = intact_damage_conditions(raw)
        # The original 0.5.0 route moves the cooked ruin and damage parts into
        # native lifecycle selectors; 0.5.1 then assigns owner-compatible names.
        sys.path.insert(0, str(ROOT / "tools/castle_next"))
        from lifecycle_modes import install
        raw, ruins = install(raw)
        raw = finish_selectors(raw)
        raw, marker = copy_native_markers(raw, old_path.read_bytes())
        raw = rebase_model(raw, stem)
        add(rows, stem + ".rgm", raw)

        geometry = (cooked / "model.rrgeom").read_bytes()
        if name not in first_geometry:
            first_geometry[name] = sha(geometry)
        elif sha(geometry) != first_geometry[name]:
            raise RuntimeError("Campaign geometry differs from principal")
        add(rows, stem + ".rrgeom", geometry)
        material, refs = rebase_material((cooked / "model.rrmaterial").read_bytes(),
                                         source_folder, destination_folder)
        if name not in first_material:
            first_material[name] = sha(material)
        elif sha(material) != first_material[name]:
            raise RuntimeError("Campaign material differs from principal")
        add(rows, stem + ".rrmaterial", material)
        for leaf, member in refs.items():
            value = (cooked / leaf).read_bytes()
            if member in first_texture:
                if sha(value) != first_texture[member]:
                    raise RuntimeError("Shared Castle texture differs")
            else:
                first_texture[member] = sha(value)
                add(rows, member, value)
        old_rgo = old_path.with_suffix(".rgo")
        baseline_rgo = FINAL["members"][stem + ".rgo"]["sha256"]
        if sha(old_rgo.read_bytes()) != baseline_rgo:
            raise RuntimeError("Existing native RGO drift")
        model_proofs.append({"model": stem, "fresh_cooked_model": str(cooked / "model.rgm"),
                             "fresh_cooked_geometry_sha256": sha(geometry),
                             "original_native_owner": str(donor_path),
                             "retained_native_rgo_sha256": baseline_rgo,
                             "retained_markers": marker,
                             "damage_transform": damage, "ruin_transform": ruins,
                             "final_selector_table": selector_table(raw),
                             "material_descriptors": ["object", "object_collection"],
                             "texture_members": sorted(refs.values())})
    if len({r["member"] for r in rows}) != len(rows):
        raise RuntimeError("Duplicate target member")
    receipt = {"schema": "ccp-061-castle-object-pbr-payload/v1",
               "status": "fresh_native_object_cook_rebased_offline_not_native_render_tested",
               "baseline_060_sha256": FINAL["candidate_sha256"],
               "native_cook_archive": str(CFG["external_root"] + "/staging/release_061/castle-object-r1/library/Mods/cc061castle/dist/cc061castle.sga"),
               "models": model_proofs, "payloads": rows,
               "existing_native_rgo_unchanged": True,
               "active_gameplay_and_stamps_unchanged": True,
               "native_appearance_and_repair": "pending imported fresh match",
               "player_colour_limit": "Native object PBR route may not reproduce full dynamic owner-colour behaviour; test two players."}
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("CASTLE_OBJECT_PAYLOAD_READY", len(rows), OUT / "receipt.json")


if __name__ == "__main__":
    main()
