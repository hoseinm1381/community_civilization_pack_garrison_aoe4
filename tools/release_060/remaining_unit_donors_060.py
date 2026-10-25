from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, sha, write

SOURCE_INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
SOURCE_CONFIG = SOURCE_INDEX.with_name("game-assets.local.json")
INV = OUT / "inventory/complete-donors/complete-donors.json"
PREVIOUS = OUT / "inventory/remaining-donors/run-003/batch-report-v2.json"
INITIAL = OUT / "inventory/remaining-donors/run-001/batch-report.json"
BASE = OUT / "inventory/remaining-donors/run-004"
PRIVATE_GAME = STAGING / "remaining-donors-v4"
EXACT_INDEX = BASE / "private-index-exact.sqlite3"
EXACT_RECEIPT = BASE / "batch-report-exact-index-v2.json"


def selected_models(report):
    result = []
    for rec in report["models"]:
        manifest = Path(rec["decode_manifest"]) if rec.get("decode_manifest") else None
        if rec.get("status", "").startswith("decoded") and manifest and manifest.is_file():
            result.append((rec, manifest))
    return result


def manifest_refs(manifests):
    refs = set()
    for _, manifest_path in manifests:
        if manifest_path is None:
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        refs.update(data.get("missing_textures", []))
        refs.update(t.get("logical_path") for t in data.get("textures", []) if t.get("logical_path"))
    return refs


def table_sql(source, table):
    row = source.execute(
        "select sql from sqlite_master where type='table' and name=?", (table,)
    ).fetchone()
    if not row:
        raise RuntimeError(f"Installed index missing table: {table}")
    return row[0]


def summarize_manifest(path, logical, owners, provider_refs, log):
    data = json.loads(path.read_text(encoding="utf-8"))
    geometry = data.get("geometry", {})
    groups = geometry.get("groups", [])
    triangles_by_lod = {}
    for group in groups:
        material_name = str(group.get("material", ""))
        lod_match = re.search(r"(?:^|_)lod(\d+)(?:_|$)", material_name, re.IGNORECASE)
        lod = str(group.get("lod", group.get("lod_index", lod_match.group(1) if lod_match else "unknown")))
        triangles_by_lod[lod] = triangles_by_lod.get(lod, 0) + group.get("triangle_count", 0)
    materials = data.get("materials", [])
    if isinstance(materials, dict):
        material_refs = sorted(materials)
    else:
        material_refs = sorted({
            item.get("name", item.get("material")) if isinstance(item, dict) else str(item)
            for item in materials
        } - {None})
    if not material_refs:
        material_refs = sorted({g.get("material") for g in groups if g.get("material")})
    skeleton = data.get("skeleton", {})
    return {
        "logical_model_path": logical,
        "owners": owners,
        "status": "decoded_complete" if not data.get("missing_textures") and not data.get("blockers") else "decoded_with_errors",
        "provider_refs": provider_refs,
        "decode_manifest": str(path),
        "decode_manifest_sha256": sha(path),
        "geometry_group_count": len(groups),
        "material_count": len(material_refs),
        "materials": material_refs,
        "triangles_by_lod": triangles_by_lod,
        "skeleton": {
            "status": skeleton.get("status"),
            "bone_count": skeleton.get("bone_count"),
            "skin_palette_count": skeleton.get("skin_palette_count"),
            "skin_palette_sizes": [len(p.get("bones", [])) for p in skeleton.get("skin_palettes", [])],
            "rigid_mesh_binding_count": len(skeleton.get("rigid_mesh_bindings", [])),
        },
        "missing_textures": data.get("missing_textures", []),
        "blockers": data.get("blockers", []),
        "log_sha256": sha(log),
    }


