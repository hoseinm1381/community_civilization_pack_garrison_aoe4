"""Decode exact stock bodies for 0.6.0 pilot authoring, without Blender or cooks."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

from common import CORE, OUT, guard, owned, read, sha, write

DEST = OUT / "pilots"
SELECT = {
    "spear2": "chi_infantry_light_age02.rgm",
    "male_villager1": "chi_villager_male_age01.rgm",
    "female_villager1": "chi_villager_female_age01.rgm",
    "horseman2": "chi_horse_combined_light_age02.rgm",
    "elephant": "sul_elephant_combined_armor_age03.rgm",
    "siege_mangonel3": "eng_mangonel.rgm",
}
INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
CONFIG = INDEX.with_name("game-assets.local.json")
_FILE_HASHES: dict[Path, str] = {}


def digest(path: Path) -> str:
    if path not in _FILE_HASHES:
        _FILE_HASHES[path] = sha(path)
    return _FILE_HASHES[path]


def provider_identity(logical: str) -> dict:
    stem = logical.removesuffix(".rgm")
    paths = [stem + ext for ext in (".rgm", ".rrgeom", ".rrmaterial")]
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        rows = [db.execute("select archive_path from resolved_assets where lower(logical_path)=?",
                           (p.lower(),)).fetchall() for p in paths]
    if any(len(group) != 1 for group in rows):
        raise RuntimeError(f"Missing or ambiguous official model provider: {paths}, {rows}")
    archives = {str(Path(group[0][0])): digest(Path(group[0][0])) for group in rows}
    return {"index_sha256": digest(INDEX), "config_sha256": digest(CONFIG),
            "model_and_companions": paths, "archives": archives}


def decode_one(name: str, trace: dict) -> dict:
    pilot = trace["pilots"][name]
    matches = [m for m in pilot["stock_models"].values()
               if m["logical_path"].endswith("/" + SELECT[name])]
    if len(matches) != 1 or matches[0]["status"] != "confirmed":
        raise RuntimeError(f"Cannot uniquely select a current official model for {name}: {matches}")
    model = matches[0]
    source_identity = provider_identity(model["logical_path"])
    fingerprint = hashlib.sha256(json.dumps(source_identity, sort_keys=True).encode()).hexdigest()[:20]
    target = owned(DEST / name / "decoded" / ("verified-" + fingerprint))
    target.mkdir(parents=True, exist_ok=True)
    receipt_path = target / "source-identity.json"
    existing = list(target.glob("*/decoded-static.json"))
    if existing:
        if len(existing) != 1:
            raise RuntimeError(f"Ambiguous existing decode for {name}: {existing}")
        manifest = existing[0]
        if not receipt_path.is_file():
            raise RuntimeError(f"Unverified old decode cache: {target}")
        receipt = read(receipt_path)
        if receipt["source_identity"] != source_identity or receipt["manifest_sha256"] != sha(manifest):
            raise RuntimeError(f"Stale or modified stock decode: {target}")
    else:
        done = subprocess.run([str(CORE), "convert", "decode-static",
                               "--logical-path", model["logical_path"],
                               "--config", str(CONFIG), "--index", str(INDEX),
                               "--output-root", str(target)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
        if done.returncode:
            raise RuntimeError(f"{name} stock decode failed: {done.stderr[-1500:]} {done.stdout[-500:]}")
        manifests = list(target.glob("*/decoded-static.json"))
        if len(manifests) != 1:
            raise RuntimeError(f"{name} did not produce one decoded manifest: {manifests}")
        manifest = manifests[0]
        write(receipt_path, {"source_identity": source_identity,
                             "manifest_sha256": sha(manifest)})
    data = read(manifest)
    groups = data.get("geometry", {}).get("groups", [])
    skeleton = data.get("skeleton") or {}
    return {"stock_model": model, "source_identity": source_identity,
            "manifest": str(manifest), "manifest_sha256": sha(manifest),
            "status": data.get("status"), "blockers": data.get("blockers"),
            "warnings": data.get("warnings"),
            "group_count": len(groups),
            "groups": [{"name": g.get("name"), "material": g.get("material"),
                        "projection_kind": g.get("projection_kind"),
                        "vertices": g.get("vertex_count"), "triangles": g.get("triangle_count"),
                        "bounds": g.get("bounds")}
                       for g in groups],
            "skeleton_keys": sorted(skeleton),
            "skeleton_bones": len(skeleton.get("bones", [])),
            "texture_count": len(data.get("textures", [])),
            "missing_texture_count": len(data.get("missing_textures", [])),
            "animated_asset_import_plan": data.get("animated_asset_import_plan")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=SELECT)
    selected = parser.parse_args().pilot
    guard()
    trace = read(DEST / "pilot-trace.json")
    summary_path = DEST / "pilot-decodes.json"
    summary = read(summary_path) if summary_path.exists() else {
        "schema": "ccp-060-pilot-decodes/v1",
        "evidence": "Garrison read-only stock decode, no Blender export/cook/runtime proof",
        "pilots": {}}
    for name in SELECT:
        if selected and selected != name:
            continue
        summary["pilots"][name] = decode_one(name, trace)
        write(summary_path, summary)
        print(name, summary["pilots"][name]["status"],
              summary["pilots"][name]["group_count"], "groups")


if __name__ == "__main__":
    main()
