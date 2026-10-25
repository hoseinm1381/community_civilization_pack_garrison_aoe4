"""Verify 0.7.4 baseline hashes, snapshot source, and pin protected paths before 0.8.0 edits."""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BASELINE_SGA,
    BASELINE_ZIP,
    CFG,
    EXPECTED_SGA_SHA256,
    EXPECTED_ZIP_SHA256,
    OUT,
    ROOT,
    guard,
    read,
    sha,
    write,
)

sys.path.insert(0, str(ROOT / "tools/release_073"))
from check_identity import check as check_identity  # noqa: E402


def collect_source_hashes() -> dict[str, str]:
    rows = {
        p.relative_to(ROOT).as_posix(): sha(p)
        for p in sorted((ROOT / "assets").rglob("*"))
        if p.is_file()
    }
    rows[CFG["project_file"]] = sha(ROOT / CFG["project_file"])
    return rows


def collect_normal_hashes() -> dict[str, str]:
    normal = Path(CFG["source_root"])
    rows = {
        p.relative_to(normal).as_posix(): sha(p)
        for p in sorted((normal / "assets").rglob("*"))
        if p.is_file()
    }
    for name in ("Vietnam_v2.aoe4mod", "workspace.json"):
        if (normal / name).exists():
            rows[name] = sha(normal / name)
    return rows


def collect_voice_080_hashes() -> dict[str, str]:
    voice_dir = ROOT / "0.8.0"
    if not voice_dir.is_dir():
        raise FileNotFoundError(f"Expected 0.8.0 voice preparation directory missing: {voice_dir}")
    return {
        p.relative_to(ROOT).as_posix(): sha(p)
        for p in sorted(voice_dir.rglob("*"))
        if p.is_file()
    }


def collect_protected_hashes() -> dict[str, str]:
    protected = dict(read(ROOT / "output/release_072/freeze/protected.json"))
    for rel in (
        "output/release_074/delivery/community_civilization_pack-0.7.4.zip",
        "output/release_074/delivery/community_civilization_pack.sga",
        "output/release_074/delivery/garrison.json",
    ):
        protected[rel] = sha(ROOT / rel)
    for p in sorted((ROOT / "art/authoring/buildings_020/barracks").rglob("*")):
        if p.is_file():
            protected[p.relative_to(ROOT).as_posix()] = sha(p)
    for p in sorted((ROOT / "art/exports/buildings_020/barracks").rglob("*")):
        if p.is_file():
            protected[p.relative_to(ROOT).as_posix()] = sha(p)
    return protected


def freeze() -> dict:
    guard()
    if not BASELINE_ZIP.is_file() or not BASELINE_SGA.is_file():
        raise FileNotFoundError("0.7.4 delivery ZIP or SGA missing")
    zip_sha = sha(BASELINE_ZIP)
    sga_sha = sha(BASELINE_SGA)
    if zip_sha != EXPECTED_ZIP_SHA256:
        raise RuntimeError(f"0.7.4 ZIP SHA-256 mismatch: {zip_sha} != {EXPECTED_ZIP_SHA256}")
    if sga_sha != EXPECTED_SGA_SHA256:
        raise RuntimeError(f"0.7.4 SGA SHA-256 mismatch: {sga_sha} != {EXPECTED_SGA_SHA256}")
    with zipfile.ZipFile(BASELINE_ZIP) as zf:
        if zf.testzip() is not None:
            raise RuntimeError("0.7.4 baseline ZIP failed integrity test")
        embedded_sga = zf.read("community_civilization_pack.sga")
    import hashlib
    if hashlib.sha256(embedded_sga).hexdigest() != EXPECTED_SGA_SHA256:
        raise RuntimeError("Embedded 0.7.4 SGA in ZIP does not match expected SGA SHA-256")
    check_identity(ROOT, BASELINE_SGA)

    # Check Hideout 30s construction time from 0.7.4 is present in current source
    for name in ("vn_building_defense_outpost_chi", "vn_building_defense_outpost_2_chi"):
        hideout_path = ROOT / f"assets/attrib/instances/ebps/vietnam/buildings/hideouts/{name}.xml"
        raw = hideout_path.read_bytes()
        if raw.count(b'<float name="time_seconds" value="30" overrideParent="True" />') != 2:
            raise RuntimeError(f"0.7.4 Hideout 30s construction time missing in {hideout_path}")

    OUT.mkdir(parents=True, exist_ok=True)
    before_json = OUT / "before.json"
    before_zip = OUT / "before-source.zip"
    normal_json = OUT / "normal-baseline.json"
    voice_json = OUT / "voice-080-baseline.json"
    protected_json = OUT / "protected-080.json"

    if not before_json.exists():
        source_rows = collect_source_hashes()
        write(before_json, source_rows)
        with zipfile.ZipFile(before_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for rel in sorted(source_rows):
                zf.write(ROOT / rel, rel)
    else:
        source_rows = read(before_json)

    if not normal_json.exists():
        write(normal_json, collect_normal_hashes())
    if not voice_json.exists():
        write(voice_json, collect_voice_080_hashes())
    if not protected_json.exists():
        write(protected_json, collect_protected_hashes())

    return verify_preserved()


def verify_preserved() -> dict:
    guard()
    if sha(BASELINE_ZIP) != EXPECTED_ZIP_SHA256:
        raise RuntimeError("0.7.4 baseline ZIP changed")
    if sha(BASELINE_SGA) != EXPECTED_SGA_SHA256:
        raise RuntimeError("0.7.4 baseline SGA changed")
    check_identity(ROOT, BASELINE_SGA)

    normal_expected = read(OUT / "normal-baseline.json")
    normal_actual = collect_normal_hashes()
    if normal_actual != normal_expected:
        raise RuntimeError("Normal edition changed during 0.8.0 work")

    voice_expected = read(OUT / "voice-080-baseline.json")
    voice_actual = collect_voice_080_hashes()
    if voice_actual != voice_expected:
        raise RuntimeError("Existing 0.8.0 voice preparation directory changed during 0.8.0 work")

    protected_expected = read(OUT / "protected-080.json")
    for rel, digest in protected_expected.items():
        if sha(ROOT / rel) != digest:
            raise RuntimeError(f"Protected file drifted: {rel}")

    for name in ("vn_building_defense_outpost_chi", "vn_building_defense_outpost_2_chi"):
        hideout_path = ROOT / f"assets/attrib/instances/ebps/vietnam/buildings/hideouts/{name}.xml"
        raw = hideout_path.read_bytes()
        if raw.count(b'<float name="time_seconds" value="30" overrideParent="True" />') != 2:
            raise RuntimeError(f"0.7.4 Hideout 30s construction time drifted in {hideout_path}")

    return {
        "status": "passed",
        "baseline_zip_sha256": EXPECTED_ZIP_SHA256,
        "baseline_sga_sha256": EXPECTED_SGA_SHA256,
        "before_source_count": len(read(OUT / "before.json")),
        "normal_file_count": len(normal_expected),
        "voice_080_file_count": len(voice_expected),
        "protected_file_count": len(protected_expected),
        "hideout_30s_preserved": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    import json
    res = verify_preserved() if args.verify else freeze()
    print(json.dumps(res, indent=2))
