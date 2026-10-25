"""Fail ports whose runtime archive namespace differs from the project GUID."""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]

def check(root, archive=None):
    cfg = json.loads((root / 'workspace.json').read_text())
    expected = cfg['project_guid'].replace('-', '').lower()
    project = ET.parse(root / cfg['project_file']).getroot()
    assert project.find('{*}ID').text.replace('-', '').lower() == expected
    manifest = ET.parse(root / 'assets/attrib/community_civilization_pack.xml').getroot()
    assert manifest.get('guid').lower() == expected
    burn = ET.parse(root / 'assets/_default.burnproj').getroot()
    names = [x.text for x in burn.iter() if x.tag.endswith('}NiceName')]
    assert names == [expected], f'Archive NiceName {names} differs from runtime GUID {expected}'
    if archive:
        listing = json.loads(subprocess.check_output([cfg['archive_tool'], 'list', str(archive), '--verify'], text=True))
        assert listing['archive']['name'].lower() == expected, f"SGA namespace {listing['archive']['name']} differs from {expected}"
        assert listing['archive']['verification']['verified']
    return expected

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    print('Identity verified:', check(args.root, args.archive))
