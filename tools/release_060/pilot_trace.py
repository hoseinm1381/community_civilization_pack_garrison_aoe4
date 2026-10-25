"""Trace exact official model donors for isolated 0.6.0 representative pilots.

This reads active source, current Attrib.sga, and the installed Garrison index.
It writes only output/release_060/pilots and never changes game or mod sources.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, OUT, ROOT, guard, owned, read, sha, write

DEST = OUT / "pilots"
INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
CONFIG = INDEX.with_name("game-assets.local.json")
PILOTS = {
    "spear2": "assets/attrib/instances/ebps/vietnam/vn_unit_spearman_2_chi.xml",
    "male_villager1": "assets/attrib/instances/ebps/vietnam/vn_unit_villager_1_chi.xml",
    "female_villager1": "assets/attrib/instances/ebps/vietnam/vn_unit_villager_1_chi.xml",
    "horseman2": "assets/attrib/instances/ebps/vietnam/vn_unit_horseman_2_chi.xml",
    "elephant": "assets/attrib/instances/ebps/vietnam/vn_unit_war_elephant_1_vit.xml",
    "siege_mangonel3": "attrib/ebps/races/chinese/units/unit_mangonel_3_chi.rgd",
}
_ARCHIVE_HASHES: dict[Path, str] = {}


def arch(*args: object) -> dict:
    done = subprocess.run([str(ARCH), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    if done.returncode:
        raise RuntimeError(f"archive command failed {done.returncode}: {done.stderr[-1000:]}")
    return json.loads(done.stdout)


def exact_member(archive: Path, member: str) -> dict:
    rows = arch("list", archive, "--filter", Path(member).name)["members"]
    hits = [r for r in rows if r["path"].lower() == member.lower()]
    if len(hits) != 1:
        raise FileNotFoundError(f"Official archive exact member mismatch: {member}: {hits}")
    return hits[0]


def decode(archive: Path, pilot: str, member: str) -> tuple[ET.Element, dict]:
    meta = exact_member(archive, member)
    if archive not in _ARCHIVE_HASHES:
        _ARCHIVE_HASHES[archive] = sha(archive)
    archive_hash = _ARCHIVE_HASHES[archive]
    target = owned(DEST / pilot / "rgd" / ("attrib-" + archive_hash[:16]) /
                   member.removeprefix("attrib/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    xml = target.with_suffix(".xml")
    receipt = target.with_suffix(".receipt.json")
    if target.exists() or xml.exists():
        if not (target.is_file() and xml.is_file() and receipt.is_file()):
            raise RuntimeError(f"Incomplete official RGD cache: {target}")
        old = read(receipt)
        expected = {"archive_sha256": archive_hash, "member": member,
                    "member_crc": meta["crc"], "member_size": meta["size"]}
        if any(old.get(k) != v for k, v in expected.items()):
            raise RuntimeError(f"Stale official RGD cache identity: {target}")
        if old["rgd_sha256"] != sha(target) or old["xml_sha256"] != sha(xml):
            raise RuntimeError(f"Modified official RGD cache: {target}")
    if not target.exists():
        arch("extract-member", archive, member, target)
    if not xml.exists():
        arch("decode-rgd", target, xml)
    if not receipt.exists():
        write(receipt, {"archive_sha256": archive_hash, "member": member,
                        "member_crc": meta["crc"], "member_size": meta["size"],
                        "rgd_sha256": sha(target), "xml_sha256": sha(xml)})
    return ET.parse(xml).getroot(), {"member": member, "member_meta": meta,
                                     "rgd": str(target), "rgd_sha256": sha(target),
                                     "xml": str(xml), "xml_sha256": sha(xml)}


def active_references(root: ET.Element) -> list[dict]:
    found = []
    for variant in root.findall("variant"):
        for node in variant.iter("instance_reference"):
            if node.get("name") in {"attachments", "animator_attachments"} and node.get("value"):
                found.append({"variant": variant.get("name"), "field": node.get("name"),
                              "value": node.get("value"), "mod": node.get("mod")})
    return found


def rgd_path(ref: str) -> str:
    return "attrib/" + ref.replace("\\", "/") + ".rgd"


def stock_models(root: ET.Element) -> list[dict]:
    records = []
    for variant in root.findall("RGDNode"):
        for node in variant.iter("RGDNode"):
            key, value = node.get("Key", ""), node.get("Value", "")
            if value.lower().startswith("art\\") and (key.startswith("animator") or key == "parent_animator"):
                records.append({"variant": variant.get("Key"), "field": key, "value": value})
    return records


def index_model(db: sqlite3.Connection, reference: str) -> dict:
    logical = reference.replace("\\", "/").lower()
    if not logical.endswith(".rgm"):
        logical += ".rgm"
    rows = db.execute("select logical_path,archive_path,archive,size from resolved_assets "
                      "where lower(logical_path)=?", (logical,)).fetchall()
    if len(rows) != 1:
        return {"logical_path": logical, "status": "unresolved", "index_matches": rows}
    path, archive_path, archive, size = rows[0]
    return {"logical_path": path, "archive_path": archive_path,
            "archive": archive, "bytes": size,
            "status": "confirmed" if Path(archive_path).is_file() else "archive_missing"}


def trace(selected: str | None = None) -> dict:
    guard()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    archive = Path(cfg["game_root"]) / "cardinal/archives/Attrib.sga"
    if not archive.is_file() or not INDEX.is_file():
        raise FileNotFoundError("Current official Attrib or Garrison index unavailable")
    prior = DEST / "pilot-trace.json"
    existing = json.loads(prior.read_text(encoding="utf-8")) if selected and prior.is_file() else None
    result = existing or {"schema": "ccp-060-pilot-donor-trace/v1",
              "evidence": "current active XML, official Attrib.sga RGD and Garrison SQLite index; no Blender or native proof",
              "official_attrib": str(archive), "official_attrib_sha256": sha(archive),
              "index": str(INDEX), "pilots": {}}
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        for pilot, source in PILOTS.items():
            if selected and pilot != selected:
                continue
            if source.endswith(".xml"):
                p = ROOT / source
                active_root = ET.parse(p).getroot()
                source_record = {"source": str(p), "source_sha256": sha(p)}
            else:
                active_root, source_record = decode(archive, pilot, source)
            refs = active_references(active_root)
            # The official RGD decoder names variants RGDNode and fields RGDNode.
            if pilot.startswith("siege"):
                refs = []
                for variant in active_root.findall("RGDNode"):
                    for n in variant.iter("RGDNode"):
                        if n.get("Key") in {"attachments", "animator_attachments"}:
                            name = n.find("./RGDNode[@Key='$PBGNAME']")
                            mapping = n.find("./RGDNode[@Key='$PBGMAP']")
                            if name is not None and mapping is not None and name.get("Value"):
                                value = mapping.get("Value", "") + "\\" + name.get("Value", "")
                                refs.append({"variant": variant.get("Key"), "field": n.get("Key"),
                                             "value": value, "mod": None})
            owners, models, missing = {}, {}, []
            for ref in refs:
                if ref["mod"]:
                    missing.append({"reference": ref, "reason": "private owner, inspect separately"})
                    continue
                member = rgd_path(ref["value"])
                if member in owners:
                    continue
                try:
                    node, evidence = decode(archive, pilot, member)
                except FileNotFoundError as exc:
                    # Compiled EBPS stores a PBG map plus basename, so resolve
                    # its one exact attachment-list member by filename.
                    hits = [m["path"] for m in arch("list", archive, "--filter", Path(member).name)["members"]
                            if m["path"].startswith("attrib/attachments/attachment_lists/")
                            and Path(m["path"]).name.lower() == Path(member).name.lower()]
                    if len(hits) != 1:
                        missing.append({"reference": ref, "reason": str(exc), "candidate_paths": hits})
                        continue
                    member = hits[0]
                    if member in owners:
                        continue
                    node, evidence = decode(archive, pilot, member)
                evidence["models"] = stock_models(node)
                owners[member] = evidence
                for model in evidence["models"]:
                    models[model["value"]] = index_model(db, model["value"])
            result["pilots"][pilot] = {"owner": source_record,
                                      "active_attachment_refs": refs,
                                      "attachment_rgds": owners,
                                      "stock_models": models,
                                      "unresolved": missing}
    write(DEST / "pilot-trace.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=PILOTS)
    report = trace(parser.parse_args().pilot)
    for name, pilot in report["pilots"].items():
        print(f"{name}: {len(pilot['attachment_rgds'])} RGDs, "
              f"{len(pilot['stock_models'])} models, {len(pilot['unresolved'])} unresolved refs")
