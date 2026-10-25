"""Read-only inventory of the exact four stock model lifecycle owners."""
from __future__ import annotations

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
sys.path.insert(0, str(ROOT / "tools/release_040"))
from garrison_shared import relic_chunky as rc
from lifecycle import _conditions, _selector

OWNERS = ROOT / "output/release_070/integration/native-owner/owners.json"
OUT = ROOT / "output/release_070/integration/native-lifecycle"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    owners = json.loads(OWNERS.read_text())["owners"]
    result = {"schema": "ccp-070-native-lifecycle-audit/v1", "owners": []}
    for owner in owners:
        rgm_info = owner["native_media"][".rgm"]
        rgo_info = owner["native_media"][".rgo"]
        rgm_path, rgo_path = Path(rgm_info["path"]), Path(rgo_info["path"])
        assert sha(rgm_path) == rgm_info["sha256"]
        assert sha(rgo_path) == rgo_info["sha256"]
        model = next(c for c in rc.parse(rgm_path.read_bytes()).roots if c.tag == b"MODL")
        bp = next(c for c in model.children if c.tag == b"MSBP")
        sets = [c for c in bp.children if c.tag == b"MSD " and len(c.payload) > 4]
        predicates = [c for c in bp.children if c.tag == b"CNBP"]
        assert len(sets) == len(predicates)
        pairs = zip(sets, predicates)
        selectors = []
        for geometry, predicate in pairs:
            name, parts = _selector(geometry)
            states = [p[-1] for p in _conditions(predicate) if p[-2] == "life_cycle_state"]
            selectors.append({"name": name, "parts": parts, "states": states})
        doc = rc.load(rgo_path)
        actions = []
        for behavior in rc.walk(doc.roots):
            if behavior.tag != b"BVBP":
                continue
            payloads = [c.payload for c in behavior.children if c.tag == b"BBPD"]
            tokens = []
            for payload in payloads:
                for candidate in (b"ruins", b"repair", b"collapse", b"damage", b"construct", b"death"):
                    if candidate in payload.lower():
                        tokens.append(candidate.decode())
            actions.append({"name": behavior.decoded_name, "payload_sha256":
                            [hashlib.sha256(p).hexdigest() for p in payloads],
                            "lifecycle_tokens": sorted(set(tokens))})
        dtbp = [c for c in rc.walk(doc.roots) if c.tag == b"DTBP"]
        result["owners"].append({"family": owner["family"],
               "rgm_sha256": rgm_info["sha256"], "rgo_sha256": rgo_info["sha256"],
               "native_selectors": selectors, "rgo_behavior_actions": actions,
               "rgo_dtbp": [{"name": c.decoded_name, "payload_hex": c.payload.hex()}
                            for c in dtbp]})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"families": [r["family"] for r in result["owners"]],
                      "file": str(OUT / "audit.json")}))


if __name__ == "__main__":
    main()
