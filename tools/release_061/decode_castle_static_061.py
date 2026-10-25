"""Read-only 0.6.0 Castle model decode with an owned, isolated asset index.

Never changes the installed asset index, source project, archives, or earlier outputs.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import configuration, check_storage

cfg = configuration(ROOT)
check_storage(ROOT, cfg)
out = ROOT / "output/release_061/castle-static-decode"
if out.exists():
    raise FileExistsError(f"Preserve existing run: {out}")
out.mkdir(parents=True)
archive = ROOT / "output/release_060/assembly/candidate-r2/community_civilization_pack.sga"
archiver = Path(cfg["archive_tool"])
core = Path(cfg["garrison_core"])
listing_process = subprocess.run([str(archiver), "list", str(archive), "--verify"],
                                 capture_output=True, text=True, check=True)
listing = json.loads(listing_process.stdout)
if not listing["archive"]["verification"]["verified"]:
    raise RuntimeError("Archive verification failed")
for name in ("imperial_citadel", "resistance_hq"):
    stem = f"art/scenario/cccastle/{name}/model"
    present = {x["path"] for x in listing["members"]}
    if not all(stem + suffix in present for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")):
        raise RuntimeError(f"Incomplete model quartet: {stem}")

spec = importlib.util.spec_from_file_location(
    "pairing", ROOT / "tools/release_060/inspect_archer_pairing_static.py")
pairing = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "tools/release_060"))
assert spec and spec.loader
spec.loader.exec_module(pairing)
pairing.INDEX = out / "game-assets.sqlite3"
pairing.tiny_index(archive.resolve(), listing["members"], cfg["project_guid"].replace("-", ""))
original_config = Path.home() / "AppData/Local/Garrison/Kit/game-assets.local.json"
config = json.loads(original_config.read_text(encoding="utf-8"))
config["index_path"] = str(pairing.INDEX)
config_path = out / "game-assets.local.json"
config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

rows = []
for name in ("imperial_citadel", "resistance_hq"):
    logical = f"art/scenario/cccastle/{name}/model.rgm"
    target = out / name
    target.mkdir()
    command = [str(core), "convert", "decode-static", "--logical-path", logical,
               "--config", str(config_path), "--index", str(pairing.INDEX),
               "--output-root", str(target)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=300)
    (out / f"{name}.log").write_text(
        f"EXIT: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        encoding="utf-8")
    manifests = list(target.glob("*/decoded-static.json"))
    rows.append({"name": name, "exit_code": proc.returncode,
                 "manifests": [str(p) for p in manifests],
                 "stderr_tail": proc.stderr[-800:]})
(out / "receipt.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
print(json.dumps(rows, indent=2))
