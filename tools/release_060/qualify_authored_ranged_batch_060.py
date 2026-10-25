"""Run the five new private ranged native geometry stages serially."""
from __future__ import annotations

import argparse
import subprocess
import sys

from common import OUT, guard

TIERS = ("archer2", "archer4", "crossbow3", "crossbow4", "handcannon4")
STAGES = ("prepare", "cook", "readback", "compare")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=TIERS)
    args = parser.parse_args()
    guard()
    names = (args.tier,) if args.tier else TIERS
    tool = __file__.replace("qualify_authored_ranged_batch_060.py", "authored_geometry_060.py")
    for slug in names:
        spec = OUT / "authored-geometry" / slug / "spec.json"
        for stage in STAGES:
            print(f"{slug}: {stage}", flush=True)
            subprocess.run([sys.executable, tool, stage, "--spec", str(spec)], check=True)
        print(f"{slug}: authored three-LOD native geometry qualified", flush=True)


if __name__ == "__main__": main()
