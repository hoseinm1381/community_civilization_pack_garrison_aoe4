"""Verify Garrison's registered private copies match roof-source PNGs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/release_020/barracks_tc"
PROJECT = OUT / "library/Mods/community_civilization_pack"
RECIPE = ROOT / "art/recipes/release_020/barracks-tc-materials.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

recipe = json.loads(RECIPE.read_text())
manifest = json.loads((PROJECT / "mod-project.json").read_text())
variants = {v["name"]: v for v in manifest["model_variants"]}
count = 0
for model in recipe["models"]:
    for row in model["roof_materials"]:
        variant = variants[row["carrier"]]
        assert variant["source"] == model["stock_model"]
        logical = variant["textures"][row["slot"]]
        registered = PROJECT / "project/source" / logical
        assert registered.exists() and sha(registered) == row["image_sha256"]
        row["registered_project_input"] = str(registered)
        row["registered_project_input_sha256"] = sha(registered)
        count += 1
assert count == len(variants) == 24
recipe["registered_inputs_verified"] = count
recipe["garrison_project_sha256"] = sha(PROJECT / "mod-project.json")
RECIPE.write_text(json.dumps(recipe, indent=2), encoding="utf8")
(OUT / "materials-ready.json").write_text(json.dumps(recipe, indent=2), encoding="utf8")
print("PROJECT_INPUTS_PASS", count)
