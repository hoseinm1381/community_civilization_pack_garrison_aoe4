r"""Read-only Garrison buffalo animation/export inventory for release 0.8.1.

Run with the configured Blender Python from the Garrison project root:
    & (Get-Content .\workspace.json -Raw | ConvertFrom-Json).blender_python -B `
        .\tools\release_081\animation_inventory.py

The script imports the installed callable Garrison prototype catalogue, reads
the retained 0.8.0 recovery indexes without restoring files, and writes only
under output/release_081/animation.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / "workspace.json").read_text(encoding="utf-8"))
EXTENSION = Path(CFG["garrison_extension"])
EXTERNAL = Path(CFG["external_root"])
STORE = EXTERNAL / "resources_080"
OUT = ROOT / "output" / "release_081" / "animation"
OUT.mkdir(parents=True, exist_ok=True)
READBACK = ROOT / "output/release_081/baseline/readback"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strings(data: bytes) -> list[str]:
    return [x.decode("ascii", "replace") for x in re.findall(rb"[\x20-\x7e]{4,}", data)]


sys.path.insert(0, str(EXTENSION))
prototypes_module = importlib.import_module("garrison_shared.unit_prototypes")
catalogue = prototypes_module.catalog()
qualified = {
    row["key"]: prototypes_module.qualified_timings(row["key"])
    for row in catalogue
}

native_archives = json.loads((STORE / "native-archives.json").read_text(encoding="utf-8"))
store_index = json.loads((STORE / "index.json").read_text(encoding="utf-8"))
attrib_archive_hash = None
data_archive_hash = None
attrib_archive_meta = None
data_archive_meta = None
for digest, record in native_archives.items():
    originals = record.get("original_keys", [])
    normalized = [x.lower() for x in originals]
    if any("output/release_0712/delivery/final-v1/attrib-assembly.sga" in x for x in normalized):
        attrib_archive_hash, attrib_archive_meta = digest, record
    if any("output/release_0712/delivery/final-v1/data-assembly.sga" in x for x in normalized):
        data_archive_hash, data_archive_meta = digest, record

payload_zip = STORE / "payloads-v1.zip"
zip_handle = zipfile.ZipFile(payload_zip, "r")
store_files = store_index["files"]


def read_recovery_path(archive_digest: str | None, relative_member: str) -> tuple[bytes, str] | None:
    if archive_digest is None:
        return None
    key = f"F/resources_080/recovered_native/{archive_digest}/{relative_member}"
    indexed = store_files.get(key)
    if indexed is None:
        return None
    payload = zip_handle.read(indexed["member"])
    actual = sha(payload)
    if actual != indexed["sha256"] or len(payload) != indexed["bytes"]:
        raise RuntimeError(f"Recovery payload failed its indexed hash/length: {key}")
    return payload, key


actor_path = "attrib/ebps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.rgd"
actor_payload = read_recovery_path(attrib_archive_hash, actor_path)
rgo_path = "art/scenario/garrison/cc076/buffalo/model.rgo"
rgo_payload = read_recovery_path(data_archive_hash, rgo_path)
recipe_author = ROOT / "art/recipes/release_079/production-source-v2/author_units.py"
recipe_package = ROOT / "art/recipes/release_079/production-source-v2/package_final.py"
recipe_author_text = recipe_author.read_text(encoding="utf-8")
recipe_package_text = recipe_package.read_text(encoding="utf-8")

actor_text: list[str] = []
if actor_payload:
    actor_text = strings(actor_payload[0])
    # Keep only animation/state identifiers observed in the compiled actor.
    interesting = [
        value for value in dict.fromkeys(actor_text)
        if value.startswith(("navigation\\", "reaction\\", "attack\\"))
        or value in {"animation_action_tree_ext", "default_animation", "use_root_motion", "events", "Death"}
    ]
else:
    interesting = []

rgo_text = strings(rgo_payload[0]) if rgo_payload else []


def rgd_xml_fields(path: Path, instance: str, extension: str) -> dict[str, str]:
    if not path.is_file():
        return {}
    root = ET.parse(path).getroot()
    block = next((n for n in root.findall("./RGDNode") if n.attrib.get("Key") == instance), None)
    if block is None:
        return {}
    ext = next((n for n in block.findall("./RGDNode") if n.attrib.get("Key") == extension), None)
    if ext is None:
        return {}
    return {n.attrib.get("Key", ""): n.attrib.get("Value", "") for n in ext.findall("./RGDNode")}


def rgd_descendant_fields(path: Path, instance: str, extension: str, child: str) -> dict[str, str]:
    if not path.is_file():
        return {}
    root = ET.parse(path).getroot()
    block = next((n for n in root.findall("./RGDNode") if n.attrib.get("Key") == instance), None)
    if block is None:
        return {}
    ext = next((n for n in block.findall("./RGDNode") if n.attrib.get("Key") == extension), None)
    if ext is None:
        return {}
    node = next((n for n in ext.iter("RGDNode") if n.attrib.get("Key") == child), None)
    return {n.attrib.get("Key", ""): n.attrib.get("Value", "") for n in node.findall("./RGDNode")} if node is not None else {}


baseline_actor_xml = OUT / "baseline-buffalo-actor.xml"
baseline_attachment_xml = OUT / "baseline-buffalo-attachment.xml"
baseline_actor_file = READBACK / "attrib/ebps/vietnam/units/economy/water_buffalo/vn_unit_war_elephant_1_vit.rgd"
baseline_attachment_file = READBACK / "attrib/attachments/attachment_lists/vietnam/release_076/vn076_water_buffalo.rgd"
baseline_model_rgo = READBACK / "art/scenario/garrison/cc076/buffalo/model.rgo"
baseline_model_rgm = READBACK / "art/scenario/garrison/cc076/buffalo/model.rgm"
baseline_actor_action = rgd_xml_fields(baseline_actor_xml, "default", "animation_action_tree_ext")
baseline_actor_parent = rgd_xml_fields(baseline_actor_xml, "default", "parent_pbg")
baseline_actor_animator = rgd_xml_fields(baseline_actor_xml, "default", "entity_blueprint_ext")
baseline_actor_action_apply = rgd_xml_fields(baseline_actor_xml, "default", "action_apply_ext")
baseline_actor_animator_link = rgd_descendant_fields(baseline_actor_xml, "default", "entity_blueprint_ext", "animator_attachments")
baseline_attachment_fields = rgd_xml_fields(baseline_attachment_xml, "default", "attachment_lists")
baseline_attachment_rows = []
if baseline_attachment_xml.is_file():
    att_root = ET.parse(baseline_attachment_xml).getroot()
    default = next((n for n in att_root.findall("./RGDNode") if n.attrib.get("Key") == "default"), None)
    if default is not None:
        for n in default.iter("RGDNode"):
            if n.attrib.get("Key") == "animator":
                baseline_attachment_rows.append(n.attrib.get("Value", ""))
baseline_model_rgo_bytes = baseline_model_rgo.read_bytes() if baseline_model_rgo.is_file() else b""
baseline_model_rgm_bytes = baseline_model_rgm.read_bytes() if baseline_model_rgm.is_file() else b""
baseline_actor_events: list[str] = []
if baseline_actor_xml.is_file():
    actor_root = ET.parse(baseline_actor_xml).getroot()
    default = next((n for n in actor_root.findall("./RGDNode") if n.attrib.get("Key") == "default"), None)
    action_tree = next((n for n in default.findall("./RGDNode") if n.attrib.get("Key") == "action_tree_ext"), None) if default is not None else None
    events = next((n for n in action_tree.findall("./RGDNode") if n.attrib.get("Key") == "events"), None) if action_tree is not None else None
    if events is not None:
        baseline_actor_events = [n.attrib.get("Value", "") for n in events.iter("RGDNode") if n is not events]

kit = Path.home() / "AppData/Local/Garrison/Kit"
asset_db = kit / "game-assets.sqlite3"
game_asset_metadata: dict[str, str] = {}
official_anim_assets: list[dict] = []
if asset_db.is_file():
    with sqlite3.connect(f"file:{asset_db.as_posix()}?mode=ro", uri=True) as db:
        game_asset_metadata = dict(db.execute("SELECT key, value FROM metadata"))
        logicals = (
            "art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rgo",
            "art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rhka",
            "art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rootmotion",
            "art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rgm",
        )
        placeholders = ",".join("?" for _ in logicals)
        rows = db.execute(
            f"SELECT logical_path, extension, archive, archive_path, size, verified FROM resolved_assets WHERE logical_path IN ({placeholders}) ORDER BY logical_path",
            logicals,
        ).fetchall()
        official_anim_assets = [
            {"logical_path": r[0], "extension": r[1], "archive": r[2], "archive_path": r[3], "size": r[4], "verified": bool(r[5])}
            for r in rows
        ]

cattle_rhka_path = OUT / "source/art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rhka"
cattle_rootmotion_path = OUT / "base_cattle.rootmotion"
cattle_clip_names: list[str] = []
if cattle_rhka_path.is_file():
    cattle_clip_names = list(dict.fromkeys(
        value for value in strings(cattle_rhka_path.read_bytes())
        if "\\" in value and value.startswith(("reaction\\", "navigation\\", "attacks\\"))
    ))


def sampled_preview(path: Path) -> dict:
    if not path.is_file():
        return {"available": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "available": True,
        "clip_index": data.get("clip_index"),
        "name": data.get("name"),
        "duration_seconds": data.get("duration_seconds"),
        "frame_count": data.get("frame_count"),
        "motion": data.get("motion"),
        "events": data.get("events"),
        "boundaries": data.get("boundaries"),
    }


cattle_sampled_previews = {
    "death_pose": sampled_preview(OUT / "cattle_clip_000.json"),
    "walk_01": sampled_preview(OUT / "cattle_walk_01.json"),
    "idle_01": sampled_preview(OUT / "cattle_idle_01.json"),
}

buffalo_ebps = ROOT / "assets/attrib/instances/ebps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml"
source_xml = buffalo_ebps.read_text(encoding="utf-8")
parent = re.search(r'<instance_reference\s+name="parent_pbg"\s+value="([^"]+)"', source_xml)

result = {
    "status": "read_only_inventory_complete",
    "scope": "Garrison animation/export admission, buffalo blueprint and retained archive ownership",
    "environment": {
        "configured_python": str(Path(sys.executable)),
        "configured_blender_python": CFG.get("blender_python"),
        "installed_extension": str(EXTENSION),
        "installed_extension_version": re.search(
            r'^version\s*=\s*"([^"]+)"',
            (EXTENSION / "blender_manifest.toml").read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        ).group(1),
        "catalogue_module": "garrison_shared.unit_prototypes.catalog()",
        "catalogue_module_file": str(Path(prototypes_module.__file__)),
    },
    "garrison_build_catalogue": {
        "actual_callable_query": True,
        "prototype_count": len(catalogue),
        "prototypes": catalogue,
        "qualified_replacement_timing": qualified,
        "buffalo_or_animal_prototype_present": any(
            any(term in (row.get("key", "") + " " + row.get("label", "") + " " + row.get("category", "")).lower()
                for term in ("buffalo", "cattle", "animal", "livestock"))
            for row in catalogue
        ),
        "scope_note": "Prototype catalogue is Build Unit admission, not a catalogue of all native game clips.",
    },
    "native_actor": {
        "editable_blueprint": "assets/attrib/instances/ebps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml",
        "parent_pbg": parent.group(1) if parent else None,
        "source_xml_sha256": sha(buffalo_ebps.read_bytes()),
        "compiled_release_0712_archives": {
            "attrib_archive_sha256": attrib_archive_hash,
            "attrib_original_keys": attrib_archive_meta.get("original_keys", []) if attrib_archive_meta else [],
            "data_archive_sha256": data_archive_hash,
            "data_original_keys": data_archive_meta.get("original_keys", []) if data_archive_meta else [],
        },
        "compiled_actor_payload": {
            "recovery_key": actor_payload[1] if actor_payload else None,
            "sha256": sha(actor_payload[0]) if actor_payload else None,
            "bytes": len(actor_payload[0]) if actor_payload else None,
            "observed_animation_state_identifiers": interesting,
            "evidence_limit": "Compiled Relic Chunky string inventory only; it does not resolve the full inherited actor/state-tree graph or prove each listed state is reachable.",
        },
        "model_rgo_payload": {
            "logical_path": rgo_path,
            "recovery_key": rgo_payload[1] if rgo_payload else None,
            "sha256": sha(rgo_payload[0]) if rgo_payload else None,
            "bytes": len(rgo_payload[0]) if rgo_payload else None,
            "ascii_strings": rgo_text,
            "evidence_limit": "This Garrison-generated model RGO contains model/resource metadata, not an exposed RHKA clip list.",
        },
    },
    "current_compiled_baseline_readback": {
        "baseline_root": str(READBACK),
        "actor_rgd": str(baseline_actor_file.relative_to(ROOT)).replace("\\", "/"),
        "actor_rgd_sha256": sha(baseline_actor_file.read_bytes()) if baseline_actor_file.is_file() else None,
        "actor_parent_pbg": baseline_actor_parent.get("$PBGNAME"),
        "actor_parent_map": baseline_actor_parent.get("$PBGMAP"),
        "actor_action_tree": {
            "branch": baseline_actor_action.get("ActionTree_OpeningBranch"),
            "default_animation": baseline_actor_action.get("default_animation"),
            "use_root_motion": baseline_actor_action.get("use_root_motion"),
            "entity_statetree_sort_tag": baseline_actor_action.get("entity_statetree_sort_tag"),
            "start_suspended": baseline_actor_action.get("start_suspended"),
            "effective_source": "compiled 0.8.0 readback; current branch differs from the stock inherited actor branch",
        },
        "actor_animator_attachments": {
            "pbgname": baseline_actor_animator_link.get("$PBGNAME"),
            "pbgnmap": baseline_actor_animator_link.get("$PBGMAP"),
        },
        "action_apply_state_tree": {
            "worker_elephant_spawn_behavior_observed": "worker_elephant_spawn_behavior" in (baseline_actor_xml.read_text(encoding="utf-8") if baseline_actor_xml.is_file() else ""),
            "action_tree_events": baseline_actor_events,
            "action_tree_events_empty": not baseline_actor_events,
            "note": "Actor ActionTree extension event list is not encoded as a direct animation event inventory; only the action-apply state-tree reference was identified.",
        },
        "private_attachment_list_rgd": str(baseline_attachment_file.relative_to(ROOT)).replace("\\", "/"),
        "private_attachment_list_sha256": sha(baseline_attachment_file.read_bytes()) if baseline_attachment_file.is_file() else None,
        "private_attachment_parent_animator": baseline_attachment_fields.get("parent_animator"),
        "private_attachment_model_animators": baseline_attachment_rows,
        "model_rgo": {
            "path": str(baseline_model_rgo.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha(baseline_model_rgo_bytes) if baseline_model_rgo_bytes else None,
            "bytes": len(baseline_model_rgo_bytes),
            "strings": strings(baseline_model_rgo_bytes) if baseline_model_rgo_bytes else [],
        },
        "model_rgm": {
            "path": str(baseline_model_rgm.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha(baseline_model_rgm_bytes) if baseline_model_rgm_bytes else None,
            "bytes": len(baseline_model_rgm_bytes),
            "observed_name_strings": [x for x in strings(baseline_model_rgm_bytes) if x.strip().lower() == "cow"] if baseline_model_rgm_bytes else [],
        },
        "native_animation_owner": "base_cattle; proven by compiled 0.8.0 private attachment parent_animator and custom animator skin attachment",
        "stock_ancestor_distinction": "The inherited Tughlaq Worker Elephant ancestry supplies gameplay/state provenance; it is not the current art animation owner because the compiled attachment binds base_cattle.",
    },
    "official_cattle_animation_resources": {
        "sqlite_path": str(asset_db),
        "index_metadata": game_asset_metadata,
        "sqlite_archive_verification_enabled": game_asset_metadata.get("verify_archives"),
        "indexed_resources": official_anim_assets,
        "rhka_source_sha256": sha(cattle_rhka_path.read_bytes()) if cattle_rhka_path.is_file() else None,
        "rootmotion_payload_sha256": sha(cattle_rootmotion_path.read_bytes()) if cattle_rootmotion_path.is_file() else None,
        "clip_names_from_rhka_tagfile": cattle_clip_names,
        "clip_name_count": len(cattle_clip_names),
        "sampled_clip_previews": cattle_sampled_previews,
        "event_inventory": {
            "sampled_animation_events": "not exposed by installed sampled-preview result (events is null)",
            "rootmotion_tag_strings": [
                value for value in dict.fromkeys(strings(cattle_rootmotion_path.read_bytes()))
                if value in cattle_clip_names or value.lower() in {"animation", "animationname", "animationcount", "specialtype", "samplecount", "partitions", "num_partitions", "keyframes", "translation_x", "translation_y", "translation_z", "rotation"}
            ] if cattle_rootmotion_path.is_file() else [],
            "rootmotion_structured_mapping": "not decoded; root-motion presence is reported per sampled RHKA clip only",
        },
        "provenance_limit": "Installed Garrison index metadata dates to 2026-10-17 and reports verify_archives=false. The archive listing/extraction identifies exact members but does not provide whole-archive CRC/SHA verification.",
    },
    "retained_recipe_evidence": {
        "author_script": str(recipe_author.relative_to(ROOT)).replace("\\", "/"),
        "author_script_sha256": sha(recipe_author.read_bytes()),
        "author_script_clears_action_on_export_copy": "rig.animation_data_clear()" in recipe_author_text,
        "author_script_fbx_animation_export_disabled": "bake_anim=False" in recipe_author_text,
        "final_assembly_script": str(recipe_package.relative_to(ROOT)).replace("\\", "/"),
        "final_assembly_checks_preserved_rgo": "suffix=='.rgo'" in recipe_package_text,
        "interpretation": "The retained 0.7.9 recipe creates/export meshes on the native donor rig and preserves native RGO members; it is not an authored buffalo Action encoder or RHKA roundtrip.",
    },
    "decision": {
        "editable_source_action_trial_supported": True,
        "native_action_encoder_supported": False,
        "reason": "A 45-bone cattle Action source trial can be authored and checked in Blender. The installed Build Unit catalogue contains only two human prototypes; no animal/buffalo Action encoding route or RHKA-to-Action validated roundtrip is installed or retained.",
        "recommended_minimal_source_action": "Retain separate editable idle and in-place walk Actions plus source previews on a copy of the final r5 45-bone cattle model. Keep root stationary and scale one; preserve the compiled base_cattle attachment owner, current action-tree branch, and existing native state/action routing. Do not publish a custom native animation package until a supported animal encoder or exact roundtrip is established.",
        "native_runtime_result": "Not tested by this inventory.",
    },
}

json_path = OUT / "inventory.json"
json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

timing_lines = []
for prototype, items in qualified.items():
    timing_lines.append(f"- `{prototype}`: " + (", ".join(f"`{name}` → `{timing}`" for name, timing in items.items()) or "no qualified replacement timings"))

actor_lines = "\n".join(f"- `{name}`" for name in interesting) if interesting else "- No compiled actor payload was found in the indexed recovery store."
report = f"""# 0.8.1 buffalo animation inventory

