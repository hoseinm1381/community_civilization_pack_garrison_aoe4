"""Strict, readback-oriented 0.7.0 release helpers. No native-match claim."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
EXT = Path(CFG["external_root"])
OUT = EXT / "output/release_070/release"
FREEZE = EXT / "output/release_070/baseline/freeze.json"
MONK = EXT / "output/release_070/monk/verification.json"
KEY = CFG["package_key"]
CREDITS = "hosein81 and chilly5"
VERSION = "0.7.0"
MONK_MEMBER = "scar/vietnam/prematch_precache.scar"
EXPECTED_FAMILIES = {"garden", "foundry", "university", "wonder", "monk_precache"}
ZIP_MEMBERS = {"garrison.json", KEY + ".sga", "START-HERE.txt", "EVIDENCE.json"}
MEMBER_RE = re.compile(r"^[a-zA-Z0-9_./-]+$")


def guard() -> None:
    check_storage(ROOT, CFG)
    if not EXT.is_dir() or not OUT.resolve().is_relative_to((EXT / "output").resolve()):
        raise ValueError("0.7.0 release output is outside owned F: storage")


def sha(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def command(*args: object, timeout: int = 300) -> dict:
    process = subprocess.run([str(CFG["archive_tool"]), *map(str, args)],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=timeout)
    if process.returncode:
        raise RuntimeError(process.stderr + "\n" + process.stdout)
    if args and args[0] == "unpack":
        # The supported unpack command emits progress/plain text (or nothing),
        # unlike list/set-members JSON responses. File bytes are verified next.
        return {"returncode": 0, "stdout": process.stdout, "stderr": process.stderr}
    return json.loads(process.stdout)


def owned_file(path: str | Path) -> Path:
    candidate = Path(path).resolve(strict=True)
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError("Missing/linked payload file: " + str(path))
    if not any(candidate.is_relative_to(parent.resolve()) for parent in (ROOT, EXT)):
        raise ValueError("Payload outside Garrison E:/F: roots: " + str(candidate))
    return candidate


def member_kind(name: str) -> str:
    if (not MEMBER_RE.fullmatch(name) or ".." in Path(name).parts or
            "//" in name or "\\" in name or name.endswith("/") or
            any(part in ("", ".", "..") for part in name.split("/"))):
        raise ValueError("Invalid archive member path: " + name)
    if not name.startswith(("attrib/", "art/", "scar/", "ui/", "en/")) and name not in ("mod.bin", "mod.rrtex"):
        raise ValueError("Unexpected archive member root: " + name)
    if name.startswith("attrib/"):
        return "attrib"
    if name.startswith("en/"):
        return "locale"
    if name in ("mod.bin", "mod.rrtex"):
        return "info"
    return "data"


def validate_allowlist(receipt: dict, baseline: dict, monk: dict) -> dict[str, dict]:
    if (receipt.get("schema") != "ccp-070-qualified-integration-allowlist/v1" or
            receipt.get("status") != "static_payloads_qualified_final_archive_not_built"):
        raise ValueError("Combined receipt is not qualified preparation")
    if receipt.get("baseline_sga_sha256") != baseline["baseline_sga_sha256"]:
        raise ValueError("Combined receipt differs from exact 0.6.1 baseline")
    if receipt.get("monk_candidate_sga_sha256") != monk["candidate_sha256"]:
        raise ValueError("Combined receipt differs from qualified monk archive")
    rows = receipt.get("payloads")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Empty combined payload")
    names = [row["member"] for row in rows]
    if names != sorted(set(names)) or set(names) != set(receipt["changed_resource_allowlist"]):
        raise ValueError("Combined allowlist must be exact, unique and sorted")
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("Case-colliding archive members")
    by_name = {}
    family_names = {family: [] for family in EXPECTED_FAMILIES}
    before = monk["member_hashes_before"]
    for row in rows:
        name = row["member"]
        member_kind(name)
        family = row["family"]
        if family not in EXPECTED_FAMILIES:
            raise ValueError("Unexpected payload family")
        path = owned_file(row["file"])
        if sha(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
            raise ValueError("Qualified payload drift: " + name)
        if name in before and row["sha256"] == before[name]["sha256"]:
            raise ValueError("Unchanged resource in explicit delta: " + name)
        if family == "monk_precache" and name != MONK_MEMBER:
            raise ValueError("Monk allowlist escaped one SCAR member")
        if family != "monk_precache" and not name.startswith(("art/", "attrib/ebps/", "attrib/attachments/attachment_lists/vietnam/release_070/")):
            raise ValueError("Visual family escaped art/actor scope")
        family_names[family].append(name)
        by_name[name] = row
    if family_names["monk_precache"] != [MONK_MEMBER]:
        raise ValueError("Missing exact monk precache member")
    actors = sorted(name for name in names if name.startswith("attrib/ebps/"))
    if len(actors) != 4 or actors != receipt.get("scoped_compiled_actor_members"):
        raise ValueError("Exactly four qualified actor members required")
    if any(not any(name.startswith("attrib/ebps/") for name in family_names[family]) or
           not any(name.startswith("art/") for name in family_names[family])
           for family in EXPECTED_FAMILIES - {"monk_precache"}):
        raise ValueError("Each visual family needs actor and art resources")
    return by_name


def validate_mounts(listing: dict) -> dict[str, str]:
    rows = listing["members"]
    names = [row["path"] for row in rows]
    if len(names) != len(set(names)) or len(names) != len({name.casefold() for name in names}):
        raise ValueError("Duplicate or case-colliding archive member")
    result = {}
    for row in rows:
        expected = member_kind(row["path"])
        if row["toc"] != expected:
            raise ValueError("Wrong archive mount for " + row["path"])
        result[row["path"]] = row["toc"]
    if not listing["archive"]["verification"]["verified"]:
        raise ValueError("Archive CRC verification failed")
    if listing["archive"]["name"].replace("-", "").lower() != CFG["project_guid"].replace("-", "").lower():
        raise ValueError("Archive identity changed")
    return result


def inventory(root: Path) -> dict[str, dict]:
    if root.is_symlink() or root.is_junction():
        raise ValueError("Linked inventory root")
    records = {}
    for folder, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            child = Path(folder) / name
            if child.is_symlink() or child.is_junction():
                raise ValueError("Linked inventory directory")
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(names):
            path = Path(folder) / name
            if path.is_symlink():
                raise ValueError("Linked inventory file")
            records[path.relative_to(root).as_posix()] = {
                "sha256": sha(path), "bytes": path.stat().st_size}
    return records


def verify_source(baseline: dict) -> int:
    actual = inventory(ROOT / "assets")
    if actual == baseline["source"]:
        return len(actual)
    # The separately owned activation helper pins the four actor edits, nine
    # private attachment lists and one monk hook. Never accept arbitrary paths
    # merely because a mutable activation receipt lists them.
    import importlib.util
    spec = importlib.util.spec_from_file_location("ccp070_source_activation", ROOT / "tools/release_070/activate_source.py")
    activation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(activation)
    rows = activation.candidates()
    expected = dict(baseline["source"])
    for path, relative, digest in rows:
        path = owned_file(path)
        if sha(path) != digest:
            raise ValueError("Qualified source overlay changed: " + relative)
        expected[relative] = {"sha256": digest, "bytes": path.stat().st_size}
    if actual != expected:
        raise ValueError("Active source differs from exact qualified 0.7.0 overlay")
    receipt = read(EXT / "output/release_070/source-activation/receipt.json")
    if (receipt.get("schema") != "ccp-070-source-activation/v1" or
            receipt.get("status") != "qualified_overlay_applied" or
            receipt.get("source_sha256") != {k: v["sha256"] for k, v in actual.items()} or
            sha(owned_file(receipt["combined_receipt"])) != receipt["combined_sha256"]):
        raise ValueError("Missing or changed source activation evidence")
    return len(actual)


def verify_normal(baseline: dict) -> dict:
    actual = inventory(Path(CFG["source_root"]))
    if actual == baseline["normal"]:
        return {"normal_files": len(actual), "normal_frozen_preservation_passed": True,
                "normal_observed_drift_inventory_preserved": False}
    drift_path = EXT / "output/release_070/external-normal-drift.json"
    if not drift_path.is_file():
        raise ValueError("Normal edition differs from frozen 0.6.1; explicit drift inventory required")
    drift = read(drift_path)
    before = baseline["normal"]
    added = sorted(set(actual) - set(before))
    removed = sorted(set(before) - set(actual))
    changed = sorted(k for k in actual.keys() & before.keys() if actual[k] != before[k])
    if (drift.get("schema") != "ccp-070-external-normal-drift/v1" or
            drift.get("freeze_sha256") != sha(FREEZE) or
            Path(drift["normal_root"]).resolve() != Path(CFG["source_root"]).resolve() or
            drift.get("normal_observed_inventory") != actual or
            drift.get("changed_paths") != sorted(added + changed + removed) or
            drift.get("observed_file_count") != len(actual) or
            drift.get("frozen_unchanged_file_count") != sum(actual.get(k) == v for k, v in before.items()) or
            drift.get("normal_frozen_preservation_passed") is not False or
            added != ["assets/attrib/instances/ai/ai_economy/complete/default_economy.xml"] or
            changed != [".aoe4/Vietnam_v2/Layout.xml", "archives/Vietnam_v2.sga"] or removed):
        raise ValueError("Normal edition drift differs from explicit observed inventory")
    differences = drift.get("differences", {})
    if set(differences) != set(added + changed + removed) or any(
            differences[k].get("frozen") != before.get(k) or differences[k].get("observed") != actual.get(k)
            for k in differences):
        raise ValueError("Normal edition drift differences lost frozen/observed evidence")
    return {"normal_files": len(actual), "baseline_normal_files": len(before),
            "normal_frozen_preservation_passed": False,
            "normal_observed_drift_inventory_preserved": True,
            "normal_drift_receipt": str(drift_path), "normal_drift_receipt_sha256": sha(drift_path),
            "normal_added_paths": added, "normal_changed_paths": changed}


def preserved_inputs(baseline: dict) -> dict:
    source_count = verify_source(baseline)
    normal = verify_normal(baseline)
    for name, digest in baseline["identity"].items():
        if sha(ROOT / name) != digest:
            raise ValueError("Project identity changed: " + name)
    art_count = 0
    for folder, rows in baseline["art"].items():
        for relative, record in rows.items():
            path = ROOT / "art" / folder / relative
            if not path.is_file() or sha(path) != record["sha256"] or path.stat().st_size != record["bytes"]:
                raise ValueError("Prior editable art changed: " + relative)
            art_count += 1
    # The historical 0.7.0 voice-preparation folder was moved, intact, to 0.8.0.
    migration = read(EXT / "output/release_070/voices/migration-080.json")
    archive = owned_file(migration["original_archive"])
    if sha(archive) != migration["original_archive_sha256"]:
        raise ValueError("Voice-preparation archive changed")
    import zipfile
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError("Voice-preparation archive CRC failure")
        for relative, record in baseline["voice_preparation"].items():
            if hashlib.sha256(package.read("0.7.0/" + relative)).hexdigest() != record["sha256"]:
                raise ValueError("Frozen voice-preparation file changed")
            if relative not in migration["changed_paths"] and sha(ROOT / "0.8.0" / relative) != record["sha256"]:
                raise ValueError("Migrated voice-preparation file changed")
    return {"source_files": source_count, "baseline_source_files": len(baseline["source"]), **normal,
            "prior_art_files": art_count, "voice_preparation_files": len(baseline["voice_preparation"])}
