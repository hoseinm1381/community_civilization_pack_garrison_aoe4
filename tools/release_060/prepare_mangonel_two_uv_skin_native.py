"""Prepare a fresh native source from the second skinned two-UV FBX."""
from __future__ import annotations

import json

from common import OUT, STAGING
import prepare_mangonel_two_uv_native as original


if __name__ == "__main__":
    original.LIBRARY = STAGING / "sms"
    original.PROJECT = original.LIBRARY / "Mods/s60m"
    original.BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native"
    original.PREP = original.BASE / "prepare.json"
    original.EXPORT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-export.json"
    print(json.dumps(original.main(), indent=2))
