"""Freeze the twelve source exports for selective native 0.4.0 integration."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/release_040/buildings"
RECIPE = ROOT / "art/recipes/release_040/buildings-source.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    sources = json.loads((OUT / "model-validation.json").read_text())
    audit = json.loads((OUT / "native-byte-audit.json").read_text())
    donors = json.loads((ROOT / "art/recipes/release_040/buildings-donors.json").read_text())
    selectors = json.loads((OUT / "donor-selectors.json").read_text())
    assert sources["status"] == "source_ready_for_integration" and audit["status"] == "passed"
    def keyed(rows):
        return {(r["family"], r["age"]): r for r in rows}
    source_map, donor_map, selector_map = map(keyed, (sources["models"], donors["models"], selectors["models"]))
    keys = {(family, age) for family in ("blacksmith", "stable", "archery_range", "market") for age in (2, 3, 4)}
    assert keys == set(source_map) == set(donor_map) == set(selector_map)
    assert {row["name"] for row in audit["models"]} == {row["name"] for row in sources["models"]}
    rows = []
    for family, age in sorted(keys):
        s, d, sel = source_map[family, age], donor_map[family, age], selector_map[family, age]
        native = Path(s["native_geometry"])
        blend = Path(s["editable_blend"])
        projection = Path(s["projection"])
        assert sha(native) == s["native_geometry_sha256"] and sha(blend) == s["editable_blend_sha256"]
        assert sha(d["manifest"]) == d["manifest_sha256"] and sha(d["geometry"]) == d["geometry_sha256"]
        assert sel["rgm_sha256"] == d["resources"]["model"]["sha256"]
        assert s["stock_model_stem"] == d["logical_path"].removesuffix(".rgm")
        rows.append({
            "family": family, "age": age, "name": s["name"],
            "stock_model_stem": s["stock_model_stem"], "private_model_stem": s["private_model_stem"],
            "donor_manifest": d["manifest"], "donor_manifest_sha256": d["manifest_sha256"],
            "donor_model": d["resources"]["model"], "donor_geometry": d["resources"]["geometry"],
            "donor_material": d["resources"]["material"],
            "selector_sets": len(sel["selector_sets"]), "selector_names": sel["selector_names"],
            "healthy_selector_names": sel["healthy_selector_names"],
            "mscl_source_object_count": sel["mscl_source_object_count"],
            "export_geometry": str(native), "export_geometry_sha256": sha(native),
            "editable_blend": str(blend), "editable_blend_sha256": sha(blend),
            "projection": str(projection), "projection_sha256": sha(projection),
            "donor_blend": s["donor_blend"], "donor_blend_sha256": s["donor_blend_sha256"],
            "native_audit": next(row for row in audit["models"] if row["name"] == s["name"]),
        })
    recipe = {"schema": "ccp.release040.building-source-handoff/v1", "status": "source_export_ready_for_integration",
              "models": rows, "donor_inventory_sha256": sha(ROOT / "art/recipes/release_040/buildings-donors.json"),
              "selector_inventory_sha256": sha(OUT / "donor-selectors.json"),
              "native_byte_audit_sha256": sha(OUT / "native-byte-audit.json"),
              "integration": "Private model stems copy official RGM/RGO/RRMaterial/markers and replace only audited RRGeom; verify exact consumer tier/stamp chain and archive allowlist",
              "proof_scope": "Garrison decoded source, Blender authoring, native RRGeom readback, and offline previews only. No native cook, import, lobby, match, or multiplayer proof."}
    RECIPE.parent.mkdir(parents=True, exist_ok=True)
    RECIPE.write_text(json.dumps(recipe, indent=2), encoding="utf8")
    print("BUILDING_SOURCE_HANDOFF", len(rows), RECIPE)


if __name__ == "__main__":
    run()
