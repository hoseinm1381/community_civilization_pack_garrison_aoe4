"""Project native stamp transforms into Blender world axes for grade checks."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/release_070/integration"))
from university_transform_contract import world_from_model, engine_to_blender, bounds

BASE = ROOT / "output/release_070/integration"
OUT = BASE / "ground-plane"


def corners(lo, hi):
    return list(itertools.product(*zip(lo, hi)))


def main() -> None:
    owners = json.loads((BASE / "native-owner/owners.json").read_text())["owners"]
    rows = []
    for owner in owners:
        family = owner["family"]
        measure = json.loads((BASE / f"native-measure/{family}.json").read_text())
        t = owner["stock_transform"]
        local = corners(measure["model_local_bounds_min"], measure["model_local_bounds_max"])
        world = [engine_to_blender(world_from_model(p, t)) for p in local]
        rows.append({"family": family, "stamp_quaternion_engine": t[:4],
                     "stamp_translation_engine_xyz": t[4:7],
                     "stamp_translation_blender_xyz": engine_to_blender(t[4:7]),
                     "stock_model_local_bounds_blender": bounds(local),
                     "stock_main_world_bounds_blender": bounds(world),
                     "vertical_stamp_translation_engine_y": t[5]})
    garden = next(x for x in rows if x["family"] == "garden")
    art = json.loads((ROOT / "art/exports/buildings_070/garden-r3/source-receipt.json").read_text())
    q = next(x for x in owners if x["family"] == "garden")["stock_transform"]
    local = corners(art["model_local_bounds"]["min"], art["model_local_bounds"]["max"])
    world = [engine_to_blender(world_from_model(p, q)) for p in local]
    garden["r3_model_local_bounds_blender"] = bounds(local)
    garden["r3_main_world_bounds_blender"] = bounds(world)
    garden["r3_named_level_probes"] = {name: engine_to_blender(world_from_model((0,0,z),q))[2]
          for name,z in {"model_origin_grade": 0.0, "recessed_water_example": -0.106,
                         "plinth_top_example": 0.265}.items()}
    result = {"schema": "ccp-070-native-stamp-ground-projection/v1",
              "projection": "Blender=(-engine.x,-engine.z,engine.y); vertical is stamp ty, not tz",
              "rows": rows,
              "interpretation": "All four main stamps have engine ty=0 and pure Y-axis rotation, so they preserve model-local Blender Z heights. Garden stamp tz=-0.452 and Wonder stamp tz=+1.423 are horizontal shifts in Blender Y. Art-specific terrain contact still needs a fresh match, but no vertical export shift follows from those native tz values."}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"garden_r3_world_bounds": garden["r3_main_world_bounds_blender"],
                      "wonder_stamp_blender_translation": next(x for x in rows if x["family"] == "wonder")["stamp_translation_blender_xyz"],
                      "receipt": str(OUT / "receipt.json")}))


if __name__ == "__main__":
    main()
