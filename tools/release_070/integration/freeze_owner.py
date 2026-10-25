"""Pin exact official main render owner and native RGO before private art graft."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
sys.path.insert(0, CFG["garrison_extension"])
sys.path.insert(0, str(ROOT / "tools/release_010"))
import integration as native

CONTRACT = ROOT / "output/release_070/integration/native-contract/contract.json"
OUT = ROOT / "output/release_070/integration/native-owner"
native.CACHEWORK = OUT / "official-cache"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    if (OUT / "owners.json").exists():
        raise FileExistsError("Preserve prior owner freeze")
    OUT.mkdir(parents=True, exist_ok=True)
    source = json.loads(CONTRACT.read_text())
    rows = []
    for actor in source["actors"]:
        primary = next(ref for ref in actor["references"] if "/outskirts/" not in ref["member"])
        stamp = primary["stamps"][0]
        bodies = [v for v in stamp["visuals"] if
                  (v["model"].startswith("art/civilizations/chinese/structures/") or
                   v["model"].startswith("art/civilizations/chinese_ha_01/structures/"))]
        if len(bodies) != 1:
            raise RuntimeError(f"Expected exactly one main native body: {actor['family']}")
        body = bodies[0]
        media = {}
        for suffix in (".rgm", ".rgo"):
            model = native.stock(body["model"] + suffix)
            media[suffix] = {"path": str(model), "sha256": sha(model), "bytes": model.stat().st_size}
        rows.append({"family": actor["family"], "main_stamp": stamp["member"],
                     "main_stamp_sha256": stamp["sha256"], "body_id": body["id"],
                     "stock_model": body["model"], "stock_transform": body["transform"],
                     "native_media": media})
    result = {"schema": "ccp-070-native-model-owner-freeze/v1",
              "contract_sha256": sha(CONTRACT), "owners": rows,
              "policy": "Retain stock RGO and native marker fields; only replace private Vietnamese visual model."}
    (OUT / "owners.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"owners": len(rows), "receipt": str(OUT / "owners.json")}))


if __name__ == "__main__":
    main()
