"""Verify 0.7.0 candidate bytes, native mounts, identity and preservation."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import (EXT, FREEZE, MONK, OUT, command, guard, inventory,
                    member_kind, preserved_inputs, read, sha, validate_allowlist,
                    validate_mounts, write_new)


def compare_members(before: dict, after: dict, rows: dict) -> dict:
    expected = set(before) | set(rows)
    if set(after) != expected:
        raise ValueError("Archive added/removed resources outside exact allowlist")
    changed = {member for member in after if before.get(member) != after[member]}
    if changed != set(rows):
        raise ValueError("Actual byte delta differs from explicit combined allowlist")
    for member, row in rows.items():
        if after[member] != {"sha256": row["sha256"], "bytes": row["bytes"]}:
            raise ValueError("Cooked member bytes differ from qualification: " + member)
    return {"changed_members": sorted(changed),
            "unchanged_baseline_members": len(before) - len(changed & set(before)),
            "new_members": sorted(changed - set(before))}


def main(assembly_path: Path, label: str) -> None:
    guard()
    if not re.fullmatch(r"[a-z0-9-]{1,32}", label):
        raise ValueError("Use a safe immutable verification label")
    assembly = read(assembly_path)
    if (assembly.get("schema") != "ccp-070-final-assembly/v1" or
            assembly.get("status") != "candidate_crc_and_tocs_checked_pending_full_byte_readback"):
        raise ValueError("Unqualified assembly receipt")
    candidate = Path(assembly["candidate"])
    if (not candidate.resolve().is_relative_to(OUT.resolve()) or
            sha(candidate) != assembly["candidate_sha256"]):
        raise ValueError("Candidate path/hash changed")
    combined_path = Path(assembly["combined_receipt"])
    if sha(combined_path) != assembly["combined_receipt_sha256"]:
        raise ValueError("Combined allowlist changed")
    baseline = read(FREEZE)
    monk = read(MONK)
    if sha(Path(baseline["baseline_sga"])) != baseline["baseline_sga_sha256"]:
        raise ValueError("0.6.1 baseline changed")
    rows = validate_allowlist(read(combined_path), baseline, monk)
    if len(rows) != assembly["allowlist_count"]:
        raise ValueError("Assembly allowlist count changed")
    preserved = preserved_inputs(baseline)
    folder = OUT / ("verification-" + label)
    if folder.exists():
        raise FileExistsError("Preserve previous verification attempt")
    folder.mkdir(parents=True)
    listing = command("list", candidate, "--verify", timeout=300)
    actual_mounts = validate_mounts(listing)
    baseline_listing = read(EXT / "output/release_061/qualification/final-r1/listing.json")
    baseline_mounts = validate_mounts(baseline_listing)
    if set(actual_mounts) != set(baseline_mounts) | set(rows):
        raise ValueError("Archive name delta differs from allowlist")
    if any(actual_mounts[name] != toc for name, toc in baseline_mounts.items()):
        raise ValueError("An existing resource changed TOC")
    if any(actual_mounts[name] != member_kind(name) for name in rows):
        raise ValueError("A qualified payload has the wrong native TOC")
    readback = folder / "members"
    # extract returns only native archive members. unpack also generates XML/RDO
    # source sidecars, which must not be mistaken for extra archive resources.
    command("extract", candidate, readback, "--filter", "", timeout=300)
    actual = inventory(readback)
    before = monk["member_hashes_before"]
    delta = compare_members(before, actual, rows)
    if len(actual) != len(actual_mounts) or len(actual) != assembly["member_count"]:
        raise ValueError("Readback/listing member counts differ")
    if sha(candidate) != assembly["candidate_sha256"]:
        raise ValueError("Candidate changed during verification")
    write_new(folder / "listing.json", listing)
    write_new(folder / "receipt.json", {
        "schema": "ccp-070-final-archive-verification/v1",
        "status": "complete_archive_bytes_mounts_identity_and_preservation_verified",
        "candidate": str(candidate), "candidate_sha256": sha(candidate),
        "assembly_receipt": str(assembly_path), "assembly_receipt_sha256": sha(assembly_path),
        "combined_receipt": str(combined_path), "combined_receipt_sha256": sha(combined_path),
        "baseline_sga_sha256": baseline["baseline_sga_sha256"],
        "member_count": len(actual), "allowlist_count": len(rows),
        "changed_members": delta["changed_members"],
        "unchanged_baseline_members": delta["unchanged_baseline_members"],
        "new_members": delta["new_members"],
        "member_hashes": actual, "mounts": actual_mounts,
        "preserved_inputs": preserved,
        "native_import_verified": False, "native_appearance_verified": False,
        "native_gameplay_verified": False, "multiplayer_verified": False})
    print(folder / "receipt.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--label", default="v1")
    args = parser.parse_args()
    main(args.assembly, args.label)
