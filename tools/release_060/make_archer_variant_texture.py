"""Prepare a conservative atlas-preserving albedo probe for the stock variant.

Only low-saturation robe texels in the donor's lower-left atlas region are
shifted. This is a cook/readback probe, not an approved final fabric design.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from common import OUT, guard, sha, write


def main() -> None:
    guard()
    decoded_path = next((OUT / "donors/decoded/archer02").rglob("decoded-static.json"))
    decoded = json.loads(decoded_path.read_text(encoding="utf-8"))
    albedo = next(t for t in decoded["textures"] if t["texture_name"].endswith("_alb"))
    source = Path(albedo["projection"]["path"])
    if sha(source) != albedo["projection"]["sha256"]:
        raise RuntimeError("Decoded stock albedo changed")
    image = Image.open(source).convert("RGBA")
    if image.size != (256, 256):
        raise RuntimeError(f"Unexpected stock atlas size: {image.size}")
    pixels = image.load()
    changed = 0
    # The source atlas was inspected first. x<126,y>=76 holds the gray robe
    # panels; red headcloth/wood, skin LUT and owner pattern remain unpainted.
    for y in range(76, 256):
        for x in range(0, 126):
            r, g, b, a = pixels[x, y]
            spread = max(r, g, b) - min(r, g, b)
            if 43 <= (r + g + b) / 3 <= 225 and spread <= 18 and a >= 220:
                pixels[x, y] = (int(r * .66), int(g * .81), int(b * .88), a)
                changed += 1
    if changed < 5000:
        raise RuntimeError(f"Too few robe texels selected: {changed}")
    target = OUT / "qualification/archer-albedo-variant-probe.png"
    image.save(target)
    write(OUT / "qualification/archer-albedo-variant-probe.json", {
        "schema": "ccp-060-archer-albedo-probe/v1",
        "status": "diagnostic_stock_material_variant_not_final_art",
        "source_dds": str(source), "source_sha256": sha(source),
        "atlas_region_xy": [0, 76, 126, 256],
        "gray_texels_changed": changed,
        "output_png": str(target), "output_sha256": sha(target),
        "owner_pattern": "unaltered separate patternTex",
        "skin_lut": "unaltered separate skinTintLUT",
    })
    print(json.dumps({"png": str(target), "gray_texels_changed": changed}, indent=2))


if __name__ == "__main__":
    main()
