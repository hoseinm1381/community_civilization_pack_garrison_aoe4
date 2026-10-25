"""Freeze the exact 0.7.0 visual+monk allowlist for final package assembly."""
from __future__ import annotations

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
BASE = ROOT / "output/release_070/integration"
MONK = ROOT / "output/release_070/monk/verification.json"
FAMILIES = ("garden", "foundry", "university", "wonder")


def digest(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main(labels: dict[str, str], out_label: str) -> None:
    if any(not x.replace("-", "").isalnum() for x in (out_label, *labels.values())):
        raise ValueError("Invalid immutable label")
    out = BASE / f"combined-{out_label}"
    if out.exists():
        raise FileExistsError("Preserve previous combined manifest")
    baseline = json.loads((ROOT / "output/release_070/baseline/freeze.json").read_text())
    monk = json.loads(MONK.read_text())
    assert digest(Path(baseline["baseline_sga"])) == baseline["baseline_sga_sha256"]
    assert monk["baseline_sha256"] == baseline["baseline_sga_sha256"]
    assert monk["changed_members"] == ["scar/vietnam/prematch_precache.scar"]
    assert digest(Path(monk["candidate"])) == monk["candidate_sha256"]
    before = monk["member_hashes_before"]
    after = monk["member_hashes_after"]
    assert set(before) == set(after)
    assert {member for member in before if before[member] != after[member]} == set(monk["changed_members"])
    rows = [{"member": monk["changed_members"][0],
             "sha256": after[monk["changed_members"][0]]["sha256"],
             "bytes": after[monk["changed_members"][0]]["bytes"],
             "family": "monk_precache", "file": monk["overlay"]}]
    evidence = {"monk": {"receipt_sha256": digest(MONK),
                          "candidate_archive_sha256": monk["candidate_sha256"]}}
    for family in FAMILIES:
        label = labels[family]
        qualified_file = BASE / f"{family}-qualification-{label}/receipt.json"
        payload_file = BASE / f"{family}-payload-{label}/receipt.json"
        uv_file = BASE / f"{family}-uv-v1/receipt.json"
        qualified = json.loads(qualified_file.read_text())
        payload = json.loads(payload_file.read_text())
        uv = json.loads(uv_file.read_text())
        assert qualified["status"].startswith("passed_static_")
        assert payload["status"] == "offline_native_cook_grafted_runtime_unverified"
        assert uv["status"] == "passed_readback_uv_projection_runtime_unverified"
        assert uv["family"] == family and uv["native_coverage_vs_fbx_v_flipped"] >= 0.999
        assert sorted(payload["allowlist"]) == sorted(qualified["changed_resource_allowlist"])
        assert {r["member"] for r in payload["payloads"]} == set(payload["allowlist"])
        for row in payload["payloads"]:
            assert digest(Path(row["file"])) == row["sha256"]
            assert row["member"] not in {r["member"] for r in rows}
            rows.append({"member": row["member"], "sha256": row["sha256"],
                         "bytes": row["bytes"], "family": family, "file": row["file"]})
        evidence[family] = {"qualification_sha256": digest(qualified_file),
                            "payload_sha256": digest(payload_file),
                            "uv_readback_sha256": digest(uv_file),
                            "member_count": len(payload["payloads"])}
    actors = [r["member"] for r in rows if r["member"].startswith("attrib/ebps/")]
    assert len(actors) == 4 and len(set(actors)) == 4
    assert all(r["member"] not in before or r["sha256"] != before[r["member"]]["sha256"]
               for r in rows)
    result = {"schema": "ccp-070-qualified-integration-allowlist/v1",
              "status": "static_payloads_qualified_final_archive_not_built",
              "baseline_sga_sha256": baseline["baseline_sga_sha256"],
              "monk_candidate_sga_sha256": monk["candidate_sha256"],
              "changed_resource_allowlist": sorted(r["member"] for r in rows),
              "payloads": sorted(rows, key=lambda r: r["member"]),
              "per_family_evidence": evidence,
              "baseline_unchanged_member_count": monk["unchanged_member_count"],
              "scoped_compiled_actor_members": sorted(actors),
              "limits": "Read-only package assembly manifest. Final SGA diff, ZIP import, appearance and native match still require separate evidence."}
    out.mkdir(parents=True)
    (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"receipt": str(out / "receipt.json"), "allowlist_members": len(rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--garden", default="r5")
    parser.add_argument("--foundry", default="v1")
    parser.add_argument("--university", default="v1")
    parser.add_argument("--wonder", default="v1")
    parser.add_argument("--out-label", default="v1")
    args = parser.parse_args()
    main({family: getattr(args, family) for family in FAMILIES}, args.out_label)
