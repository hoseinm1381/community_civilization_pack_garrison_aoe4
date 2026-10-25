"""Record frozen 0.2.0 model inputs and placement calculations for integration."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES = ROOT / "art/recipes/release_020"
OUT = ROOT / "output/release_020/ministry_farm_hideout/final-handoff.json"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_recipe(stem):
    path = RECIPES / f"{stem}-source.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert digest(data["source"]) == data["source_sha256"], stem
    for name, expected in data["export_files"].items():
        assert digest(Path(data["export"]) / name) == expected, (stem, name)
    return {"recipe": str(path), "recipe_sha256": digest(path),
            "editable_source": data["source"], "editable_source_sha256": data["source_sha256"],
            "exports": {name: {"path": str(Path(data["export"]) / name), "sha256": value}
                        for name, value in data["export_files"].items()}}


source = json.loads((RECIPES / "hideout-source.json").read_text(encoding="utf-8"))
hideout = {}
for entry in source["models"]:
    checks = (("editable_blend", "editable_blend_sha256"),
              ("geometry_export", "geometry_sha256"))
    for path_key, hash_key in checks:
        assert digest(entry[path_key]) == entry[hash_key], (entry["variant"], path_key)
    hideout[entry["variant"]] = {
        "donor_manifest": entry["donor_manifest"],
        "donor_manifest_sha256": digest(entry["donor_manifest"]),
        "donor_geometry_sha256": entry["donor_geometry_sha256"],
        "editable_blend": entry["editable_blend"],
        "editable_blend_sha256": entry["editable_blend_sha256"],
        "rrgeom": entry["geometry_export"],
        "rrgeom_sha256": entry["geometry_sha256"],
        "stock_bounds": entry["before_bounds"],
        "remodeled_bounds": entry["after_bounds"],
        "topology_contact_audit": entry["contact_checks"],
    }

data = {
    "schema": "ccp.020-ministry-farm-hideout-final-handoff/v1",
    "scope": "frozen editable art and exports only; integration owns native cook/binding",
    "art": {key: frozen_recipe(key) for key in
            ("ministry", "farm", "shelter_default", "shelter_stone")},
    "hideout_native_remodel_recipe": str(RECIPES / "hideout-source.json"),
    "hideout_native_remodel_recipe_sha256": digest(RECIPES / "hideout-source.json"),
    "hideout": hideout,
    "placement": {
        "ministry": {
            "source_axis_shift": "Blender Y -1.812 m; expected Garrison native local Z +1.812 m",
            "unchanged_native_stamp": "180 degree Y rotation, translation local Z +1.881305 m",
            "pre_shift_cooked_native_local_z": [-3.635, 3.773],
            "expected_final_native_local_z": [-1.823, 5.585],
            "expected_world_horizontal_z": [-3.704, 3.704],
            "world_floor_y": 0.0,
            "qualification": "calculation only; confirm exact final cooked RRGEOM world bounds before release"
        },
        "farm_edge": {
            "world_floor_y": 0.0,
            "binding": "retained sagebush visual positions/yaws across four clearable native outskirts stamps",
            "central_crop": "unchanged farm_rice_a stamp and resource_animator",
            "qualification": "visual proxy, not native game placement proof"
        },
        "hideout_shelters": {
            "world_min_y_m": {"default": 0.02, "stone": 0.02},
            "binding": "new private visual stamp identity coordinates; 180 degree native Y yaw mirrors horizontal only",
            "stock_buried_geometry": "stock donor body already extends below terrain; untouched low vertices retained",
            "qualification": "source vertex minimum from screened footing geometry; verify cooked composite"
        }
    },
    "previews": {
        "hideout_default_composite": str(ROOT / "output/release_020/ministry_farm_hideout/hideout/composite/default/iso.png"),
        "hideout_stone_composite": str(ROOT / "output/release_020/ministry_farm_hideout/hideout/composite/stone/iso.png"),
        "farm_before": str(ROOT / "output/release_020/ministry_farm_hideout/farm/context/isolated-before.png"),
        "farm_after": str(ROOT / "output/release_020/ministry_farm_hideout/farm/context/isolated-after.png"),
        "farm_adjacent": str(ROOT / "output/release_020/ministry_farm_hideout/farm/context/adjacent-after.png"),
        "farm_context_receipt": str(ROOT / "output/release_020/ministry_farm_hideout/farm/context/context.json"),
    },
    "gates": {"authoring_export": "passed hash/preflight", "native_cook": "integration-owned pending",
              "client_import": "outside milestone", "native_match": "outside milestone"}
}
for item in data["previews"].values():
    assert Path(item).is_file(), item
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"handoff": str(OUT), "sha256": digest(OUT),
                  "hideout": {key: value["rrgeom_sha256"] for key, value in hideout.items()}}, indent=2))
