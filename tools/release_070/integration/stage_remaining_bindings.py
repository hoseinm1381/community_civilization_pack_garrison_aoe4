"""Stage seven private lists and three Vietnamese actor source overlays only."""
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
OUT = EXT / "staging/release_070/integration/remaining-binding-draft"
BASE = ROOT / "output/release_070/integration"
CONTRACT = BASE / "native-contract/contract.json"
IDENTITY = BASE / "remaining-identities-v1/receipt.json"
OFFICIAL = BASE / "native-contract/official-cache/official"
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
        raise FileExistsError("Preserve prior private binding draft")
    contract = json.loads(CONTRACT.read_text())
    cooked = json.loads(IDENTITY.read_text())
    assert cooked["contract_sha256"] == sha(CONTRACT)
    staged, actors = [], []
    for family in ("foundry", "university", "wonder"):
        actor = next(a for a in contract["actors"] if a["family"] == family)
        refs = actor["references"]
        derived = [x for x in cooked["derived"] if x["family"] == family]
        assert len(refs) == len(derived)
        source = ROOT / "assets/attrib/instances/ebps/vietnam" / (actor["actor"] + ".xml")
        original = source.read_bytes()
        modified = original.decode("utf-8-sig")
        changes = []
        for ref, gen in zip(refs, derived):
            assert ref["member"] == gen["source"]
            allocated = BASE / "remaining-identities-v1/readback" / gen["generated_member"]
            pbgids = {n.value for _, n in rgd.flatten(rgd.read(allocated.read_bytes()).nodes)
                      if n.key == "pbgid"}
            assert len(pbgids) == 1
            pbgid = next(iter(pbgids))
            donor = ref["member"].removeprefix("attrib/").removesuffix(".rgd").replace("/", "\\")
            name = gen["name"]
            doc = ET.Element("instance", version="2",
                             description=f"Private 0.7.0 {family} visual identity",
                             template=r"attachments\attachment_lists")
            ET.SubElement(doc, "uniqueid", name="pbgid", value=str(pbgid))
            ET.SubElement(doc, "instance_reference", name="parent_pbg", value=donor)
            ET.indent(doc, space="\t")
            xml = ET.tostring(doc, encoding="utf-8", xml_declaration=True) + b"\n"
            identity_source = write("assets/attrib/instances/attachments/attachment_lists/vietnam/release_070/" + name + ".xml", xml)
            official = OFFICIAL / ref["member"]
            assert sha(official) == ref["official_sha256"]
            private = copy.deepcopy(rgd.read(official.read_bytes()))
            rgd.find(private.nodes, "default/pbgid").value = pbgid
            restored = copy.deepcopy(private)
            rgd.find(restored.nodes, "default/pbgid").value = rgd.find(rgd.read(official.read_bytes()).nodes, "default/pbgid").value
            assert rgd.write(restored) == official.read_bytes()
            compiled = write("payload/attrib/attachments/attachment_lists/vietnam/release_070/" + name + ".rgd", rgd.write(private))
            staged.append({"family": family, "name": name, "pbgid": pbgid,
                           "donor": ref["member"], "source_xml": str(identity_source),
                           "source_xml_sha256": sha(identity_source),
                           "compiled": str(compiled), "compiled_sha256": sha(compiled)})
            before = ref["reference"]
            after = "attachments\\attachment_lists\\vietnam\\release_070\\" + name
            pattern = r'(<instance_reference name="attachments" value=")' + re.escape(before) + r'("[^>]*/>)'
            modified, count = re.subn(pattern, lambda m: m[1] + after + f'" mod="{GUID32}"' + m[2][1:], modified)
            if count not in (1, 2):
                raise RuntimeError(f"Unexpected {family} consumer count for {before}: {count}")
            changes.append({"donor": before, "private": after, "source_occurrences": count})
        actor_source = write("assets/attrib/instances/ebps/vietnam/" + source.name, modified.encode("utf-8"))
        ET.parse(actor_source)
        actors.append({"family": family, "actor": actor["actor"],
                       "source_before_sha256": sha(source), "source_after_sha256": sha(actor_source),
                       "source": str(actor_source), "changes": changes})
    receipt = {"schema": "ccp-070-remaining-binding-draft/v1", "status": "staged_not_active",
               "contract_sha256": sha(CONTRACT), "identity_receipt_sha256": sha(IDENTITY),
               "identities": staged, "actors": actors,
               "limit": "No art, private stamp or final compiled actor payload selected. Active source unchanged."}
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"), "identities": len(staged), "actors": len(actors)}))


if __name__ == "__main__":
    main()
