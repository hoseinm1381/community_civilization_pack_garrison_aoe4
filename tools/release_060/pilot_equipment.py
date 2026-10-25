"""Decode actual stock equipment used in 0.6.0 representative assemblies."""
from __future__ import annotations

import json
import hashlib
import sqlite3
import subprocess
from pathlib import Path

from common import CORE, OUT, guard, owned, read, sha, write
from pilot_trace import decode as decode_rgd, index_model, stock_models
from pilot_decode import provider_identity

DEST = OUT / "pilots"
INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
CONFIG = INDEX.with_name("game-assets.local.json")
SELECTION = {
    "spear2": ["spear_basic.rgm"],
    "male_villager1": ["hammer_construction.rgm", "res_rice_carry.rgm"],
    "female_villager1": ["sickle_farming.rgm", "res_rice_carry.rgm"],
    "horseman2": ["spear_basic.rgm"],
    "elephant": ["sul_spear_goad.rgm"],
    "siege_mangonel3": [],
}


def decode_stock(pilot: str, model: dict, role: str) -> dict:
    source_identity = provider_identity(model["logical_path"])
    fingerprint = hashlib.sha256(json.dumps(source_identity, sort_keys=True).encode()).hexdigest()[:20]
    target = owned(DEST / pilot / "equipment" / role / ("verified-" + fingerprint))
    target.mkdir(parents=True, exist_ok=True)
    receipt_path = target / "source-identity.json"
    manifests = list(target.glob("*/decoded-static.json"))
    if manifests:
        if len(manifests) != 1 or not receipt_path.is_file():
            raise RuntimeError(f"Unverified equipment decode cache: {target}")
        receipt = read(receipt_path)
        if (receipt["source_identity"] != source_identity or
                receipt["manifest_sha256"] != sha(manifests[0])):
            raise RuntimeError(f"Stale or modified equipment decode cache: {target}")
    if not manifests:
        run = subprocess.run([str(CORE), "convert", "decode-static",
                              "--logical-path", model["logical_path"],
                              "--config", str(CONFIG), "--index", str(INDEX),
                              "--output-root", str(target)], capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
        if run.returncode:
            raise RuntimeError(f"{pilot}/{role} stock decode failed: {run.stderr[-1000:]}")
        manifests = list(target.glob("*/decoded-static.json"))
        if len(manifests) == 1:
            write(receipt_path, {"source_identity": source_identity,
                                 "manifest_sha256": sha(manifests[0])})
    if len(manifests) != 1:
        raise RuntimeError(f"{pilot}/{role} ambiguous equipment decode: {manifests}")
    manifest = manifests[0]
    data = read(manifest)
    return {"stock_model": model, "source_identity": source_identity,
            "manifest": str(manifest),
            "manifest_sha256": sha(manifest), "status": data.get("status"),
            "blockers": data.get("blockers"),
            "groups": [{"name": g["name"], "material": g["material"],
                        "triangles": g["triangle_count"]}
                       for g in data.get("geometry", {}).get("groups", [])],
            "skeleton_bones": len((data.get("skeleton") or {}).get("bones", []))}


def main() -> None:
    guard()
    trace = read(DEST / "pilot-trace.json")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    archive = Path(cfg["game_root"]) / "cardinal/archives/Attrib.sga"
    result = {"schema": "ccp-060-pilot-equipment/v1", "pilots": {}}
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        for pilot, endings in SELECTION.items():
            models = list(trace["pilots"][pilot]["stock_models"].values())
            if pilot == "siege_mangonel3":
                cart_member = "attrib/attachments/attachment_lists/races/core/units/unit_siege_cart.rgd"
                cart, evidence = decode_rgd(archive, pilot, cart_member)
                result["siege_cart_attachment"] = evidence
                models.extend(index_model(db, item["value"]) for item in stock_models(cart))
                result["siege_cart_visual_limit"] = (
                    "The attached stock siege_cart archetype RGM has no same-stem RRGeometry "
                    "provider; it is a native attachment/animation owner, not a separate "
                    "qualified visible mesh for this pilot.")
                endings = []
            selected = {}
            for ending in endings:
                matches = list({m["logical_path"]: m for m in models
                                if m["logical_path"].endswith("/" + ending)}.values())
                if len(matches) != 1 or matches[0]["status"] != "confirmed":
                    raise RuntimeError(f"Cannot confirm {pilot} equipment {ending}: {matches}")
                selected[ending] = decode_stock(pilot, matches[0], Path(ending).stem)
            result["pilots"][pilot] = selected
            print(pilot, list(selected))
    write(DEST / "pilot-equipment.json", result)


if __name__ == "__main__":
    main()
