"""Archive verify and model-resource extraction for skinned two-UV probe."""
from __future__ import annotations

import json

from common import OUT
import readback_mangonel_two_uv_native as original


if __name__ == "__main__":
    original.BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native"
    print(json.dumps(original.main(), indent=2))
