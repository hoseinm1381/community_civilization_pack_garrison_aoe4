"""Bind independently skinned ranged weapons to 0.6.0 rig-route evidence."""
from __future__ import annotations

import json

from common import OUT, guard, owned, read, sha, write

SOURCE = OUT / "inventory/weapon-rig-supplement/weapon-rig-supplement.json"
BODY = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
DEST = OUT / "qualification/nonhumanoid-route-preflight/20261018-ranged-weapon-contract.json"
EXPECTED = {"bow_recurve": (4, 102, [148, 108, 80], "base_bow"),
            "bow_cross": (5, 28, [440, 240, 138], "base_cross"),
            "bow_arbalest": (5, 27, [537, 316, 222], "base_arbalest")}


def main():
    guard()
    owned(DEST)
    if DEST.exists():
        raise FileExistsError(f"Preserve earlier weapon preflight: {DEST}")
    source, body = read(SOURCE), read(BODY)
    if (source["status"] != "three_weapon_decodes_complete"
            or body["status"] != "three_donors_pinned_generic_export_possible_manual_native_source_unproved"):
        raise RuntimeError("Weapon or body source contract drift")
    weapons = {}
    for row in source["weapons"]:
        name = row["label"]
        if name not in EXPECTED:
            raise RuntimeError(f"Unexpected decoded ranged weapon: {name}")
        bones, clips, tris, owner = EXPECTED[name]
        action = row["animation_contract"]
        if (row["classification"] != "skinned" or row["skeleton_bone_count"] != bones
                or row["skin_palette_bone_counts"] != [bones]
                or [lod["triangles"] for lod in row["lods"]] != tris
                or action["template_id"] != owner or action["clip_count"] != clips
                or action["gameplay_action_mapping_status"] != "not_decoded"
                or sha(row["manifest_path"]) != row["manifest_sha256"]):
            raise RuntimeError(f"{name} native skin or animation contract drift")
        weapons[name] = {"manifest": row["manifest_path"],
                         "manifest_sha256": row["manifest_sha256"],
                         "full_bones": bones, "bone_names": row["skeleton_bone_names"],
                         "palette_bones": row["skin_palette_bone_names"],
                         "lods": row["lods"], "animation_owner": owner,
                         "clip_count": clips,
                         "action_mapping": action["gameplay_action_mapping_status"],
                         "route": "independent skinned weapon export and native pair qualification required; preserve original stock RHKA/attachment owner"}
    if set(weapons) != set(EXPECTED):
        raise RuntimeError("Missing ranged weapon inventory")
    report = {"schema": "ccp-060-ranged-weapon-rig-route-preflight/v1",
              "status": "three_animated_stock_weapon_rigs_pinned_no_export_or_cook",
              "source": str(SOURCE), "source_sha256": sha(SOURCE),
              "body_contract": str(BODY), "body_contract_sha256": sha(BODY),
              "weapons": weapons,
              "boundary": "48-bone archer body geometry proof does not qualify any 4/5-bone bow rig; rigid export would discard deformation",
              "handcannon": "Ottoman gun rig/LOD classification unknown pending decode",
              "prototype_admission": "No Garrison weapon Build Unit prototype identified; no fingerprint invented",
              "blender_or_native_cook_run": False}
    write(DEST, report)
    return {"status": report["status"], "receipt": str(DEST),
            "weapons": {k: [v["full_bones"], v["clip_count"]] for k, v in weapons.items()}}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