Status: read-only inventory completed. This report does not claim Blender scene, cook, import, or native-game validation.

## Installed Garrison admission

The callable installed query `garrison_shared.unit_prototypes.catalog()` returned {len(catalogue)} Build Unit prototypes. It exposes no buffalo, cattle, or animal prototype. The matching per-prototype qualified replacement timing query returned:

{chr(10).join(timing_lines)}

These slots are the installed human-prototype export contracts. They do not admit a buffalo Action or establish that a native buffalo RHKA clip can roundtrip through Garrison's Action encoder.

## Current compiled buffalo ownership

The editable buffalo EBPS points to `{parent.group(1) if parent else 'unresolved parent_pbg'}`. The 0.8.0 package is an exact 0.7.12 SGA preservation rebuild; its native compiled actor payload was read from the 0.8.0 recovery ZIP in memory and verified against the recovery index. Animation-related strings observed in that actor are:

{actor_lines}

The exact 0.8.0 compiled readback changes the interpretation: actor `vn_unit_war_elephant_1_vit` inherits `unit_worker_elephant_2_sul_ha_tug`, but its owning animator attachment is the private `vn076_water_buffalo` list. That list has `parent_animator = art\\civilizations\\common\\animals\\archetypes\\base_cattle\\base_cattle` and skins the Garrison model resource `art\\scenario\\garrison\\cc076\\buffalo\\model`. The `model.rgo` itself contains model/resource metadata; the compiled `.rgm` identifies the mesh resource as `cow`. The current art animation owner is therefore official `base_cattle`, while Worker Elephant is ancestry/gameplay provenance.

