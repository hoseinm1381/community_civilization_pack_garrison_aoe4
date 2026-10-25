"""Record Garrison's rig_text limit and a donor-derived minimal mangonel .rig.

The minimal file is a diagnostic candidate only. Native burner acceptance is
unknown until an actual stock-rig FBX source and fresh isolated cook exist.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import CFG, OUT, guard, owned, read, sha, write

CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
DEST = OUT / "qualification/nonhumanoid-route-preflight/20261018-rig-text-probe.json"
RIG = OUT / "qualification/nonhumanoid-route-preflight/minimal-mangonel-14bone-diagnostic.rig"
EXTENSION = Path(CFG["garrison_extension"])
PYTHON = Path(CFG["blender_python"])

CODE = """import json,sys
sys.path.insert(0,sys.argv[1])
from garrison_shared import unit_model_export as module
with open(sys.argv[2],encoding='utf-8') as stream:
    document=json.load(stream)
print(module.rig_text(document['skeleton']['bones']))
"""


def main():
    guard()
    for path in (DEST, RIG):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier rig-source probe: {path}")
    contract = read(CONTRACT)
    if contract["status"] != "three_donors_pinned_generic_export_possible_manual_native_source_unproved":
        raise RuntimeError("Mounted/siege stock source contract changed")
    if not PYTHON.is_file() or not (EXTENSION / "garrison_shared.cp313-win_amd64.pyd").is_file():
        raise RuntimeError("Installed Blender Python or Garrison core changed")
    probes = {}
    for pilot, row in contract["donors"].items():
        manifest = Path(row["donor_manifest"])
        if sha(manifest) != row["donor_manifest_sha256"]:
            raise RuntimeError(f"{pilot} donor manifest changed")
        result = subprocess.run([str(PYTHON), "-c", CODE, str(EXTENSION), str(manifest)],
                                capture_output=True, text=True, errors="replace", timeout=30)
        probes[pilot] = {"exit_code": result.returncode,
                         "stdout": result.stdout[-3000:], "stderr": result.stderr[-3000:]}
        if result.returncode == 0 or "only the stock civilian skeleton's partitions are known" not in result.stderr:
            raise RuntimeError(f"Unexpected installed rig_text outcome for {pilot}")
    mangonel = read(Path(contract["donors"]["siege_mangonel3"]["donor_manifest"]))
    bones = mangonel["skeleton"]["bones"]
    names = [bone["name"] for bone in bones]
    if len(names) != 14 or len(set(names)) != 14 or [bone["index"] for bone in bones] != list(range(14)):
        raise RuntimeError("Mangonel native bone ordering changed")
    text = "[HAVOK SKELETON DEFINITION FILE]\n\n[BONES START]\n" + "\n".join(names) + "\n[END]\n"
    RIG.write_text(text, encoding="utf-8")
    report = {"schema": "ccp-060-nonhumanoid-rig-source-probe/v1",
              "status": "installed_rig_text_rejects_non_civilian_skeletons_minimal_14bone_candidate_unburned",
              "contract": str(CONTRACT), "contract_sha256": sha(CONTRACT),
              "installed_blender_python": str(PYTHON),
              "installed_unit_model_export_sha256": sha(EXTENSION / "garrison_shared.cp313-win_amd64.pyd"),
              "rig_text_probes": probes,
              "minimal_candidate": str(RIG), "minimal_candidate_sha256": sha(RIG),
              "minimal_candidate_exact_donor_bone_names": names,
              "minimal_candidate_has_partitions": False,
              "scope": "diagnostic native-burner input candidate only; no FBX, cook, RRGeom or stock palette comparison exists",
              "next_gate": "after exact 14-bone/six-group mangonel FBX export, isolate a new short manual Structure-material source project and cook under shared native byte lock; require full stock two-palette/six-group readback before pairing geometry only"}
    write(DEST, report)
    return {"status": report["status"], "receipt": str(DEST),
            "minimal_rig_sha256": report["minimal_candidate_sha256"]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
