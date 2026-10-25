"""Package only a fully read-back verified 0.7.0 archive into strict four-file ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import date
from pathlib import Path

from common import (CREDITS, FREEZE, KEY, OUT, VERSION, ZIP_MEMBERS, guard,
                    preserved_inputs, read, sha, write_new)

GATES = {"archive_bytes_and_tocs": True, "qualified_native_asset_cooks": True,
         "source_and_prior_art_preservation": True,
         "normal_frozen_preservation_passed": False,
         "normal_observed_drift_inventory_preserved": True, "import": False,
         "native_appearance": False, "native_gameplay": False,
         "multiplayer": False}


def check_manifest(manifest: dict, sga_sha: str) -> None:
    details = manifest["details"]
    if (manifest.get("schema") != "garrison.mod/v1" or
            manifest.get("bundle_key") != KEY or details.get("id") != KEY or
            details.get("version") != VERSION or details.get("author") != CREDITS or
            details.get("content_types") != ["game-mode", "tuning-pack"] or
            manifest.get("members") != [{"mod_key": KEY, "role": "tuning",
                                         "path": KEY + ".sga", "sha256": sga_sha}]):
        raise ValueError("Garrison manifest/identity/version/credits mismatch")


def check_evidence(evidence: dict, sga_sha: str, baseline_sha: str) -> None:
    if (evidence.get("schema") != "ccp.release070.evidence/v1" or
            evidence.get("version") != VERSION or
            evidence.get("is_final_release") is not True or
            evidence.get("credits") != CREDITS or
            evidence.get("sga_sha256") != sga_sha or
            evidence.get("baseline061_sga_sha256") != baseline_sha or
            evidence.get("gates") != GATES):
        raise ValueError("Release evidence or native-gate states differ")


def inspect_zip(path: Path, baseline_sha: str) -> dict:
    if path.name != KEY + "-" + VERSION + ".zip":
        raise ValueError("Strict 0.7.0 delivery filename required")
    before = sha(path)
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        if len(names) != 4 or set(names) != ZIP_MEMBERS or len(names) != len(set(names)):
            raise ValueError("ZIP must have four exact unique members")
        if package.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        with package.open(KEY + ".sga") as stream:
            sga_sha = hashlib.file_digest(stream, "sha256").hexdigest()
        check_manifest(json.loads(package.read("garrison.json")), sga_sha)
        check_evidence(json.loads(package.read("EVIDENCE.json")), sga_sha, baseline_sha)
        instructions = package.read("START-HERE.txt").decode("utf-8")
        if CREDITS not in instructions or "0.6.1" not in instructions or "Rollback" not in instructions:
            raise ValueError("Missing credited rollback instructions")
    if sha(path) != before:
        raise ValueError("ZIP changed during inspection")
    return {"schema": "ccp-070-package-verification/v1",
            "status": "zip_crc_manifest_identity_embedded_sga_verified",
            "zip": str(path), "zip_sha256": before, "zip_bytes": path.stat().st_size,
            "sga_sha256": sga_sha, "members": sorted(ZIP_MEMBERS),
            "gates": GATES, "native_match_verified": False}


def main(verification_path: Path, label: str) -> None:
    guard()
    if not label.replace("-", "").isalnum() or len(label) > 32:
        raise ValueError("Safe immutable package label required")
    proof = read(verification_path)
    if (proof.get("schema") != "ccp-070-final-archive-verification/v1" or
            proof.get("status") != "complete_archive_bytes_mounts_identity_and_preservation_verified"):
        raise ValueError("Full archive readback verification required")
    candidate = Path(proof["candidate"])
    if (not candidate.resolve().is_relative_to(OUT.resolve()) or
            sha(candidate) != proof["candidate_sha256"]):
        raise ValueError("Verified candidate changed")
    baseline = read(FREEZE)
    if (sha(Path(baseline["baseline_sga"])) != baseline["baseline_sga_sha256"] or
            sha(Path(baseline["baseline_zip"])) != baseline["baseline_zip_sha256"]):
        raise ValueError("Exact 0.6.1 rollback/baseline changed")
    if sha(Path(proof["combined_receipt"])) != proof["combined_receipt_sha256"]:
        raise ValueError("Qualified combined allowlist changed")
    preserved = preserved_inputs(baseline)
    if (preserved["normal_frozen_preservation_passed"] is not GATES["normal_frozen_preservation_passed"] or
            preserved["normal_observed_drift_inventory_preserved"] is not GATES["normal_observed_drift_inventory_preserved"]):
        raise ValueError("Normal-edition gate state differs from reviewed release evidence")
    import re
    if not re.fullmatch(r"[a-z0-9-]{1,32}", label):
        raise ValueError("Safe immutable package label required")
    folder = OUT / ("package-" + label)
    delivery = OUT / (KEY + "-" + VERSION + ".zip")
    if folder.exists() or delivery.exists():
        raise FileExistsError("Preserve previous package attempt/delivery")
    with zipfile.ZipFile(baseline["baseline_zip"]) as earlier:
        manifest = json.loads(earlier.read("garrison.json"))
    sga_sha = sha(candidate)
    manifest["members"] = [{"mod_key": KEY, "role": "tuning",
                            "path": KEY + ".sga", "sha256": sga_sha}]
    manifest["details"].update(
        version=VERSION, author=CREDITS, updated=date.today().isoformat(),
        summary="Vietnamese Imperial architecture and private monk precache repair",
        description=("Four Age IV Vietnamese building visuals use qualified private native "
                     "resources while preserving their gameplay actors and lifecycle owners. "
                     "The monk prematch precache is corrected. Import and native match testing remain required."),
        changelog=("Imperial Garden, Trung Foundries, University overlay and Kinh Thien Hall "
                   "visuals; private monk EBP/SBP precache. Earlier gameplay and archive resources "
                   "remain unchanged outside the explicit qualified allowlist."))
    check_manifest(manifest, sga_sha)
    evidence = {"schema": "ccp.release070.evidence/v1", "version": VERSION,
                "is_final_release": True, "credits": CREDITS,
                "sga_sha256": sga_sha,
                "baseline061_sga_sha256": baseline["baseline_sga_sha256"],
                "changed_members": proof["changed_members"],
                "unchanged_baseline_members": proof["unchanged_baseline_members"],
                "new_members": proof["new_members"], "gates": GATES,
                "preserved_inputs": preserved,
                "reports": {"final_archive": {"path": str(verification_path),
                                               "sha256": sha(verification_path)},
                            "assembly": {"path": proof["assembly_receipt"],
                                         "sha256": proof["assembly_receipt_sha256"]},
                            "combined_allowlist": {"path": proof["combined_receipt"],
                                                   "sha256": proof["combined_receipt_sha256"]}},
                "limits": ["Native import, selection, appearance, damage/ruins/repair and multiplayer have not been tested.",
                           "The four-map object-PBR cook does not establish dynamic team tint for new visuals.",
                           "The University stock main body/material remain native; its separate add-on and pot swap require in-match visual review.",
                           "No additional camera-distance LOD activation is claimed."]}
    evidence["limits"].append("The normal edition has separately observed external drift in three paths; frozen preservation failed. Its exact observed inventory is pinned and no normal-edition content is used to assemble this release.")
    check_evidence(evidence, sga_sha, baseline["baseline_sga_sha256"])
    instructions = f"""Community Civilization Pack {VERSION}
