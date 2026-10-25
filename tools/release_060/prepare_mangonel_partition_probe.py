"""Second, isolated native probe: all 14 observed bones in skeletal LOD3."""
from __future__ import annotations

import json
from pathlib import Path

from common import OUT, STAGING, guard, owned, read, sha, write
import prepare_mangonel_manual_geometry as original


def main():
    guard()
    base = OUT / "qualification/nonhumanoid-route-preflight/mangonel/partition-probe"
    rig, probe = base / "all14-lod3-diagnostic.rig", base / "rig-probe.json"
    for p in (rig, probe):
        owned(p)
        if p.exists(): raise FileExistsError("Preserve prior partition probe")
    old = original.RIG.read_text(encoding="utf-8")
    if "[PARTITION START]" in old or not old.endswith("[END]\n"):
        raise RuntimeError("Original 14-bone minimal candidate changed")
    names = old.split("[BONES START]\n", 1)[1].split("\n[END]", 1)[0].splitlines()
    if len(names) != 14 or names[0] != "bone_root" or names[-1] != "bone_crank_base":
        raise RuntimeError("Actual mangonel bone order drift")
    candidate = old + "\n[PARTITION START]\nfullbody_lod3 bone_root bone_crank_base\n[END]\n"
    rig.parent.mkdir(parents=True, exist_ok=True)
    rig.write_text(candidate, encoding="utf-8")
    source_probe = read(original.RIG_PROBE)
    source_probe["schema"] = "ccp-060-mangonel-all14-lod3-partition-probe/v1"
    source_probe["status"] = "diagnostic_partition_candidate_not_stock_partition_proof"
    source_probe["minimal_candidate_sha256"] = sha(rig)
    source_probe["partition_candidate"] = "fullbody_lod3 bone_root bone_crank_base"
    write(probe, source_probe)
    original.LIBRARY = STAGING / "smp"
    original.PROJECT = original.LIBRARY / "Mods/s60m"
    original.SCAFFOLD = original.PROJECT / "project/source"
    original.BODY = original.SCAFFOLD / original.BODY_REL
    original.LOG = base / "create.log"
    original.RECEIPT = base / "prepare.json"
    original.RIG = rig
    original.RIG_PROBE = probe
    return original.main()


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
