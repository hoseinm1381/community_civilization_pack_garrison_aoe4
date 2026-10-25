"""Stage only Garden private identities and Vietnamese actor references."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
from garrison_shared import rgd

EXT = Path(CFG["external_root"])
OUT = EXT / "staging/release_070/integration/garden-binding-draft"
CONTRACT = ROOT / "output/release_070/integration/native-contract/contract.json"
IDENTITY = ROOT / "output/release_070/integration/garden-identities-v1/receipt.json"
OFFICIAL = ROOT / "output/release_070/integration/native-contract/official-cache/official"
BASE = ROOT / "output/release_070/monk/readback/after"
GUID32 = CFG["project_guid"].replace("-", "")


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(relative: str, raw: bytes) -> Path:
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return target


def main() -> None:
    if OUT.exists():
        raise FileExistsError("Preserve prior Garden draft")
    contract = json.loads(CONTRACT.read_text())
    identity = json.loads(IDENTITY.read_text())
    if identity["contract_sha256"] != sha(CONTRACT):
        raise RuntimeError("Garden identity no longer matches native contract")
    garden = next(a for a in contract["actors"] if a["family"] == "garden")
    refs = garden["references"]
    stage = []
    for ref, generated in zip(refs, identity["derived"]):
        if ref["member"] != generated["source"]:
            raise RuntimeError("Derived identity order mismatch")
        allocated = ROOT / "output/release_070/integration/garden-identities-v1/readback" / generated["generated_member"]
        pbgids = {n.value for _, n in rgd.flatten(rgd.read(allocated.read_bytes()).nodes)
                  if n.key == "pbgid"}
        if len(pbgids) != 1:
            raise RuntimeError("Allocated identity lacks unique PBG ID")
        pbgid = next(iter(pbgids))
        source_ref = ref["member"].removeprefix("attrib/").removesuffix(".rgd").replace("/", "\\")
        name = generated["name"]
        doc = ET.Element("instance", version="2", description="Private 0.7.0 Garden visual identity",
                         template=r"attachments\attachment_lists")
        ET.SubElement(doc, "uniqueid", name="pbgid", value=str(pbgid))
        ET.SubElement(doc, "instance_reference", name="parent_pbg", value=source_ref)
        ET.indent(doc, space="\t")
        xml_bytes = ET.tostring(doc, encoding="utf-8", xml_declaration=True) + b"\n"
        xml_path = write("assets/attrib/instances/attachments/attachment_lists/vietnam/release_070/" + name + ".xml", xml_bytes)
        official = OFFICIAL / ref["member"]
        if sha(official) != ref["official_sha256"]:
            raise RuntimeError("Official list changed")
        base = rgd.read(official.read_bytes())
        clone = copy.deepcopy(base)
        field = rgd.find(clone.nodes, "default/pbgid")
        field.value = pbgid
        reverted = copy.deepcopy(clone)
        rgd.find(reverted.nodes, "default/pbgid").value = rgd.find(base.nodes, "default/pbgid").value
        if rgd.write(reverted) != official.read_bytes():
            raise RuntimeError("Private list altered non-identity fields")
        compiled = write("payload/attrib/attachments/attachment_lists/vietnam/release_070/" + name + ".rgd", rgd.write(clone))
        stage.append({"name": name, "pbgid": pbgid, "source": ref["member"],
                      "source_xml": str(xml_path), "source_xml_sha256": sha(xml_path),
                      "compiled": str(compiled), "compiled_sha256": sha(compiled),
                      "status": "identity_only_stock_visual_still_selected"})
    source = ROOT / "assets/attrib/instances/ebps/vietnam/vn_building_landmark_age3_imperial_garden_vit.xml"
    original = source.read_bytes()
    actor = original.decode("utf-8-sig")
    for ref, generated in zip(refs, identity["derived"]):
        before = ref["reference"]
        after = "attachments\\attachment_lists\\vietnam\\release_070\\" + generated["name"]
        pattern = r'(<instance_reference name="attachments" value=")' + re.escape(before) + r'("[^>]*/>)'
        actor, count = re.subn(pattern, lambda m: m[1] + after + f'" mod="{GUID32}"' + m[2][1:], actor)
        if count != 1:
            raise RuntimeError(f"Expected one Garden source reference to {before}, got {count}")
    actor_path = write("assets/attrib/instances/ebps/vietnam/" + source.name, actor.encode("utf-8"))
    receipt = {"schema": "ccp-070-garden-binding-draft/v1", "status": "staged_not_active",
               "baseline_sga_sha256": contract["baseline_sga_sha256"],
               "actor_source_before_sha256": sha(source), "actor_source_after_sha256": sha(actor_path),
               "actor_source": str(actor_path), "identities": stage,
               "limits": "Art model/stamp payload and actor native compile remain pending. No active source or final archive modified."}
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"), "identities": len(stage)}))


if __name__ == "__main__":
    main()
