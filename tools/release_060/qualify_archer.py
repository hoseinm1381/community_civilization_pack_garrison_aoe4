"""Record the first Archer II art sample without claiming a native model cook."""
from __future__ import annotations

import json
from pathlib import Path

from common import ART, OUT, ROOT, guard, read, sha, write

QUAL = OUT / "qualification"
DONORS = OUT / "donors"
BLEND = ART / "archer/archer-base-rattan-prototype.blend"
RECIPE = ROOT / "tools/release_060/archer_sample.py"
HISTORY = ROOT / "art/recipes/release_060/historical-reference.json"
NEXT_PASS = ROOT / "art/recipes/release_060/archer-refinement-plan.json"
COOK_ROUTE = QUAL / "archer-cook-route.json"
VIEWS = (
    "archer-stock-donor-front-material.png",
    "archer-base-front-material.png",
    "archer-base-game-distance.png",
    "archer-rattan-front-material.png",
    "archer-rattan-back-material.png",
    "archer-rattan-threequarter-material.png",
    "archer-rattan-game-distance.png",
)


def file_record(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": sha(path)}


def main() -> None:
    guard()
    trace_path = DONORS / "archer-trace.json"
    trace = read(trace_path)
    decoder = next((DONORS / "decoded/archer02").rglob("decoded-static.json"))
    decoded = read(decoder)
    if decoded["status"] != "decoded" or decoded["blockers"]:
        raise RuntimeError("Stock Archer II donor decode is not complete")
    # Decoder groups share a source name; the projection labels them lod1..3.
    body = max(decoded["geometry"]["groups"], key=lambda g: g["vertex_count"])
    report = {
        "schema": "ccp-060-archer-sample-qualification/v1",
        "status": "authoring_prototype_not_release_qualified",
        "stock_donor": {
            "trace": file_record(trace_path),
            "decoded_manifest": file_record(decoder),
            "source_archive_sha256": trace["source_archive_sha256"],
            "logical_body": "art/civilizations/chinese/humans/chi_ranged_bow_age02/chi_ranged_bow_age02.rgm",
            "logical_bow": "art/civilizations/common/weapons/ranged/bow_recurve/bow_recurve.rgm",
            "lod1_vertices": body["vertex_count"],
            "lod1_triangles": body["triangle_count"],
            "skeleton_bones": len(decoded["skeleton"]["bones"]),
            "original_lods": [{"name": g["name"], "vertices": g["vertex_count"],
                               "triangles": g["triangle_count"]}
                              for g in decoded["geometry"]["groups"]],
        },
        "authoring": {
            "blend": file_record(BLEND),
            "deterministic_geometry_recipe": file_record(RECIPE),
            "historical_reference": file_record(HISTORY),
            "refinement_plan": file_record(NEXT_PASS),
            "cook_route_audit": file_record(COOK_ROUTE),
            "base": "Stock LOD1 weighted body copied with native texture nodes and local cloth tint mask; new weighted continuous short tunic, waist tie and headwrap; stock hands/head/skin/quiver retained.",
            "rattan": "Separate optional collection with torso-wrap vest, fine reed bands, left-of-quiver back shield and weighted carrying straps.",
            "rig": "Imported native 48-bone archer armature and original 46 vertex-group weighted LOD1 body; overlay vertices transfer nearest donor weights. Blender viewport and authoring proof only.",
            "bow": "Native bow logical path resolved, but bow grip/orientation not yet imported or posed in sample.",
        },
        "views": {Path(name).stem: file_record(QUAL / name) for name in VIEWS},
        "measurements": {
            "vest_vertical_span_m": [1.14, 1.445],
            "shield_x_span_m": [-0.31, -0.09],
            "shield_z_span_m": [1.16, 1.52],
            "shield_y_face_m": [0.158, 0.173],
            "quiver_clearance_vertex_sample_m": 0.06911,
            "quiver_clearance_method": "221 shield grid vertices versus 176 stock LOD1 vertices in rear disconnected components with max y > 0.2 m and min z > 0.78 m. This is a sampled vertex distance, not a continuous surface collision proof.",
        },
        "gates": {
            "official_attachment_trace": "pass",
            "stock_model_decode": "pass",
            "weighted_blender_import": "pass_authoring_only",
            "base_visual": "prototype_needs_revision",
            "rattan_visual": "prototype_needs_revision",
            "generic_model_export_and_native_cook": "unqualified",
            "private_runtime_binding": "not_started",
            "content_editor_build": "not_started",
            "client_import": "not_started",
            "native_match": "not_started",
        },
        "review_issues": [
            "Base still keeps too much stock Chinese robe/metal shoulder and forearm armor; the short overlay reads as an apron at game distance.",
            "Uniform pale waist tie and headwrap need donor-derived fabric detail, seam variation and an intentional cloth treatment.",
            "Rattan vest silhouette is too boxy across arms; reshape to torso and refine rear strap contact against shield.",
            "Native bow grip, compatible weighted export/cook route, animation and LOD acceptance remain unproved.",
            "Replaying the Blender script through MCP after deleting an earlier sample returned a stale StructRNA bridge error despite creating the final objects; a clean idempotent rerun has not been proven.",
        ],
    }
    write(QUAL / "archer-sample.json", report)
    print(json.dumps({"status": report["status"], "report": str(QUAL / "archer-sample.json"),
                      "views": len(report["views"])}, indent=2))


if __name__ == "__main__":
    main()
