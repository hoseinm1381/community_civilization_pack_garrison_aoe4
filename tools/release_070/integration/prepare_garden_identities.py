"""Allocate two native Vietnamese Garden attachment-list identities, isolated."""
from __future__ import annotations

import hashlib
import json
import msvcrt
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
check_storage(ROOT, CFG)
EXT = Path(CFG["external_root"])
LOCK = EXT / "output/release_020/native-build.lock"
OUT = ROOT / "output/release_070/integration/garden-identities-v1"
WORK = EXT / "staging/release_070/integration/garden-identities-v1"
PROJECT_NAME = "cc070gardenids"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(label: str, args: list[str], timeout=2100) -> None:
    proc = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    (OUT / (label + ".log")).write_text("COMMAND: " + " ".join(args) +
            f"\nEXIT: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"{label} failed; diagnostics retained")


def main() -> None:
    if OUT.exists() or WORK.exists():
        raise FileExistsError("Preserve Garden identity attempt")
    contract = ROOT / "output/release_070/integration/native-contract/contract.json"
    data = json.loads(contract.read_text())
    garden = next(a for a in data["actors"] if a["family"] == "garden")
    references = garden["references"]
    if len(references) != 2 or len({r["member"] for r in references}) != 2:
        raise RuntimeError("Expected one Garden main and one outskirts list")
    OUT.mkdir(parents=True)
    WORK.mkdir(parents=True)
    library = WORK / "library"
    project = library / "Mods" / PROJECT_NAME
    core = str(CFG["garrison_core"])
    names = ["vn070_garden_main", "vn070_garden_outskirts"]
    with LOCK.open("r+b") as stream:
        msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        try:
            run("create", [core, "mod-project", "create", "--library", str(library),
                           "--name", PROJECT_NAME], timeout=120)
            run("settings", [core, "mod-project", "settings", "--project", str(project),
                             "--live-reload", "off", "--mod-id", CFG["project_guid"]], timeout=120)
            for name, row in zip(names, references):
                source = row["member"].removeprefix("attrib/").removesuffix(".rgd")
                run("derive-" + name, [core, "mod-project", "derive", "--project", str(project),
                                       "--source", source, "--name", name], timeout=180)
            config = json.loads((project / "mod-project.json").read_text())
            if (config["game_mode"]["enabled"] or config["game_mode"]["live_reload"]
                    or len(config["derived_blueprints"]) != 2):
                raise RuntimeError("Unexpected identity project configuration")
            run("native-cook", [core, "mod-project", "cook", "--project", str(project),
                                "--editor", str(CFG["art_editor"]), "--timeout", "1800"])
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    archive = project / "dist" / (PROJECT_NAME + ".sga")
    readback = OUT / "readback"
    run("readback", [str(CFG["archive_tool"]), "extract", str(archive),
                     str(readback), "--filter", "."], timeout=600)
    generated = []
    for name, source in zip(names, references):
        member = f"attrib/attachments/attachment_lists/garrison/{PROJECT_NAME}/{name}.rgd"
        path = readback / member
        if not path.is_file():
            raise RuntimeError(f"No readback identity {member}")
        generated.append({"name": name, "source": source["member"],
                          "source_sha256": source["official_sha256"],
                          "generated_member": member, "sha256": sha(path)})
    receipt = {"schema": "ccp-070-garden-private-identity-cook/v1",
               "status": "fresh_native_identity_cook_readback_runtime_unverified",
               "contract_sha256": sha(contract), "project": str(project),
               "project_config_sha256": sha(project / "mod-project.json"),
               "archive": str(archive), "archive_sha256": sha(archive),
               "derived": generated, "active_source_modified": False}
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(OUT / "receipt.json"), "derived": len(generated)}))


if __name__ == "__main__":
    main()
