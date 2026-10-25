"""Pin six artist-exported ranged tiers to isolated authored native projects."""
from __future__ import annotations

import json

from authored_geometry_060 import SCHEMA, source_contract, rig_contract, fbx_skin_counts
from common import EXPORT, OUT, STAGING, guard, read, sha, write

TIERS = (("archer2", "v1", "a62r"), ("archer3", "v4", "a63r"),
         ("archer4", "v4", "a64r"), ("crossbow3", "v4", "c63r"),
         ("crossbow4", "v4", "c64r"), ("handcannon4", "v4", "h64r"))
TEMPLATE_PROJECT = STAGING / "l/Mods/u60l"
TEMPLATE_BODY = TEMPLATE_PROJECT / "project/source/art/scenario/garrison/u60l/units/u60l_archer_3lod_control/body"


def main() -> None:
    guard()
    template = {"template_project": str(TEMPLATE_PROJECT), "template_body": str(TEMPLATE_BODY),
                "template_rig_sha256": sha(TEMPLATE_BODY / "model.rig"),
                "template_rgo_sha256": sha(TEMPLATE_BODY / "model.rgo"),
                "template_rgotemplate_sha256": sha(TEMPLATE_BODY / "model.rgotemplate")}
    for slug, version, key in TIERS:
        folder = EXPORT / "ranged_roster" / slug / version
        receipt = OUT / "qualification/ranged_roster" / slug / version / "export.json"
        snapshot = folder / "authored-snapshot.json"
        source = read(snapshot)
        donor = read(source["source_manifest"])
        if sha(source["source_manifest"]) != source["source_manifest_sha256"]:
            raise RuntimeError(f"{slug}: pinned donor changed")
        group = source["geometry"]["groups"][0]["name"]
        spec = {"schema": SCHEMA, "slug": slug, "project_key": key,
                "skeleton_bones": 48, "group_name": group,
                "fbx": str(folder / "model.fbx"), "action": str(folder / "action.json"),
                "albedo": str(folder / "albedo.png"), "authored_snapshot": str(snapshot),
                "export_receipt": str(receipt), "stock_manifest": source["source_manifest"],
                "stock_manifest_sha256": sha(source["source_manifest"]), **template}
        source_contract(spec, source, donor)
        rig_contract(source, donor, 48)
        fbx_skin_counts(folder / "model.fbx")
        target = OUT / "authored-geometry" / slug / "spec.json"
        if target.exists():
            existing = read(target)
            if (existing["slug"] != slug or existing["project_key"] != key
                    or existing["stock_manifest_sha256"] != spec["stock_manifest_sha256"]
                    or sha(existing["fbx"]) != sha(spec["fbx"])
                    or sha(existing["authored_snapshot"]) != sha(spec["authored_snapshot"])):
                raise FileExistsError(f"Preserve prior different spec: {target}")
        else:
            write(target, spec)
        print(json.dumps({"slug": slug, "spec": str(target),
                          "source_lod_triangles": [g["triangle_count"] for g in source["geometry"]["groups"]]}))


if __name__ == "__main__": main()
