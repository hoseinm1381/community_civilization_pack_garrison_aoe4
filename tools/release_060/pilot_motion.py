"""Read exact linked stock idle clips for isolated pilot composition previews."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import CORE, OUT, guard, owned, read, sha, write
from pilot_decode import CONFIG, INDEX

CHOICES = {"spear2": 136, "horseman2": 372, "elephant": 55}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", required=True, choices=CHOICES)
    args = parser.parse_args()
    guard()
    donor = read(OUT / "pilots/pilot-decodes.json")["pilots"][args.pilot]
    manifest = Path(donor["manifest"])
    if sha(manifest) != donor["manifest_sha256"]:
        raise RuntimeError("Exact donor decode changed")
    plan = read(manifest)["animated_asset_import_plan"]["layers"]["animation"]
    source = plan["source"]
    index = CHOICES[args.pilot]
    clip = next((c for c in plan["clips"] if c["index"] == index), None)
    if clip is None or clip.get("status") != "ready_for_animation_clip_projection":
        raise RuntimeError(f"Linked stock idle clip unavailable: {args.pilot}/{index}")
    folder = owned(OUT / "pilots" / args.pilot / "animation")
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / (source["rhka_sha256"][:16] + f"-{index}.json")
    receipt = folder / (source["rhka_sha256"][:16] + f"-{index}-receipt.json")
    identity = {"rhka_logical_path": source["rhka_logical_path"],
                "rhka_sha256": source["rhka_sha256"], "clip_index": index,
                "clip_name": clip["name"], "manifest_sha256": sha(manifest),
                "config_sha256": sha(CONFIG), "index_sha256": sha(INDEX)}
    if dest.is_file() and receipt.is_file():
        old = read(receipt)
        if old.get("source_identity") == identity and old.get("payload_sha256") == sha(dest):
            print(json.dumps({"pilot": args.pilot, "status": "verified_existing", "path": str(dest)}))
            return
    result = subprocess.run([str(CORE), "-m", "src.core.animation_clip",
                             "--logical-path", source["rhka_logical_path"],
                             "--clip-index", str(index), "--expected-sha256", source["rhka_sha256"],
                             "--config", str(CONFIG), "--index", str(INDEX),
                             "--output", str(dest)], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode or not dest.is_file():
        raise RuntimeError(f"Native stock clip sample failed: {result.returncode}; "
                           f"{result.stderr[-1600:]} {result.stdout[-400:]}")
    payload = read(dest)
    write(receipt, {"schema": "ccp-060-stock-clip-receipt/v1",
                    "source_identity": identity, "payload_sha256": sha(dest),
                    "payload_status": payload.get("status")})
    print(json.dumps({"pilot": args.pilot, "status": payload.get("status"),
                      "path": str(dest), "bytes": dest.stat().st_size}))


if __name__ == "__main__":
    main()
