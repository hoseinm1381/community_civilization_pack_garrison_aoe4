"""Freeze task-owned barracks/TC donor, export and editable source hashes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/release_020/barracks_tc"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def box(groups):
    pts = [p for g in groups for p in g["positions"]]
    return {"minimum": [min(p[i] for p in pts) for i in range(3)],
            "maximum": [max(p[i] for p in pts) for i in range(3)]}


models = []
for family in ("barracks", "town_center"):
    for age in range(1, 5):
        stem = f"vn_{'barracks' if family == 'barracks' else 'towncenter'}_age{age:02}"
        author = ROOT / f"art/authoring/buildings_020/{family}"
        donor = next((ROOT / f"art/stock_cache/buildings_020/barracks_tc/{family}/age{age:02}").rglob("decoded-static.json"))
        d = json.loads(donor.read_text())
        projection = author / f"{stem}-projection.json"
        p = json.loads(projection.read_text())
        native = ROOT / f"art/exports/buildings_020/{family}/{stem}.rrgeom"
        orig = Path(d["geometry"]["source"]["path"])
        assert sha(orig) == d["geometry"]["source"]["sha256"]
        assert native.stat().st_size == orig.stat().st_size and sha(native) != sha(orig)
        assert len(d["geometry"]["groups"]) == len(p["geometry"]["groups"])
        seen = {}
        repeated = 0
        grounded = 0
        for oldg, newg in zip(d["geometry"]["groups"], p["geometry"]["groups"]):
            assert len(oldg["positions"]) == len(newg["positions"])
            for before, after in zip(oldg["positions"], newg["positions"]):
                if before[2] <= 0:
                    assert before == after, (family, age, "ground contract")
                    grounded += 1
                key = tuple(before)
                if key in seen:
                    repeated += 1
                    assert seen[key] == after
                seen[key] = after
        editable = author / f"Vietnam_{family}_Age{age:02}.blend"
        donor_blend = author / f"Chinese_{family}_age{age:02}_donor.blend"
        models.append({
            "family": family, "age": age, "name": stem,
            "logical_stock_model": d["request"]["logical_path"].removesuffix(".rgo"),
            "donor_manifest": str(donor), "donor_manifest_sha256": sha(donor),
            "donor_geometry": str(orig), "donor_geometry_sha256": sha(orig),
            "donor_model_sha256": d["resources"]["model"]["sha256"],
            "donor_material_sha256": d["resources"]["material"]["sha256"],
            "native_geometry": str(native), "native_geometry_sha256": sha(native),
            "native_geometry_bytes": native.stat().st_size,
            "projection": str(projection), "projection_sha256": sha(projection),
            "donor_blend": str(donor_blend), "donor_blend_sha256": sha(donor_blend),
            "editable_blend": str(editable), "editable_blend_sha256": sha(editable),
            "groups": len(p["geometry"]["groups"]),
            "vertices": sum(len(g["positions"]) for g in p["geometry"]["groups"]),
            "repeated_contact_coordinates": repeated,
            "max_repeated_contact_gap_m": 0,
            "ground_or_buried_vertices_unchanged": grounded,
            "donor_bounds": box(d["geometry"]["groups"]),
            "remodel_bounds": box(p["geometry"]["groups"]),
            "native_binding": f"art/scenario/cc020/{family}_age{age:02}/model",
            "source_contract": "Native donor index, UV, collection, material and owner-mask inputs retained; every GEOB position/normal/tangent stream transformed by one continuous map",
        })

report = {"schema": "ccp.barracks-tc-source-handoff/v1", "status": "source_export_ready_for_integration", "models": models,
          "garrison_project": str(OUT / "library/Mods/community_civilization_pack"),
          "proof_scope": "Offline decoded donor/source native geometry and packed Blender source; no native cook, import or match proof",
          "integration_gate": "Copy native donor RGM/RGO/material/collection contract; substitute only verified geometry and private stamp model references; fresh native cook/readback and culling review"}
dest = OUT / "source-handoff.json"
dest.write_text(json.dumps(report, indent=2), encoding="utf8")
print(f"SOURCE_HANDOFF_READY models={len(models)} path={dest}")
