"""Private decode of the skinned two-UV mangonel native control."""
from __future__ import annotations

import json

from common import OUT, STAGING
import decode_mangonel_two_uv_native as original


if __name__ == "__main__":
    original.BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native"
    original.PRIVATE_ROOT = STAGING / "sms"
    print(json.dumps(original.main(), indent=2))
