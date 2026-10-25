"""Create and verify the isolated 0.7.0 private-monk prematch precache patch.

Only the prematch SCAR member is replaced. Active Content Editor source is not edited.
"""

import hashlib
import json
import subprocess
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONFIG = json.loads((ROOT / "workspace.json").read_text(encoding="utf-8"))
EXT = Path(CONFIG["external_root"])
OUT = EXT / "output/release_070/monk"
FREEZE = EXT / "output/release_070/baseline/freeze.json"
SOURCE = ROOT / "assets/scar/vietnam/prematch_precache.scar"
BASE = EXT / "output/release_061/final-r1/community_civilization_pack.sga"
ARCHIVER = Path(CONFIG["archive_tool"])
MEMBER = "scar/vietnam/prematch_precache.scar"
GUID = "b7fcea91257b408fb9e8ae4d8bc402e1"
OLD = f'    "{GUID}:vn_unit_monk_3_chi",'.encode("ascii")
PRIVATE_EBP = f'    "{GUID}:v6icf9e7cc",'.encode("ascii")
PRIVATE_SBP = f'    "{GUID}:v6i4880d13",'.encode("ascii")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def command(*args: str) -> dict:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def patch_scar(data: bytes) -> bytes:
    """Insert exact actor/squad names once; repeated application is a no-op."""
    marker = b"local squads = {"
    assert data.count(marker) == 1
    entities, squads = data.split(marker)
    assert entities.count(OLD) == squads.count(OLD) == 1
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    if PRIVATE_EBP not in entities:
        entities = entities.replace(OLD, OLD + newline + PRIVATE_EBP, 1)
    else:
        assert entities.count(PRIVATE_EBP) == 1
    if PRIVATE_SBP not in squads:
        squads = squads.replace(OLD, OLD + newline + PRIVATE_SBP, 1)
    else:
        assert squads.count(PRIVATE_SBP) == 1
    result = entities + marker + squads
    assert result.count(PRIVATE_EBP) == result.count(PRIVATE_SBP) == 1
    assert result.count(OLD) == 2
    return result


def hashes(folder: Path, members: set[str]) -> dict[str, dict]:
    return {
        name: {"sha256": file_sha(folder / name), "bytes": (folder / name).stat().st_size}
        for name in sorted(members)
    }


def main() -> None:
    subprocess.run(
        [CONFIG["python"], str(ROOT / "tools/verify_workspace.py"), "--storage-only"],
        check=True, capture_output=True, text=True,
    )
    assert EXT.is_dir() and OUT.resolve().is_relative_to((EXT / "output").resolve())
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert freeze["schema"] == "ccp-070-baseline/v1"
    assert file_sha(BASE) == freeze["baseline_sga_sha256"]
    source = SOURCE.read_bytes()
    assert sha(source) == freeze["source"][MEMBER]["sha256"]
    assert source.count(OLD) == 2
    assert PRIVATE_EBP not in source and PRIVATE_SBP not in source
    patched = patch_scar(source)
    assert patch_scar(patched) == patched
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    assert patched.replace(newline + PRIVATE_EBP, b"").replace(
        newline + PRIVATE_SBP, b""
    ) == source

    OUT.mkdir(parents=True, exist_ok=True)
    overlay = OUT / "prematch_precache.scar"
    candidate = OUT / "community_civilization_pack-monk-precache.sga"
    if overlay.exists():
        assert overlay.read_bytes() == patched
    else:
        overlay.write_bytes(patched)
    if not candidate.exists():
        command(str(ARCHIVER), "replace-member", str(BASE), str(overlay), str(candidate), MEMBER)

    old_listing = command(str(ARCHIVER), "list", "--verify", str(BASE))
    new_listing = command(str(ARCHIVER), "list", "--verify", str(candidate))
    assert old_listing["member_count"] == new_listing["member_count"] == 1202
    before_listing = {row["path"]: row for row in old_listing["members"]}
    after_listing = {row["path"]: row for row in new_listing["members"]}
    assert before_listing.keys() == after_listing.keys()
    assert before_listing[MEMBER]["crc"] == zlib.crc32(source)
    assert after_listing[MEMBER]["crc"] == zlib.crc32(patched)
    assert before_listing[MEMBER]["toc"] == after_listing[MEMBER]["toc"]
    assert all(before_listing[name] == after_listing[name] for name in before_listing if name != MEMBER)

    readback = OUT / "readback"
    for label, archive in (("before", BASE), ("after", candidate)):
        target = readback / label
        if not target.exists():
            subprocess.run(
                [str(ARCHIVER), "unpack", "--output", str(target), str(archive)],
                check=True, capture_output=True, text=True,
            )
    before = hashes(readback / "before", set(before_listing))
    after = hashes(readback / "after", set(before_listing))
    assert before.keys() == after.keys() == before_listing.keys()
    changed = [name for name in before if before[name] != after[name]]
    assert changed == [MEMBER], changed
    assert before[MEMBER]["sha256"] == sha(source)
    assert after[MEMBER]["sha256"] == sha(patched)
    assert (readback / "after" / MEMBER).read_bytes() == patched
    mode_member = "scar/winconditions/vietnammode.scar"
    mode = (readback / "after" / mode_member).read_bytes().lower()
    assert mode.count(b'import("vietnam/prematch_precache.scar")') == 1
    assert patched.count(b"Scar_AddInit(VietnamPrecache_Init)") == 1
    assert patched.count(b"Scar_PrecachePrematchResource(BP_GetEntityBlueprint(name))") == 1
    assert patched.count(b"Scar_PrecachePrematchResource(BP_GetSquadBlueprint(name))") == 1
    mounts_preserved = all(
        before_listing[name]["toc"] == after_listing[name]["toc"]
        for name in before_listing
    )
    assert mounts_preserved
    report = {
        "schema": "ccp-070-monk-precache/v1",
        "status": "archive_readback_passed_runtime_unverified",
        "baseline": str(BASE), "baseline_sha256": file_sha(BASE),
        "source": str(SOURCE), "source_sha256": sha(source),
        "overlay": str(overlay), "overlay_sha256": sha(patched),
        "candidate": str(candidate), "candidate_sha256": file_sha(candidate),
        "member_count": len(before), "unchanged_member_count": len(before) - 1,
        "changed_members": changed,
        "mounts_preserved": mounts_preserved,
        "prematch_import_preserved": True,
        "prematch_init_hook_preserved": True,
        "member_hashes_before": before,
        "member_hashes_after": after,
        "source_preserved": file_sha(SOURCE) == sha(source),
        "idempotent_patch": patch_scar(patched) == patched,
        "native_import_and_match_tested": False,
    }
    (OUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "baseline_sha256", "candidate_sha256", "member_count",
        "unchanged_member_count", "changed_members", "mounts_preserved",
        "prematch_import_preserved", "source_preserved", "idempotent_patch"
    )}, indent=2))


if __name__ == "__main__":
    main()
