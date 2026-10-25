"""Pin six qualified private ranged media pairs without grafting gameplay.

Each pair keeps the supported stock-variant RGM/RGO and its albedo-only native
RRMaterial/RRTex, and substitutes only a separately qualified authored RRGeom
at the variant's own logical stem. Diagnostic manual material/RGO are excluded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from authored_geometry_060 import rig_contract
from common import CFG, OUT, guard, owned, read, sha, write
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import model_variants

TIERS = ("archer2", "archer3", "archer4", "crossbow3", "crossbow4", "handcannon4")


def variant_rgm_stock_except_path(stock: dict, variant: dict) -> dict:
    donor = Path(stock["resources"]["model"]["cache_path"])
    private = Path(variant["extracted"][".rgm"]["path"])
    if sha(donor) != stock["resources"]["model"]["sha256"] or sha(private) != variant["extracted"][".rgm"]["sha256"]:
        raise RuntimeError("Pinned RGM source/readback changed")
    original = stock["resources"]["model"]["logical_path"].removesuffix(".rgm").replace("/", "\\").encode()
    renamed = variant["extracted"][".rgm"]["member"].removesuffix(".rgm").replace("/", "\\").encode()
    a, b = donor.read_bytes(), private.read_bytes()
    i, j = a.find(original), b.find(renamed)
    if (i < 0 or i != j or a.find(original, i + 1) >= 0 or b.find(renamed, j + 1) >= 0
            or a[i + len(original):] != b[j + len(renamed):]):
        raise RuntimeError("Supported variant RGM differs beyond private path")
    differences = [k for k in range(i) if a[k] != b[k]]
    expected=model_variants.rewrite_model_path(a,original.decode(),renamed.decode())
    if expected!=b:
        raise RuntimeError('Variant RGM differs from exact supported native model-path rewrite')
    return {"stock_rgm_sha256": sha(donor), "private_rgm_sha256": sha(private),
            "only_changed_prefix_offsets": differences,
            "supported_native_path_rewrite_exact": True,
            "tail_after_private_path_exact": True, "renamed_path_offset": i}


def _qualify_pair(slug: str, variant_report: Path, geometry_slug: str) -> dict:
    guard()
    owned(variant_report)
    base = owned(OUT / "authored-geometry" / geometry_slug)
    comparison_path = base / ("comparison-qualified.json" if (base / "comparison-qualified.json").exists()
                              else "comparison.json")
    spec, geometry, readback = read(base / "spec.json"), read(comparison_path), read(base / "readback.json")
    material = read(variant_report)
    stock_path = Path(spec["stock_manifest"])
    stock = read(stock_path)
    if (geometry["status"] != "authored_three_lod_geometry_qualified"
            or material["status"] != "albedo_only_all_other_material_chunks_exact"
            or geometry["stock_manifest_sha256"] != sha(stock_path)
            or material["donor_manifest_sha256"] != sha(stock_path)
            or not material["stock_geometry_byte_identical"]
            or not material["normal_metal_owner_pattern_skin_lut_and_other_params_exact"]
            or len(material["changes"]) != 3):
        raise RuntimeError(f"{slug}: geometry/material qualification incomplete")
    model = read(Path(readback["decoded_manifest"]))
    rig = rig_contract(model, stock, spec["skeleton_bones"])
    groups = [(g["name"], g["material"], g["effect"]) for g in model["geometry"]["groups"]]
    expected = [(spec["group_name"], f"lod{i}", "unit") for i in (1, 2, 3)]
    if groups != expected or not all(r["passed"] for r in geometry["lods"]):
        raise RuntimeError(f"{slug}: native group/LOD records changed")
    if groups != [(g["name"], g["material"], g["effect"]) for g in stock["geometry"]["groups"]]:
        raise RuntimeError(f"{slug}: stock RGM material group names differ from authored geometry")
    private = material["extracted"]
    if set(private) != {".rgm", ".rgo", ".rrgeom", ".rrmaterial", ".rrtex"}:
        raise RuntimeError(f"{slug}: private variant resource set changed")
    for suffix, item in private.items():
        if sha(item["path"]) != item["sha256"]:
            raise RuntimeError(f"{slug}: private {suffix} readback drift")
    geometry_item = readback["resources"][".rrgeom"]
    if (sha(geometry_item["path"]) != geometry_item["sha256"]
            or geometry_item["sha256"] != geometry["compiled_rrgeom_sha256"]
            or private[".rrgeom"]["sha256"] != stock["geometry"]["source"]["sha256"]):
        raise RuntimeError(f"{slug}: geometry source/target hashes changed")
    stem = private[".rgm"]["member"].removesuffix(".rgm")
    if any(private[suffix]["member"].removesuffix(suffix) != stem
           for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")):
        raise RuntimeError(f"{slug}: private variant resources have different logical stems")
    if not private[".rrtex"]["member"].startswith(stem.rsplit("/", 1)[0] + "/"):
        raise RuntimeError(f"{slug}: private albedo texture is outside model folder")
    if any(change["slot"] != "albedoTexture" or
           change["new_value"].replace("\\", "/") != private[".rrtex"]["member"]
           for change in material["changes"]):
        raise RuntimeError(f"{slug}: three material albedo references changed")
    rgm = variant_rgm_stock_except_path(stock, material)
    return {"slug": slug, "geometry_attempt_slug": geometry_slug or slug,
            "status": "qualified_media_pair_inputs_not_grafted",
            "model_logical_path": stem + ".rgm", "replacement_rrgeom_logical_path": stem + ".rrgeom",
            "stock_manifest": str(stock_path), "stock_manifest_sha256": sha(stock_path),
            "geometry_comparison": str(comparison_path),
            "geometry_comparison_sha256": sha(comparison_path),
            "albedo_material_verification": str(variant_report),
            "albedo_material_verification_sha256": sha(variant_report),
            "native_group_material_effect": groups, "native_lod_triangle_counts":
                [g["triangle_count"] for g in model["geometry"]["groups"]],
            "rig": rig, "variant_rgm_stock_except_path": rgm,
            "private_supported_variant_rgm": private[".rgm"],
            "private_supported_variant_rgo": private[".rgo"],
            "private_albedo_only_rrmaterial": private[".rrmaterial"],
            "private_albedo_rrtex": private[".rrtex"],
            "native_qualified_authored_rrgeom": geometry_item,
            "stock_variant_rrgeom_before_replacement": private[".rrgeom"],
            "only_intended_media_replacement": stem + ".rrgeom",
            "diagnostic_geometry_cook_rgo_rrmaterial_actor_rhka_excluded": True,
            "no_final_archive_or_gameplay_binding_created": True,
            "native_match_animation_and_appearance_unverified": True}


def qualify_geometry_material_pair(geometry_slug: str, variant_report: Path) -> dict:
    """Qualify an explicit humanoid source against its own exact native donor."""
    if not geometry_slug or '/' in geometry_slug or '\\' in geometry_slug or geometry_slug in ('.','..'):
        raise ValueError('Expected one explicit geometry attempt key')
    return _qualify_pair(geometry_slug, variant_report, geometry_slug)


def qualify_pair(slug: str, variant_report: Path, geometry_slug: str | None = None) -> dict:
    if slug not in TIERS: raise ValueError(slug)
    return _qualify_pair(slug, variant_report, geometry_slug or slug)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant-map", type=Path, required=True,
                    help="Owned JSON mapping each of six tier slugs to material-verification.json")
    args = ap.parse_args()
    guard(); owned(args.variant_map)
    mapping = read(args.variant_map)
    if set(mapping) != set(TIERS): raise RuntimeError("Require exactly six ranged tiers")
    target = owned(OUT / "authored-geometry/ranged-media-pairs.json")
    if target.exists(): raise FileExistsError("Preserve prior media pair manifest")
    if any(not isinstance(mapping[slug], dict)
           or set(mapping[slug]) != {"geometry_slug", "material_verification"}
           for slug in TIERS):
        raise RuntimeError("Each tier must select explicit geometry attempt and material report")
    pairs = [qualify_pair(slug, Path(mapping[slug]["material_verification"]),
                          mapping[slug]["geometry_slug"]) for slug in TIERS]
    record = {"schema": "ccp-060-ranged-qualified-media-pairs/v1",
              "status": "six_native_geometry_and_albedo_material_pairs_ready_for_separate_integration",
              "variant_map": str(args.variant_map), "variant_map_sha256": sha(args.variant_map),
              "pairs": pairs, "active_gameplay_and_final_archive_unchanged": True,
              "client_import_and_native_match_unverified": True}
    write(target, record)
    print(json.dumps({"status": record["status"], "manifest": str(target),
                      "models": [p["model_logical_path"] for p in pairs]}, indent=2))


if __name__ == "__main__": main()