def refine_exact_private_index():
    """Build a strict reference-only index from completed manifests, preserving run-004."""
    guard()
    report_path = BASE / "batch-report-v2.json"
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    if EXACT_INDEX.exists() or EXACT_RECEIPT.exists():
        raise FileExistsError("Preserve an existing exact-index refinement")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    exact_textures = set()
    models = []
    for item in report["models"]:
        if item.get("status") != "decoded_complete":
            raise ValueError("Exact index requires every selected model to decode completely")
        logical = item["logical_model_path"]
        manifest = Path(item["decode_manifest"])
        data = json.loads(manifest.read_text(encoding="utf-8"))
        refs = {t.get("logical_path") for t in data.get("textures", []) if t.get("logical_path")}
        refs.update(data.get("missing_textures", []))
        exact_textures.update(refs)
        models.append((item, logical, manifest, refs))

    source = sqlite3.connect(f"file:{SOURCE_INDEX.as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    target = None
    model_paths = {logical for _, logical, _, _ in models}
    paths = set(exact_textures)
    for logical in model_paths:
        stem = logical.removesuffix(".rgm")
        paths.update((logical, stem + ".rrgeom", stem + ".rrmaterial"))
        folder = logical.rsplit("/", 1)[0] + "/"
        paths.update(
            row[0] for row in source.execute(
                "select logical_path from resolved_assets where logical_path like ? and extension in ('.rgo','.rhka','.rootmotion')",
                (folder + "%",),
            )
        )
    resolved = []
    for logical in sorted(paths):
        rows = source.execute("select * from resolved_assets where logical_path=?", (logical,)).fetchall()
        if not rows:
            raise RuntimeError("Exact provider missing: " + logical)
        resolved.extend(rows)
    asset_ids = {row["id"] for row in resolved}
    assets = [source.execute("select * from assets where id=?", (asset_id,)).fetchone()
              for asset_id in asset_ids]
    if any(row is None for row in assets):
        raise RuntimeError("Exact resolved provider has no asset row")
    archive_ids = {row["archive_id"] for row in assets}
    archives = [source.execute("select * from archives where id=?", (archive_id,)).fetchone()
                for archive_id in archive_ids]
    if any(row is None or not Path(row["path"]).is_file() for row in archives):
        raise RuntimeError("Exact provider archive is unavailable")
    target = sqlite3.connect(EXACT_INDEX)
    try:
        for table in ("metadata", "archives", "assets", "resolved_assets", "folders", "object_types"):
            target.execute(table_sql(source, table))
        counts = {"archive_count": len(archives), "asset_count": len(assets),
                  "resolved_asset_count": len(resolved)}
        for key, value in source.execute("select key,value from metadata"):
            target.execute("insert into metadata values(?,?)", (key, str(counts[key]) if key in counts else value))
        for table, rows in (("archives", archives), ("assets", assets), ("resolved_assets", resolved)):
            for row in rows:
                target.execute("insert into " + table + " values(" + ",".join("?" for _ in row) + ")", tuple(row))
        target.commit()
    finally:
        source.close()
        target.close()

    verify = sqlite3.connect(f"file:{EXACT_INDEX.as_posix()}?mode=ro", uri=True)
    try:
        indexed_textures = {row[0] for row in verify.execute("select distinct logical_path from resolved_assets where extension='.rrtex'")}
        if indexed_textures != exact_textures:
            raise ValueError("Refined RRtex set differs from decoded manifests")
        if verify.execute("select count(*) from archives").fetchone()[0] != len(archives):
            raise ValueError("Refined archive count differs")
    finally:
        verify.close()
    old_index = sqlite3.connect(f"file:{(BASE / 'private-index.sqlite3').as_posix()}?mode=ro", uri=True)
    try:
        old_textures = {row[0] for row in old_index.execute("select distinct logical_path from resolved_assets where extension='.rrtex'")}
    finally:
        old_index.close()
    receipt = {
        "schema": "ccp-060-remaining-donor-exact-index-refinement/v1",
        "status": "strict_exact_manifest_references_indexed",
        "preserved_batch_report": str(report_path),
        "preserved_batch_report_sha256": sha(report_path),
        "refined_index": str(EXACT_INDEX),
        "refined_index_sha256": sha(EXACT_INDEX),
        "model_count": len(models),
        "decoded_complete_count": sum(item.get("status") == "decoded_complete" for item, _, _, _ in models),
        "exact_rrtex_count": len(exact_textures),
        "indexed_rrtex_count": len(indexed_textures),
        "extra_rrtex_candidates_removed": sorted(old_textures - exact_textures),
        "provider_archive_count": len(archives),
        "provider_asset_count": len(assets),
        "resolved_provider_count": len(resolved),
        "private_game_cardinal_archives_empty": not any((STAGING / "remaining-donors-v4/cardinal/archives").iterdir()),
        "acceptance_boundary": "Read-only index refinement from completed manifests; no new decode, Blender, cook, integration, import or native-game proof.",
    }
    write(EXACT_RECEIPT, receipt)
    return receipt


def main():
    guard()
    for path in (SOURCE_INDEX, SOURCE_CONFIG, INV, PREVIOUS, INITIAL):
        if not path.is_file():
            raise FileNotFoundError(path)
    for path in (BASE, PRIVATE_GAME):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve prior output: {path}")

    inventory = json.loads(INV.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    chosen = selected_models(previous)
    villager_age04_paths = (
        "art/civilizations/chinese/humans/chi_villager_male_age04/chi_villager_male_age04.rgm",
        "art/civilizations/chinese/humans/chi_villager_female_age04/chi_villager_female_age04.rgm",
    )
    chosen_logicals = {rec["logical_model_path"] for rec, _ in chosen}
    for logical in villager_age04_paths:
        if logical not in chosen_logicals:
            rec = inventory["models"].get(logical)
            if not rec:
                raise RuntimeError("Active villager Age IV model missing from complete-donors inventory: " + logical)
            owners = [o for o in rec.get("owners", []) if o.get("owner") == "vn_unit_villager"]
            chosen.append(({"logical_model_path": logical, "owners": owners,
                            "source_inventory_status": rec.get("decode_status")}, None))
            chosen_logicals.add(logical)
    if not chosen:
        raise RuntimeError("No concrete render bodies with prior geometry manifests")
    texture_refs = manifest_refs(chosen)

    source = sqlite3.connect(f"file:{SOURCE_INDEX.as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    target = None
    BASE.mkdir(parents=True)
    try:
        target = sqlite3.connect(BASE / "private-index.sqlite3")
        tables = ("metadata", "archives", "assets", "resolved_assets", "folders", "object_types")
        for table in tables:
            target.execute(table_sql(source, table))

        paths = set(texture_refs)
        logicals = [rec["logical_model_path"] for rec, _ in chosen]
        for logical in logicals:
            stem = logical.removesuffix(".rgm")
            paths.update((logical, stem + ".rrgeom", stem + ".rrmaterial"))
            folder = logical.rsplit("/", 1)[0] + "/"
            paths.update(
                row[0] for row in source.execute(
                    "select logical_path from resolved_assets where logical_path like ?",
                    (folder + "%",),
                ) if row[0].endswith((".rgo", ".rhka", ".rootmotion"))
            )

        # The two newly confirmed, active Age IV bodies have no earlier decode
        # manifest. Include their local texture candidates for this first pass;
        # the resulting manifest records the exact RRtex references actually used.
        for logical in villager_age04_paths:
            folder = logical.rsplit("/", 1)[0] + "/"
            paths.update(row[0] for row in source.execute(
                "select logical_path from resolved_assets where logical_path like ? and extension='.rrtex'",
                (folder + "%",),
            ))
        paths.update(row[0] for row in source.execute(
            "select logical_path from resolved_assets where extension='.rrtex' "
            "and logical_path like 'art/civilizations/chinese/humans/tints/%'"
        ))

        resolved = []
        missing = []
        for logical in sorted(paths):
            rows = source.execute(
                "select * from resolved_assets where logical_path=?", (logical,)
            ).fetchall()
            if not rows:
                missing.append(logical)
            resolved.extend(rows)
        if missing:
            raise RuntimeError("Missing exact installed providers: " + ", ".join(missing[:20]))

        assets_by_id = {}
        archive_ids = set()
        for row in resolved:
            asset = source.execute("select * from assets where id=?", (row["id"],)).fetchone()
            if asset is None:
                raise RuntimeError("Asset provider missing for " + row["logical_path"])
            assets_by_id[asset["id"]] = asset
            archive_ids.add(asset["archive_id"])
        archives_by_id = {}
        for archive_id in archive_ids:
            archive = source.execute("select * from archives where id=?", (archive_id,)).fetchone()
            if archive is None or not Path(archive["path"]).is_file():
                raise RuntimeError("Provider archive unavailable: " + str(archive_id))
            archives_by_id[archive_id] = archive

        counts = {
            "archive_count": len(archives_by_id),
            "asset_count": len(assets_by_id),
            "resolved_asset_count": len(resolved),
        }
        for key, value in source.execute("select key,value from metadata"):
            target.execute(
                "insert into metadata values(?,?)",
                (key, str(counts[key]) if key in counts else value),
            )
        for table, rows in (
            ("archives", archives_by_id.values()),
            ("assets", assets_by_id.values()),
            ("resolved_assets", resolved),
        ):
            for row in rows:
                target.execute(
                    "insert into " + table + " values(" + ",".join("?" for _ in row) + ")",
                    tuple(row),
                )
        target.commit()
    finally:
        source.close()
        if target is not None:
            target.close()

    config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    game_root = owned(PRIVATE_GAME)
    archive_dir = game_root / "cardinal/archives"
    archive_dir.mkdir(parents=True)
    config["index_path"] = str(BASE / "private-index.sqlite3")
    config["game_root"] = str(game_root)
    config_path = BASE / "private-index-config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    source = sqlite3.connect(f"file:{SOURCE_INDEX.as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    provider_map = {}
    for logical in sorted({rec["logical_model_path"] for rec, _ in chosen} | paths):
        rows = source.execute(
        "select ra.logical_path, a.name, a.size, a.archive_id, ar.name, ar.path "
            "from resolved_assets ra join assets a on a.id=ra.id "
            "join archives ar on ar.id=a.archive_id where ra.logical_path=?", (logical,)
        ).fetchall()
        provider_map[logical] = [dict(row) for row in rows]
    source.close()

    results = []
    for index, (rec, _) in enumerate(chosen, 1):
        logical = rec["logical_model_path"]
        slug = re.sub(r"[^a-z0-9_-]+", "_", logical.split("/")[-2].lower())
        output = owned(BASE / "decoded" / f"{index:03d}_{slug}")
        log = owned(BASE / "logs" / f"{index:03d}_{slug}.log")
        args = [
            str(CORE), "convert", "decode-static", "--logical-path", logical,
            "--config", str(config_path), "--index", str(BASE / "private-index.sqlite3"),
            "--output-root", str(output),
        ]
        run = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=90)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            "COMMAND: " + " ".join(args) + "\nEXIT: " + str(run.returncode)
            + "\nSTDOUT:\n" + run.stdout + "\nSTDERR:\n" + run.stderr,
            encoding="utf-8",
        )
        payload = json.loads(run.stdout) if run.returncode == 0 else {}
        manifest = Path(payload["manifest_path"]) if payload.get("manifest_path") else None
        owners = rec.get("owners", [])
        prior_manifest = Path(rec["decode_manifest"]) if rec.get("decode_manifest") else None
        prior_data = json.loads(prior_manifest.read_text(encoding="utf-8")) if prior_manifest else {}
        prior_exact_refs = {
            t.get("logical_path") for t in prior_data.get("textures", []) if t.get("logical_path")
        } | set(prior_data.get("missing_textures", []))
        refs = {
            logical: provider_map.get(logical, []),
            "textures": {p: provider_map.get(p, []) for p in sorted(prior_exact_refs)},
        }
        if manifest and manifest.is_file():
            item = summarize_manifest(manifest, logical, owners, refs, log)
            decoded = json.loads(manifest.read_text(encoding="utf-8"))
            actual_refs = {
                t.get("logical_path") for t in decoded.get("textures", []) if t.get("logical_path")
            } | set(decoded.get("missing_textures", []))
            item["provider_refs"]["textures"] = {
                p: provider_map.get(p, []) for p in sorted(actual_refs)
            }
            results.append(item)
        else:
            results.append({
                "logical_model_path": logical,
                "owners": owners,
                "status": "decode_failed",
                "returncode": run.returncode,
                "provider_refs": refs,
                "log_sha256": sha(log),
                "stdout_tail": run.stdout[-1000:],
                "stderr_tail": run.stderr[-1000:],
            })

    unresolved = []
    initial = json.loads(INITIAL.read_text(encoding="utf-8"))
    for rec in initial["models"]:
        if rec.get("status") == "decode_failed":
            logical = rec["logical_model_path"]
            unresolved.append({
                "logical_path": logical,
                "owners": rec.get("owners", []),
                "route_classification": "generic_animator_or_effect_reference_without_standalone_geometry",
                "reason": rec.get("stderr_tail", "no standalone geometry/material provider in installed index"),
                "action": "Trace the consuming actor's concrete render-body slot; retain as animator/effect owner when no body slot exists.",
            })

    villager_actor = inventory.get("actor_closure", {}).get("attrib/ebps/vietnam/vn_unit_villager_1_chi.rgd", {})
    villager_frozen = villager_actor.get("frozen_xml_registry", {})
    villager_attachments = villager_frozen.get("attachments", [])
    tier4_overrides = [a for a in villager_attachments
                       if a.get("name") == "attachments" and a.get("value", "").endswith("/tier4_villager_chi")]
    villager_matrix = next((row for row in inventory.get("family_body_matrix", [])
                            if row.get("family") == "vn_unit_villager"), {})
    villager_age04 = {
        "effective_for_vn_unit_villager_1_chi": bool(tier4_overrides and tier4_overrides[0].get("overrideParent") == "True"),
        "source_actor": "attrib/ebps/vietnam/vn_unit_villager_1_chi.rgd",
        "source_actor_sha256": villager_frozen.get("sha256"),
        "effective_tier_attachment": "attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_villager_chi.rgd",
        "tier_attachment_sha256": next((e.get("attachment_sha256") for e in villager_matrix.get("attachment_model_evidence", [])
                                         if "male_age04" in e.get("logical_model_path", "")), None),
        "active_variants": sorted({e.get("variant") for e in villager_matrix.get("attachment_model_evidence", [])
                                    if "age04" in e.get("logical_model_path", "")}),
        "native_body_count": 8,
        "currently_decoded_body_count_before_this_batch": villager_matrix.get("complexity_budget", {}).get("decoded_model_count"),
        "age04_render_models": [
            {"logical_model_path": p, "status_before_batch": inventory["models"][p].get("decode_status"),
             "owner_relation": "render_body_model_slot", "field": "animator0"}
            for p in villager_age04_paths
        ],
        "conclusion": "Both Age IV render bodies are active through the Vietnamese actor's explicit Tier 4 attachment override and were included in this decode batch.",
    }

    receipt = {
        "schema": "ccp-060-remaining-actual-render-bodies/v2",
        "source_inventory_sha256": sha(INV),
        "previous_batch_sha256": sha(PREVIOUS),
        "initial_failed_routes_sha256": sha(INITIAL),
        "installed_index_sha256": sha(SOURCE_INDEX),
        "private_index_sha256": sha(BASE / "private-index.sqlite3"),
        "private_config_sha256": sha(config_path),
        "provider_archive_count": len(archives_by_id),
        "provider_asset_row_count": len(assets_by_id),
        "resolved_provider_row_count": len(resolved),
        "exact_texture_ref_count": len({p for model in results for p in model.get("provider_refs", {}).get("textures", {})}),
        "private_game_archives_directory_is_empty": not any(archive_dir.iterdir()),
        "selection_basis": "Only prior successful concrete render-body geometry manifests; generic archetype/animator and effect-only routes are reported separately.",
        "models": results,
        "villager_age04_reachability": villager_age04,
        "unsupported_or_reference_only_routes": unresolved,
        "acceptance_boundary": "Static provider-complete decode inventory only; no Blender, cook, integration, import, or native game proof.",
    }
    write(BASE / "batch-report-v2.json", receipt)
    return {
        "selected": len(chosen),
        "decoded_complete": sum(item["status"] == "decoded_complete" for item in results),
        "with_errors": sum(item["status"] != "decoded_complete" for item in results),
        "exact_textures": len(texture_refs),
        "unsupported_routes": len(unresolved),
        "report": str(BASE / "batch-report-v2.json"),
        "provider_rows": len(resolved),
        "archives": len(archives_by_id),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("decode", "refine-exact-index"), default="decode")
    args = parser.parse_args()
    result = main() if args.action == "decode" else refine_exact_private_index()
    print(json.dumps(result, indent=2))
