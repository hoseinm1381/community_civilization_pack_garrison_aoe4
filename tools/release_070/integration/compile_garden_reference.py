"""Isolated Content Editor reference compile of staged private Garden source."""
from __future__ import annotations

import argparse
import hashlib
import json
import msvcrt
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
EXT = Path(CFG["external_root"])
LOCK = EXT / "output/release_020/native-build.lock"
DRAFT = EXT / "staging/release_070/integration/garden-binding-draft"
WORK = EXT / "staging/release_070/integration/garden-reference-v1"
OUT = ROOT / "output/release_070/integration/garden-reference-v1"
PROJECT_NAME = CFG["project_file"]
MEMBERS = [
    "attrib/ebps/vietnam/vn_building_landmark_age3_imperial_garden_vit.rgd",
    "attrib/attachments/attachment_lists/vietnam/release_070/vn070_garden_main.rgd",
    "attrib/attachments/attachment_lists/vietnam/release_070/vn070_garden_outskirts.rgd",
]


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(label: str, args: list[str], timeout: int) -> subprocess.CompletedProcess:
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, cwd=Path(CFG["content_editor"]).parent)
    (OUT / (label + ".log")).write_text(
        "COMMAND: " + " ".join(args) + f"\nEXIT: {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    if p.returncode:
        raise RuntimeError(f"{label} failed; inspect {OUT / (label + '.log')}")
    return p


def main(scope: str) -> None:
    global DRAFT, WORK, OUT, MEMBERS
    if scope == "remaining":
        DRAFT = EXT / "staging/release_070/integration/remaining-binding-draft"
        WORK = EXT / "staging/release_070/integration/remaining-reference-v1"
        OUT = ROOT / "output/release_070/integration/remaining-reference-v1"
        MEMBERS = [
            "attrib/ebps/vietnam/vn_building_landmark_age3_trung_foundaries_vit.rgd",
            "attrib/ebps/vietnam/vn_building_tech_university_control_chi.rgd",
            "attrib/ebps/vietnam/vn_building_wonder_age4_forbidden_control_chi.rgd",
            *["attrib/attachments/attachment_lists/vietnam/release_070/" + name + ".rgd"
              for name in ("vn070_foundry_main", "vn070_foundry_outskirts",
                           "vn070_university_main", "vn070_university_outskirts_chi",
                           "vn070_university_outskirts_eng", "vn070_wonder_main",
                           "vn070_wonder_outskirts")],
        ]
    elif scope != "garden":
        raise ValueError("Unknown reference scope")
    if WORK.exists() or OUT.exists():
        raise FileExistsError("Preserve earlier Garden native reference attempt")
    WORK.mkdir(parents=True)
    OUT.mkdir(parents=True)
    source = WORK / "source"
    shutil.copytree(ROOT / "assets", source / "assets")
    shutil.copy2(ROOT / PROJECT_NAME, source / PROJECT_NAME)
    before = {p.relative_to(ROOT / "assets").as_posix(): sha(p)
              for p in (ROOT / "assets").rglob("*") if p.is_file()}
    staged = list(DRAFT.glob("assets/**/*.xml"))
    assert len(staged) == len(MEMBERS) and all(p.is_file() for p in staged)
    overlay = {}
    for path in staged:
        rel = path.relative_to(DRAFT)
        target = source / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        assert sha(target) == sha(path)
        overlay[rel.as_posix()] = sha(path)
    if before != {p.relative_to(ROOT / "assets").as_posix(): sha(p)
                  for p in (ROOT / "assets").rglob("*") if p.is_file()}:
        raise RuntimeError("Active source changed during isolated source copy")
    build = WORK / "build"
    command = [str(CFG["content_editor"]), "-rtm", "--safe_settings", "--do_not_restore",
               "--quiet_crash_report", "--no_source_control", "--log_path", str(WORK / "logs"),
               "--build_mod", str(source / PROJECT_NAME), "--build_path", str(build),
               "--no_burn_window", "--burn_cache_type", "Local", "--burn_max_threads", "1",
               "--burn_platform", "PC", "--burn_log_path", str(WORK / "burn.log"),
               "--intermediate_path", str(WORK / "intermediate")]
    (OUT / "input-freeze.json").write_text(json.dumps({"source_project_sha256": sha(ROOT / PROJECT_NAME),
        "baseline_source_sha256": before, "staged_overlay_sha256": overlay,
        "command": command}, indent=2) + "\n")
    with LOCK.open("r+b") as stream:
        msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        try:
            process = run("content-editor", command, 1800)
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    log = process.stdout + process.stderr
    errors = [line for line in log.splitlines() if "EssenceEditor.exe Error:" in line]
    counts = re.findall(r"(\d+) instances validated", log)
    expected_count = len(list((source / "assets/attrib/instances").rglob("*.xml")))
    if errors or not counts or int(counts[-1]) != expected_count:
        raise RuntimeError(f"Native source validation failed: {errors[:3]}, {counts}, {expected_count}")
    archives = list(build.rglob("*.sga"))
    if len(archives) != 1:
        raise RuntimeError(f"Expected one compiled SGA: {archives}")
    archive = archives[0]
    listing = run("archive-verify", [str(CFG["archive_tool"]), "list", str(archive), "--verify"], 600)
    info = json.loads(listing.stdout)
    if not info["archive"]["verification"]["verified"]:
        raise RuntimeError("Native reference SGA verification failed")
    extracted = {}
    for member in MEMBERS:
        target = OUT / "readback" / member
        target.parent.mkdir(parents=True, exist_ok=True)
        run("extract-" + target.stem, [str(CFG["archive_tool"]), "extract-member",
             str(archive), member, str(target)], 180)
        extracted[member] = {"file": str(target), "sha256": sha(target), "bytes": target.stat().st_size}
    if before != {p.relative_to(ROOT / "assets").as_posix(): sha(p)
                  for p in (ROOT / "assets").rglob("*") if p.is_file()}:
        raise RuntimeError("Active source changed during Garden native reference compile")
    receipt = {"schema": "ccp-070-garden-isolated-native-reference/v1",
               "status": "content_editor_compile_and_readback_passed_runtime_unverified",
               "native_validated_instances": expected_count,
               "archive": str(archive), "archive_sha256": sha(archive),
               "overlay_sha256": overlay, "readback": extracted,
               "active_source_unchanged": True,
               "private_binding_behavior": "compare reference readback against staged payload separately"}
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"), "archive_sha256": sha(archive)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scope", choices=("garden", "remaining"), nargs="?", default="garden")
    main(parser.parse_args().scope)
