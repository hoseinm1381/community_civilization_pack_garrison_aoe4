"""Trace exact stock attachment donors without changing game or mod sources.

The native attachment RGD, rather than a name search, is the authority for each
model. All extracts and reports are confined to release_060/donors.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, CORE, OUT, ROOT, CFG, guard, owned, read, sha, write

INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
CONFIG = INDEX.with_name("game-assets.local.json")
DEST = OUT / "donors"

# Exact references in active Vietnamese archer II EBPS, ordinary/default branch.
ARCHER_ATTACHMENTS = {
    "body": "attrib/attachments/attachment_lists/civilizations/chinese/units/tier2_archer_chi.rgd",
    "bow": "attrib/attachments/attachment_lists/races/chinese/weapons/wpn_range_archer_2_chi.rgd",
    "body_parent": "attrib/attachments/attachment_lists/civilizations/core/units/core_archer.rgd",
}


def command(*args: object) -> dict:
    proc = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode:
        raise RuntimeError(f"Command exit {proc.returncode}: {args}; "
                           f"stdout={proc.stdout[-1500:]} stderr={proc.stderr[-1500:]}")
    return json.loads(proc.stdout)


def exact_attrib_member(archive: Path, member: str) -> dict:
    listing = command(ARCH, "list", archive, "--filter", Path(member).name)
    matches = [row for row in listing["members"] if row["path"].lower() == member.lower()]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one exact Attrib member {member}, got {matches}")
    return matches[0]


def extract_rgd(archive: Path, archive_sha256: str, role: str,
                member: str) -> tuple[Path, ET.Element, dict]:
    meta = exact_attrib_member(archive, member)
    # A file's existence is never evidence that it came from the current
    # official archive. Keep older extracts, including the original flat cache,
    # and use a new directory when the archive/member identity changes.
    cache_key = f"{archive_sha256[:20]}-{meta['crc']:08x}-{meta['size']}"
    folder = owned(DEST / "rgd" / role / cache_key)
    binary = folder / Path(member).name
    xml = binary.with_suffix(".xml")
    receipt = folder / "receipt.json"
    identity = {"archive_sha256": archive_sha256, "member": member,
                "member_crc": meta["crc"], "member_size": meta["size"],
                "member_stored_size": meta["stored_size"]}
    if folder.exists():
        if not receipt.is_file() or not binary.is_file() or not xml.is_file():
            raise RuntimeError(f"Incomplete donor cache; refusing reuse: {folder}")
        recorded = read(receipt)
        if recorded.get("source") != identity or sha(binary) != recorded.get("rgd_sha256") \
                or sha(xml) != recorded.get("xml_sha256"):
            raise RuntimeError(f"Donor cache identity/hash drift; refusing reuse: {folder}")
    else:
        folder.mkdir(parents=True)
        command(ARCH, "extract-member", archive, member, binary)
        command(ARCH, "decode-rgd", binary, xml)
        write(receipt, {"schema": "ccp-060-donor-cache/v1", "source": identity,
                        "rgd_sha256": sha(binary), "xml_sha256": sha(xml)})
    return xml, ET.parse(xml).getroot(), {
        "member": member, "archive": str(archive), "archive_sha256": archive_sha256,
        "archive_member": meta, "cache_key": cache_key, "receipt": str(receipt),
        "rgd": str(binary), "rgd_sha256": sha(binary),
        "xml": str(xml), "xml_sha256": sha(xml),
    }


def references(root: ET.Element) -> dict:
    variants = {}
    for branch in root.findall("RGDNode"):
        name = branch.get("Key")
        if name not in {"default", "campaign", "cordoba", "xp3"}:
            continue
        records = []
        for node in branch.iter("RGDNode"):
            key, value = node.get("Key", ""), node.get("Value", "")
            if (key in {"animator", "parent_animator", "animator0", "animator1", "animator2", "animator3"}
                    or key.startswith("animator") and key.endswith("_mesh")) and value:
                records.append({"key": key, "value": value})
        variants[name] = records
    return variants


def resolve_model(logical: str) -> dict:
    logical = logical.replace("\\", "/").lower()
    if not logical.endswith(".rgm"):
        logical += ".rgm"
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        rows = db.execute("select logical_path,archive_path,archive,size from resolved_assets "
                          "where lower(logical_path)=?", (logical,)).fetchall()
    if len(rows) != 1:
        raise FileNotFoundError(f"Expected one exact Garrison model index row {logical}; got {rows}")
    path, archive_path, archive, size = rows[0]
    if not Path(archive_path).is_file():
        raise FileNotFoundError(archive_path)
    return {"logical_path": path, "archive_path": archive_path,
            "archive": archive, "bytes": size}


def trace_archer() -> dict:
    guard()
    game = json.loads(CONFIG.read_text(encoding="utf-8"))
    archive = Path(game["game_root"]) / "cardinal/archives/Attrib.sga"
    if not archive.is_file():
        raise FileNotFoundError(archive)
    archive_sha256 = sha(archive)
    owners = {}
    models = {}
    for role, member in ARCHER_ATTACHMENTS.items():
        xml, root, record = extract_rgd(archive, archive_sha256, role, member)
        record["branches"] = references(root)
        record["parent_pbg"] = [n.get("Value") for n in root.iter("RGDNode")
                                if n.get("Key") == "$PBGNAME"]
        owners[role] = record
        for branch_refs in record["branches"].values():
            for ref in branch_refs:
                if ref["value"].lower().startswith("art\\"):
                    m = resolve_model(ref["value"])
                    models[m["logical_path"]] = m
    active = ROOT / "assets/attrib/instances/ebps/vietnam/vn_unit_archer_2_vit.xml"
    active_root = ET.parse(active).getroot()
    active_refs = sorted({n.get("value") for n in active_root.iter("instance_reference")
                          if n.get("name") in {"attachments", "animator_attachments"} and n.get("value")})
    expected = {p.removeprefix("attrib/").removesuffix(".rgd").replace("/", "\\")
                for role, p in ARCHER_ATTACHMENTS.items() if role != "body_parent"}
    if not expected.issubset(set(active_refs)):
        raise RuntimeError(f"Active archer II changed: missing {expected - set(active_refs)}")
    if sha(archive) != archive_sha256:
        raise RuntimeError(f"Official archive changed during donor trace: {archive}")
    report = {"schema": "ccp-060-stock-donor-trace/v1", "status": "traced",
              "evidence_level": "stock source/index/decode, no Blender or native match proof",
              "active_ebps": str(active), "active_ebps_sha256": sha(active),
              "active_attachment_refs": active_refs, "source_archive": str(archive),
              "source_archive_sha256": archive_sha256, "index": str(INDEX),
              "config": str(CONFIG), "owners": owners, "models": models}
    write(DEST / "archer-trace.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["trace-archer"])
    args = parser.parse_args()
    if args.command == "trace-archer":
        result = trace_archer()
        print(json.dumps({"status": result["status"], "report": str(DEST / "archer-trace.json"),
                          "models": result["models"]}, indent=2))


if __name__ == "__main__":
    main()
