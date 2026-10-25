"""Allocate, cook, read back, and register all 23 private 0.8.0 attachment-list identities."""
from __future__ import annotations

import argparse
import copy
import json
import msvcrt
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, ART_EDITOR, CFG, CORE, GUID, NATIVE_LOCK, OUT, RECIPES, ROOT, STAGING, guard, owned, read, sha, write

sys.path.insert(0, str(CFG["garrison_extension"]))
from garrison_shared import rgd  # noqa: E402

PROJECT_KEY = "v80ids"
PROJECT = STAGING / "ids/Mods" / PROJECT_KEY
EVIDENCE = OUT / "bindings"

OFFICIAL_ATTRIB = Path(r"E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga")

DERIVED_LISTS = [
    # 1. Dock (3)
    {
        "key": "dock_age02",
        "name": "vn_080_dock_age02_visual",
        "kind": "building",
        "family": "dock",
        "age": 2,
        "stock_source": r"attachments\attachment_lists\races\chinese\buildings\tier2_unit_naval_control_chi",
        "stock_stamp": "art/stamps/civ_chinese/chi_dock_age_02.bin",
    },
    {
        "key": "dock_age03",
        "name": "vn_080_dock_age03_visual",
        "kind": "building",
        "family": "dock",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\chinese\buildings\tier3_unit_naval_control_chi",
        "stock_stamp": "art/stamps/civ_chinese/chi_dock_age_03.bin",
    },
    {
        "key": "dock_age04",
        "name": "vn_080_dock_age04_visual",
        "kind": "building",
        "family": "dock",
        "age": 4,
        "stock_source": r"attachments\attachment_lists\races\chinese\buildings\tier4_unit_naval_control_chi",
        "stock_stamp": "art/stamps/civ_chinese/chi_dock_age_04.bin",
    },
    # 2. Barracks (4)
    {
        "key": "barracks_age01",
        "name": "vn_080_barracks_age01_visual",
        "kind": "building",
        "family": "barracks",
        "age": 1,
        "stock_source": r"attachments\attachment_lists\races\chinese\buildings\tier1_unit_infantry_control_chi",
        "stock_stamp": "art/stamps/civ_chinese/chi_barracks_age_01.bin",
    },
    {
        "key": "barracks_age02",
        "name": "vn_080_barracks_age02_visual",
        "kind": "building",
        "family": "barracks",
        "age": 2,
        "stock_source": r"attachments\attachment_lists\races\chinese\buildings\tier2_unit_infantry_control_chi",
        "stock_stamp": "art/stamps/civ_chinese/chi_barracks_age_02.bin",
    },
    {
        "key": "barracks_age03",
        "name": "vn_080_barracks_age03_visual",
        "kind": "building",
        "family": "barracks",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\chinese\buildings\tier3_unit_infantry_control_chi",
        "stock_stamp": "art/stamps/civ_chinese/chi_barracks_age_03.bin",
    },
    {
        "key": "barracks_age04",
        "name": "vn_080_barracks_age04_visual",
        "kind": "building",
        "family": "barracks",
        "age": 4,
        "stock_source": r"attachments\attachment_lists\races\chinese\buildings\tier4_unit_infantry_control_chi",
        "stock_stamp": "art/stamps/civ_chinese/chi_barracks_age_04.bin",
    },
    # 3. Water Buffalo (2)
    {
        "key": "water_buffalo_tier",
        "name": "vn_080_water_buffalo_tier_visual",
        "kind": "nonhumanoid",
        "family": "water_buffalo",
        "age": 1,
        "stock_source": r"attachments\attachment_lists\gaia\animals\gaia_herdable_cattle_mal",
        "stock_model": r"art\civilizations\gaia\animals\cow\cow",
    },
    {
        "key": "water_buffalo_anim",
        "name": "vn_080_water_buffalo_anim_visual",
        "kind": "nonhumanoid",
        "family": "water_buffalo",
        "age": 1,
        "stock_source": r"attachments\attachment_lists\gaia\animals\gaia_herdable_cattle_mal",
        "stock_model": r"art\civilizations\gaia\animals\cow\cow",
    },
    # 4. No than / Reinforced No than (2)
    {
        "key": "no_than",
        "name": "vn_080_no_than_visual",
        "kind": "nonhumanoid",
        "family": "no_than",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\english\weapons\tier3_scorpion_eng",
        "stock_model": r"art\civilizations\english\team_weapons\eng_springald\eng_springald",
    },
    {
        "key": "no_than_reinforced",
        "name": "vn_080_no_than_reinforced_visual",
        "kind": "nonhumanoid",
        "family": "no_than",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\english\weapons\tier3_scorpion_eng",
        "stock_model": r"art\civilizations\english\team_weapons\eng_springald\eng_springald",
    },
    # 5. Lam Son Skirmishers base (3)
    {
        "key": "skirmisher2",
        "name": "vn_080_body_skirmisher2",
        "kind": "humanoid",
        "family": "skirmisher",
        "age": 2,
        "stock_source": r"attachments\attachment_lists\races\malians\units\tier2_javelin_mal",
        "stock_model": r"art\civilizations\malian\humans\mal_ranged_crossbow_age02\mal_ranged_crossbow_age02",
    },
    {
        "key": "skirmisher3",
        "name": "vn_080_body_skirmisher3",
        "kind": "humanoid",
        "family": "skirmisher",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\malians\units\tier3_javelin_mal",
        "stock_model": r"art\civilizations\malian\humans\mal_ranged_crossbow_age03\mal_ranged_crossbow_age03",
    },
    {
        "key": "skirmisher4",
        "name": "vn_080_body_skirmisher4",
        "kind": "humanoid",
        "family": "skirmisher",
        "age": 4,
        "stock_source": r"attachments\attachment_lists\races\malians\units\tier4_javelin_mal",
        "stock_model": r"art\civilizations\malian\humans\mal_ranged_crossbow_age04\mal_ranged_crossbow_age04",
    },
    # 6. Rattan Armor / Back-Shield (9)
    {
        "key": "rattan_archer2",
        "name": "vn_080_rattan_archer2",
        "kind": "rattan",
        "family": "rattan",
        "age": 2,
        "stock_source": r"attachments\attachment_lists\races\chinese\units\tier2_archer_chi",
        "stock_model": r"art\civilizations\chinese\humans\chi_ranged_bow_age02\chi_ranged_bow_age02",
    },
    {
        "key": "rattan_archer3",
        "name": "vn_080_rattan_archer3",
        "kind": "rattan",
        "family": "rattan",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\chinese\units\tier3_archer_chi",
        "stock_model": r"art\civilizations\chinese\humans\chi_ranged_bow_age03\chi_ranged_bow_age03",
    },
    {
        "key": "rattan_archer4",
        "name": "vn_080_rattan_archer4",
        "kind": "rattan",
        "family": "rattan",
        "age": 4,
        "stock_source": r"attachments\attachment_lists\races\chinese\units\tier4_archer_chi",
        "stock_model": r"art\civilizations\chinese\humans\chi_ranged_bow_age04\chi_ranged_bow_age04",
    },
    {
        "key": "rattan_skirmisher2",
        "name": "vn_080_rattan_skirmisher2",
        "kind": "rattan",
        "family": "rattan",
        "age": 2,
        "stock_source": r"attachments\attachment_lists\races\malians\units\tier2_javelin_mal",
        "stock_model": r"art\civilizations\malian\humans\mal_ranged_crossbow_age02\mal_ranged_crossbow_age02",
    },
    {
        "key": "rattan_skirmisher3",
        "name": "vn_080_rattan_skirmisher3",
        "kind": "rattan",
        "family": "rattan",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\malians\units\tier3_javelin_mal",
        "stock_model": r"art\civilizations\malian\humans\mal_ranged_crossbow_age03\mal_ranged_crossbow_age03",
    },
    {
        "key": "rattan_skirmisher4",
        "name": "vn_080_rattan_skirmisher4",
        "kind": "rattan",
        "family": "rattan",
        "age": 4,
        "stock_source": r"attachments\attachment_lists\races\malians\units\tier4_javelin_mal",
        "stock_model": r"art\civilizations\malian\humans\mal_ranged_crossbow_age04\mal_ranged_crossbow_age04",
    },
    {
        "key": "rattan_crossbow3",
        "name": "vn_080_rattan_crossbow3",
        "kind": "rattan",
        "family": "rattan",
        "age": 3,
        "stock_source": r"attachments\attachment_lists\races\chinese\units\tier3_crossbow_chi",
        "stock_model": r"art\civilizations\chinese\humans\chi_ranged_crossbow_age03\chi_ranged_crossbow_age03",
    },
    {
        "key": "rattan_crossbow4",
        "name": "vn_080_rattan_crossbow4",
        "kind": "rattan",
        "family": "rattan",
        "age": 4,
        "stock_source": r"attachments\attachment_lists\races\chinese\units\tier4_crossbow_chi",
        "stock_model": r"art\civilizations\chinese\humans\chi_ranged_crossbow_age04\chi_ranged_crossbow_age04",
    },
    {
        "key": "rattan_handcannon4",
        "name": "vn_080_rattan_handcannon4",
        "kind": "rattan",
        "family": "rattan",
        "age": 4,
        "stock_source": r"attachments\attachment_lists\races\chinese\units\tier4_handcannon_chi",
        "stock_model": r"art\civilizations\chinese\humans\chi_ranged_cannoneer_age04\chi_ranged_cannoneer_age04",
    },
]


