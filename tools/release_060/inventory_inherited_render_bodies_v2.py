"""Trace and statically decode the newly proven inherited render bodies."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

from common import CORE, OUT, guard, owned, sha

BASE = OUT / "inventory/inherited-render-bodies-v2"
RUN = BASE / "run-003"
SOURCE_INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
SOURCE_CONFIG = SOURCE_INDEX.with_name("game-assets.local.json")
PRIVATE_GAME = owned(RUN / "task-game")
PRIVATE_INDEX = owned(RUN / "private-index-models.sqlite3")
EXACT_INDEX = owned(RUN / "private-index-exact.sqlite3")
CONFIG = owned(RUN / "private-index-config.json")
EXACT_CONFIG = owned(RUN / "private-index-exact-config.json")
RECEIPT = owned(RUN / "receipt.json")

MODELS = {
    "english-battering-ram": "art/civilizations/english/team_weapons/eng_battering_ram/eng_battering_ram.rgm",
    "english-springald": "art/civilizations/english/team_weapons/eng_springald/eng_springald.rgm",
    "english-counterweight-trebuchet": "art/civilizations/english/team_weapons/eng_trebuchet_counterweight/eng_trebuchet_counterweight.rgm",
    "english-traction-trebuchet": "art/civilizations/english/team_weapons/eng_trebuchet_traction/eng_trebuchet_traction.rgm",
    "chinese-monk-tier4": "art/civilizations/chinese/humans/chi_infantry_monk_age04/chi_infantry_monk_age04.rgm",
    "chinese-trade-cart-tier4": "art/civilizations/chinese/animals/chi_horse_combined_trade_age04/chi_horse_combined_trade_age04.rgm",
    "chinese-repeater-crossbow-tier4": "art/civilizations/chinese/humans/chi_ranged_crossbow_age04/chi_ranged_crossbow_age04.rgm",
    "generic-siege-cart-owner-probe": "art/civilizations/common/team_weapons/archetypes/siege_cart/siege_cart.rgm",
}
COMPANIONS = (".rgm", ".rrgeom", ".rrmaterial", ".rgo", ".rhka", ".rootmotion")


def json_write(path: Path, data: object) -> None:
    path = owned(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def table_sql(db: sqlite3.Connection, table: str) -> str:
    row = db.execute("select sql from sqlite_master where type='table' and name=?", (table,)).fetchone()
    if not row or not row[0]:
        raise RuntimeError(f"Installed index table missing: {table}")
    return row[0]


def extract_candidate_rows(source: sqlite3.Connection, logical_models: list[str]) -> tuple[dict, dict, list]:
    paths: set[str] = set()
    for logical in logical_models:
        stem = logical.removesuffix(".rgm")
        paths.update(stem + ext for ext in COMPANIONS)
        folder = stem.rsplit("/", 1)[0] + "/"
        paths.update(row[0] for row in source.execute(
            "select distinct logical_path from resolved_assets where lower(logical_path) like lower(?) and lower(extension)='.rrtex'",
            (folder + "%",),
        ))
    resolved = []
    missing = []
    for logical in sorted(paths):
        rows = source.execute("select * from resolved_assets where lower(logical_path)=lower(?)", (logical,)).fetchall()
        if rows:
            resolved.extend(rows)
        elif logical.lower().endswith(".rgm"):
            missing.append(logical)
    if missing:
        raise RuntimeError("Missing official current model providers: " + ", ".join(missing))
    ids = {int(row[0]) for row in resolved}
    assets = {asset_id: source.execute("select * from assets where id=?", (asset_id,)).fetchone() for asset_id in ids}
    if any(row is None for row in assets.values()):
        raise RuntimeError("Resolved provider references a missing asset row")
    archive_ids = {int(row[1]) for row in assets.values()}
    archives = {archive_id: source.execute("select * from archives where id=?", (archive_id,)).fetchone() for archive_id in archive_ids}
    if any(row is None or not Path(row[3]).is_file() for row in archives.values()):
        raise RuntimeError("An exact provider archive is unavailable")
    return assets, archives, resolved


def create_private_index(source_path: Path, target_path: Path, logical_models: list[str], exact_textures: set[str] | None = None) -> dict:
    source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    try:
        paths: set[str] = set()
        for logical in logical_models:
            stem = logical.removesuffix(".rgm")
            paths.update(stem + ext for ext in COMPANIONS)
            if exact_textures is None:
                folder = stem.rsplit("/", 1)[0] + "/"
                paths.update(row[0] for row in source.execute(
                    "select distinct logical_path from resolved_assets where lower(folder)=lower(?) and lower(extension)='.rrtex'",
                    (folder,),
                ))
        if exact_textures is not None:
            paths.update(exact_textures)
        resolved = []
        missing = []
        for logical in sorted(paths):
            rows = source.execute("select * from resolved_assets where lower(logical_path)=lower(?)", (logical,)).fetchall()
            if rows:
                resolved.extend(rows)
            elif logical.lower().endswith((".rgm", ".rrtex")):
                missing.append(logical)
        if missing:
            raise RuntimeError("Missing official current model providers: " + ", ".join(missing))
        assets = {}
        archives = {}
        for row in resolved:
            asset_id = int(row[0])
            if asset_id not in assets:
                asset = source.execute("select * from assets where id=?", (asset_id,)).fetchone()
                if asset is None:
                    raise RuntimeError("Missing exact asset row for " + str(row[1]))
                assets[asset_id] = asset
                archive_id = int(asset[1])
                if archive_id not in archives:
                    archive = source.execute("select * from archives where id=?", (archive_id,)).fetchone()
                    if archive is None or not Path(archive[3]).is_file():
                        raise RuntimeError("Unavailable provider archive for " + str(row[1]))
                    archives[archive_id] = archive
        target = sqlite3.connect(target_path)
        try:
            for table in ("metadata", "archives", "assets", "resolved_assets", "folders", "object_types"):
                target.execute(table_sql(source, table))
            counts = {"archive_count": len(archives), "asset_count": len(assets), "resolved_asset_count": len(resolved)}
            for key, value in source.execute("select key,value from metadata"):
                target.execute("insert into metadata values(?,?)", (key, str(counts.get(key, value))))
            for table, records in (("archives", archives.values()), ("assets", assets.values()), ("resolved_assets", resolved)):
                for row in records:
                    target.execute("insert into " + table + " values(" + ",".join("?" for _ in row) + ")", tuple(row))
            target.commit()
        finally:
            target.close()
        return {
            "index_path": str(target_path), "index_sha256": sha(target_path),
            "model_paths": logical_models, "indexed_logical_paths": sorted(paths),
            "provider_archives": [dict(row) for row in archives.values()],
            "provider_asset_count": len(assets), "resolved_provider_count": len(resolved),
        }
    finally:
        source.close()


def decode(index: Path, config: Path, label: str, logical: str) -> dict:
    output = owned(RUN / "decodes" / label)
    log = owned(RUN / "logs" / (label + ".log"))
    if output.exists() or log.exists():
        raise FileExistsError(f"Preserving existing decode output: {output if output.exists() else log}")
    args = [str(CORE), "convert", "decode-static", "--logical-path", logical,
            "--config", str(config), "--index", str(index), "--output-root", str(output)]
    run = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("COMMAND: " + " ".join(args) + "\nEXIT: " + str(run.returncode)
                   + "\nSTDOUT:\n" + run.stdout + "\nSTDERR:\n" + run.stderr, encoding="utf-8")
    payload = {}
    try:
        payload = json.loads(run.stdout)
    except json.JSONDecodeError:
        pass
    manifest = Path(payload["manifest_path"]) if payload.get("manifest_path") else None
    result = {"logical_path": logical, "returncode": run.returncode, "stdout": run.stdout[-2000:],
              "stderr": run.stderr[-2000:], "log": str(log), "log_sha256": sha(log),
              "manifest": str(manifest) if manifest else None,
              "manifest_sha256": sha(manifest) if manifest and manifest.is_file() else None}
    if manifest and manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        groups = data.get("geometry", {}).get("groups", [])
        result.update({"status": data.get("status"), "blockers": data.get("blockers", []),
                       "warnings": data.get("warnings", []), "groups": [
                           {"name": g.get("name"), "material": g.get("material"),
                            "vertices": g.get("vertex_count"), "triangles": g.get("triangle_count"),
                            "bounds": g.get("bounds")} for g in groups],
                       "textures": [t.get("logical_path") for t in data.get("textures", []) if t.get("logical_path")],
                       "missing_textures": data.get("missing_textures", [])})
    return result


def main() -> None:
    guard()
    BASE.mkdir(parents=True, exist_ok=True)
    for path in (PRIVATE_INDEX, EXACT_INDEX, CONFIG, EXACT_CONFIG, RECEIPT):
        if path.exists():
            raise FileExistsError(f"Preserving prior inventory output: {path}")
    if not SOURCE_INDEX.is_file() or not SOURCE_CONFIG.is_file():
        raise FileNotFoundError("Installed resolved-assets index/config is unavailable")
    if PRIVATE_GAME.exists() and any(PRIVATE_GAME.rglob("*")):
        raise FileExistsError(f"Task-owned game root is not empty: {PRIVATE_GAME}")
    (PRIVATE_GAME / "cardinal/archives").mkdir(parents=True, exist_ok=True)
    if any((PRIVATE_GAME / "cardinal/archives").iterdir()):
        raise RuntimeError("Task game cardinal/archives must be empty for this decode")

    source_config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    source_conn = sqlite3.connect(f"file:{SOURCE_INDEX.as_posix()}?mode=ro", uri=True)
    source_conn.row_factory = sqlite3.Row
    try:
        candidates = create_private_index(SOURCE_INDEX, PRIVATE_INDEX, list(MODELS.values()))
        source_identity = {"index": str(SOURCE_INDEX), "index_sha256": sha(SOURCE_INDEX),
                           "config": str(SOURCE_CONFIG), "config_sha256": sha(SOURCE_CONFIG),
                           "game_root": source_config.get("game_root"),
                           "archives": candidates["provider_archives"]}
    finally:
        source_conn.close()
    config_data = dict(source_config)
    config_data["index_path"] = str(PRIVATE_INDEX)
    config_data["game_root"] = str(PRIVATE_GAME)
    config_data["sga_archiver"] = str(Path(config_data["sga_archiver"]))
    json_write(CONFIG, config_data)

    candidate_results = {}
    for label, logical in MODELS.items():
        candidate_results[label] = decode(PRIVATE_INDEX, CONFIG, label + "-candidate", logical)
    exact_textures = {p for item in candidate_results.values()
                      for p in (item.get("textures", []) + item.get("missing_textures", []))}
    exact = create_private_index(SOURCE_INDEX, EXACT_INDEX, list(MODELS.values()), exact_textures)
    exact_config = dict(config_data)
    exact_config["index_path"] = str(EXACT_INDEX)
    json_write(EXACT_CONFIG, exact_config)
    exact_results = {}
    for label, logical in MODELS.items():
        exact_results[label] = decode(EXACT_INDEX, EXACT_CONFIG, label + "-exact", logical)

    receipt = {
        "schema": "ccp-060-inherited-render-bodies-v2/v1",
        "status": "targeted_current_official_asset_decode_complete",
        "acceptance_boundary": "Static official-resource reference and Garrison decode evidence only; no Blender authoring, cook, source integration, import, lobby selection, or native-match behavior was performed or established.",
        "source_identity": source_identity,
        "task_game_cardinal_archives_empty": not any((PRIVATE_GAME / "cardinal/archives").iterdir()),
        "attachment_decode_files": [str(BASE / f) for f in ("tier4-monk.xml", "tier4-trade-cart.xml", "siege-cart-core.xml")],
        "candidate_index": candidates,
        "exact_index": exact,
        "candidate_decodes": candidate_results,
        "exact_decodes": exact_results,
    }
    json_write(RECEIPT, receipt)
    print(json.dumps({"status": receipt["status"], "receipt": str(RECEIPT),
                      "exact_models": {k: {"status": v.get("status"), "groups": v.get("groups"),
                                           "blockers": v.get("blockers")} for k, v in exact_results.items()}}, indent=2))


if __name__ == "__main__":
    main()
