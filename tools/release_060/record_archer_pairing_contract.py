"""Pin the stock-variant selector/bind contract before any new geometry exists."""
from __future__ import annotations

import hashlib
from pathlib import Path

from common import OUT, guard, read, sha, write

DEST = OUT / "qualification/archer-pairing-prep"
RECEIPT = DEST / "static-contract.json"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
VARIANT = OUT / "qualification/archer-variant-readback.json"
OLD_PATH = b"art\\civilizations\\chinese\\humans\\chi_ranged_bow_age02\\chi_ranged_bow_age02"
NEW_PATH = b"art\\scenario\\garrison\\v60av\\v60av_stock\\v60av_stock"


def main() -> None:
    guard()
    if RECEIPT.exists():
        raise FileExistsError(RECEIPT)
    stock, variant = read(STOCK), read(VARIANT)
    old = Path(variant["extracted"][".rgm"]["donor_path"])
    new = Path(variant["extracted"][".rgm"]["path"])
    a, b = old.read_bytes(), new.read_bytes()
    i, j = a.find(OLD_PATH), b.find(NEW_PATH)
    if i != j or i < 0 or a.find(OLD_PATH, i+1) >= 0 or b.find(NEW_PATH, j+1) >= 0:
        raise RuntimeError("Variant RGM path rename is not unique/position-preserving")
    prefix_diffs = [k for k in range(i) if a[k] != b[k]]
    expected_offsets = [36, i-12, i-4]
    if (prefix_diffs != expected_offsets
            or a[i+len(OLD_PATH):] != b[j+len(NEW_PATH):]
            or sha(old) != variant["extracted"][".rgm"]["donor_sha256"]
            or sha(new) != variant["extracted"][".rgm"]["sha256"]):
        raise RuntimeError("Private variant RGM differs beyond path/length fields")
    stock_groups = [{"name": x["name"], "material": x["material"], "effect": x["effect"],
                     "vertices": x["vertex_count"], "triangles": x["triangle_count"]}
                    for x in stock["geometry"]["groups"]]
    palettes = stock["skeleton"]["skin_palettes"]
    if len(palettes) != 1 or len(palettes[0]["bones"]) != 46 or len(palettes[0]["lod_palettes"]) != 3:
        raise RuntimeError("Native donor palette shape changed")
    rgo = Path(variant["extracted"][".rgo"]["path"])
    if sha(rgo) != variant["extracted"][".rgo"]["sha256"]:
        raise RuntimeError("Private selector RGO drift")
    if (variant["extracted"][".rrgeom"]["sha256"] != stock["geometry"]["source"]["sha256"]
            or variant["extracted"][".rrmaterial"]["sha256"] != stock["material"]["source"]["sha256"]):
        raise RuntimeError("Private variant stock geometry/material byte proof drift")
    by_lod = []
    for group, skin in zip(stock_groups, palettes[0]["lod_palettes"]):
        by_lod.append({"geometry_group": group, "skin_palette_name": skin["name"],
                       "skin_palette_material": skin["material"], "skin_palette_effect": skin["effect"],
                       "skin_index_count": len(skin["skin_indices"]),
                       "identity_consistent": (skin["name"] == group["name"] + "_" + group["material"]
                                               and skin["material"] == group["material"]
                                               and skin["effect"] == group["effect"])})
    if not all(x["identity_consistent"] for x in by_lod):
        raise RuntimeError("Native donor geometry/palette names disagree")
    write(RECEIPT, {
        "schema": "ccp-060-archer-pairing-static-contract/v1",
        "status": "stock_variant_contract_pinned_new_geometry_unproved",
        "stock_manifest": str(STOCK), "stock_manifest_sha256": sha(STOCK),
        "variant_readback": str(VARIANT), "variant_readback_sha256": sha(VARIANT),
        "variant_rgm_path": str(new), "variant_rgm_sha256": sha(new),
        "stock_rgm_path": str(old), "stock_rgm_sha256": sha(old),
        "rgm_old_bytes": len(a), "rgm_variant_bytes": len(b),
        "rgm_renamed_path_offset": i, "rgm_only_changed_prefix_byte_offsets": prefix_diffs,
        "rgm_post_path_tail_sha256": hashlib.sha256(a[i+len(OLD_PATH):]).hexdigest(),
        "rgm_other_bytes_exact_after_path_length_normalization": True,
        "variant_rgo_path": str(rgo), "variant_rgo_sha256": sha(rgo),
        "variant_rrgeom_byte_exact_stock": True, "variant_rrmaterial_byte_exact_stock": True,
        "required_geometry_and_palette_lods": by_lod,
        "required_material_names": ["lod1", "lod2", "lod3"],
        "single_lod1_material_for_all_three_lods_is_unsupported": True,
        "private_decode_attempt": "A task-owned eight-member private index was built, but decode-static exceeded its 300-second bound before a manifest was written. Partial decoder cache is retained. No installed index mutation.",
        "rgo_limit": "No supported standalone RGO selector parser or original-Chinese-animator runtime consumer check was found. The unchanged variant RGO is proven to cook with byte-identical stock RRGeom; substituting new geometry remains a separate candidate gate.",
        "next_gate": "Export three weighted LODs with exact basename/LOD/material/effect and bind records; normal prototype validator/cook and compiled geometry readback; only then assemble a new test-only eight-member archive by replacing RRGeom in the private variant, with exact allowlist and dependency checks.",
    })
    print(f"stock variant static contract pinned: {RECEIPT}")


if __name__ == "__main__":
    main()
