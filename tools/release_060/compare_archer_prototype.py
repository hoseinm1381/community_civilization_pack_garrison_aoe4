"""Compare complete native Archer II/Spearman II bind records read-only."""
from __future__ import annotations

import json
from pathlib import Path

from common import OUT, guard, sha, write

DONORS = OUT / "donors"


def max_delta(left: dict, right: dict) -> float:
    return max(abs(a - b) for field in ("quaternion_xyzw", "translation_xyz", "scale_xyz")
               for a, b in zip(left[field], right[field]))


def main() -> None:
    guard()
    archer_path = DONORS / "decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
    prototype_path = (DONORS / "prototype-probe"
                      / "2bd91fe1b0f69a897d468faecbeaeeb0fb624cc8a59069f5b29bf1cda3115770"
                      / "prototype.json")
    if not archer_path.is_file() or not prototype_path.is_file():
        raise FileNotFoundError("Pinned donor/prototype manifest is missing")
    archer = json.loads(archer_path.read_text(encoding="utf-8"))
    prototype = json.loads(prototype_path.read_text(encoding="utf-8"))
    ab, pb = archer["skeleton"]["bones"], prototype["skeleton"]["bones"]
    paired = list(zip(ab, pb))
    names = [i for i, (a, b) in enumerate(paired) if a["name"] != b["name"]]
    parents = [i for i, (a, b) in enumerate(paired)
               if a["parent_index"] != b["parent_index"] or a["parent_name"] != b["parent_name"]]
    local_delta = max((max_delta(a["local_reference_transform"], b["local_reference_transform"])
                       for a, b in paired), default=0)
    global_delta = max((max_delta(a["global_reference_transform"], b["global_reference_transform"])
                        for a, b in paired), default=0)
    ap = archer["skeleton"]["skin_palettes"]
    pp = prototype["skeleton"]["skin_palettes"]
    pairs = list(zip(ap[0]["bones"], pp[0]["bones"])) if len(ap) == len(pp) == 1 else []
    palette_names = [i for i, (a, b) in enumerate(pairs) if a["name"] != b["name"]]
    palette_indices = [i for i, (a, b) in enumerate(pairs)
                       if a["palette_index"] != b["palette_index"]
                       or a["skeleton_index"] != b["skeleton_index"]
                       or a["parent_index"] != b["parent_index"]]
    palette_global_delta = max((max_delta(a["global_reference_transform"], b["global_reference_transform"])
                                for a, b in pairs), default=0)
    inverse_delta = max((max_delta(a["inverse_bind_transform"], b["inverse_bind_transform"])
                         for a, b in pairs), default=0)
    alod = [x["skin_indices"] for x in ap[0]["lod_palettes"]]
    plod = [x["skin_indices"] for x in pp[0]["lod_palettes"]]
    # Raw record equality also checks vector lengths, omitted fields and any
    # newly added decoder fields. Numeric diagnostics below aid review but are
    # never substituted for a complete admission comparison.
    exact_skeleton = (len(ab) == len(pb) == 48 and ab == pb and not names and not parents
                      and local_delta == 0 and global_delta == 0)
    palette_structural_match = (len(ap) == len(pp) == 1
                                and len(ap[0]["bones"]) == len(pp[0]["bones"]) == 46
                                and ap[0]["bones"] == pp[0]["bones"]
                                and len(alod) == len(plod) == 3 and alod == plod
                                and not palette_names and not palette_indices
                                and palette_global_delta == 0 and inverse_delta == 0)
    result = {
        "schema": "ccp-060-archer-spearman-record-comparison/v1",
        "status": "exact_bind_records_distinct_animation_owners" if exact_skeleton and palette_structural_match
                  else "bind_records_mismatch",
        "archer_decoded_manifest": {"path": str(archer_path), "sha256": sha(archer_path)},
        "admitted_prototype_manifest": {"path": str(prototype_path), "sha256": sha(prototype_path),
                                         "key": prototype["prototype"]["key"],
                                         "fingerprint": prototype["fingerprint"]},
        "hierarchy": {"archer_count": len(ab), "spearman_count": len(pb),
                      "ordered_name_mismatches": names, "parent_mismatches": parents,
                      "max_local_transform_float_delta": local_delta,
                      "max_global_transform_float_delta": global_delta,
                      "all_48_records_exact": exact_skeleton},
        "skin_palette": {"archer_count": len(ap[0]["bones"]),
                         "spearman_count": len(pp[0]["bones"]),
                         "ordered_name_mismatches": palette_names,
                         "index_or_parent_mismatches": palette_indices,
                         "max_global_transform_float_delta": palette_global_delta,
                         "max_inverse_bind_float_delta": inverse_delta,
                         "archer_lod_indices": alod, "spearman_lod_indices": plod,
                         "all_lod_palette_indices_exact": alod == plod,
                         "structure_match": palette_structural_match},
        "distinct_contracts": {
            "archer_animation_owner": archer["animated_asset_import_plan"]["layers"]["animation"]["template"]["template_id"],
            "spearman_animation_owner": prototype["prototype"]["owner"],
            "spearman_generated_model_partitions": prototype["prototype"]["partitions"],
            "spearman_build_status": prototype["prototype"]["status"],
            "archer_has_no_spearman_prototype_fingerprint": True,
        },
        "interpretation": "Exact hierarchy and skin-palette records justify a bounded model-only cook experiment through the admitted spearman prototype. They do not admit Archer II as a Build Unit prototype, replace the archer animation owner, prove three exported LOD partitions, or authorize binding a generated spearman actor to the live Vietnamese archer.",
    }
    write(OUT / "qualification/archer-spearman-rig-comparison.json", result)
    print(json.dumps({"status": result["status"],
                      "exact_48": exact_skeleton,
                      "palette_structure": palette_structural_match,
                      "max_inverse_bind_delta": inverse_delta,
                      "max_palette_global_delta": palette_global_delta}, indent=2))


if __name__ == "__main__":
    main()
