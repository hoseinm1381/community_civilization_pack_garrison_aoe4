"""Refresh the compact 0.6.0 representative-art review index."""
from __future__ import annotations

from pathlib import Path

from common import ART, OUT, RECIPES, ROOT, guard, read, sha, write

NAMES = {
    "spear2": "Age II spearman",
    "male_villager1": "Age I male villager",
    "female_villager1": "Age I female villager",
    "horseman2": "Age II horseman and mount",
    "elephant": "Vietnamese war elephant I, Sultanate stock donor",
    "siege_mangonel3": "Age III mangonel frame and boulders",
}
ASSEMBLIES = {
    "spear2": "stock weighted body; spear, charge, brace and torch stay native attachments",
    "male_villager1": "stock weighted male body; work tools and cargo stay native attachments",
    "female_villager1": "stock weighted female body; work tools and cargo stay native attachments",
    "horseman2": "stock weighted horse plus rider; stock ordinary/charge spear and torch stay native attachments",
    "elephant": "stock weighted elephant plus mahout; original goad and charge remain native",
    "siege_mangonel3": "stock mangonel frame, moving parts and boulders; attached siege cart remains native; human crew presence unresolved",
}
VISIBLE = {"spear2": [1236], "male_villager1": [1188],
           "female_villager1": [1312], "horseman2": [1656, 1204],
           "elephant": [3349, 1272], "siege_mangonel3": [4449, 384]}


def main() -> None:
    guard()
    trace = read(OUT / "pilots/pilot-trace.json")
    decode = read(OUT / "pilots/pilot-decodes.json")
    equipment = read(OUT / "pilots/pilot-equipment.json")
    reference_index = read(OUT / "references/source-index.json")
    source_links = [{"id": source["id"], "title": source["title"],
                     "url": source["page_url"]} for source in reference_index["sources"]]
    prior_path = OUT / "pilots/sample-index.json"
    prior = read(prior_path) if prior_path.exists() else {}
    old = {s["id"]: s for s in prior.get("samples", [])}
    samples = []
    for key, name in NAMES.items():
        donor = decode["pilots"][key]
        chain = trace["pilots"][key]
        authored = OUT / "pilots" / key / "authoring.json"
        authored_data = read(authored) if authored.is_file() else None
        blend = Path(authored_data["blend"]) if authored_data else ART / "pilots" / key / (key + "_review.blend")
        screenshots = {"donor_close": None, "redesign_close": None,
                       "donor_game_distance": None, "redesign_game_distance": None,
                       "owner_color_previews": []}
        screenshots.update({k: v for k, v in old.get(key, {}).get("screenshots", {}).items()
                            if k in screenshots})
        sample = {"id": key, "name": name,
                  "official_donor_model": donor["stock_model"]["logical_path"],
                  "stock_decode_manifest": donor["manifest"],
                  "stock_equipment_decodes": {name: item["manifest"] for name, item in
                                              equipment["pilots"][key].items()},
                  "donor_attachment_trace": str(OUT / "pilots/pilot-trace.json"),
                  "historical_recipe": str(RECIPES / "historical-reference.json"),
                  "official_history_sources": source_links,
                  "authoring_script": str(ROOT / "tools/release_060/pilot_author_blender.py"),
                  "stock_assembly": ASSEMBLIES[key],
                  "highest_detail_visible_base_triangles": sum(VISIBLE[key]),
                  "all_lod_inventory_triangles": sum(g["triangles"] for g in donor["groups"]),
                  "blend": str(blend) if blend.exists() else None,
                  "blend_sha256": sha(blend) if blend.is_file() else None,
                  "screenshots": screenshots,
                  "gates": {
                      "official_attachment_trace": "passed" if not chain["unresolved"] else "unresolved",
                      "stock_weighted_decode": "passed" if donor["status"] == "decoded" and not donor["blockers"] else "failed",
                      "authoring_blend": "created" if blend.is_file() else "pending_blender_slot",
                      "visual_review": "pending_user_review",
                      "export_cook_readback": "not_run",
                      "native_appearance_behavior": "user_gate_not_run"},
                  "known_limits": (["Mangonel human crew presence and animation import are unresolved; retain its native mechanism and stock loadout."]
                                   if key == "siege_mangonel3" else [])}
        samples.append(sample)
    write(prior_path, {"schema": "ccp-060-sample-index/v1",
                       "scope": "Representative art only; active assets/source unchanged",
                       "samples": samples})
    print(str(prior_path), len(samples), "samples")


if __name__ == "__main__":
    main()
