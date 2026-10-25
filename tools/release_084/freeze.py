"""Freeze current 083 delivery and editable input hashes without rewriting history."""
from pathlib import Path
import json
import subprocess
import sys
from pipeline import digest, save_json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/release_084'
CFG = json.loads((ROOT / 'workspace.json').read_text())


def main():
    sys.path.insert(0, str(ROOT / 'tools'))
    from workspace_support import check_storage
    check_storage(ROOT, CFG)
    base = ROOT / 'output/release_083/delivery/final-v2'
    sga = base / 'community_civilization_pack.sga'
    package = base / 'community_civilization_pack-0.8.3.zip'
    assert digest(sga) == '85abef75f6c0ea5ccb1236140e97895232b061fbf1e50db81d7edc90252ac034'
    assert digest(package) == '08f7129c7f200b47f83b48a8a33bc1a46a4923c70c01b9237d4fa91da8cccd2c'
    sys.path.insert(0, str(ROOT / 'tools/release_073'))
    from check_identity import check
    check(ROOT, sga)
    target = OUT / 'baseline.json'
    if target.exists():
        baseline = json.loads(target.read_text())
        assert all(digest(p) == h for p, h in baseline['protected'].items())
        print('084_BASELINE_RECHECK_PASSED', len(baseline['protected']))
        return
    listing = json.loads(subprocess.check_output([CFG['archive_tool'], 'list', str(sga), '--verify']))
    protected = {}
    for folder in [ROOT.parent/'Community_civilization_pack_normal', ROOT/'assets', ROOT/'art/authoring', ROOT/'art/exports', ROOT/'art/recipes']:
        for p in folder.rglob('*'):
            if p.is_file():
                protected[str(p)] = digest(p)
    save_json(target, dict(sga=str(sga), sga_sha256=digest(sga), zip=str(package), zip_sha256=digest(package), listing=listing, protected=protected))
    print('084_BASELINE_FROZEN', len(protected))


if __name__ == '__main__':
    main()
