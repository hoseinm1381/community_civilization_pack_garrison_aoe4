"""Verify current official Archer II pattern RRtex; convert its decoded top mip to PNG.

This is format conversion for a source mask, not repainting. No Blender/native
cook/project source is touched; a later geometry design must audit its own UVs.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from PIL import Image

from common import ARCH, OUT, guard, owned, read, sha, write

INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
DONOR = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
DEST = OUT / "qualification/material-route-probe"
RECEIPT = DEST / "stock-pattern-conversion.json"
PNG = DEST / "stock-archer02-pattern.png"
RR = DEST / "current-stock-archer02-pattern.rrtex"


def main() -> None:
    guard()
    for path in (RECEIPT, PNG, RR):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve earlier conversion: {path}")
    donor = read(DONOR)
    slots = [t for material in donor["material"]["materials"]
             for block in material["blocks"] for t in block.get("textures", [])
             if t.get("name") == "patternTex"]
    if len(slots) != 3 or len({t["logical_path"] for t in slots}) != 1:
        raise RuntimeError("Archer II LOD pattern texture slots differ")
    logical = slots[0]["logical_path"]
    paths = [t for t in donor["textures"] if Path(t["source"]["path"]).name == Path(logical).name]
    if len(paths) != 1:
        raise RuntimeError("Decoded stock pattern RRtex is not unique")
    source = paths[0]
    decoded_rr = Path(source["source"]["path"])
    if sha(decoded_rr) != source["source"]["sha256"]:
        raise RuntimeError("Decoded pattern RRtex changed")
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        rows = db.execute("select archive_path,size from resolved_assets where lower(logical_path)=?",
                          (logical.lower(),)).fetchall()
    if len(rows) != 1:
        raise RuntimeError(f"Pattern RRtex not unique in current index: {rows}")
    archive = Path(rows[0][0])
    archive_hash = sha(archive)
    command = [str(ARCH), "extract-member", str(archive), logical, str(RR)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=90,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"Exact pattern extract failed {result.returncode}: {result.stderr[-1000:]}")
    if RR.stat().st_size != rows[0][1] or sha(RR) != source["source"]["sha256"]:
        raise RuntimeError("Current official pattern bytes differ from pinned decoded donor")
    dds = Path(slots[0]["projection_path"])
    if not dds.is_file():
        raise FileNotFoundError(dds)
    image = Image.open(dds)
    image.load()
    if image.mode != "RGBA" or image.size != (256, 256):
        raise RuntimeError(f"Unexpected current decoder pattern projection: {image.mode} {image.size}")
    extrema = image.getextrema()
    image.save(PNG, format="PNG", optimize=False)
    reopened = Image.open(PNG)
    reopened.load()
    if reopened.mode != image.mode or reopened.size != image.size or reopened.tobytes() != image.tobytes():
        raise RuntimeError("PNG top-mip pixel round-trip mismatch")
    write(RECEIPT, {"schema": "ccp-060-stock-pattern-conversion/v1",
                    "status": "verified_current_stock_mask_top_mip_png_pixel_exact",
                    "donor_manifest": str(DONOR), "donor_manifest_sha256": sha(DONOR),
                    "logical_pattern_rrtex": logical, "current_archive": str(archive),
                    "current_archive_sha256": archive_hash,
                    "current_rrtex": str(RR), "rrtex_sha256": sha(RR),
                    "decoded_dds": str(dds), "decoded_dds_sha256": sha(dds),
                    "png": str(PNG), "png_sha256": sha(PNG), "size": list(image.size),
                    "mode": image.mode, "channel_extrema": extrema,
                    "all_three_stock_lods_share_mask": True,
                    "no_new_clothing_uv_validation_or_native_cook": True})
    print(json.dumps({"status": "verified", "png": str(PNG), "sha256": sha(PNG),
                      "channel_extrema": extrema}, indent=2))


if __name__ == "__main__":
    main()
