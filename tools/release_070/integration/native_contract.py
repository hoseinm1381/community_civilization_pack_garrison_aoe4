"""Inventory exact 0.7.0 Vietnamese visual consumers and stock stamp owners.

Read-only against project/official assets. Writes only release_070 integration evidence.
"""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
sys.path.insert(0, str(ROOT / "tools/release_010"))
import integration as native
from garrison_shared import rgd

OUT = ROOT / "output/release_070/integration/native-contract"
native.CACHEWORK = OUT / "official-cache"
ACTORS = {
    "garden": "vn_building_landmark_age3_imperial_garden_vit",
    "foundry": "vn_building_landmark_age3_trung_foundaries_vit",
    "university": "vn_building_tech_university_control_chi",
    "wonder": "vn_building_wonder_age4_forbidden_control_chi",
}


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    if (OUT / "contract.json").exists():
        raise FileExistsError("Preserve prior native contract")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for family, actor in ACTORS.items():
        source = ROOT / "assets/attrib/instances/ebps/vietnam" / (actor + ".xml")
        tree = ET.parse(source).getroot()
        refs = []
        for node in tree.iter("instance_reference"):
            if node.get("name") != "attachments":
                continue
            value = node.get("value", "")
            if not value.startswith("attachments\\attachment_lists\\"):
                continue
            member = "attrib/" + value.replace("\\", "/") + ".rgd"
            if any(r["member"] == member for r in refs):
                continue
            official = native.stock(member)
            attachment = rgd.read(official.read_bytes())
            stamps = []
            for field, leaf in rgd.flatten(attachment.nodes):
                if leaf.key != "stamp" or not leaf.value:
                    continue
                stamp_member = leaf.value.replace("\\", "/") + ".bin"
                stamp_file = native.stock(stamp_member)
                visuals = native.active_visuals(native.NativeTree(stamp_file))
                stamps.append({"field": field, "member": stamp_member,
                               "sha256": sha(stamp_file), "visuals": visuals})
            refs.append({"reference": value, "member": member,
                         "official_sha256": sha(official), "stamps": stamps})
        rows.append({"family": family, "actor": actor,
                     "source": str(source), "source_sha256": sha(source),
                     "references": refs})
    result = {"schema": "ccp-070-native-visual-contract/v1",
              "baseline_sga_sha256": "9e797ab14faf293ec1570c6dc38f1e7cab2ffda9df7d5078b7a0ecf564233c85",
              "status": "read_only_official_and_private_source_inventory",
              "actors": rows,
              "policy": "Private Vietnamese attachment lists and stamps; replace only approved main visual model paths. Preserve native markers, actors, nonvisual stamp nodes, outskirts markers and all previous model resources.",
              "runtime": "unverified"}
    (OUT / "contract.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"actors": len(rows), "references": sum(len(r["references"]) for r in rows),
                      "contract": str(OUT / "contract.json")}))


if __name__ == "__main__":
    main()
