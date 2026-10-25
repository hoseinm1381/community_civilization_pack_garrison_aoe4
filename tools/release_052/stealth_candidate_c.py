"""Prepare a one-XML, three-field villager-stealth diagnostic overlay.

This is an isolated native-test candidate, not a claim of persistent stealth.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration  # noqa: E402

CFG = configuration(ROOT)
OUT = Path(CFG["external_root"]) / "output/release_052/stealth/diagnostic-c"
SOURCE = ROOT / "assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml"
ARCHER = ROOT / "assets/attrib/instances/abilities/vietnam/vn_activate_stealth_for_archer.xml"
SCAR = ROOT / "assets/scar/vietnam/landmarks.scar"
OFFICIAL = Path(CFG["external_root"]) / "output/release_052/stealth/official/reference-abilities/instances/abilities/always_on_abilities"
ANALOGUES = (
    "mongol/kurultai_khan_aura_mon.xml",
    "byzantine/winery_villager_buff_byz.xml",
    "ayyubid_cmp/medical_centers_ayy.xml",
)
BASELINE_SHA = "329b5fe1cec68fb415f21d8f6b48b75f036f53c3ad67691e093b96139e4f2901"
ARCHER_SHA = "c0ee10a5c456d069d0c1d03992ee1d34d8b2cae256b4ec820d47eb6ab6894d99"
CHANGES = (
    (b'<bool name="disable_when_active" value="True" />', b'<bool name="disable_when_active" value="False" />'),
    (b'<float name="recharge_time" value="6" />', b'<float name="recharge_time" value="0" />'),
    (b'<bool name="can_queue_passive_ability" value="True" />', b'<bool name="can_queue_passive_ability" value="False" />'),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_value(root: ET.Element, name: str) -> str:
    nodes = [node for node in root.iter() if node.get("name") == name]
    assert len(nodes) == 1, (name, len(nodes))
    return nodes[0].get("value") or ""


def main() -> None:
    check_storage(ROOT, CFG)
    original = SOURCE.read_bytes()
    assert digest(original) == BASELINE_SHA, "Villager source changed; recapture the baseline before preparing this fixture"
    assert digest(ARCHER.read_bytes()) == ARCHER_SHA, "Working archer control changed"
    candidate = original
    for before, after in CHANGES:
        assert candidate.count(before) == 1, before
        assert candidate.count(after) == 0, after
        candidate = candidate.replace(before, after, 1)
    restored = candidate
    for before, after in CHANGES:
        assert restored.count(after) == 1, after
        restored = restored.replace(after, before, 1)
    assert restored == original, "Unexpected change outside the three allowed fields"

    before_root = ET.fromstring(original)
    after_root = ET.fromstring(candidate)
    expected = {
        "disable_when_active": ("True", "False"),
        "recharge_time": ("6", "0"),
        "can_queue_passive_ability": ("True", "False"),
    }
    for field, (old, new) in expected.items():
        assert unique_value(before_root, field) == old
        assert unique_value(after_root, field) == new
    for field, expected_value in (
        ("activation", "always_on"),
        ("entity_tree", "activate_stealth_mal"),
        ("outer_radius", "33"),
    ):
        assert unique_value(before_root, field) == expected_value, field
        assert unique_value(after_root, field) == expected_value, field
    for root in (before_root, after_root):
        durations = [node for node in root.iter("template_reference")
                     if any(child.get("name") == "id" and child.get("value") == "duration" for child in node)]
        assert len(durations) == 1
        assert [child.get("value") for child in durations[0] if child.get("name") == "value"] == ["10"]

    analogues = []
    for relative in ANALOGUES:
        path = OFFICIAL / relative
        data = path.read_bytes()
        root = ET.fromstring(data)
        bag = next(node for node in root if node.get("name") == "ability_bag")
        for field, value in (
            ("activation", "always_on"),
            ("disable_when_active", "False"),
            ("recharge_time", "0"),
            ("can_queue_passive_ability", "False"),
        ):
            assert unique_value(bag, field) == value, (relative, field)
        assert unique_value(bag, "entity_tree"), relative
        analogues.append({"file": str(path), "sha256": digest(data),
                          "entity_tree": unique_value(bag, "entity_tree")})

    diff = "".join(difflib.unified_diff(
        [line + "\n" for line in original.decode("utf-8").splitlines()],
        [line + "\n" for line in candidate.decode("utf-8").splitlines()],
        fromfile="active/vn_activate_stealth_forvills_vit.xml",
        tofile="diagnostic-c/vn_activate_stealth_forvills_vit.xml",
    ))
    removed = [line for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    added = [line for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    assert len(removed) == len(added) == 3, "Diff exceeded the three-field allowlist"

    OUT.mkdir(parents=True, exist_ok=True)
    overlay = OUT / SOURCE.name
    overlay.write_bytes(candidate)
    (OUT / "source.diff").write_text(diff, encoding="utf-8")
    receipt = {
        "schema": "ccp.release052.stealth-diagnostic-c/v1",
        "status": "native_test_pending",
        "scope": "One villager ability XML; only three existing passive scheduling fields change",
        "overlay": {"file": str(overlay), "sha256": digest(candidate), "bytes": len(candidate)},
        "baseline": {"file": str(SOURCE), "sha256": BASELINE_SHA},
        "preserved_controls": {
            "archer": {"file": str(ARCHER), "sha256": ARCHER_SHA},
            "landmarks_scar": {"file": str(SCAR), "sha256": digest(SCAR.read_bytes())},
            "native_entity_tree": "activate_stealth_mal", "native_duration_seconds": 10,
            "required_near_entity_outer_radius": 33,
        },
        "changes": {key: {"before": old, "after": new} for key, (old, new) in expected.items()},
        "official_analogues": analogues,
        "uncertainty": "The retained native graph has a ten-second timer and explicit SetStealthAllowed(false); these scheduling fields may reduce rapid requeue flicker but cannot be claimed to provide persistent stealth without a native match test.",
        "native_acceptance": [
            "Stationary villager within 33 m of HQ for at least 45 seconds, inspect continuous camouflage and 10-second boundaries",
            "Exit and reenter 33 m; verify loss and reacquisition without rapid flicker",
            "Destroy last HQ; verify removal. With multiple HQs, verify union of coverage",
            "Test combat, enemy reveal/detection, and reentry after those states",
            "Verify activated archer stealth remains unchanged",
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("DIAGNOSTIC_C_PREPARED", digest(candidate), len(candidate), len(analogues))


if __name__ == "__main__":
    main()
