"""Build optional Garrison roof-surface carriers for Vietnamese donor remixes.

Only roof albedo sources are recoloured; native masks, all owner parameters,
normal/metal channels, damage inputs and construction collections stay stock.
Carriers are separate because each native material block must be selected by name
during integration. This script never cooks or changes gameplay source.
"""
import hashlib
import io
import json
import os
import struct
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
CORE = EXT / "bin/core/garrison-core.exe"
OUT = ROOT / "output/release_020/barracks_tc"
PROJECT = OUT / "library/Mods/community_civilization_pack"
RECIPE = ROOT / "art/recipes/release_020/barracks-tc-materials.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def image_path(path):
    s = str(path)
    return Path("\\\\?\\" + s) if os.name == "nt" and len(s) >= 240 else Path(s)


def decode_dds(entry, destination):
    raw = bytearray(image_path(entry["projection"]["path"]).read_bytes())
    if raw[84:88] == b"DX10":
        fmt = struct.unpack_from("<I", raw, 128)[0]
        if fmt in (72, 75, 78):
            struct.pack_into("<I", raw, 128, fmt - 1)
    Image.open(io.BytesIO(raw)).convert("RGBA").save(destination)


def recolor(src, dest, rgb):
    arr = np.asarray(Image.open(src).convert("RGBA")).copy()
    luminance = np.sum(arr[:, :, :3].astype(float) * [.2126, .7152, .0722], axis=2) / 255
    variation = .66 + .47 * luminance
    arr[:, :, :3] = np.clip(variation[:, :, None] * np.asarray(rgb), 0, 255).astype("uint8")
    Image.fromarray(arr, "RGBA").save(dest)


def run(label, *argv):
    result = subprocess.run([str(CORE), *map(str, argv)], capture_output=True, text=True, encoding="utf8")
    if result.returncode:
        raise RuntimeError(f"{label}: {result.stdout[-1000:]} {result.stderr[-1000:]}")


current = json.loads((PROJECT / "mod-project.json").read_text())
assert current["mod_id"] == "b7fcea91-257b-408f-b9e8-ae4d8bc402e1"
assert current["release"]["version"] == "0.2.0"
assert current["game_mode"]["enabled"] is False and current["game_mode"]["live_reload"] is False
registered = {v["name"] for v in current.get("model_variants", [])}
models = []
palette = {1: (157, 119, 75), 2: (148, 90, 61), 3: (133, 79, 56), 4: (103, 79, 73)}
for family in ("barracks", "town_center"):
    author = ROOT / f"art/authoring/buildings_020/{family}"
    textures = author / "textures"
    textures.mkdir(parents=True, exist_ok=True)
    for age in range(1, 5):
        d = json.loads(next((ROOT / f"art/stock_cache/buildings_020/barracks_tc/{family}/age{age:02}").rglob("decoded-static.json")).read_text())
        logical = d["request"]["logical_path"].removesuffix(".rgo")
        texture_lookup = {t["texture_name"]: t for t in d["textures"] if t.get("texture_name")}
        rows = []
        for m in d["material"]["materials"]:
            name = m["name"]
            if name.endswith("_collection") or "roof" not in name:
                continue
            candidates = [t for b in m["blocks"] for t in b.get("textures", [])
                          if t["name"].startswith("albedoTex") and t["name"] != "albedoTexCharred"
                          and ("/shingle/" in t["logical_path"].lower() or "/wood/" in t["logical_path"].lower())]
            candidates.sort(key=lambda t: ("/shingle/" not in t["logical_path"].lower(), t["name"]))
            if not candidates:
                continue
            t = candidates[0]
            entry = texture_lookup[t["texture_name"]]
            src = textures / f"donor_age{age:02}_{name}_{t['name']}.png"
            if not src.exists():
                decode_dds(entry, src)
            dest = textures / f"vn_age{age:02}_{name}_{t['name']}.png"
            recolor(src, dest, palette[age])
            carrier = f"vn_{family}_age{age:02}_{name}"
            if carrier not in registered:
                run("variant " + carrier, "mod-project", "variant", "--project", PROJECT, "--source", logical, "--name", carrier)
                registered.add(carrier)
            run("slot " + carrier, "mod-project", "variant-set", "--project", PROJECT, "--name", carrier, "--slot", t["name"], "--image", dest)
            rows.append({"material_name": name, "carrier": carrier, "slot": t["name"],
                         "source_logical_path": t["logical_path"], "source_png": str(src), "source_png_sha256": sha(src),
                         "image": str(dest), "image_sha256": sha(dest), "colour_rgb": list(palette[age]),
                         "source_type": "native shingle" if "/shingle/" in t["logical_path"].lower() else "native roof timber"})
        models.append({"family": family, "age": age, "stock_model": logical, "roof_materials": rows})
        print("MATERIAL_READY", family, age, len(rows), flush=True)
report = {"schema": "ccp.barracks-tc-roof-carriers/v1", "status": "registered_uncooked", "models": models,
          "garrison_project": str(PROJECT), "garrison_project_sha256": sha(PROJECT / "mod-project.json"),
          "owner_mask_policy": "Original maskTex*, debug/team albedo, secondary masks, all shader owner parameters and charred/damage inputs remain unchanged",
          "proof_scope": "Private surface PNG and Garrison variant recipe only; native cook and in-game owner colours remain unproven"}
RECIPE.parent.mkdir(parents=True, exist_ok=True)
RECIPE.write_text(json.dumps(report, indent=2), encoding="utf8")
(OUT / "materials-ready.json").write_text(json.dumps(report, indent=2), encoding="utf8")
print("MATERIAL_RECIPE_READY", len(models), sum(len(m["roof_materials"]) for m in models), flush=True)
