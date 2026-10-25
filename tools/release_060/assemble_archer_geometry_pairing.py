"""PREPARED, NOT RUN: make one test-only 8-member stock-material/new-geometry SGA.

Requires a separate native-cooked/read-back three-real-LOD geometry candidate.
It keeps private stock RGM/RGO/RRMaterial byte-identical, and never edits the
generated actor/RGO/RHKA or gameplay. A candidate's diagnostic material is unused.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import ARCH, OUT, STAGING, guard, owned, read, sha, write

STATIC = OUT / "qualification/archer-pairing-prep/static-contract.json"
PAIR = OUT / "qualification/archer-geometry-pair-contract.json"
VARIANT = OUT / "qualification/archer-variant-readback.json"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
DEST = OUT / "qualification/archer-pairing-prep/assembled-test"
ARCHIVE = STAGING / "q/v60av_archer_geometry_pair_test.sga"
RECEIPT = DEST / "assembly.json"
BASE = "art/scenario/garrison/v60av/v60av_stock/v60av_stock"
TARGET = BASE + ".rrgeom"


def archiver(*args: object, timeout: int = 120) -> dict:
    proc = subprocess.run([str(ARCH), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"Archiver {args[0]} failed exit {proc.returncode}: {proc.stderr[-1200:]}")
    return json.loads(proc.stdout)


def _scalar_delta(left: object, right: object) -> float:
    if isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys():
        return max((_scalar_delta(left[key], right[key]) for key in left), default=0.0)
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return max((_scalar_delta(a, b) for a, b in zip(left, right)), default=0.0)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right))
    raise ValueError("Bind transform shape or scalar type changed")


def rig_compatibility(candidate: dict, stock: dict) -> dict:
    sa, sb = candidate["skeleton"], stock["skeleton"]
    pa, pb = sa["skin_palettes"], sb["skin_palettes"]
    bone_keys = ("index", "name", "parent_index", "parent_name")
    palette_keys = ("palette_index", "name", "parent_index", "parent_name", "skeleton_index")
    identity = (len(sa["bones"]) == len(sb["bones"]) == 48
                and all(tuple(a[key] for key in bone_keys) == tuple(b[key] for key in bone_keys)
                        for a, b in zip(sa["bones"], sb["bones"]))
                and len(pa) == len(pb) == 1
                and len(pa[0]["bones"]) == len(pb[0]["bones"]) == 46
                and all(tuple(a[key] for key in palette_keys) == tuple(b[key] for key in palette_keys)
                        for a, b in zip(pa[0]["bones"], pb[0]["bones"])))
    if not identity:
        raise RuntimeError("Ordered skeleton or skin palette identities differ")
    local_delta = max(_scalar_delta(a["local_reference_transform"], b["local_reference_transform"])
                      for a, b in zip(sa["bones"], sb["bones"]))
    global_delta = max(_scalar_delta(a["global_reference_transform"], b["global_reference_transform"])
                       for a, b in zip(sa["bones"], sb["bones"]))
    palette_global_delta = max(_scalar_delta(a["global_reference_transform"], b["global_reference_transform"])
                               for a, b in zip(pa[0]["bones"], pb[0]["bones"]))
    inverse_delta = max(_scalar_delta(a["inverse_bind_transform"], b["inverse_bind_transform"])
                        for a, b in zip(pa[0]["bones"], pb[0]["bones"]))
    lod_a, lod_b = pa[0]["lod_palettes"], pb[0]["lod_palettes"]
    lod_maps_exact = (len(lod_a) == len(lod_b) == 3 and
                      all(a == b for a, b in zip(lod_a, lod_b)))
    result = {
        "ordered_skeleton_and_palette_identity_exact": True,
        "lod_palette_records_exact": lod_maps_exact,
        "max_local_reference_scalar_delta": local_delta,
        "max_global_reference_scalar_delta": global_delta,
        "max_palette_global_scalar_delta": palette_global_delta,
        "max_inverse_bind_scalar_delta": inverse_delta,
        "numeric_tolerance": 0.0002,
    }
    if not lod_maps_exact or max(local_delta, global_delta, palette_global_delta, inverse_delta) > 0.0002:
        raise RuntimeError(f"Compiled bind/LOD skin records diverged: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-receipt", type=Path, required=True,
                        help="Future native-cooked geometry candidate receipt, schema ccp-060-archer-paired-geometry-candidate/v2")
    args = parser.parse_args()
    guard()
    owned(args.candidate_receipt)
    for path in (DEST, ARCHIVE):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier assembly attempt: {path}")
    static, pair, variant, stock = read(STATIC), read(PAIR), read(VARIANT), read(STOCK)
    candidate = read(args.candidate_receipt)
    if (static["status"] != "stock_variant_contract_pinned_new_geometry_unproved"
            or sha(STATIC) != candidate.get("static_contract_sha256")
            or pair["status"] != "source_and_private_selector_contract_pinned_three_lod_export_unrun"
            or sha(PAIR) != candidate.get("pair_contract_sha256")
            or variant["archive_sha256"] != sha(variant["archive"])
            or candidate.get("schema") != "ccp-060-archer-paired-geometry-candidate/v2"
            or candidate.get("status") != "native_cook_readback_compared"
            or candidate.get("source_route") not in {"garrison_unit_add", "essence_manual_geometry_only"}
            or candidate.get("prototype") != "english-spearman-2"
            or not candidate.get("genuine_matched_prototype_rig")
            or not candidate.get("generated_spearman_actor_rgo_rhka_prohibited_from_integration")
            or not candidate.get("diagnostic_cooked_material_excluded_from_pair")
            or not candidate.get("stock_rrmaterial_and_private_rgm_rgo_not_replaced")):
        raise RuntimeError("Candidate/prototype/static contract is not qualified")
    if candidate["source_route"] == "garrison_unit_add" and not candidate.get("installed_unit_validate_passed"):
        raise RuntimeError("Garrison unit-add route lacks an installed unit-validator pass")
    if candidate["source_route"] == "essence_manual_geometry_only" and candidate.get("claims_build_unit_admission"):
        raise RuntimeError("Manual Essence source may not claim Build Unit admission")
    new_geom = Path(candidate["compiled_body_rrgeom"])
    decoded_path = Path(candidate["decoded_body_manifest"])
    cook_archive = Path(candidate["native_cook_archive"])
    for path in (new_geom, decoded_path, cook_archive):
        owned(path)
    if (sha(new_geom) != candidate["compiled_body_rrgeom_sha256"]
            or sha(decoded_path) != candidate["decoded_body_manifest_sha256"]
            or sha(cook_archive) != candidate["native_cook_archive_sha256"]):
        raise RuntimeError("Candidate native cook/readback input changed")
    comparison_path = owned(Path(candidate["decoded_comparison"]))
    if sha(comparison_path) != candidate["decoded_comparison_sha256"]:
        raise RuntimeError("Full three-LOD UV/topology/weight comparison receipt changed")
    comparison = read(comparison_path)
    if (comparison["status"] != "three_native_lods_topology_weights_uv_bind_qualified"
            or comparison["compiled_manifest_sha256"] != sha(decoded_path)
            or comparison["compiled_rrgeom_sha256"] != sha(new_geom)
            or len(comparison["three_lods"]) != 3
            or not all(lod["passed"] and lod["maximum_uv_scalar_delta"] <= lod["uv_tolerance"]
                       and lod["normal_corner_identity_keys_and_counts_exact"]
                       and lod["maximum_normal_vector_delta"] <= lod["normal_vector_tolerance"]
                       and lod["triangle_topology_multiset_exact"]
                       and lod["weighted_corner_multiset_exact_after_influence_order_normalization"]
                       for lod in comparison["three_lods"])):
        raise RuntimeError("Full native direct-UV, topology, or byte-weight comparison did not pass")
    decoded = read(decoded_path)
    if decoded.get("status") != "decoded":
        raise RuntimeError("Compiled candidate decode did not complete")
    rig_check = rig_compatibility(decoded, stock)
    expected = [(x["geometry_group"]["name"], x["geometry_group"]["material"],
                 x["geometry_group"]["effect"]) for x in static["required_geometry_and_palette_lods"]]
    actual = [(x["name"], x["material"], x["effect"]) for x in decoded["geometry"]["groups"]]
    if actual != expected or len(actual) != 3:
        raise RuntimeError(f"Compiled geometry group/material/effect identity mismatch: {actual} != {expected}")
    for number, group in enumerate(decoded["geometry"]["groups"], 1):
        stock_group = stock["geometry"]["groups"][number - 1]
        skin = group["skin_projection"]
        if (group["vertex_stride"] != stock_group["vertex_stride"]
                or group["index_stride"] != stock_group["index_stride"]
                or group["collection_bone_index_count"] != 0
                or set(group["uv_layers"]) != {"UVMap"}
                or len(group["uv_layers"]["UVMap"]) != group["vertex_count"]
                or len(group["skin_indices"]) != group["vertex_count"]
                or len(group["skin_weights"]) != group["vertex_count"]
                or skin["status"] != "palette_indices_and_weights_decoded"
                or skin["index_encoding"] != "uint8x4"
                or skin["weight_encoding"] != "unorm8x4"
                or skin["weight_byte_sum"] != 255
                or skin["maximum_influences"] > 4
                or skin["maximum_palette_index"] >= static["required_geometry_and_palette_lods"][number - 1]["skin_index_count"]):
            raise RuntimeError(f"Compiled LOD{number} vertex/UV/skinning format cannot pair with stock selector/material")
    actual_triangles = [x["triangle_count"] for x in decoded["geometry"]["groups"]]
    source_triangles = candidate.get("source_lod_triangle_counts")
    if (source_triangles != actual_triangles or len(actual_triangles) != 3
            or not actual_triangles[0] > actual_triangles[1] > actual_triangles[2] > 0):
        raise RuntimeError(f"Compiled LOD triangle counts are cloned or differ from source: {actual_triangles} vs {source_triangles}")
    if candidate.get("unchanged_donor_geometry_control") and actual_triangles != [1236, 522, 155]:
        raise RuntimeError("Unchanged donor geometry control LOD triangle counts differ")
    if sha(decoded["geometry"]["source"]["path"]) != sha(new_geom):
        raise RuntimeError("Decoded candidate geometry source is not the read-back RRGeom")
    cooked_member = candidate.get("native_cook_rrgeom_member", "")
    if not cooked_member.endswith(".rrgeom") or ".." in Path(cooked_member).parts:
        raise RuntimeError("Candidate lacks an exact native-cooked RRGeom member path")
    cooked_list = archiver("list", "--verify", cook_archive)
    if (not cooked_list["archive"]["verification"]["verified"]
            or cooked_member not in {item["path"] for item in cooked_list["members"]}):
        raise RuntimeError("Candidate RRGeom is not a verified native-cook archive member")
    cooked_extract = owned(DEST / "candidate" / "cooked-member.rrgeom")
    cooked_extract.parent.mkdir(parents=True, exist_ok=True)
    archiver("extract-member", cook_archive, cooked_member, cooked_extract)
    if sha(cooked_extract) != sha(new_geom):
        raise RuntimeError("Candidate read-back RRGeom differs from verified native-cook member")
    base_archive = Path(variant["archive"])
    if ({suffix: variant["extracted"][suffix]["sha256"] for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
            != pair["private_variant_resource_sha256"]):
        raise RuntimeError("Pinned private selector/material resource hashes changed")
    base_list = archiver("list", "--verify", base_archive)
    if ({x["path"] for x in base_list["members"]} != set(variant["exact_resource_allowlist"])
            or not base_list["archive"]["verification"]["verified"]
            or len(base_list["members"]) != 8):
        raise RuntimeError("Original private stock variant allowlist or verification drift")
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    archiver("replace-member", base_archive, new_geom, ARCHIVE, TARGET)
    modified = archiver("list", "--verify", ARCHIVE)
    if ({x["path"] for x in modified["members"]} != set(variant["exact_resource_allowlist"])
            or not modified["archive"]["verification"]["verified"]
            or len(modified["members"]) != 8):
        raise RuntimeError("Assembled test archive member allowlist/CRC/SHA verification failed")
    DEST.mkdir(parents=True)
    checks = {}
    for member in sorted(variant["exact_resource_allowlist"]):
        before, after = owned(DEST / "base" / Path(member).name), owned(DEST / "assembled" / Path(member).name)
        before.parent.mkdir(parents=True, exist_ok=True)
        after.parent.mkdir(parents=True, exist_ok=True)
        archiver("extract-member", base_archive, member, before)
        archiver("extract-member", ARCHIVE, member, after)
        correct = (sha(after) == sha(new_geom)) if member == TARGET else (sha(after) == sha(before))
        if not correct:
            raise RuntimeError(f"Assembled archive changed an unexpected resource: {member}")
        checks[member] = {"base_sha256": sha(before), "assembled_sha256": sha(after),
                          "changed": sha(before) != sha(after), "expected": True}
    write(RECEIPT, {
        "schema": "ccp-060-archer-paired-geometry-assembly/v1",
        "status": "test_only_eight_member_archive_verified_not_runtime_tested",
        "candidate_receipt": str(args.candidate_receipt),
        "candidate_receipt_sha256": sha(args.candidate_receipt),
        "source_route": candidate["source_route"],
        "pair_contract": str(PAIR), "pair_contract_sha256": sha(PAIR),
        "base_variant_archive": str(base_archive), "base_variant_archive_sha256": sha(base_archive),
        "assembled_archive": str(ARCHIVE), "assembled_archive_sha256": sha(ARCHIVE),
        "exact_member_allowlist": sorted(variant["exact_resource_allowlist"]),
        "only_changed_resource": TARGET, "member_sha256_comparison": checks,
        "three_group_material_effect_names_exact_stock": True,
        "source_and_compiled_lod_triangle_counts": actual_triangles,
        "compiled_rig_compatibility": rig_check,
        "unchanged_private_rgm_rgo_rrmaterial": True,
        "private_stock_rrmaterial_byte_identical_official": True,
        "diagnostic_cooked_material_excluded": True,
        "generated_spearman_actor_rgo_rhka_never_integrated": True,
        "active_gameplay_not_changed": True,
        "native_original_archer_animator_consumer_compatibility_unproved": True,
        "client_import_and_native_match_unproved": True,
    })
    print(json.dumps({"status": "test_only_eight_member_archive_verified_not_runtime_tested",
                      "archive": str(ARCHIVE), "sha256": sha(ARCHIVE),
                      "receipt": str(RECEIPT)}, indent=2))


if __name__ == "__main__":
    main()
