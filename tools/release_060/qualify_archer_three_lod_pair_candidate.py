"""PREPARED, NOT RUN: admit a UV-corrected, native-cooked geometry-only pair candidate.

This records evidence for selective stock-material pairing; it does not perform
that pairing or assert native Chinese animator/runtime compatibility.
"""
from __future__ import annotations

import json
from pathlib import Path

from common import OUT, guard, owned, read, sha, write

STATIC = OUT / "qualification/archer-pairing-prep/static-contract.json"
PAIR = OUT / "qualification/archer-geometry-pair-contract.json"
EXPORT = OUT / "qualification/archer-pairing-prep/uvfix-export.json"
PREPARE = OUT / "qualification/archer-pairing-prep/manual-uvfix/prepare.json"
COOK = OUT / "qualification/archer-pairing-prep/manual-uvfix/cook.json"
READBACK = OUT / "qualification/archer-pairing-prep/manual-uvfix/readback.json"
DECODE = OUT / "qualification/archer-pairing-prep/manual-uvfix/decode.json"
COMPARE = OUT / "qualification/archer-pairing-prep/manual-uvfix/three-lod-comparison.json"
DEST = OUT / "qualification/archer-pairing-prep/manual-uvfix/candidate.json"


def main() -> None:
    guard()
    owned(DEST)
    if DEST.exists():
        raise FileExistsError("Preserve prior pair-candidate admission")
    static, pair, exported, prepared, cooked, readback, decoded, compared = (
        read(path) for path in (STATIC, PAIR, EXPORT, PREPARE, COOK, READBACK, DECODE, COMPARE))
    if (static["status"] != "stock_variant_contract_pinned_new_geometry_unproved"
            or pair["status"] != "source_and_private_selector_contract_pinned_three_lod_export_unrun"
            or exported["schema"] != "ccp-060-archer-paired-stock-lod-uvfix-export/v1"
            or exported["prototype"] != "english-spearman-2"
            or prepared["status"] != "manual_neutral_material_geometry_source_prepared_not_cooked"
            or prepared["source_export_receipt_sha256"] != sha(EXPORT)
            or cooked["status"] != "native_cook_completed_pending_readback"
            or cooked["prepare_receipt_sha256"] != sha(PREPARE)
            or not cooked["source_bytes_preserved"]
            or readback["status"] != "native_archive_verified_four_model_resources_extracted_pending_decode"
            or readback["cook_receipt_sha256"] != sha(COOK)
            or decoded["status"] != "decoded"
            or decoded["readback_receipt_sha256"] != sha(READBACK)
            or compared["status"] != "three_native_lods_topology_weights_uv_bind_qualified"
            or compared["decode_receipt_sha256"] != sha(DECODE)
            or compared["compiled_rrgeom_sha256"] != readback["extracted"][".rrgeom"]["sha256"]
            or not all(row["passed"] for row in compared["three_lods"])):
        raise RuntimeError("Export/native/full-LOD candidate proof incomplete")
    source_folder = Path(exported["folder"])
    owned(source_folder)
    for name, item in exported["files"].items():
        path = source_folder / name
        if not path.is_file() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise RuntimeError(f"UV-corrected source drift: {path}")
    if sha(Path(prepared["source_body"]) / "model.fbx") != exported["files"]["model.fbx"]["sha256"]:
        raise RuntimeError("Native manual FBX differs from source export")
    archive = Path(readback["archive"])
    geom = Path(readback["extracted"][".rrgeom"]["path"])
    manifest = Path(decoded["manifest_path"])
    for path in (archive, geom, manifest):
        owned(path)
    if (sha(archive) != readback["archive_sha256"]
            or sha(geom) != readback["extracted"][".rrgeom"]["sha256"]
            or sha(manifest) != decoded["manifest_sha256"]
            or compared["compiled_manifest_sha256"] != sha(manifest)):
        raise RuntimeError("Cooked archive/geometry/decode hashes changed")
    source_triangles = [row["triangles"] for row in exported["source_lods"]]
    compiled_triangles = [row["compiled_triangles"] for row in compared["three_lods"]]
    if source_triangles != compiled_triangles or source_triangles != [1236, 522, 155]:
        raise RuntimeError("Unchanged donor triangle LOD control differs")
    candidate = {
        "schema": "ccp-060-archer-paired-geometry-candidate/v2",
        "status": "native_cook_readback_compared",
        "source_route": "essence_manual_geometry_only",
        "claims_build_unit_admission": False,
        "prototype": "english-spearman-2",
        "genuine_matched_prototype_rig": True,
        "generated_spearman_actor_rgo_rhka_prohibited_from_integration": True,
        "diagnostic_cooked_material_excluded_from_pair": True,
        "unchanged_donor_geometry_control": True,
        "static_contract_sha256": sha(STATIC), "pair_contract_sha256": sha(PAIR),
        "source_export_receipt": str(EXPORT), "source_export_receipt_sha256": sha(EXPORT),
        "manual_prepare_receipt": str(PREPARE), "manual_prepare_receipt_sha256": sha(PREPARE),
        "native_cook_receipt": str(COOK), "native_cook_receipt_sha256": sha(COOK),
        "native_readback_receipt": str(READBACK), "native_readback_receipt_sha256": sha(READBACK),
        "decoded_comparison": str(COMPARE), "decoded_comparison_sha256": sha(COMPARE),
        "source_lod_triangle_counts": source_triangles,
        "native_cook_archive": str(archive), "native_cook_archive_sha256": sha(archive),
        "native_cook_rrgeom_member": readback["extracted"][".rrgeom"]["member"],
        "compiled_body_rrgeom": str(geom), "compiled_body_rrgeom_sha256": sha(geom),
        "decoded_body_manifest": str(manifest), "decoded_body_manifest_sha256": sha(manifest),
        "stock_rrmaterial_and_private_rgm_rgo_not_replaced": True,
        "original_chinese_animator_consumer_not_proven": True,
        "next_gate": "Only test-assemble one eight-member private archive replacing RRGeom; verify unchanged RGM/RGO/RRMaterial and native consumer separately."
    }
    write(DEST, candidate)
    print(json.dumps({"status": candidate["status"], "candidate": str(DEST),
                      "compiled_rrgeom_sha256": sha(geom)}, indent=2))


if __name__ == "__main__":
    main()
