"""Assemble exact qualified 0.7.0 payloads over immutable 0.6.1.

Requires an already written combined integration receipt. This only creates a
candidate archive; full extracted-byte verification and packaging are separate.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import (EXT, FREEZE, MONK, OUT, ROOT, command, guard, member_kind,
                    owned_file, preserved_inputs, read, sha, validate_allowlist,
                    validate_mounts, write_new)


def verify_evidence(receipt: dict) -> dict:
    evidence = receipt["per_family_evidence"]
    integration = EXT / "output/release_070/integration"
    if set(evidence) != {"monk", "garden", "foundry", "university", "wonder"}:
        raise ValueError("Missing qualified family evidence")
    if evidence["monk"]["receipt_sha256"] != sha(MONK):
        raise ValueError("Monk qualification changed")
    matches = {}
    for family in ("garden", "foundry", "university", "wonder"):
        row = evidence[family]
        for stage, field in (("qualification", "qualification_sha256"),
                             ("payload", "payload_sha256"),
                             ("uv", "uv_readback_sha256")):
            candidates = list(integration.glob(f"{family}-{stage}-*/receipt.json"))
            selected = [path for path in candidates if sha(path) == row[field]]
            if len(selected) != 1:
                raise ValueError("Qualified evidence missing/ambiguous: " + family + "/" + stage)
            document = read(selected[0])
            if stage == "uv" and (document.get("status") != "passed_readback_uv_projection_runtime_unverified" or
                    document.get("family") != family or
                    document.get("native_coverage_vs_fbx_v_flipped", 0) < 0.999):
                raise ValueError("Incomplete UV readback qualification: " + family)
            if stage == "uv" and document.get("rrgeom_sha256") != next(
                    (r["sha256"] for r in receipt["payloads"] if r["family"] == family and r["member"].endswith("/model.rrgeom")), None):
                raise ValueError("UV readback geometry differs from payload: " + family)
            if stage == "qualification" and not document.get("status", "").startswith("passed_static_"):
                raise ValueError("Incomplete family qualification: " + family)
            if stage == "qualification" and set(document.get("changed_resource_allowlist", [])) != {
                    r["member"] for r in receipt["payloads"] if r["family"] == family}:
                raise ValueError("Combined allowlist differs from qualification: " + family)
            if stage == "payload":
                if document.get("status") != "offline_native_cook_grafted_runtime_unverified":
                    raise ValueError("Incomplete family payload: " + family)
                family_rows = [r for r in receipt["payloads"] if r["family"] == family]
                keys = ("member", "sha256", "bytes", "file")
                normalized = lambda rows: sorted(tuple(r[k] for k in keys) for r in rows)
                if normalized(family_rows) != normalized(document.get("payloads", [])):
                    raise ValueError("Combined payload differs from family evidence: " + family)
            matches[family + "/" + stage] = str(selected[0])
    return matches


def main(receipt_path: Path, label: str) -> None:
    guard()
    if not re.fullmatch(r"[a-z0-9-]{1,32}", label):
        raise ValueError("Use a safe immutable assembly label")
    receipt_path = owned_file(receipt_path)
    if not receipt_path.is_relative_to((EXT / "output/release_070/integration").resolve()):
        raise ValueError("Combined receipt outside 0.7.0 integration evidence")
    baseline = read(FREEZE)
    monk = read(MONK)
    if (baseline["schema"] != "ccp-070-baseline/v1" or
            sha(Path(baseline["baseline_sga"])) != baseline["baseline_sga_sha256"] or
            sha(Path(baseline["baseline_zip"])) != baseline["baseline_zip_sha256"]):
        raise ValueError("Exact frozen 0.6.1 delivery changed")
    if (monk["schema"] != "ccp-070-monk-precache/v1" or
            monk["baseline_sha256"] != baseline["baseline_sga_sha256"] or
            sha(Path(monk["candidate"])) != monk["candidate_sha256"] or
            monk["changed_members"] != ["scar/vietnam/prematch_precache.scar"]):
        raise ValueError("Monk-only archive not qualified")
    receipt = read(receipt_path)
    rows = validate_allowlist(receipt, baseline, monk)
    evidence = verify_evidence(receipt)
    inputs = preserved_inputs(baseline)
    folder = OUT / ("assembly-" + label)
    if folder.exists():
        raise FileExistsError("Preserve previous assembly attempt")
    folder.mkdir(parents=True)
    # The baseline is the exact 0.6.1 archive. The monk SCAR is an explicit
    # overlay, not a premodified base that could obscure another delta.
    current = Path(baseline["baseline_sga"])
    commands = []
    for alias in ("attrib", "data"):
        selected = [row for member, row in rows.items() if member_kind(member) == alias]
        mapping = folder / (alias + "-members.txt")
        mapping.write_text("".join(row["member"] + "=" + str(owned_file(row["file"])) + "\n"
                                   for row in selected), encoding="utf-8")
        target = folder / ("attrib-stage.sga" if alias == "attrib" else "community_civilization_pack.sga")
        command_result = command("set-members", current, mapping, target, "--alias", alias, timeout=300)
        commands.append({"alias": alias, "mapping_sha256": sha(mapping),
                         "input_sha256": sha(current), "output_sha256": sha(target),
                         "archiver": command_result})
        current = target
    listing = command("list", current, "--verify", timeout=300)
    mounts = validate_mounts(listing)
    expected_names = set(monk["member_hashes_before"]) | set(rows)
    if set(mounts) != expected_names:
        raise ValueError("Candidate resource names differ from baseline plus allowlist")
    for member in rows:
        if mounts[member] != member_kind(member):
            raise ValueError("Qualified member mounted incorrectly: " + member)
    write_new(folder / "listing.json", listing)
    write_new(folder / "assembly.json", {
        "schema": "ccp-070-final-assembly/v1",
        "status": "candidate_crc_and_tocs_checked_pending_full_byte_readback",
        "candidate": str(current), "candidate_sha256": sha(current),
        "combined_receipt": str(receipt_path), "combined_receipt_sha256": sha(receipt_path),
        "baseline_sga_sha256": baseline["baseline_sga_sha256"],
        "monk_candidate_sha256": monk["candidate_sha256"],
        "member_count": len(mounts), "allowlist_count": len(rows),
        "evidence_files": evidence, "preserved_inputs": inputs,
        "archive_commands": commands,
        "native_import_verified": False, "native_match_verified": False})
    print(current)
    print(sha(current))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combined", type=Path, required=True)
    parser.add_argument("--label", default="v1")
    args = parser.parse_args()
    main(args.combined, args.label)
