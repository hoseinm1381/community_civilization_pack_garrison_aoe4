"""Shared-lock cook of second skinned two-UV FBX source."""
from __future__ import annotations

from common import OUT, STAGING
import cook_mangonel_manual_geometry as original


if __name__ == "__main__":
    original.PROJECT = STAGING / "sms/Mods/s60m"
    original.PREPARE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native/prepare.json"
    original.RECEIPT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native/cook.json"
    original.RUN = original.PROJECT / "dist/manual-two-uv-skin-native-cook"
    original.main()
