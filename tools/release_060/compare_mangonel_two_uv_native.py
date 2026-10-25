"""Require two palettes and six true native LOD groups for the two-UV source."""
from __future__ import annotations

import json

from common import OUT
import compare_mangonel_manual_geometry as original


if __name__ == "__main__":
    base = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-native"
    original.BASE = base
    original.DECODE = base / "decode.json"
    original.READBACK = base / "readback.json"
    original.REPORT = base / "six-group-comparison.json"
    print(json.dumps(original.main(), indent=2))
