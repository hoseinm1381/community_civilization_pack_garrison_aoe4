"""Static native-reference and exact-difference proof for Garden payload v2."""
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
sys.path.insert(0, str(ROOT / "tools/release_061"))
from garrison_shared import relic_chunky as rc, rgd
from assemble_castle_object_061 import selector_table

BASE = ROOT / "output/release_070/integration"
PAYLOAD = BASE / "garden-payload-v2"
REF = BASE / "garden-reference-v1"
COOK = BASE / "garden-cook-v1"
CONTRACT = BASE / "native-contract/contract.json"
OFFICIAL = BASE / "native-contract/official-cache/official"
OUT = BASE / "garden-qualification-v2"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def leaf_map(path: Path):
    return dict(rgd.flatten(rgd.read(path.read_bytes()).nodes))


def main(cook_label: str, payload_label: str, qualification_label: str) -> None:
    global COOK, PAYLOAD, OUT
    if any(not x.replace("-", "").isalnum() for x in
           (cook_label, payload_label, qualification_label)):
        raise ValueError("Invalid immutable Garden label")
    COOK = BASE / ("garden-" + cook_label)
    PAYLOAD = BASE / ("garden-" + payload_label)
    OUT = BASE / ("garden-" + qualification_label)
    if OUT.exists():
        raise FileExistsError("Preserve prior Garden qualification")
    payload = json.loads((PAYLOAD / "receipt.json").read_text())
    reference = json.loads((REF / "receipt.json").read_text())
    cook = json.loads((COOK / "receipt.json").read_text())
    contract = json.loads(CONTRACT.read_text())
    actor = next(a for a in contract["actors"] if a["family"] == "garden")
    rows = {r["member"]: r for r in payload["payloads"]}
    assert set(rows) == set(payload["allowlist"]) and len(rows) == 11
    assert all(sha(Path(r["file"])) == r["sha256"] for r in rows.values())
    assert payload["baseline_sga_sha256"] == contract["baseline_sga_sha256"]
    model = "art/scenario/cc070/garden/model"
    assert sha(Path(rows[model + ".rgo"]["file"])) == payload["native_owner_rgo_sha256"]
    assert sha(Path(rows[model + ".rrgeom"]["file"])) == cook["media"]["model.rrgeom"]
    table = selector_table(Path(rows[model + ".rgm"]["file"]).read_bytes())
    assert json.loads(json.dumps(table)) == payload["selector_table"]
    def selected(state):
        return sorted({part for _, parts, predicates in table for part in parts
                       if (2,0,1,"life_cycle_state",state) in predicates})
    prefix = "garrison_part_"
    expected = {"healthy": [0,1,4,5,6], "damage_1": [0,1,4,5,6],
                "damage_2": [0,1,4,5,6], "damage_3": [0,3],
                "damage_4": [0,3], "damage_5": [0,3], "ruins": [2]}
    for state, indices in expected.items():
        assert selected(state) == [prefix + f"{i:04}" for i in indices], state
    for index in range(0,100,5):
        assert selected(f"construct_{index:02}") == [prefix + f"{i:04}" for i in
            ([0] if index < 20 else [0,1,4,5,6])]
    assert selected("preview") == selected("targeting") == selected("healthy")
    roots = rc.parse(Path(rows[model + ".rrmaterial"]["file"]).read_bytes()).roots
    descriptors = [(x.decoded_name, x.tag.decode()) for x in roots if x.tag == b"GMat"]
    frozen = json.loads((COOK / "input-freeze.json").read_text())
    material_name = frozen["building"]["material_name"].lower()
    assert {n for n, _ in descriptors} == {
        material_name, material_name + "_collection"}
    # Every private material texture member is present in the exact payload allowlist.
    texture_members = [m for m in rows if m.endswith(".rrtex")]
    assert len(texture_members) == 3
    actor_member = "attrib/ebps/vietnam/vn_building_landmark_age3_imperial_garden_vit.rgd"
    native_actor = Path(reference["readback"][actor_member]["file"])
    private_actor = Path(rows[actor_member]["file"])
    assert sha(native_actor) == sha(private_actor)
    actor_paths = {p["path"] for p in payload["actor_attachment_fields"]}
    assert len(actor_paths) == 2
    leaves = leaf_map(private_actor)
    assert all(leaves[p].value == row["after"] for row in payload["actor_attachment_fields"] for p in [row["path"]])
    identity = []
    for name, donor in (("vn070_garden_main", actor["references"][0]),
                        ("vn070_garden_outskirts", actor["references"][1])):
        member = f"attrib/attachments/attachment_lists/vietnam/release_070/{name}.rgd"
        native = Path(reference["readback"][member]["file"])
        private = Path(rows[member]["file"])
        n, p = leaf_map(native), leaf_map(private)
        assert n["default/pbgid"].value == p["default/pbgid"].value
        assert n["default/parent_pbg/$PBGNAME"].value == donor["reference"].rsplit("\\",1)[-1]
        assert n["default/parent_pbg/$PBGMAP"].value == "attachments\\attachment_lists"
        official = OFFICIAL / donor["member"]
        restored = copy.deepcopy(rgd.read(private.read_bytes()))
        rgd.find(restored.nodes,"default/pbgid").value = leaf_map(official)["default/pbgid"].value
        if name.endswith("main"):
            for _, node in rgd.flatten(restored.nodes):
                if node.key == "stamp" and node.value == "art\\stamps\\cc070\\garden_main":
                    node.value = "art\\stamps\\civ_chinese\\chi_wonder_daming_palace"
        assert rgd.write(restored) == official.read_bytes(), name
        identity.append({"name": name, "native_compiled_identity_sha256": sha(native),
                         "final_private_sha256": sha(private),
                         "native_pbgid": n["default/pbgid"].value,
                         "full_official_donor_restoration_byte_identical": True})
    result = {"schema": "ccp-070-garden-private-payload-qualification/v1",
              "status": "passed_static_native_reference_runtime_unverified",
              "garden_cook_archive_sha256": cook["archive_sha256"],
              "garden_reference_archive_sha256": reference["archive_sha256"],
              "actor_native_compile_equals_private_payload": True,
              "private_list_donor_restoration_byte_identical": True,
              "native_rgo_sha256": payload["native_owner_rgo_sha256"],
              "model_selector_state_parts": expected,
              "texture_members": texture_members,
              "material_descriptors": descriptors,
              "identities": identity, "changed_resource_allowlist": payload["allowlist"],
              "limits": "Static cook/readback and compiled-reference proof; imported match appearance, player colour, construction, persistent ruins and repair remain untested."}
    OUT.mkdir(parents=True)
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"), "members": len(rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cook-label", default="cook-v1")
    parser.add_argument("--payload-label", default="payload-v2")
    parser.add_argument("--qualification-label", default="qualification-v2")
    options = parser.parse_args()
    main(options.cook_label, options.payload_label, options.qualification_label)
