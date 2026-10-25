"""Decode exact official riderless worker-elephant model with a tiny read-only provider index."""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from common import CORE, OUT, STAGING, guard, owned, sha, write

SOURCE_INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
SOURCE_CONFIG = SOURCE_INDEX.with_name("game-assets.local.json")
LOGICAL = "art/civilizations/sultanate_ha_tug/animals/tug_elephant_worker_age01/tug_elephant_worker_age01.rgm"
BASE = OUT / "qualification/nonhumanoid-route-preflight/worker-elephant-stock"
INDEX, CONFIG, DECODE, LOG, REPORT = [BASE / n for n in
                                     ("private-index.sqlite3", "private-index-config.json", "decoded", "decode.log", "report.json")]


def main():
    guard()
    for path in (INDEX, CONFIG, DECODE, LOG, REPORT):
        owned(path)
        if path.exists():
            raise FileExistsError("Preserve previous official worker-elephant inspection")
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect("file:" + SOURCE_INDEX.as_posix() + "?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    target = sqlite3.connect(INDEX)
    try:
        paths = [LOGICAL.removesuffix(".rgm") + ext for ext in (".rgm", ".rrgeom", ".rrmaterial")]
        resolved = [source.execute("select * from resolved_assets where logical_path=?", (path,)).fetchone()
                    for path in paths]
        if any(row is None for row in resolved):
            raise RuntimeError("Official worker-elephant model/geometry/material provider incomplete")
        asset_rows = [source.execute("select * from assets where id=?", (row["id"],)).fetchone()
                      for row in resolved]
        if any(row is None for row in asset_rows):
            raise RuntimeError("Official worker-elephant asset rows missing")
        archive_ids = sorted({row["archive_id"] for row in asset_rows})
        archives = [source.execute("select * from archives where id=?", (id,)).fetchone()
                    for id in archive_ids]
        if any(row is None or not Path(row["path"]).is_file() for row in archives):
            raise RuntimeError("Official worker-elephant archive provider absent")
        for table in ("metadata", "archives", "assets", "resolved_assets", "folders", "object_types"):
            sql = source.execute("select sql from sqlite_master where type='table' and name=?", (table,)).fetchone()[0]
            target.execute(sql)
        for row in source.execute("select * from metadata"):
            key, value = row
            if key == "archive_count": value = str(len(archives))
            elif key in ("asset_count", "resolved_asset_count"): value = "3"
            target.execute("insert into metadata values(?,?)", (key, value))
        for table, rows in (("archives", archives), ("assets", asset_rows), ("resolved_assets", resolved)):
            for row in rows:
                target.execute("insert into " + table + " values(" + ",".join("?" for _ in row) + ")", tuple(row))
        target.commit()
        provenance = [{"logical_path": row["logical_path"], "archive": row["archive"],
                       "archive_path": row["archive_path"], "size": row["size"]} for row in resolved]
    finally:
        source.close(); target.close()
    cfg = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    private_root = owned(STAGING / "swe")
    (private_root / "cardinal/archives").mkdir(parents=True, exist_ok=True)
    cfg["index_path"], cfg["game_root"] = str(INDEX), str(private_root)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    args = [str(CORE), "convert", "decode-static", "--logical-path", LOGICAL,
            "--config", str(CONFIG), "--index", str(INDEX), "--output-root", str(DECODE)]
    run = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=120)
    LOG.write_text("COMMAND: " + " ".join(args) + "\nEXIT: " + str(run.returncode)
                   + "\nSTDOUT:\n" + run.stdout + "\nSTDERR:\n" + run.stderr, encoding="utf-8")
    payload = json.loads(run.stdout) if run.returncode == 0 else {}
    manifest = Path(payload["manifest_path"]) if payload.get("manifest_path") else None
    status = "official_worker_elephant_decoded" if manifest and manifest.is_file() else "official_worker_elephant_decode_failed_preserved"
    result = {"schema": "ccp-060-worker-elephant-official-source-inspection/v1", "status": status,
              "logical_path": LOGICAL, "providers": provenance,
              "private_index_sha256": sha(INDEX), "private_config_sha256": sha(CONFIG),
              "decode_exit_code": run.returncode, "decode_log_sha256": sha(LOG),
              "decoded_manifest": str(manifest) if manifest else None,
              "decoded_manifest_sha256": sha(manifest) if manifest and manifest.is_file() else None,
              "not_an_integrated_binding_or_native_game_proof": True}
    write(REPORT, result)
    if status != "official_worker_elephant_decoded":
        raise RuntimeError("Official worker-elephant source decode failed; report preserved")
    donor = json.loads(manifest.read_text(encoding="utf-8"))
    return {"status": status, "bones": len(donor["skeleton"]["bones"]),
            "palettes": [len(x["bones"]) for x in donor["skeleton"]["skin_palettes"]],
            "groups": [(g["name"], g["material"], g["triangle_count"]) for g in donor["geometry"]["groups"]],
            "report": str(REPORT)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
