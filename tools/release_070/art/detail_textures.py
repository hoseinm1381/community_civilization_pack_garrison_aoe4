"""Generate deterministic 2048 object-PBR source atlases for 0.7.0 buildings.

The atlas has eight physically named zones in a 4x2 grid: stone, wood,
plaster, clay roof, water, fired clay, metal, foliage. It contains no
player-colour-blue pixels or owner-colour claims. These are editable source
PNGs, not native cooked textures. Reruns refuse to overwrite existing maps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
KINDS = ("garden", "foundry", "wonder", "university")
CATS = ("stone", "wood", "plaster", "roof", "water", "clay", "metal", "foliage")
PALETTES = {
    "garden": ((139, 126, 106), (91, 54, 36), (196, 178, 141), (118, 65, 47),
               (57, 102, 100), (148, 91, 57), (81, 85, 82), (63, 103, 63)),
    "foundry": ((126, 116, 100), (83, 50, 33), (173, 154, 125), (109, 60, 43),
                (56, 86, 88), (142, 81, 47), (77, 77, 73), (75, 91, 55)),
    "wonder": ((157, 145, 121), (95, 52, 32), (205, 186, 150), (130, 67, 43),
               (62, 98, 99), (159, 88, 52), (153, 125, 58), (65, 100, 61)),
    "university": ((151, 139, 116), (92, 54, 35), (195, 180, 154), (121, 66, 47),
                   (60, 97, 98), (151, 85, 55), (90, 93, 89), (69, 98, 64)),
}
ROUGH = (.82, .74, .88, .76, .33, .85, .49, .96)
METAL = (0, 0, 0, 0, 0, 0, .66, 0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(kind: str) -> dict:
    output = ROOT / "art/exports/buildings_070" / kind / "textures"
    expected = [output / f"{kind}_{channel}_2048.png"
                for channel in ("albedo", "normal", "roughness", "metalness")]
    if any(p.exists() for p in expected):
        raise FileExistsError("Refusing to replace existing 0.7.0 texture source")
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(70070 + KINDS.index(kind))
    size = 2048
    albedo = np.empty((size, size, 3), np.uint8)
    normal = np.empty_like(albedo)
    roughness = np.empty((size, size), np.uint8)
    metalness = np.empty((size, size), np.uint8)
    zone_w, zone_h = 512, 1024
    for index, category in enumerate(CATS):
        x0 = index % 4 * zone_w
        y0 = index // 4 * zone_h
        yy, xx = np.mgrid[0:zone_h, 0:zone_w]
        grain = rng.normal(0, 1, (zone_h, zone_w)).astype(np.float32)
        # Three scales of low-amplitude mineral/brush texture; output remains
        # stylized and legible at strategy-game camera distance.
        sm = Image.fromarray(rng.integers(0, 255, (64, 32), dtype=np.uint8))
        sm = np.asarray(sm.resize((zone_w, zone_h), Image.Resampling.BICUBIC), dtype=np.float32)
        low = (sm - 127.5) / 50
        relief = low*3.3 + grain*1.65
        if category == "wood":
            relief += np.sin(xx*.078 + low*.45)*5.2 + np.sin(xx*.20)*1.4
        elif category == "stone":
            relief += np.where((yy % 144) < 3, -12.0, 0)
            relief += np.where(((xx + ((yy//144) % 2)*160) % 320) < 3, -11.0, 0)
        elif category == "plaster":
            relief += rng.normal(0, 1.0, relief.shape)
        elif category == "roof":
            relief += np.cos(xx*.10)*2.7 + np.where((yy % 83) < 5, -8.0, 0)
        elif category == "water":
            relief += np.sin(xx*.06+yy*.02)*3 + np.sin(xx*.015-yy*.038)*2
        elif category == "metal":
            relief += np.sin(xx*.19)*1.3
        elif category == "foliage":
            relief += np.sin(xx*.025+yy*.016)*3
        color = np.array(PALETTES[kind][index], np.float32)
        tile = np.clip(color[None, None, :] + relief[:, :, None], 0, 255).astype(np.uint8)
        albedo[y0:y0+zone_h, x0:x0+zone_w] = tile
        # Tangent normal inferred from small texture height, not mesh relief.
        gy, gx = np.gradient(relief)
        nx = np.clip(128 - gx*1.4, 1, 254)
        ny = np.clip(128 - gy*1.4, 1, 254)
        normal[y0:y0+zone_h, x0:x0+zone_w, 0] = nx.astype(np.uint8)
        normal[y0:y0+zone_h, x0:x0+zone_w, 1] = ny.astype(np.uint8)
        normal[y0:y0+zone_h, x0:x0+zone_w, 2] = 252
        roughness[y0:y0+zone_h, x0:x0+zone_w] = np.clip(
            ROUGH[index]*255 + grain*4, 0, 255).astype(np.uint8)
        metalness[y0:y0+zone_h, x0:x0+zone_w] = int(METAL[index]*255)
    for path, data, mode in zip(expected,
                                (albedo, normal, roughness, metalness),
                                ("RGB", "RGB", "L", "L")):
        Image.fromarray(data, mode=mode).save(path, optimize=True)
    manifest = {"schema": "ccp-070-building-texture-sources/v1",
                "asset": kind, "size": [2048, 2048],
                "atlas_zones": list(CATS),
                "maps": {p.name: digest(p) for p in expected},
                "player_colour": "none baked; native owner-mask route separately qualified"}
    (output / "texture-sources.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("asset", choices=KINDS)
    args = parser.parse_args()
    print(json.dumps(generate(args.asset), indent=2))