The current compiled actor’s effective action-tree branch is `infantry`, `default_animation = navigation\\idle_01`, and `use_root_motion = true`; this differs from the stock ancestor’s `elephant_combined` branch. `worker_elephant_spawn_behavior` is also present as an action-apply state-tree reference. The compiled actor’s `action_tree_ext/events` list is empty; the full effective state-tree graph remains unresolved. The animation preview returns `events: null`, and the root-motion companion binary’s structured clip mapping was not decoded.

The installed official SQLite index locates `base_cattle.rgo`, `.rhka`, `.rootmotion`, and `.rgm` under `ArtCivilizations.sga`/`ArtHigh.sga`. RHKA inspection found 11 cattle clips: `reaction\\death_pose_01`, `reaction\\death_01`, `navigation\\walk_to_stop_01`, `navigation\\walk_01`, `navigation\\trot_to_stop_01`, `navigation\\trot_01`, `navigation\\sprint_01`, `navigation\\run_01`, `navigation\\idle_grazing_01`, `navigation\\idle_02`, `navigation\\idle_01`. The installed sampler decoded `navigation\\walk_01` (4.267 s, 129 frames, sampled root motion true) and `navigation\\idle_01` (9.867 s, 297 frames, sampled root motion false). Its preview marks native game export unsupported and runtime Action selection undecoded. The SQLite index is dated 2026-10-17 and says `verify_archives=false`; archive member identification and extraction do not prove current whole-archive verification.

