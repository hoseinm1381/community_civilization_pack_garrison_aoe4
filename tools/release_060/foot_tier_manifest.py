"""Pin the exact decoded 48-bone Chinese foot donors for the 0.6.0 art batch."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from common import OUT, RECIPES, guard, owned


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    guard()
    inventory = OUT / "inventory"
    original = inventory / "complete-donors" / "complete-donors.json"
    extension = inventory / "complete-donors-next" / "complete-donors-next.json"
    first = json.loads(original.read_text(encoding="utf-8"))
    second = json.loads(extension.read_text(encoding="utf-8"))
    added = {r["logical_model_path"]: r["decode"] for r in second["results"]
             if r["status"] == "decoded_new"}
    families = {
        "chi_infantry_light_age": ((1, 2, 3, 4),
                                   ("vn_unit_spearman", "vn_unit_spearman_fire")),
        "chi_ranged_bow_age": ((2, 3, 4), ("vn_unit_archer",)),
        "chi_ranged_crossbow_age": ((3, 4), ("vn_unit_crossbowman",)),
        "chi_ranged_cannoneer_age": ((4,), ("vn_unit_handcannon",)),
    }
    entries = []
    for stem, (ages, consumers) in families.items():
        for age in ages:
            name = f"{stem}{age:02d}"
            logical = f"art/civilizations/chinese/humans/{name}/{name}.rgm"
            decoded = added.get(logical) or first["models"][logical]["existing_decode"]
            if not decoded:
                raise RuntimeError("No pinned decode: " + logical)
            manifest = Path(decoded["manifest"])
            expected = decoded["manifest_sha256"]
            if digest(manifest).lower() != expected.lower():
                raise RuntimeError("Donor manifest changed: " + logical)
            bone_count = decoded.get("skeleton_bone_count", decoded.get("skeleton_bones"))
            if bone_count != 48:
                raise RuntimeError(f"Not a 48-bone foot donor: {logical}: {bone_count}")
            lod1 = next(g.get("triangles", g.get("triangle_count"))
                        for g in decoded["geometry_groups"] if g["material"] == "lod1")
            entries.append({"age": age, "model_path": logical,
                            "manifest": str(manifest), "manifest_sha256": expected,
                            "stock_lod1_triangles": lod1, "skeleton_bones": bone_count,
                            "consuming_families": list(consumers),
                            "weapon_rule": "Preserve each consumer native weapon and attachments",
                            "source_coverage": ("decoded_new" if logical in added
                                                else "existing_verified")})
    recipe = {
        "schema": "ccp-060-foot-tier-donor-batch/v1",
        "status": "pinned_donor_preparation_only",
        "design_basis": "Approved normal-distance Vietnamese representatives; each tier retains its exact stock body, 48-bone rig, age silhouette, animations, weapons, material effects and owner pattern. New art uses broad weighted native-UV garment surfaces and one native albedo variant per donor atlas.",
        "source_inventory": {"complete_donors": str(original),
                             "complete_donors_sha256": digest(original),
                             "complete_donors_next": str(extension),
                             "complete_donors_next_sha256": digest(extension)},
        "models": entries,
        "boundaries": "No gameplay tuning or native binding changes; man-at-arms, villagers, mounted units, elephant and siege are separate. Archer tier ownership awaits artist coordination.",
    }
    target = owned(RECIPES / "representative-foot-tier-batch.json")
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(json.dumps({"recipe": str(target), "sha256": digest(target),
                      "models": len(entries),
                      "consumers": sorted({c for e in entries for c in e["consuming_families"]})}))


if __name__ == "__main__":
    main()