def invoke(label: str, args: list[str | Path], timeout: int = 300) -> Path:
    proc = subprocess.run(
        [str(x) for x in args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    log = owned(EVIDENCE / "logs" / f"{label}.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"EXIT {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}", encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {proc.returncode}); see {log}")
    return log


def locked(action):
    with NATIVE_LOCK.open("r+b") as handle:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            return action()
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def prepare() -> dict:
    guard()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    plan_path = write(RECIPES / "derived-lists-080.json", {"schema": "ccp.release080.derived-lists/v1", "entries": DERIVED_LISTS})
    receipt = EVIDENCE / "prepare.json"
    if receipt.exists() and read(receipt).get("status") == "prepared":
        return read(receipt)

    def op():
        if not (PROJECT / "mod-project.json").exists():
            invoke("create", [CORE, "mod-project", "create", "--library", PROJECT.parent.parent, "--name", PROJECT.name])
        invoke("settings", [CORE, "mod-project", "settings", "--project", PROJECT, "--live-reload", "off", "--mod-id", GUID])
        cfg = read(PROJECT / "mod-project.json")
        existing = {r["name"] for r in cfg.get("derived_blueprints", [])}
        for row in DERIVED_LISTS:
            if row["name"] not in existing:
                invoke(
                    "derive-" + row["key"],
                    [CORE, "mod-project", "derive", "--project", PROJECT, "--source", row["stock_source"].replace("\\", "/"), "--name", row["name"]],
                )
        cfg = read(PROJECT / "mod-project.json")
        assert not cfg.get("game_mode", {}).get("enabled") and not cfg.get("game_mode", {}).get("live_reload")
        assert len(cfg.get("derived_blueprints", [])) == len(DERIVED_LISTS)
        state = {
            "status": "prepared",
            "project": str(PROJECT),
            "plan": str(plan_path),
            "plan_sha256": sha(plan_path),
            "config_sha256": sha(PROJECT / "mod-project.json"),
            "count": len(DERIVED_LISTS),
        }
        write(receipt, state)
        return state

    return locked(op)


def cook() -> dict:
    guard()
    prep = prepare()
    receipt = EVIDENCE / "cook.json"
    if receipt.exists() and read(receipt).get("status") == "cooked":
        return read(receipt)

    def op():
        log = invoke("cook", [CORE, "mod-project", "cook", "--project", PROJECT, "--editor", ART_EDITOR, "--timeout", "1200"], timeout=1300)
        cfg = read(PROJECT / "mod-project.json")
        assert cfg.get("cooks"), "No cook recorded in mod-project.json"
        last = cfg["cooks"][-1]
        archive = owned(last["archive"])
        assert sha(archive) == last["sha256"]
        listed = json.loads(subprocess.check_output([str(ARCH), "list", "--verify", str(archive)], text=True))
        assert listed["archive"]["verification"]["verified"]
        state = {
            "status": "cooked",
            "archive": str(archive),
            "archive_sha256": sha(archive),
            "log": str(log),
            "log_sha256": sha(log),
            "member_count": len(listed["members"]),
        }
        write(receipt, state)
        return state

    return locked(op)


def register(write_source: bool = False) -> dict:
    guard()
    cooked = cook()
    archive = Path(cooked["archive"])
    assert sha(archive) == cooked["archive_sha256"]

    # Collect all existing PBGIDs in source XMLs to prevent collisions
    existing_pbgids = set()
    for xml_path in (ROOT / "assets/attrib/instances").rglob("*.xml"):
        if "release_080" in xml_path.parts:
            continue
        for node in ET.parse(xml_path).getroot().iter("uniqueid"):
            if node.attrib.get("name") == "pbgid":
                existing_pbgids.add(int(node.attrib["value"]))

    readback_dir = owned(STAGING / "ids/readback")
    stock_dir = owned(STAGING / "ids/stock")
    readback_dir.mkdir(parents=True, exist_ok=True)
    stock_dir.mkdir(parents=True, exist_ok=True)

    entries = {}
    for row in DERIVED_LISTS:
        name = row["name"]
        gen_member = f"attrib/attachments/attachment_lists/garrison/{PROJECT_KEY}/{name}.rgd"
        stock_member = "attrib/" + row["stock_source"].replace("\\", "/") + ".rgd"
        gen_path = readback_dir / f"{name}.rgd"
        stk_path = stock_dir / f"{Path(stock_member).name}"
        if not gen_path.exists():
            subprocess.run([str(ARCH), "extract-member", str(archive), gen_member, str(gen_path)], check=True, capture_output=True)
        if not stk_path.exists():
            subprocess.run([str(ARCH), "extract-member", str(OFFICIAL_ATTRIB), stock_member, str(stk_path)], check=True, capture_output=True)

        gen_doc = rgd.read(gen_path.read_bytes())
        pbgids = {n.value for _, n in rgd.flatten(gen_doc.nodes) if n.key == "pbgid"}
        assert len(pbgids) == 1, (name, pbgids)
        pbgid = next(iter(pbgids))
        assert isinstance(pbgid, int) and pbgid not in existing_pbgids, f"PBGID collision for {name}: {pbgid}"
        existing_pbgids.add(pbgid)

        # Verify stock RGD roundtrip and identity-only clone reversibility
        stk_bytes = stk_path.read_bytes()
        stk_doc = rgd.read(stk_bytes)
        assert rgd.write(stk_doc) == stk_bytes, f"Stock roundtrip mismatch for {stock_member}"
        cloned = copy.deepcopy(stk_doc)
        for _, n in rgd.flatten(cloned.nodes):
            if n.key == "pbgid":
                n.value = pbgid
        cloned_bytes = rgd.write(cloned)
        clone_path = readback_dir / f"{name}.identity_clone.rgd"
        clone_path.write_bytes(cloned_bytes)

        rel_xml = f"attrib/instances/attachments/attachment_lists/vietnam/release_080/{name}.xml"
        final_member = f"attrib/attachments/attachment_lists/vietnam/release_080/{name}.rgd"
        instance_ref = f"attachments\\attachment_lists\\vietnam\\release_080\\{name}"

        if write_source:
            doc = ET.Element(
                "instance",
                version="2",
                description="Private 0.8.0 visual attachment list identity",
                template=r"attachments\attachment_lists",
            )
            ET.SubElement(doc, "uniqueid", name="pbgid", value=str(pbgid))
            ET.SubElement(doc, "instance_reference", name="parent_pbg", value=row["stock_source"])
            ET.indent(doc, space="\t")
            raw_xml = ET.tostring(doc, encoding="utf-8", xml_declaration=True) + b"\n"
            dest_xml = ROOT / "assets" / rel_xml
            dest_xml.parent.mkdir(parents=True, exist_ok=True)
            dest_xml.write_bytes(raw_xml)

        entries[row["key"]] = {
            **row,
            "pbgid": pbgid,
            "generated_member": gen_member,
            "generated_path": str(gen_path),
            "generated_sha256": sha(gen_path),
            "stock_member": stock_member,
            "stock_path": str(stk_path),
            "stock_sha256": sha(stk_path),
            "identity_clone_path": str(clone_path),
            "identity_clone_sha256": sha(clone_path),
            "source_xml": rel_xml,
            "instance_reference": instance_ref,
            "final_member": final_member,
        }

    result = {
        "schema": "ccp.release080.registered-identities/v1",
        "status": "registered",
        "count": len(entries),
        "write_source": write_source,
        "entries": entries,
    }
    write(EVIDENCE / "registered-identities.json", result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("prepare", "cook", "register"))
    ap.add_argument("--write-source", action="store_true")
    args = ap.parse_args()
    if args.action == "prepare":
        res = prepare()
    elif args.action == "cook":
        res = cook()
    else:
        res = register(write_source=args.write_source)
    print(json.dumps({"status": res["status"], "count": res.get("count")}, indent=2))


if __name__ == "__main__":
    main()
