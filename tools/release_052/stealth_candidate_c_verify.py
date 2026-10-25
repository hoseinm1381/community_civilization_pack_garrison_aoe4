"""Independently verify the diagnostic-C overlay and untouched controls."""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def named(root: ET.Element, name: str) -> list[ET.Element]:
    return [element for element in root.iter() if element.get("name") == name]


def main() -> None:
    cfg = configuration(ROOT)
    check_storage(ROOT, cfg)
    out = Path(cfg["external_root"]) / "output/release_052/stealth/diagnostic-c"
    receipt = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
    source = ROOT / "assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml"
    archer = ROOT / "assets/attrib/instances/abilities/vietnam/vn_activate_stealth_for_archer.xml"
    candidate = out / source.name
    original_bytes, candidate_bytes = source.read_bytes(), candidate.read_bytes()
    assert sha(original_bytes) == receipt["baseline"]["sha256"]
    assert sha(candidate_bytes) == receipt["overlay"]["sha256"]
    assert len(candidate_bytes) == receipt["overlay"]["bytes"]
    assert sha(archer.read_bytes()) == receipt["preserved_controls"]["archer"]["sha256"]
    assert sha(Path(receipt["preserved_controls"]["landmarks_scar"]["file"]).read_bytes()) == receipt["preserved_controls"]["landmarks_scar"]["sha256"]

    # Byte-exact reconstruction checks every character beyond the allowed values,
    # including IDs, requirement hierarchy, radius, timer and tree references.
    reconstructed = candidate_bytes
    for tag, name, previous, proposed in (
        ("bool", "disable_when_active", "True", "False"),
        ("float", "recharge_time", "6", "0"),
        ("bool", "can_queue_passive_ability", "True", "False"),
    ):
        old = f'<{tag} name="{name}" value="{previous}" />'.encode()
        new = f'<{tag} name="{name}" value="{proposed}" />'.encode()
        assert original_bytes.count(old) == 1
        assert candidate_bytes.count(new) == 1
        assert reconstructed.count(new) == 1
        reconstructed = reconstructed.replace(new, old, 1)
    assert reconstructed == original_bytes

    original, modified = ET.fromstring(original_bytes), ET.fromstring(candidate_bytes)
    for root in (original, modified):
        assert len(named(root, "outer_radius")) == 1
        assert named(root, "outer_radius")[0].get("value") == "33"
        assert len(named(root, "entity_tree")) == 1
        assert named(root, "entity_tree")[0].get("value") == "activate_stealth_mal"
        assert len(named(root, "activation")) == 1
        assert named(root, "activation")[0].get("value") == "always_on"
        durations = [node for node in root.iter("template_reference")
                     if any(child.get("name") == "id" and child.get("value") == "duration" for child in node)]
        assert len(durations) == 1
        assert [child.get("value") for child in durations[0] if child.get("name") == "value"] == ["10"]
    for analogue in receipt["official_analogues"]:
        data = Path(analogue["file"]).read_bytes()
        assert sha(data) == analogue["sha256"]
        root = ET.fromstring(data)
        bag = next(child for child in root if child.get("name") == "ability_bag")
        for field, value in (("activation", "always_on"), ("disable_when_active", "False"),
                             ("recharge_time", "0"), ("can_queue_passive_ability", "False")):
            found = named(bag, field)
            assert len(found) == 1 and found[0].get("value") == value
        found = named(bag, "entity_tree")
        assert len(found) == 1 and found[0].get("value") == analogue["entity_tree"]
        assert analogue["entity_tree"]
    assert len(receipt["official_analogues"]) == 3
    assert receipt["status"] == "native_test_pending"
    print("DIAGNOSTIC_C_VERIFIED", sha(candidate_bytes), "three-fields-only", "archer-preserved")


if __name__ == "__main__":
    main()
