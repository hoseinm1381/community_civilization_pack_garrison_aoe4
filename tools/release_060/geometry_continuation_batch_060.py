"""Pin and serially qualify exact 0.6.0 humanoid exports through native geometry."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import authored_geometry_060 as route
from common import EXPORT, OUT, STAGING, guard, owned, read, sha, write

ROSTER = {"maa3": "m13g", "maa4": "m14g", "monk4": "k44g", "repeater4": "r44g",
          "maa3_female": "f13g", "maa4_female": "f14g", "monk3": "k33g"}
VERSIONS = {"monk3": "v2"}
STAGES = ("prepare", "cook", "readback", "compare")
TEMPLATE_PROJECT = STAGING / "l/Mods/u60l"
TEMPLATE_BODY = TEMPLATE_PROJECT / "project/source/art/scenario/garrison/u60l/units/u60l_archer_3lod_control/body"
VILLAGER_TEMPLATE_PROJECT = STAGING / "vf/Mods/v60f"
VILLAGER_TEMPLATE_BODY = (VILLAGER_TEMPLATE_PROJECT /
    "project/source/art/scenario/garrison/v60f/units/v60f_villager_geometry_control/body")
CORRECTED_73 = {
    "villager-female1-v2": "f11b", "villager-female2-v2": "f12b",
    "villager-female3-v3": "f33d", "villager-female4-v2": "f14b",
    "villager-male1-v2": "m11b", "villager-male2-v2": "m12b",
    "villager-male3-v2": "m13b", "villager-male4-v2": "m14b",
    "monk4-v2": "k44d",
}
INTERRUPTED_RETRY = {"villager-female2-v2-r73": "f12c", "monk4-v2-r73": "k44e"}


def build_spec(slug: str, key: str) -> dict:
    if ROSTER.get(slug) != key:
        raise ValueError("Unregistered geometry slug/key")
    version = VERSIONS.get(slug, "v1")
    folder = EXPORT / "remaining_roster" / slug / version
    snapshot = folder / "authored-snapshot.json"
    source = read(snapshot)
    donor = Path(source["source_manifest"])
    stock = read(donor)
    if source["source_manifest_sha256"] != sha(donor):
        raise RuntimeError("Source donor pin drift")
    body = VILLAGER_TEMPLATE_BODY if len(stock["skeleton"]["bones"]) == 73 else TEMPLATE_BODY
    project = VILLAGER_TEMPLATE_PROJECT if body == VILLAGER_TEMPLATE_BODY else TEMPLATE_PROJECT
    spec = {"schema": route.SCHEMA, "slug": f"{slug}-{version}", "project_key": key,
            "skeleton_bones": len(stock["skeleton"]["bones"]),
            "group_name": source["geometry"]["groups"][0]["name"],
            "fbx": str(folder / "model.fbx"), "action": str(folder / "action.json"),
            "albedo": str(folder / "albedo.png"), "authored_snapshot": str(snapshot),
            "export_receipt": str(OUT / "qualification/remaining_roster" / slug / version / "export.json"),
            "stock_manifest": str(donor), "stock_manifest_sha256": sha(donor),
            "template_project": str(project), "template_body": str(body),
            "template_rig_sha256": sha(body / "model.rig"),
            "template_rgo_sha256": sha(body / "model.rgo"),
            "template_rgotemplate_sha256": sha(body / "model.rgotemplate")}
    route.source_inputs(spec)
    route.source_contract(spec, source, stock)
    route.rig_contract(source, stock, spec["skeleton_bones"])
    route.fbx_skin_counts(folder / "model.fbx")
    return spec


def corrected_73_spec(previous_slug: str) -> dict:
    key = CORRECTED_73[previous_slug]
    prior = read(OUT / "authored-geometry" / previous_slug / "spec.json")
    spec = copy.deepcopy(prior)
    spec["slug"] = previous_slug + "-r73"
    spec["project_key"] = key
    spec["template_project"] = str(VILLAGER_TEMPLATE_PROJECT)
    spec["template_body"] = str(VILLAGER_TEMPLATE_BODY)
    for name, field in (("model.rig", "template_rig_sha256"),
                        ("model.rgo", "template_rgo_sha256"),
                        ("model.rgotemplate", "template_rgotemplate_sha256")):
        spec[field] = sha(VILLAGER_TEMPLATE_BODY / name)
    donor = read(Path(spec["stock_manifest"]))
    if spec["skeleton_bones"] != 73 or route.rig_file_contract(VILLAGER_TEMPLATE_BODY / "model.rig", donor) != 73:
        raise RuntimeError("Corrected 73-bone template donor contract differs")
    route.source_inputs(spec)
    route.source_contract(spec, read(Path(spec["authored_snapshot"])), donor)
    return spec


def interrupted_retry_spec(previous_slug: str) -> dict:
    spec = copy.deepcopy(read(OUT / "authored-geometry" / previous_slug / "spec.json"))
    spec["slug"] = previous_slug + "-retry1"
    spec["project_key"] = INTERRUPTED_RETRY[previous_slug]
    source = read(Path(spec["authored_snapshot"]))
    donor = read(Path(spec["stock_manifest"]))
    route.source_inputs(spec)
    route.source_contract(spec, source, donor)
    route.rig_contract(source, donor, spec["skeleton_bones"])
    return spec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("pin", "pin-73", "pin-retry", *STAGES))
    parser.add_argument("--slug", choices=tuple(ROSTER))
    args = parser.parse_args()
    guard()
    if args.stage == "pin-retry":
        if args.slug: raise ValueError("pin-retry processes exact interrupted attempts")
        for previous in INTERRUPTED_RETRY:
            spec = interrupted_retry_spec(previous)
            path = owned(OUT / "authored-geometry" / spec["slug"] / "spec.json")
            if path.exists(): raise FileExistsError(path)
            write(path, spec)
            print(json.dumps({"slug": spec["slug"], "spec": str(path)}), flush=True)
        return
    if args.stage == "pin-73":
        if args.slug: raise ValueError("pin-73 processes its exact fixed roster")
        for previous in CORRECTED_73:
            spec = corrected_73_spec(previous)
            path = owned(OUT / "authored-geometry" / spec["slug"] / "spec.json")
            if path.exists(): raise FileExistsError(path)
            write(path, spec)
            print(json.dumps({"slug": spec["slug"], "spec": str(path)}), flush=True)
        return
    for slug in ((args.slug,) if args.slug else ROSTER):
        path = owned(OUT / "authored-geometry" / f"{slug}-{VERSIONS.get(slug, 'v1')}/spec.json")
        if args.stage == "pin":
            if path.exists():
                raise FileExistsError(f"Preserve existing exact geometry spec: {path}")
            spec = build_spec(slug, ROSTER[slug])
            write(path, spec)
            print(json.dumps({"slug": slug, "spec": str(path)}), flush=True)
        else:
            if not path.is_file(): raise FileNotFoundError(path)
            result = getattr(route, args.stage)(path)
            print(json.dumps({"slug": slug, **result}), flush=True)


if __name__ == "__main__": main()
