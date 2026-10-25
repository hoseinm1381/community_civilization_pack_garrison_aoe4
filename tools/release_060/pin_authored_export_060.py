"""Pin one immutable artist export to a fresh 0.6.0 native geometry attempt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from authored_geometry_060 import SCHEMA, fbx_skin_counts, rig_contract, source_contract, source_inputs
from common import OUT, STAGING, guard, owned, read, sha, write

TEMPLATE_PROJECT = STAGING / "l/Mods/u60l"
TEMPLATE_BODY = (TEMPLATE_PROJECT / "project/source/art/scenario/garrison/u60l/units/"
                 "u60l_archer_3lod_control/body")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, help="New immutable attempt folder, e.g. spear1-v3")
    parser.add_argument("--key", required=True, help="Fresh four-character private native project key")
    parser.add_argument("--bones", required=True, type=int, choices=(48, 73))
    parser.add_argument("--export-folder", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    guard()
    folder, receipt = owned(args.export_folder), owned(args.receipt)
    snapshot_path = folder / "authored-snapshot.json"
    snapshot = read(snapshot_path)
    donor_path = Path(snapshot["source_manifest"])
    donor = read(donor_path)
    spec = {
        "schema": SCHEMA,
        "slug": args.attempt,
        "project_key": args.key,
        "skeleton_bones": args.bones,
        "group_name": snapshot["geometry"]["groups"][0]["name"],
        "fbx": str(folder / "model.fbx"),
        "action": str(folder / "action.json"),
        "albedo": str(folder / "albedo.png"),
        "authored_snapshot": str(snapshot_path),
        "export_receipt": str(receipt),
        "stock_manifest": str(donor_path),
        "stock_manifest_sha256": sha(donor_path),
        "template_project": str(TEMPLATE_PROJECT),
        "template_body": str(TEMPLATE_BODY),
        "template_rig_sha256": sha(TEMPLATE_BODY / "model.rig"),
        "template_rgo_sha256": sha(TEMPLATE_BODY / "model.rgo"),
        "template_rgotemplate_sha256": sha(TEMPLATE_BODY / "model.rgotemplate"),
    }
    if snapshot["source_manifest_sha256"] != spec["stock_manifest_sha256"]:
        raise RuntimeError("Artist snapshot donor hash drift")
    source_inputs(spec)
    source_contract(spec, snapshot, donor)
    rig_contract(snapshot, donor, args.bones)
    skins, clusters = fbx_skin_counts(Path(spec["fbx"]))
    if skins != 3 or clusters != 3 * args.bones:
        raise RuntimeError(f"Unexpected three-LOD skin/cluster records: {skins=}, {clusters=}")
    target = owned(OUT / "authored-geometry" / args.attempt / "spec.json")
    if target.exists():
        raise FileExistsError(f"Preserve existing pinned attempt: {target}")
    write(target, spec)
    print(json.dumps({"status": "pinned", "spec": str(target),
                      "spec_sha256": sha(target), "fbx_skins": skins,
                      "fbx_clusters": clusters,
                      "authored_triangles": [group["triangle_count"]
                                              for group in snapshot["geometry"]["groups"]]}))


if __name__ == "__main__":
    main()
