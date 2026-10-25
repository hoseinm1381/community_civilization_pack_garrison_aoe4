"""Validate the pinned three-LOD source with the installed Garrison validator."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import CORE, EXPORT, OUT, guard, owned, read, sha, write

SOURCE = OUT / "qualification/archer-pairing-prep/export.json"
LOG = OUT / "qualification/archer-pairing-prep/validation.log"
RECEIPT = OUT / "qualification/archer-pairing-prep/validation.json"


def main() -> None:
    guard()
    for path in (LOG, RECEIPT):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve prior validation: {path}")
    source = read(SOURCE)
    if (source["schema"] != "ccp-060-archer-paired-stock-lod-export/v1"
            or source["status"] != "source_export_only_not_validated_or_cooked"
            or source["prototype"] != "english-spearman-2"
            or source["mesh_names"] != [f"chi_ranged_bow_age02_lod{i}" for i in (1, 2, 3)]
            or source["material_names"] != [f"lod{i}" for i in (1, 2, 3)]):
        raise RuntimeError("Source export identity drift")
    folder = Path(source["folder"])
    if not folder.resolve().is_relative_to(EXPORT.resolve()):
        raise RuntimeError("Source folder escaped owned export root")
    for name, item in source["files"].items():
        path = folder / name
        if not path.is_file() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise RuntimeError(f"Source file drift: {path}")
    if sha(source["saved_blend"]) != source["saved_blend_sha256"]:
        raise RuntimeError("Saved Blender source drift")
    action = json.loads((folder / "action.json").read_text(encoding="utf-8"))
    if (action.get("prototype") != "english-spearman-2"
            or action.get("fingerprint") != source["fingerprint"]
            or action.get("material_name") != "lod1"
            or action.get("overrides") != []
            or action.get("attachments") != []
            or len(action.get("bones", [])) != 48):
        raise RuntimeError("Prototype action contract drift")
    command = [str(CORE), "mod-project", "unit-validate", "--source", str(folder / "action.json")]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=180)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                   + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
                   encoding="utf-8")
    write(RECEIPT, {"schema": "ccp-060-archer-paired-stock-lod-validation/v1",
                    "status": "passed" if result.returncode == 0 else "rejected",
                    "source_receipt": str(SOURCE), "source_receipt_sha256": sha(SOURCE),
                    "action_sha256": sha(folder / "action.json"), "exit_code": result.returncode,
                    "log": str(LOG), "log_sha256": sha(LOG),
                    "scope": "installed action validator; FBX three-LOD native cook remains separate"})
    print(json.dumps({"status": "passed" if result.returncode == 0 else "rejected",
                      "exit_code": result.returncode, "log": str(LOG),
                      "stdout": result.stdout[-2500:], "stderr": result.stderr[-2500:]}, indent=2))
    if result.returncode:
        raise RuntimeError("Installed unit-validate rejected source")


if __name__ == "__main__":
    main()
