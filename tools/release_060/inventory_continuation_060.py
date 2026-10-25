"""Continue the 0.6.0 siege visual inventory from current official archives."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

from common import CFG, OUT, guard, owned, read, sha

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = OUT / "inventory/continuation"
ATTRIB = Path(r"E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga")
ART_HIGH = ATTRIB.parent / "ArtHigh.sga"
ART_CIV = ATTRIB.parent / "ArtCivilizations.sga"
INDEX = OUT / "inventory/inherited-render-bodies-v2/run-003/private-index-exact.sqlite3"
OLD_LEDGER = OUT / "inventory/inherited-render-bodies-v2/render-body-ledger-v2.json"
COVERAGE = OUT / "inventory/coverage-audit-v2.json"
TOOL = Path(CFG["archive_tool"])

ATTRIB_MEMBERS = [
    "attrib/ebps/races/chinese/units/unit_ram_3_chi.rgd",
    "attrib/attachments/attachment_lists/races/chinese/units/unit_ram_3_chi.rgd",
    "attrib/sbps/races/chinese/unit_ram_3_chi.rgd",
    "attrib/ebps/races/chinese/units/unit_workshop_ram_3_chi.rgd",
    "attrib/sbps/races/chinese/unit_workshop_ram_3_chi.rgd",
    "attrib/ebps/races/chinese/units/unit_springald_3_chi.rgd",
    "attrib/attachments/attachment_lists/races/chinese/units/unit_scorpion_3_chi.rgd",
    "attrib/sbps/races/chinese/unit_springald_3_chi.rgd",
    "attrib/ebps/races/chinese/units/unit_trebuchet_4_cw_chi.rgd",
    "attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_trebuchet_cw_chi.rgd",
    "attrib/attachments/attachment_lists/races/chinese/units/unit_trebuchet_4_cw_chi.rgd",
    "attrib/sbps/races/chinese/unit_trebuchet_4_cw_chi.rgd",
    "attrib/ebps/races/chinese/units/unit_trebuchet_4_tr_chi.rgd",
    "attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_trebuchet_tr_chi.rgd",
    "attrib/attachments/attachment_lists/races/chinese/units/unit_trebuchet_4_tr_chi.rgd",
    "attrib/sbps/races/chinese/unit_trebuchet_4_tr_chi.rgd",
    "attrib/attachments/attachment_lists/races/core/units/unit_siege_cart.rgd",
    "attrib/ebps/dev/units/unit_siege_cart.rgd",
    "attrib/sbps/dev/unit_siege_cart.rgd",
    "attrib/attachments/attachment_lists/races/english/units/unit_ram_3_eng.rgd",
    "attrib/attachments/attachment_lists/races/english/units/unit_trebuchet_4_cw_eng.rgd",
    "attrib/attachments/attachment_lists/races/english/units/unit_trebuchet_4_tr_eng.rgd",
    "attrib/attachments/attachment_lists/civilizations/english/units/tier4_trebuchet_cw_eng.rgd",
    "attrib/attachments/attachment_lists/civilizations/english/units/tier4_trebuchet_tr_eng.rgd",
]

FAMILIES = {
    "ram": {
        "reachable_actor": "ebps\\races\\chinese\\units\\unit_ram_3_chi",
        "squad_consumers": ["unit_ram_3_chi", "unit_workshop_ram_3_chi"],
        "native_attachment": "attrib/attachments/attachment_lists/races/chinese/units/unit_ram_3_chi.rgd",
        "private_visual_targets": ["Vietnamese unit_ram_3_chi actor", "Vietnamese workshop_ram squad consumer"],
        "variants": ["base", "campaign", "xp3"],
    },
    "springald": {
        "reachable_actor": "sbps\\races\\chinese\\unit_springald_3_chi -> ebps\\races\\chinese\\units\\unit_springald_3_chi",
        "squad_consumers": ["unit_springald_3_chi"],
        "native_attachment": "attrib/attachments/attachment_lists/races/chinese/units/unit_scorpion_3_chi.rgd",
        "private_visual_targets": ["Vietnamese siege-control Springald base/campaign spawn item"],
        "variants": ["base", "campaign"],
    },
    "trebuchet_counterweight": {
        "reachable_actor": "sbps\\races\\chinese\\unit_trebuchet_4_cw_chi -> ebps\\races\\chinese\\units\\unit_trebuchet_4_cw_chi",
        "squad_consumers": ["unit_trebuchet_4_cw_chi"],
        "native_attachment": "attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_trebuchet_cw_chi.rgd",
        "private_visual_targets": ["Vietnamese siege-control Counterweight Trebuchet base item"],
        "variants": ["base", "campaign"],
    },
    "trebuchet_traction": {
        "reachable_actor": "sbps\\races\\chinese\\unit_trebuchet_4_tr_chi -> ebps\\races\\chinese\\units\\unit_trebuchet_4_tr_chi",
        "squad_consumers": ["unit_trebuchet_4_tr_chi"],
        "native_attachment": "attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_trebuchet_tr_chi.rgd",
        "private_visual_targets": ["Vietnamese siege-control Traction Trebuchet campaign item"],
        "variants": ["base", "campaign"],
    },
}


def call_json(*args: str) -> dict:
    return json.loads(subprocess.check_output([str(TOOL), *args], text=True, encoding="utf-8"))


def archive_member_hash(archive: Path, member: str, folder: Path, run: str) -> dict:
    target = owned(folder / run / member.replace("/", "__"))
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        call_json("extract-member", str(archive), member, str(target))
    return {"archive": archive.name, "archive_path": str(archive), "member": member,
            "bytes": target.stat().st_size, "sha256": sha(target), "readback": str(target)}


def variant_paths(xml_path: Path) -> dict:
    root = ET.parse(xml_path).getroot()
    variants = {}
    for node in root.findall("RGDNode"):
        if node.attrib.get("Type") != "List":
            continue
        name = node.attrib.get("Key", "")
        if name not in {"default", "campaign", "xp3", "cordoba"}:
            continue
        vals = []
        for item in node.iter("RGDNode"):
            key, val = item.attrib.get("Key", ""), item.attrib.get("Value", "")
            if val and (key in {"parent_animator", "alternate_sua", "animator"} or key.startswith("animator")):
                vals.append({"field": key, "value": val.replace("\\", "/")})
        variants[name] = vals
    return variants


def main() -> None:
    guard()
    for p in (ATTRIB, ART_HIGH, ART_CIV, INDEX, OLD_LEDGER, COVERAGE):
        if not p.is_file():
            raise FileNotFoundError(p)
    if not OUT_DIR.resolve().is_relative_to(OUT.resolve()):
        raise ValueError("Continuation output escaped release_060 ownership")
    run = "official-archive-readback-001"
    evidence_dir = owned(OUT_DIR / "archive-readback")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    old = read(OLD_LEDGER)
    coverage = read(COVERAGE)
    attrib_listing = call_json("list", str(ATTRIB))
    available = {item["path"]: item for item in attrib_listing["members"]}
    civ_listing = call_json("list", str(ART_CIV))
    available_civ = {item["path"]: item for item in civ_listing["members"]}
    extracted = {}
    xml_by_member = {}
    for member in ATTRIB_MEMBERS:
        if member not in available:
            raise RuntimeError(f"Current Attrib.sga is missing required member: {member}")
        row = archive_member_hash(ATTRIB, member, evidence_dir, run)
        xml_path = owned(Path(row["readback"]).with_suffix(".xml"))
        if not xml_path.exists():
            call_json("decode-rgd", row["readback"], str(xml_path))
        row["member_size_from_archive_list"] = available[member]["size"]
        row["decoded_xml"] = str(xml_path)
        row["decoded_xml_sha256"] = sha(xml_path)
        row["variant_render_fields"] = variant_paths(xml_path)
        extracted[member] = row
        xml_by_member[member] = xml_path

    db = sqlite3.connect(INDEX)
    db.row_factory = sqlite3.Row
    models = {}
    candidates = {}
    for consumer in old["consumers"]:
        for item in consumer.get("candidate_decode_evidence") or []:
            logical = item["logical_path"]
            candidates[logical] = item
    manifests = {}
    for logical, item in candidates.items():
        mpath = Path(item["manifest"])
        if sha(mpath) != item["manifest_sha256"]:
            raise RuntimeError(f"Pinned candidate manifest drift: {mpath}")
        manifest = read(mpath)
        manifests[logical] = manifest
        model_path = Path(manifest["resources"]["model"]["cache_path"])
        models[logical] = archive_member_hash(ART_HIGH, logical, evidence_dir, run)
        if sha(model_path) != manifest["resources"]["model"]["sha256"]:
            raise RuntimeError(f"Official model source differs from pinned decode: {logical}")
        models[logical]["sha256_matches_pinned_decode"] = True
        models[logical]["geometry_groups"] = manifest["geometry"]["group_count"]
        models[logical]["triangle_count"] = item.get("triangle_count")
        models[logical]["skeleton_bones"] = manifest["skeleton"].get("bone_count")
        models[logical]["animation_projection"] = manifest["animation_projection"].get("status")
        models[logical]["crew_named_mesh_groups"] = [g.get("name") for g in manifest["geometry"]["groups"]
                                                       if any(t in (g.get("name") or "").lower() for t in ("crew", "human", "man", "soldier"))]
        deps = []
        for ext in ("geometry", "material"):
            source = manifest["resources"].get(ext) or {}
            if source.get("logical_path"):
                deps.append({"logical_path": source["logical_path"], "archive": source.get("archive"),
                             "archive_path": source.get("archive_path"), "bytes": source.get("size"),
                             "sha256": source.get("sha256"), "evidence": "Garrison exact decoder source manifest"})
        for tex in manifest.get("textures", []):
            src = tex.get("source") or {}
            logical_tex = tex.get("logical_path")
            if logical_tex:
                provider = db.execute("select archive, archive_path, size from resolved_assets where logical_path=?", (logical_tex,)).fetchone()
                deps.append({"logical_path": logical_tex, "archive": provider["archive"] if provider else None,
                             "archive_path": provider["archive_path"] if provider else None,
                             "bytes": src.get("size"), "sha256": src.get("sha256"),
                             "evidence": "Garrison exact decoder source manifest"})
        models[logical]["private_visual_dependencies"] = deps

    common_owners = {}
    for consumer in old["consumers"]:
        if not any(k in consumer["id"] for k in ("ram", "springald", "trebuchet")):
            continue
        for logical in consumer.get("active_render_models", []):
            if logical in common_owners:
                continue
            stem = logical.removesuffix(".rgm")
            sidecars = []
            for suffix in (".rgo", ".rhka", ".rootmotion"):
                logical_file = stem + suffix
                if logical_file in available_civ:
                    sidecars.append(archive_member_hash(ART_CIV, logical_file, evidence_dir, run))
            if sidecars:
                common_owners[logical] = {"role": "native parent animator and motion owners; preserve",
                    "sidecars": sidecars,
                    "same_stem_rrgeom_rrmaterial_indexed": bool(db.execute(
                        "select 1 from resolved_assets where logical_path in (?,?)",
                        (stem + ".rrgeom", stem + ".rrmaterial")).fetchone())}

    actor_coverage = {x["id"]: x for x in coverage["included_inherited_stock_actors"]}
    covered = {}
    for key, spec in FAMILIES.items():
        matches = [x for x in coverage["included_inherited_stock_actors"]
                   if x["id"] in spec["squad_consumers"] or x["id"] == Path(spec["reachable_actor"].split(" -> ")[0].split("\\")[-1]).stem]
        covered[key] = {"plan": spec, "coverage": matches}

    vn_control = ROOT / "assets/attrib/instances/ebps/vietnam/vn_building_unit_siege_control_chi.xml"
    vn_hash = sha(vn_control)
    discounts = coverage.get("discounted_or_free_alternate_consumers", [])
    ram_alternates = [name for name in actor_coverage["unit_ram_3_chi"]["consumers"]
                      if name.endswith("_cheap") or name.endswith("_free")]

    # The native generic parent animators own mechanics and motion. English bodies
    # are already explicit visual references on the applicable Chinese actors/lists.
    ledger = {
        "schema": "ccp-060-inventory-continuation/v1",
        "status": "official_render_routes_corrected; crew_render_closure_unresolved",
        "created_utc_date": "2026-10-18",
        "authority": "user-approved 0.6.0 continuation",
        "storage_guard": "passed before output writes",
        "inputs": {"coverage_audit": {"path": str(COVERAGE), "sha256": sha(COVERAGE)},
                   "previous_render_ledger": {"path": str(OLD_LEDGER), "sha256": sha(OLD_LEDGER)},
                   "official_attrib_archive": {"path": str(ATTRIB), "member_count": attrib_listing["archive"]["file_count"]},
                   "official_asset_index": {"path": str(INDEX), "sha256": sha(INDEX)},
                   "vietnamese_siege_control_source": {"path": str(vn_control), "sha256": vn_hash}},
        "coverage_gate": {"families": covered, "discounted_or_free_alternates": discounts,
                          "alternate_discounted_or_free_consumers_of_ram_builder": ram_alternates,
                          "item_gate_evaluation": "coverage audit records not_evaluated; verify at integration against all source/base/campaign consumers",
                          "vn_siege_control_source_variants": ["base", "campaign"],
                          "source_fields_preserved": ["spawn item IDs", "costs", "requirements", "queue values", "weapons", "abilities", "upgrades", "animation owners"]},
        "attributed_consumer_paths": extracted,
        "candidate_visual_models": models,
        "native_parent_animator_owner_rgos": common_owners,
        "binding_plan": [
            {"family": "ram", "consumers": "22 Vietnamese army builders listed for official unit_ram_3_chi plus the Vietnamese workshop ram squad", "native_actor": "attrib/ebps/races/chinese/units/unit_ram_3_chi.rgd", "native_squad": "attrib/sbps/races/chinese/unit_ram_3_chi.rgd; workshop squad attrib/sbps/races/chinese/unit_workshop_ram_3_chi.rgd", "native_attachment": "attrib/attachments/attachment_lists/races/chinese/units/unit_ram_3_chi.rgd", "body": "native parent animator art/civilizations/common/team_weapons/archetypes/battering_ram/battering_ram; EBPS alternate_sua explicitly points to English eng_battering_ram", "binding": "one private VN actor/list route for base/campaign/xp3 and private eng_battering_ram visual under Vietnamese identity; update all 22 VN builder construction references and workshop squad binding while preserving the Chinese actor", "weapon_mount_crew": "retain native ram weapon and generic parent RGO/action owner; not a weapon/model replacement", "status": "route evidenced; alternate_sua should be treated as a separate state path from the base animator"},
            {"family": "springald", "consumers": "Vietnamese siege-control base/campaign item", "native_actor": "attrib/ebps/races/chinese/units/unit_springald_3_chi.rgd", "native_squad": "attrib/sbps/races/chinese/unit_springald_3_chi.rgd", "native_attachment": "attrib/attachments/attachment_lists/races/chinese/units/unit_scorpion_3_chi.rgd", "body": "native parent animator common springald; EBPS alternate_sua explicitly points to English eng_springald", "binding": "private VN squad/actor/list route for base/campaign and private eng_springald visual; preserve native parent animator and weapon/ability references", "weapon_mount_crew": "retain native springald weapon and parent RGO/action owner", "status": "route evidenced; alternate_sua is an additional state path"},
            {"family": "trebuchet_counterweight", "consumers": "Vietnamese siege-control base spawn item", "native_actor": "attrib/ebps/races/chinese/units/unit_trebuchet_4_cw_chi.rgd", "native_squad": "attrib/sbps/races/chinese/unit_trebuchet_4_cw_chi.rgd", "native_attachment": "attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_trebuchet_cw_chi.rgd", "body": "common trebuchet_counterweight parent animator plus existing English eng_trebuchet_counterweight skin attachment in default/cordoba; campaign uses merge-mesh attachment", "binding": "private VN Tier IV list for default/campaign/cordoba/xp3 matching source variants, replace only the English animator path with qualified private visual, preserve attachment type and common parent animator", "weapon_mount_crew": "SBPS also references core unit_siege_cart; preserve this actor and native trebuchet parent RGO. Candidate geometry contains frame/mast/sling/projectile groups and no crew-named mesh group", "status": "body route directly evidenced; separate crew render actor unresolved"},
            {"family": "trebuchet_traction", "consumers": "Vietnamese siege-control campaign spawn item", "native_actor": "attrib/ebps/races/chinese/units/unit_trebuchet_4_tr_chi.rgd", "native_squad": "attrib/sbps/races/chinese/unit_trebuchet_4_tr_chi.rgd", "native_attachment": "attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_trebuchet_tr_chi.rgd", "body": "common trebuchet_traction parent animator plus existing English eng_trebuchet_traction skin attachment in default/cordoba; campaign uses merge-mesh attachment", "binding": "private VN Tier IV list for default/campaign/cordoba/xp3 matching source variants, replace only the English animator path with qualified private visual, preserve attachment type and common parent animator", "weapon_mount_crew": "SBPS also references core unit_siege_cart; preserve this actor and native trebuchet parent RGO. Candidate geometry contains trebuchet/rope/projectile groups and no crew-named mesh group", "status": "body route directly evidenced; separate crew render actor unresolved"},
            {"family": "siege_cart_shared", "consumers": "both Vietnamese counterweight and traction treb squads", "native_actor": "attrib/ebps/dev/units/unit_siege_cart.rgd", "native_squad": "attrib/sbps/dev/unit_siege_cart.rgd", "native_attachment": "attrib/attachments/attachment_lists/races/core/units/unit_siege_cart.rgd", "body": "generic siege_cart path lacks same-stem geometry/material provider; installed stock exposes RGO/RHKA/rootmotion only in current exact index", "binding": "keep native cart and animation owners byte-for-byte until complete crew/body closure is identified; do not graft the English trebuchet body as a substitute for this dependency", "status": "unresolved render/crew route"}
        ],
        "unresolved": ["exact rendered model/crew dependency for core unit_siege_cart", "full parse of generic RGO action/crew references", "item eligibility for each native base/campaign/XP3 variant", "native appearance and selected-weapon animation"],
        "scope_note": "Ships, buildings and official consumers the user has confirmed unavailable remain excluded. No source or old release was changed. No Blender, cook, package, import, lobby or match operation was run."
    }
    ledger_path = owned(OUT_DIR / "continuation-ledger-v3.json")
    if ledger_path.exists():
        raise FileExistsError(ledger_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": ledger["status"], "ledger": str(ledger_path),
                      "official_rgds": len(extracted), "direct_model_candidates": len(models),
                      "crew_route": "unresolved"}, indent=2))


if __name__ == "__main__":
    main()