Credits: {CREDITS}

Close Age of Empires IV, import this ZIP through Garrison, then select Community
Civilization Pack as both Game Mode and Tuning Pack. This is a full replacement
ZIP. Start China and select Vietnam using the existing civilization flow.

The four new Imperial building visuals and private monk prematch precache have
offline archive/cook qualification. Fresh native testing remains required for
building appearance, construction, damage, selectable ruins and repair, monk
visibility, near/far views and two player colours. No in-match pass is claimed.

Rollback: retain and reimport the exact 0.6.1 ZIP at
{baseline['baseline_zip']}
It is the frozen starting point for 0.7.0. Preserve all editable source,
textures, Blender masters, recipes, native cook receipts and prior deliveries.

See tools/release_070/release/NATIVE_TEST_CHECKLIST.md and REBUILD_ROLLBACK.md in
the editable project for precise tests and rebuild dependencies.
"""
    folder.mkdir(parents=True)
    write_new(folder / "garrison.json", manifest)
    write_new(folder / "EVIDENCE.json", evidence)
    (folder / "START-HERE.txt").write_text(instructions, encoding="utf-8")
    staged = folder / delivery.name
    with zipfile.ZipFile(staged, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        for name in ("garrison.json", "START-HERE.txt", "EVIDENCE.json"):
            package.write(folder / name, name)
        package.write(candidate, KEY + ".sga")
    inspect_zip(staged, baseline["baseline_sga_sha256"])
    staged.replace(delivery)
    result = inspect_zip(delivery, baseline["baseline_sga_sha256"])
    write_new(OUT / ("package-verification-" + label + ".json"), result)
    print(delivery)
    print(result["zip_sha256"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--label", default="v1")
    args = parser.parse_args()
    main(args.verification, args.label)
