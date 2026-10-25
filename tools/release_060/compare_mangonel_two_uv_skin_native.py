"""Run six-group/two-palette and UV2 comparisons for skinned FBX probe."""
from __future__ import annotations

import json

from common import OUT
import compare_mangonel_manual_geometry as geometry
import compare_mangonel_uv2 as uv2


if __name__ == "__main__":
    base = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native"
    geometry.BASE = base
    geometry.DECODE = base / "decode.json"
    geometry.READBACK = base / "readback.json"
    geometry.REPORT = base / "six-group-comparison.json"
    uv2.BASE = base
    uv2.REPORT = base / "six-group-uv2-comparison.json"
    try:
        first = geometry.main()
    except RuntimeError as error:
        first = {"status": "six_group_geometry_not_qualified", "error": str(error)}
    second = uv2.main()
    print(json.dumps({"geometry": first, "uv2": second}, indent=2))
