"""Decode all scoped official donor models for 0.8.0 into staging and pin their hashes."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import CORE, OUT, RECIPES, STAGING, guard, owned, read, sha, write

INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
CONFIG = INDEX.with_name("game-assets.local.json")

DONORS = [
    # Buildings: Dock Ages II-IV
    {
        "key": "dock_age02",
        "family": "dock",
        "age": 2,
        "kind": "building",
        "logical_path": "art/civilizations/chinese/structures/dock/chi_dock_control_age02/chi_dock_control_age02.rgm",
        "animation_owner": None,
    },
    {
        "key": "dock_age03",
        "family": "dock",
        "age": 3,
        "kind": "building",
        "logical_path": "art/civilizations/chinese/structures/dock/chi_dock_control_age03/chi_dock_control_age03.rgm",
        "animation_owner": None,
    },
    {
        "key": "dock_age04",
        "family": "dock",
        "age": 4,
        "kind": "building",
        "logical_path": "art/civilizations/chinese/structures/dock/chi_dock_control_age04/chi_dock_control_age04.rgm",
        "animation_owner": None,
    },
    # Buildings: Barracks Ages I-IV
    {
        "key": "barracks_age01",
        "family": "barracks",
        "age": 1,
        "kind": "building",
        "logical_path": "art/civilizations/chinese/structures/barracks/chi_barracks_control_age01/chi_barracks_control_age01.rgm",
        "animation_owner": None,
    },
    {
        "key": "barracks_age02",
        "family": "barracks",
        "age": 2,
        "kind": "building",
        "logical_path": "art/civilizations/chinese/structures/barracks/chi_barracks_control_age02/chi_barracks_control_age02.rgm",
        "animation_owner": None,
    },
    {
        "key": "barracks_age03",
        "family": "barracks",
        "age": 3,
        "kind": "building",
        "logical_path": "art/civilizations/chinese/structures/barracks/chi_barracks_control_age03/chi_barracks_control_age03.rgm",
        "animation_owner": None,
    },
    {
        "key": "barracks_age04",
        "family": "barracks",
        "age": 4,
        "kind": "building",
        "logical_path": "art/civilizations/chinese/structures/barracks/chi_barracks_control_age04/chi_barracks_control_age04.rgm",
        "animation_owner": None,
    },
    # Non-humanoid: Water Buffalo (official cattle rig/model)
    {
        "key": "water_buffalo",
        "family": "water_buffalo",
        "age": 1,
        "kind": "nonhumanoid",
        "logical_path": "art/civilizations/gaia/animals/cow/cow.rgm",
        "animation_owner": "attachments/attachment_lists/gaia/animals/gaia_herdable_cattle_mal",
    },
    # Non-humanoid: No than / Reinforced No than (official springald rig/model)
    {
        "key": "no_than",
        "family": "no_than",
        "age": 3,
        "kind": "nonhumanoid",
        "logical_path": "art/civilizations/english/team_weapons/eng_springald/eng_springald.rgm",
        "animation_owner": "attachments/attachment_lists/races/english/weapons/tier3_scorpion_eng",
    },
    # Humanoid: Lam Son Skirmishers Ages II-IV
    {
        "key": "skirmisher2",
        "family": "skirmisher",
        "age": 2,
        "kind": "humanoid",
        "logical_path": "art/civilizations/malian/humans/mal_ranged_crossbow_age02/mal_ranged_crossbow_age02.rgm",
        "animation_owner": "attachments/attachment_lists/races/malians/units/tier2_javelin_mal",
    },
    {
        "key": "skirmisher3",
        "family": "skirmisher",
        "age": 3,
        "kind": "humanoid",
        "logical_path": "art/civilizations/malian/humans/mal_ranged_crossbow_age03/mal_ranged_crossbow_age03.rgm",
        "animation_owner": "attachments/attachment_lists/races/malians/units/tier3_javelin_mal",
    },
    {
        "key": "skirmisher4",
        "family": "skirmisher",
        "age": 4,
        "kind": "humanoid",
        "logical_path": "art/civilizations/malian/humans/mal_ranged_crossbow_age04/mal_ranged_crossbow_age04.rgm",
        "animation_owner": "attachments/attachment_lists/races/malians/units/tier4_javelin_mal",
    },
    # Humanoid: Ranged Rattan donors (Archers II-IV, Crossbows III-IV, Handcannoneer IV)
    {
        "key": "archer2",
        "family": "ranged",
        "age": 2,
        "kind": "humanoid",
        "logical_path": "art/civilizations/chinese/humans/chi_ranged_bow_age02/chi_ranged_bow_age02.rgm",
        "animation_owner": "attachments/attachment_lists/races/chinese/units/tier2_archer_chi",
    },
    {
        "key": "archer3",
        "family": "ranged",
        "age": 3,
        "kind": "humanoid",
        "logical_path": "art/civilizations/chinese/humans/chi_ranged_bow_age03/chi_ranged_bow_age03.rgm",
        "animation_owner": "attachments/attachment_lists/races/chinese/units/tier3_archer_chi",
    },
    {
        "key": "archer4",
        "family": "ranged",
        "age": 4,
        "kind": "humanoid",
        "logical_path": "art/civilizations/chinese/humans/chi_ranged_bow_age04/chi_ranged_bow_age04.rgm",
        "animation_owner": "attachments/attachment_lists/races/chinese/units/tier4_archer_chi",
    },
    {
        "key": "crossbow3",
        "family": "ranged",
        "age": 3,
        "kind": "humanoid",
        "logical_path": "art/civilizations/chinese/humans/chi_ranged_crossbow_age03/chi_ranged_crossbow_age03.rgm",
        "animation_owner": "attachments/attachment_lists/races/chinese/units/tier3_crossbow_chi",
    },
    {
        "key": "crossbow4",
        "family": "ranged",
        "age": 4,
        "kind": "humanoid",
        "logical_path": "art/civilizations/chinese/humans/chi_ranged_crossbow_age04/chi_ranged_crossbow_age04.rgm",
        "animation_owner": "attachments/attachment_lists/races/chinese/units/tier4_crossbow_chi",
    },
    {
        "key": "handcannon4",
        "family": "ranged",
        "age": 4,
        "kind": "humanoid",
        "logical_path": "art/civilizations/chinese/humans/chi_ranged_cannoneer_age04/chi_ranged_cannoneer_age04.rgm",
        "animation_owner": "attachments/attachment_lists/races/chinese/units/tier4_handcannon_chi",
    },
]


def box(groups: list[dict]) -> dict:
    points = [pt for g in groups for pt in g["positions"]]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return {
        "minimum": lo,
        "maximum": hi,
        "dimensions": [hi[i] - lo[i] for i in range(3)],
        "vertices": len(points),
    }


def main() -> None:
    guard()
    if not INDEX.is_file() or not CONFIG.is_file():
        raise FileNotFoundError("Garrison asset index/config missing")
    donor_root = owned(STAGING / "donors")
    donor_root.mkdir(parents=True, exist_ok=True)
    records = []
    for item in DONORS:
        key = item["key"]
        dest = owned(donor_root / key)
        manifests = list(dest.rglob("decoded-static.json")) if dest.exists() else []
        if len(manifests) != 1:
            cmd = [
                str(CORE),
                "convert",
                "decode-static",
                "--logical-path",
                item["logical_path"],
                "--config",
                str(CONFIG),
                "--index",
                str(INDEX),
                "--output-root",
                str(dest),
            ]
            if item["animation_owner"]:
                cmd.extend(["--animation-owner", item["animation_owner"]])
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            manifests = list(dest.rglob("decoded-static.json"))
            if proc.returncode != 0 or len(manifests) != 1:
                raise RuntimeError(f"Decode failed for {key} (exit {proc.returncode}): {proc.stderr[-600:]}")
        manifest = manifests[0]
        data = read(manifest)
        geom_path = Path(data["geometry"]["source"]["path"])
        assert sha(geom_path) == data["geometry"]["source"]["sha256"], f"Geometry hash mismatch for {key}"
        groups = data["geometry"]["groups"]
        skeleton = data.get("skeleton")
        records.append({
            **item,
            "manifest": str(manifest),
            "manifest_sha256": sha(manifest),
            "geometry": str(geom_path),
            "geometry_sha256": sha(geom_path),
            "resources": {
                rk: {
                    field: rv.get(field)
                    for field in ("logical_path", "archive", "archive_path", "sha256", "cache_path")
                }
                for rk, rv in data["resources"].items()
                if rk in ("model", "geometry", "material", "object") and isinstance(rv, dict)
            },
            "group_count": len(groups),
            "triangle_count_all_fragments": sum(g["triangle_count"] for g in groups),
            "bounds_all_fragments": box(groups),
            "groups": [
                {
                    "name": g["name"],
                    "material": g["material"],
                    "preview_material": g.get("preview_material"),
                    "effect": g.get("effect"),
                    "vertices": len(g["positions"]),
                    "triangles": g["triangle_count"],
                    "bounds": box([g]),
                }
                for g in groups
            ],
            "skeleton_bones": len(skeleton.get("bones", [])) if skeleton else 0,
            "palette_bones": [len(p.get("bones", [])) for p in skeleton.get("skin_palettes", [])] if skeleton else [],
            "has_collection_contract": data.get("structure_collection_contract") is not None,
        })
    recipe_doc = {
        "schema": "ccp.release080.donors/v1",
        "status": "decoded_source_inventory",
        "index": str(INDEX),
        "index_sha256": sha(INDEX),
        "config": str(CONFIG),
        "config_sha256": sha(CONFIG),
        "models": records,
    }
    write(RECIPES / "donors.json", recipe_doc)
    write(OUT / "donors-summary.json", {
        "count": len(records),
        "recipe": str(RECIPES / "donors.json"),
        "recipe_sha256": sha(RECIPES / "donors.json"),
        "models": [
            {
                "key": r["key"],
                "kind": r["kind"],
                "logical_path": r["logical_path"],
                "groups": r["group_count"],
                "triangles": r["triangle_count_all_fragments"],
                "skeleton_bones": r["skeleton_bones"],
                "palette_bones": r["palette_bones"],
                "dimensions": [round(x, 3) for x in r["bounds_all_fragments"]["dimensions"]],
            }
            for r in records
        ],
    })
    print(json.dumps(read(OUT / "donors-summary.json"), indent=2))


if __name__ == "__main__":
    main()
