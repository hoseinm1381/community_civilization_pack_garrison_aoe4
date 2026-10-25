"""Fresh source after verified interrupted cook; run one bounded stage at a time."""
from __future__ import annotations

import argparse
import json

from common import OUT, STAGING, read

BASE = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native-resume"
PROJECT = STAGING / "smr/Mods/s60m"


def main(stage: str):
    audit = read(OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-native/interrupted-cook-audit.json")
    if audit["status"] != "interrupted_no_final_archive_source_preserved" or not audit["shared_native_byte_lock_free"]:
        raise RuntimeError("Interrupted cook has not been safely audited")
    if stage == "prepare":
        import prepare_mangonel_two_uv_native as module
        module.LIBRARY = STAGING / "smr"
        module.PROJECT = PROJECT
        module.BASE = BASE
        module.PREP = BASE / "prepare.json"
        module.EXPORT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-export.json"
        return module.main()
    if stage == "cook":
        import cook_mangonel_manual_geometry as module
        module.PROJECT = PROJECT
        module.PREPARE = BASE / "prepare.json"
        module.RECEIPT = BASE / "cook.json"
        module.RUN = PROJECT / "dist/manual-two-uv-skin-native-resume-cook"
        return module.main()
    if stage == "readback":
        import readback_mangonel_two_uv_native as module
        module.BASE = BASE
        return module.main()
    if stage == "decode":
        import decode_mangonel_two_uv_native as module
        module.BASE = BASE
        module.PRIVATE_ROOT = STAGING / "smr"
        return module.main()
    if stage == "compare":
        import compare_mangonel_manual_geometry as geometry
        import compare_mangonel_uv2 as uv2
        geometry.BASE = BASE
        geometry.DECODE = BASE / "decode.json"
        geometry.READBACK = BASE / "readback.json"
        geometry.REPORT = BASE / "six-group-comparison.json"
        uv2.BASE = BASE
        uv2.REPORT = BASE / "six-group-uv2-comparison.json"
        try: first = geometry.main()
        except RuntimeError as error: first = {"status": "six_group_geometry_not_qualified", "error": str(error)}
        second = uv2.main()
        return {"geometry": first, "uv2": second}
    raise ValueError(stage)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("prepare", "cook", "readback", "decode", "compare"))
    print(json.dumps(main(ap.parse_args().stage), indent=2))
