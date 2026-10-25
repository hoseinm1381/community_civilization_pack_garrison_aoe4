"""Admit exact weighted geometry while exposing an unskinned socket rest delta."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from assemble_archer_geometry_pairing import _scalar_delta
from common import OUT, guard, owned, read, sha, write


def main(gender: str):
    guard()
    base = OUT / f"qualification/villager-geometry-route/20261018-resume/{gender}/manual"
    old_file, report_file = base / "stock-geometry-comparison-v2.json", base / "deform-geometry-qualification.json"
    owned(report_file)
    if report_file.exists(): raise FileExistsError("Preserve earlier villager qualification")
    old = read(old_file)
    stock = read(Path(old["stock_manifest"]))
    cooked = read(Path(old["compiled_manifest"]))
    if sha(Path(old["stock_manifest"])) != old["stock_manifest_sha256"] or sha(Path(old["compiled_manifest"])) != old["compiled_manifest_sha256"]:
        raise RuntimeError("Native manifest drift")
    sa, sb = stock["skeleton"], cooked["skeleton"]
    palette = {b["name"] for b in sa["skin_palettes"][0]["bones"]}
    child_counts = {b["name"]: 0 for b in sa["bones"]}
    for b in sa["bones"]:
        if b["parent_name"] in child_counts: child_counts[b["parent_name"]] += 1
    local = sorted(({"bone": a["name"], "delta": _scalar_delta(a["local_reference_transform"], b["local_reference_transform"]),
                     "skin_palette_member": a["name"] in palette, "child_count": child_counts[a["name"]]}
                    for a, b in zip(sa["bones"], sb["bones"])), key=lambda x: x["delta"], reverse=True)
    rig = old["rig_compatibility"]
    all_lods = old["three_lods"]
    exact_geometry = (len(all_lods) == 3 and all(x["passed"] and x["stock_and_compiled_skin_palette_lod_record_exact"]
                     and x["stock_and_compiled_vertex_stride_exact"] and x["stock_and_compiled_index_stride_exact"]
                     and x["maximum_uv_scalar_delta"] == 0.0 for x in all_lods))
    critical = (rig["skeleton_identity_exact"] and rig["palette_identity_exact"]
                and rig["lod_palette_records_exact"] and rig["max_palette_global_scalar_delta"] <= 0.0002
                and rig["max_inverse_bind_scalar_delta"] <= 0.0002)
    exception = [x for x in local if x["delta"] > 0.0002]
    isolated = (len(exception) == 1 and exception[0]["bone"] == "metarig_pelvissocket"
                and not exception[0]["skin_palette_member"] and exception[0]["child_count"] == 0
                and exception[0]["delta"] <= 0.002)
    passed = old["status"] == "three_lod_comparison_failed" and exact_geometry and critical and isolated
    report = {"schema": "ccp-060-villager-deforming-geometry-qualification/v1",
              "status": "deforming_geometry_qualified_socket_delta_disclosed" if passed else "deforming_geometry_not_qualified",
              "gender": gender, "strict_all_bone_rest_match": False,
              "source_comparison": str(old_file), "source_comparison_sha256": sha(old_file),
              "exact_three_lod_topology_weights_uv_normals": exact_geometry,
              "ordered_73_skeleton_46_skin_palette_and_lod_identity": critical,
              "palette_global_reference_max_delta": rig["max_palette_global_scalar_delta"],
              "palette_inverse_bind_max_delta": rig["max_inverse_bind_scalar_delta"],
              "socket_exception_is_leaf_and_unskinned": isolated,
              "bones_over_strict_0_0002_scalar_tolerance": exception,
              "maximum_other_local_scalar_delta": max(x["delta"] for x in local if x["bone"] != "metarig_pelvissocket"),
              "native_match_animation_and_equipment_visuals_not_tested": True,
              "diagnostic_material_and_generated_english_actor_not_for_integration": True}
    write(report_file, report)
    return {"status": report["status"], "gender": gender, "socket_delta": exception[0]["delta"] if exception else None,
            "report": str(report_file)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gender", choices=("male", "female"))
    print(json.dumps(main(ap.parse_args().gender), indent=2))
