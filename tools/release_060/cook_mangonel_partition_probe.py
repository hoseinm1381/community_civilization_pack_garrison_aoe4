"""Cook the isolated all-14-bone skeletal-LOD3 diagnostic candidate."""
from __future__ import annotations

from common import OUT, STAGING
import cook_mangonel_manual_geometry as original


if __name__ == "__main__":
    base = OUT / "qualification/nonhumanoid-route-preflight/mangonel/partition-probe"
    original.PROJECT = STAGING / "smp/Mods/s60m"
    original.PREPARE = base / "prepare.json"
    original.RECEIPT = base / "cook.json"
    original.RUN = original.PROJECT / "dist/manual-partition-probe-cook"
    original.main()
