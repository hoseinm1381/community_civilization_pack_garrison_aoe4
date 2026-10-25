"""Write the nine-consumer inherited render-body closure ledger."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from common import OUT, guard, owned, sha

ROOT = Path(__file__).resolve().parents[2]
BASE = OUT / "inventory/inherited-render-bodies-v2"
COVERAGE = OUT / "inventory/coverage-audit-v2.json"
DECODE = BASE / "run-003/receipt.json"
PREVIOUS = OUT / "inventory/remaining-donors/run-004/batch-report-v2.json"
DEST = owned(BASE / "render-body-ledger-v2.json")

ROWS = [
    {
        "id": "unit_ram_3_chi", "variants": ["base", "campaign", "xp3"],
        "tier_and_parent": "Chinese RGD unit_ram_3_chi, all four list variants use parent_animator common/team_weapons/archetypes/battering_ram/battering_ram; empty attachment list.",
        "active_render_models": ["art/civilizations/common/team_weapons/archetypes/battering_ram/battering_ram.rgm"],
        "render_status": "active animator reference, no same-stem RRGeometry or RRMaterial; actual geometry unresolved",
        "decoded_donor_candidates": ["art/civilizations/english/team_weapons/eng_battering_ram/eng_battering_ram.rgm"],
        "donor_role": "decoded geometry candidate only; current Chinese attachment RGD does not reference this English path",
    },
    {
        "id": "unit_siege_tower_3_chi", "variants": ["base", "campaign", "xp3"],
        "tier_and_parent": "Chinese RGD unit_siege_tower_3_chi parents unit_siege_tower_3; all variants attach animator_skin_attachment eng_siege_tower.",
        "active_render_models": ["art/civilizations/common/team_weapons/archetypes/siege_tower/siege_tower.rgm", "art/civilizations/english/team_weapons/eng_siege_tower/eng_siege_tower.rgm"],
        "render_status": "active English skin attachment; decoded concrete geometry manifest exists",
        "decoded_donor_candidates": [], "donor_role": "active body route",
    },
    {
        "id": "unit_monk_3_chi", "variants": ["base", "campaign"],
        "tier_and_parent": "VN EBPS base and campaign tier selectors reference Chinese tier4_monk_chi; official RGD parents core_monk and merges chi_infantry_monk_age04, adds chi_staff_khakkhara_2 and base_civilian animation attachment.",
        "active_render_models": ["art/civilizations/chinese/humans/chi_infantry_monk_age04/chi_infantry_monk_age04.rgm"],
        "render_status": "active VN Tier IV body, statically decoded with exact texture providers",
        "decoded_donor_candidates": [], "donor_role": "active body route",
    },
    {
        "id": "unit_repeater_crossbowman_4_chi", "variants": ["base", "campaign"],
        "tier_and_parent": "Official tier4_crossbowman_chi parents tier3_crossbowman_chi and merges chi_ranged_crossbow_age04; VN Tier IV crossbowman source references this list. Separate repeater-crossbow hand weapon remains a weapon attachment.",
        "active_render_models": ["art/civilizations/chinese/humans/chi_ranged_crossbow_age04/chi_ranged_crossbow_age04.rgm"],
        "render_status": "active Tier IV body, statically decoded with exact texture providers",
        "decoded_donor_candidates": [], "donor_role": "active body route",
    },
    {
        "id": "unit_springald_3_chi", "variants": ["base", "campaign"],
        "tier_and_parent": "Chinese RGD unit_scorpion_3_chi, all four list variants use parent_animator common/team_weapons/archetypes/springald/springald; empty attachment list.",
        "active_render_models": ["art/civilizations/common/team_weapons/archetypes/springald/springald.rgm"],
        "render_status": "active animator reference, no same-stem RRGeometry or RRMaterial; actual geometry unresolved",
        "decoded_donor_candidates": ["art/civilizations/english/team_weapons/eng_springald/eng_springald.rgm"],
        "donor_role": "decoded geometry candidate only; current Chinese attachment RGD does not reference this English path",
    },
    {
        "id": "unit_trade_cart_chi", "variants": ["base"],
        "tier_and_parent": "VN trade-cart EBPS base and campaign tier selectors explicitly overrideParent with tier4_trade_cart_chi; official RGD parents core_trade_cart and skin-attaches chi_horse_combined_trade_age04, speaker villagerMale.",
        "active_render_models": ["art/civilizations/chinese/animals/chi_horse_combined_trade_age04/chi_horse_combined_trade_age04.rgm"],
        "render_status": "active VN Tier IV combined horse, rider, and trade-goods body; statically decoded with exact texture providers",
        "decoded_donor_candidates": [], "donor_role": "active body route",
    },
    {
        "id": "unit_trebuchet_4_cw_chi", "variants": ["base"],
        "tier_and_parent": "Chinese squad parents unit_trebuchet_4_counterweight and references both core unit_siege_cart and Chinese unit_trebuchet_4_cw_chi lists; these lists expose generic siege_cart and generic trebuchet_counterweight parent_animator values, with no child attachments.",
        "active_render_models": ["art/civilizations/common/team_weapons/archetypes/siege_cart/siege_cart.rgm", "art/civilizations/common/team_weapons/archetypes/trebuchet_counterweight/trebuchet_counterweight.rgm"],
        "render_status": "crew/body closure unresolved; neither parent has same-stem RRGeometry or RRMaterial",
        "decoded_donor_candidates": ["art/civilizations/english/team_weapons/eng_trebuchet_counterweight/eng_trebuchet_counterweight.rgm"],
        "donor_role": "decoded geometry candidate only; current Chinese attachment lists do not reference this English path",
    },
    {
        "id": "unit_trebuchet_4_tr_chi", "variants": ["campaign"],
        "tier_and_parent": "Chinese squad parents unit_trebuchet_4_traction and references both core unit_siege_cart and Chinese unit_trebuchet_4_tr_chi lists; these lists expose generic siege_cart and generic trebuchet_traction parent_animator values, with no child attachments.",
        "active_render_models": ["art/civilizations/common/team_weapons/archetypes/siege_cart/siege_cart.rgm", "art/civilizations/common/team_weapons/archetypes/trebuchet_traction/trebuchet_traction.rgm"],
        "render_status": "crew/body closure unresolved; neither parent has same-stem RRGeometry or RRMaterial",
        "decoded_donor_candidates": ["art/civilizations/english/team_weapons/eng_trebuchet_traction/eng_trebuchet_traction.rgm"],
        "donor_role": "decoded geometry candidate only; current Chinese attachment lists do not reference this English path",
    },
    {
        "id": "unit_workshop_ram_3_chi", "variants": ["base"],
        "tier_and_parent": "Chinese squad parents unit_ram_3 and uses the same unit_ram_3_chi attachment list as ordinary ram; parent animator is common/team_weapons/archetypes/battering_ram/battering_ram with an empty child list.",
        "active_render_models": ["art/civilizations/common/team_weapons/archetypes/battering_ram/battering_ram.rgm"],
        "render_status": "active animator reference, no same-stem RRGeometry or RRMaterial; actual geometry unresolved",
        "decoded_donor_candidates": ["art/civilizations/english/team_weapons/eng_battering_ram/eng_battering_ram.rgm"],
        "donor_role": "decoded geometry candidate only; current Chinese attachment RGD does not reference this English path",
    },
]


def main() -> None:
    guard()
    for path in (COVERAGE, DECODE, PREVIOUS):
        if not path.is_file():
            raise FileNotFoundError(path)
    if DEST.exists():
        raise FileExistsError(DEST)
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    decoded = json.loads(DECODE.read_text(encoding="utf-8"))
    old = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    ids = {row["id"] for row in ROWS}
    official = {row["id"]: row for row in coverage["included_inherited_stock_actors"]}
    if ids != {row["id"] for row in ROWS} or not ids <= set(official):
        raise RuntimeError("Roster ledger IDs do not match the current coverage audit")
    tower = next(row for row in old["models"]
                 if row.get("logical_model_path", "").endswith("/eng_siege_tower.rgm"))
    tower_manifest = Path(tower["manifest_path"] if tower.get("manifest_path") else
                          tower.get("manifest", ""))
    if not tower_manifest.is_file():
        tower_manifest = Path(r"F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_060\inventory\remaining-donors\run-004\decoded\013_eng_siege_tower\424e058acf167e2ca486\decoded-static.json")
    for row in ROWS:
        source = official[row["id"]]
        row["coverage"] = {key: source.get(key) for key in
                            ("category", "official_member_path", "relation_types", "relation_count", "consumers", "variants", "item_gate_evaluation")}
        row["native_parent_chain"] = source.get("parent_chain", [])
        row["native_attachment_members"] = sorted({item["member"] for item in source.get("visual_weapon_links", [])
                                                   if item.get("source_field") == "entity_blueprint_ext/animator_attachments"})
        row["official_stock_model_refs"] = source.get("model_refs", [])
        row["reachability_status"] = source.get("reachability_status")
        for model_path in row["decoded_donor_candidates"]:
            match = next((item for item in decoded["exact_decodes"].values()
                          if item.get("logical_path") == model_path), None)
            if match is None:
                raise RuntimeError("Missing exact candidate decode: " + model_path)
            row.setdefault("candidate_decode_evidence", []).append({
                "logical_path": model_path, "status": match.get("status"),
                "manifest": match.get("manifest"), "manifest_sha256": match.get("manifest_sha256"),
                "group_count": len(match.get("groups") or []),
                "triangle_count": sum(g.get("triangles", 0) or 0 for g in (match.get("groups") or [])),
                "texture_count": len(match.get("textures") or []),
                "missing_texture_count": len(match.get("missing_textures") or []),
            })
    tower_entry = next(row for row in ROWS if row["id"] == "unit_siege_tower_3_chi")
    tower_entry["active_body_decode"] = {"manifest": str(tower_manifest), "manifest_sha256": sha(tower_manifest),
                                          "status": "decoded_complete", "materials": 2, "bones": 31,
                                          "geometry_groups": 25, "triangle_count_semantics": "construction-stage groups; not assigned artificial LODs"}
    rgo_paths = sorted((BASE / "owner-rgos").glob("*.rgo"))
    rgo_evidence = [{"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p),
                     "container_prefix": p.read_bytes()[:20].decode("ascii", errors="replace"),
                     "inspection": "raw printable-string scan found RGO state/action/animation names, no child model path; this is not a complete RGO parse"}
                    for p in rgo_paths]
    receipt = {
        "schema": "ccp-060-inherited-render-body-ledger/v2",
        "status": "nine_consumers_traced_with_three_active_age_iv_bodies_and_unresolved_generic_siege_routes",
        "created_utc": "2026-10-18",
        "evidence": {
            "coverage_audit": {"path": str(COVERAGE), "sha256": sha(COVERAGE)},
            "targeted_decode_receipt": {"path": str(DECODE), "sha256": sha(DECODE)},
            "prior_exact_19_model_batch": {"path": str(PREVIOUS), "sha256": sha(PREVIOUS)},
            "current_official_source": "installed Age of Empires IV Attrib.sga, ArtHigh.sga, ArtCivilizations.sga and Garrison game-assets.sqlite3 metadata",
            "task_game_cardinal_archives_empty": decoded.get("task_game_cardinal_archives_empty"),
            "private_exact_index": decoded["exact_index"],
            "owner_rgo_evidence": rgo_evidence,
            "unverified_gates": ["native actor list-item eligibility", "lobby selection", "native-match appearance and crew body"]
        },
        "consumer_count": len(ROWS),
        "consumers": ROWS,
        "interpretation": [
            "The prior 686-RGD closure's missing monk/trade Tier IV attachment rows were a coverage gap, not evidence that the official resources were absent. Both exact members exist in current Attrib.sga and resolve through the Vietnamese Tier IV selectors.",
            "English ram, springald, and trebuchet models are real decoded stock geometries, but current Chinese attachment-list RGDs do not point to them; they remain donor candidates only.",
            "The current generic battering-ram, springald, trebuchet, siege-tower and siege-cart animator references have no same-stem RRGeometry/RRMaterial provider in the installed resolved-assets index. The generic siege-cart RGM and RGO also fail Garrison static decode for lack of same-stem RRGeometry. No exact trebuchet crew render-body path was established from this evidence.",
            "No Blender, cook, source integration, import, lobby selection, or match test was run."
        ]
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt": str(DEST), "consumer_count": len(ROWS),
                      "candidate_decodes": len(decoded["exact_decodes"]), "owner_rgos": len(rgo_evidence)}, indent=2))


if __name__ == "__main__":
    main()
