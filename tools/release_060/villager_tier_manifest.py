"""Pin six exact native 73-bone villager body donors for separate art work."""
from __future__ import annotations

import json
from pathlib import Path

from common import OUT, RECIPES, guard, owned, read, sha


def main() -> None:
    guard()
    source = OUT / "inventory/complete-donors/complete-donors.json"
    inventory = read(source)
    entries = []
    for gender in ("male", "female"):
        for age in (1, 2, 3):
            stem = f"chi_villager_{gender}_age{age:02d}"
            logical = f"art/civilizations/chinese/humans/{stem}/{stem}.rgm"
            decoded = inventory["models"][logical]["existing_decode"]
            if not decoded:
                raise RuntimeError("Exact donor decode absent: " + logical)
            manifest = Path(decoded["manifest"])
            if sha(manifest) != decoded["manifest_sha256"]:
                raise RuntimeError("Pinned villager manifest changed: " + logical)
            if decoded["skeleton_bones"] != 73:
                raise RuntimeError("Villager rig bone count changed: " + logical)
            detail = read(manifest)
            palette = detail["skeleton"]["skin_palettes"]
            if len(palette) != 1 or len(palette[0]["bones"]) != 46:
                raise RuntimeError("Expected exact 46-bone skin palette: " + logical)
            lods = [{"lod": int(g["material"][-1]), "triangles": g["triangles"]}
                    for g in decoded["geometry_groups"]]
            entries.append({"gender": gender, "age": age, "model_path": logical,
                            "manifest": str(manifest),
                            "manifest_sha256": decoded["manifest_sha256"],
                            "skeleton_bones": 73, "native_skin_palette_bones": 46,
                            "lods": lods, "consumer_family": "vn_unit_villager",
                            "tools_and_tasks": "Preserve native separate attachment and task bindings"})
    target = owned(RECIPES / "representative-villager-tier-batch.json")
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps({
        "schema": "ccp-060-villager-tier-donor-batch/v1",
        "status": "pinned_donor_preparation_only",
        "source_inventory": str(source), "source_inventory_sha256": sha(source),
        "model_count": len(entries), "models": entries,
        "design_basis": "Approved male/female Age I work cloth extended to each actual native age donor; use broad garment shapes and one stock owner-pattern-compatible albedo per atlas.",
        "qualification_boundary": "Exact 73-bone hierarchy and 46-bone Chinese skin palette must survive export/cook/readback. Older English prototype 45-bone palette is not an acceptable shortcut. Age IV donors are source-linked but not decoded in this six-body stage."
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"recipe": str(target), "sha256": sha(target),
                      "models": len(entries)}))


if __name__ == "__main__":
    main()
