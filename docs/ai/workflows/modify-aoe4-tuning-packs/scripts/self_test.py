#!/usr/bin/env python3
"""Build and validate a minimal temporary Attribute Editor tuning pack."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


GUID = "11111111-2222-3333-4444-555555555555"


def guid_parts(value: str) -> list[int]:
    data = uuid.UUID(value).bytes_le
    return [int.from_bytes(data[offset : offset + 4], "little") for offset in range(0, 16, 4)]


def write_fixture(root: Path) -> None:
    assets = root / "assets"
    attrib = assets / "attrib"
    instances = attrib / "instances" / "weapon"
    locdb = assets / "locdb"
    instances.mkdir(parents=True)
    locdb.mkdir(parents=True)
    parts = guid_parts(GUID)
    (root / "fixture.aoe4mod").write_text(
        """<Mod>
  <DataGenericPath>assets</DataGenericPath>
  <DataIntermediatePath>cache</DataIntermediatePath>
  <ID>11111111-2222-3333-4444-555555555555</ID>
  <LocDBPath>locdb\\fixture.locdb</LocDBPath>
  <Type>Extension</Type>
</Mod>
""",
        encoding="utf-8",
    )
    (attrib / "fixture.xml").write_text(
        '<mod guid="11111111222233334444555555555555" locdb_path="..\\locdb\\fixture.locdb" override_instances="True" />\n',
        encoding="utf-8",
    )
    (locdb / "fixture.locdb").write_text(
        """<Metadata><Locales><Locale><Name>en</Name></Locale></Locales></Metadata>
""",
        encoding="utf-8",
    )
    (locdb / "fixture_en.csv").write_text(
        "ID,Text\n1,Fixture Name\n2,Fixture Description\n",
        encoding="utf-8",
    )
    reflect = "".join(
        f"<DataProperty Name=\"m_modPart{index}\" Value=\"{part}\"/>"
        for index, part in enumerate(parts)
    )
    (assets / "mod.rdo").write_text(
        f"""<DataWarehouse>
  <DataObject Type=\"util::ReflectLocString\">{reflect}<DataProperty Name=\"m_locStringKey\" Value=\"1\"/></DataObject>
  <DataObject Type=\"util::ReflectLocString\">{reflect}<DataProperty Name=\"m_locStringKey\" Value=\"2\"/></DataObject>
</DataWarehouse>
""",
        encoding="utf-8",
    )
    (instances / "fixture.xml").write_text(
        """<instance version="6" template="weapon">
  <uniqueid name="pbgid" value="1073741825" />
  <instance_reference name="parent_pbg" value="weapon\\races\\common\\melee\\weapon_spearman_2" />
  <group name="weapon_bag"><group name="damage"><float name="min" value="1" overrideParent="True" /><float name="max" value="1" overrideParent="True" /></group></group>
</instance>
""",
        encoding="utf-8",
    )


def main() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    validator = skill_root / "scripts" / "validate_tuning_pack.py"
    with tempfile.TemporaryDirectory(prefix="aoe4_tuning_skill_") as directory:
        project = Path(directory)
        write_fixture(project)
        result = subprocess.run(
            [sys.executable, str(validator), str(project), "--strict", "--json", "-"],
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    report = json.loads(result.stdout)
    if report["summary"]["errors"] or report["summary"]["warnings"]:
        print(result.stdout)
        return 1
    print("Tuning-pack skill self-test passed: minimal project validates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
