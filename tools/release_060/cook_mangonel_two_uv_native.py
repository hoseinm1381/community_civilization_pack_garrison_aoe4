"""Shared-lock native cook of fresh two-UV mangonel source."""
from __future__ import annotations

from common import OUT, STAGING
import cook_mangonel_manual_geometry as original


if __name__ == "__main__":
    original.PROJECT = STAGING / "smu/Mods/s60m"
    original.PREPARE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-native/prepare.json"
    original.RECEIPT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-native/cook.json"
    original.RUN = original.PROJECT / "dist/manual-two-uv-native-cook"
    original.main()