The 0.7.9 report records that the pilot's buffalo movement/animation worked in-game, and its art integration preserved the native animation owner. That proves the native model/rig route for the exercised pilot, not custom Action encoding or all states.

The retained 0.7.9 production recipe confirms this boundary: its authoring/export copy clears the rig Action and disables FBX animation baking, while final assembly retains `.rgo` members. It rebuilds mesh/texture resources on the donor skeleton and leaves native animation ownership in place.

## Recommendation

Continue the requested idle-then-walk trial as editable Blender source on a copy of the final 45-bone cattle model, with stationary root and scale one. Preserve the compiled `base_cattle` animation owner, current action-tree branch, and existing action/state routing. The installed catalogue and sampler do not qualify native export or package integration, so the Actions remain source-only until an animal-capable encoder or exact RHKA-to-Action roundtrip is demonstrated.

The native game was not launched or tested during this inventory. See `inventory.json` for catalogue rows, timing names, archive identities, payload hashes, and source paths.
"""
(OUT / "inventory.md").write_text(report, encoding="utf-8")
zip_handle.close()
print(json.dumps({"status": result["status"], "json": str(json_path), "report": str(OUT / "inventory.md"), "prototype_count": len(catalogue), "buffalo_supported": result["garrison_build_catalogue"]["buffalo_or_animal_prototype_present"], "attrib_archive_sha256": attrib_archive_hash, "data_archive_sha256": data_archive_hash}, indent=2))
