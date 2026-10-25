"""Verify all Foundry, University and Wonder normal/campaign private refs."""
from __future__ import annotations

import copy
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
from garrison_shared import rgd

BASE = ROOT / "output/release_070/integration"
REF = BASE / "remaining-reference-v1/receipt.json"
DRAFT = Path(CFG["external_root"]) / "staging/release_070/integration/remaining-binding-draft/receipt.json"
OFFICIAL = BASE / "native-contract/official-cache/official"
MONK = ROOT / "output/release_070/monk/readback/after"
OUT = BASE / "remaining-binding-qualification-v1"
GUID32 = CFG["project_guid"].replace("-", "")


def sha(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def leaves(doc):
    return dict(rgd.flatten(doc.nodes))


def main() -> None:
    if OUT.exists():
        raise FileExistsError("Preserve earlier remaining-binding proof")
    reference = json.loads(REF.read_text())
    draft = json.loads(DRAFT.read_text())
    assert reference["status"] == "content_editor_compile_and_readback_passed_runtime_unverified"
    assert len(draft["actors"]) == 3 and len(draft["identities"]) == 7
    identities = []
    for row in draft["identities"]:
        member = f"attrib/attachments/attachment_lists/vietnam/release_070/{row['name']}.rgd"
        native = rgd.read(Path(reference["readback"][member]["file"]).read_bytes())
        private = rgd.read(Path(row["compiled"]).read_bytes())
        assert leaves(native)["default/pbgid"].value == leaves(private)["default/pbgid"].value == row["pbgid"]
        expected_parent = row["donor"].removeprefix("attrib/").removesuffix(".rgd").replace("/", "\\")
        assert leaves(native)["default/parent_pbg/$PBGNAME"].value == expected_parent.rsplit("\\",1)[-1]
        assert leaves(native)["default/parent_pbg/$PBGMAP"].value == "attachments\\attachment_lists"
        official = OFFICIAL / row["donor"]
        restored = copy.deepcopy(private)
        rgd.find(restored.nodes,"default/pbgid").value = leaves(rgd.read(official.read_bytes()))["default/pbgid"].value
        assert rgd.write(restored) == official.read_bytes()
        identities.append({"name": row["name"], "pbgid": row["pbgid"],
                           "native_compiled_sha256": reference["readback"][member]["sha256"],
                           "full_donor_restoration_byte_identical": True})
    actors = []
    for row in draft["actors"]:
        actor = row["actor"]
        member = f"attrib/ebps/vietnam/{actor}.rgd"
        accepted = (MONK / member).read_bytes()
        compiled = Path(reference["readback"][member]["file"]).read_bytes()
        before, after = rgd.read(accepted), rgd.read(compiled)
        left, right = leaves(before), leaves(after)
        assert left.keys() == right.keys()
        expected = {x["donor"].rsplit("\\",1)[-1]: x["private"].rsplit("\\",1)[-1]
                    for x in row["changes"]}
        changed = []
        reverted = copy.deepcopy(after)
        for path, old in left.items():
            new = right[path]
            if old.kind in ("List", "List2") or old.value == new.value:
                continue
            assert old.key == "$PBGNAME" and "/attachments/" in path
            assert old.value in expected
            assert new.value == GUID32 + ":" + expected[old.value]
            rgd.find(reverted.nodes,path).value = old.value
            changed.append({"path": path, "before": old.value, "after": new.value})
        assert rgd.write(reverted) == accepted
        assert len(changed) == 4 and {x["path"].split("/",1)[0] for x in changed} == {"default", "campaign"}
        assert {x["before"] for x in changed} == set(expected)
        actors.append({"family": row["family"], "actor": actor,
                       "baseline_sha256": sha(MONK / member), "compiled_sha256": sha(Path(reference["readback"][member]["file"])),
                       "changes": changed, "all_other_compiled_bytes_identical": True})
    result = {"schema": "ccp-070-remaining-private-bindings-qualification/v1",
              "status": "passed_isolated_native_reference_runtime_unverified",
              "reference_archive_sha256": reference["archive_sha256"],
              "actors": actors, "identities": identities,
              "active_source_modified": False,
              "limit": "Private art model/stamp payload and final package pending."}
    OUT.mkdir(parents=True)
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"), "actors": len(actors),
                      "identities": len(identities)}))


if __name__ == "__main__":
    main()
