"""Fresh buffalo/skirmisher native cook from retained exports; no active edits."""
from pathlib import Path
import importlib.util
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/release_079'))
import common as legacy


def main(label):
    legacy.guard()
    if not re.fullmatch('[a-z0-9-]{1,8}', label):
        raise ValueError('Unsafe qualification label')
    dest = Path(legacy.CFG['external_root']) / 'output/consolidation_080/recent-units' / label
    stage = Path(legacy.CFG['external_root']) / 'staging/r80c' / ('units-' + label)
    if dest.exists() or stage.exists():
        raise FileExistsError('Preserve previous qualification')
    donors = {}
    sources = {'buffalo': ('release_0710', 'buffalo', 'r1'),
               'skirmisher2': ('release_079', '', 'r3')}
    frozen = {}
    for family, (release, branch, revision) in sources.items():
        source = ROOT / 'art/exports' / release / family / revision
        evidence = ROOT / 'output' / release
        if branch:
            evidence /= branch
        receipt = evidence / 'art' / family / revision / 'export.json'
        row = legacy.read(receipt)
        actual = {p.name: legacy.sha(p) for p in source.iterdir() if p.is_file()}
        assert row['files'] == actual
        frozen[str(source)] = actual
        target = dest / 'exports' / family / revision
        shutil.copytree(source, target)
        (dest / 'art' / family / revision).mkdir(parents=True)
        shutil.copy2(receipt, dest / 'art' / family / revision / 'export.json')
        donors[family] = legacy.read(evidence / 'donors.json')[family]
    legacy.write(dest / 'donors.json', donors)
    legacy.OUT, legacy.EXPORT = dest, dest / 'exports'
    legacy.STAGE = stage
    legacy.RECIPES = ROOT / 'art/recipes/release_079'
    sys.path.insert(1, str(ROOT / 'tools/release_076'))
    spec = importlib.util.spec_from_file_location('consolidation_recent_cook', ROOT / 'tools/release_076/cook.py')
    cook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cook)
    cook.main({'buffalo': 'r1', 'skirmisher2': 'r3'}, 'native')
    from rig_contract import read_contract, validate_contract
    for family, (_, _, revision) in sources.items():
        export = legacy.read(dest / 'art' / family / revision / 'export.json')
        body = dest / 'cooks/native/readback/art/scenario/garrison/cc076' / family
        validate_contract(read_contract((body / 'model.rgm').read_bytes()), export['donor_contract'])
    assert all({p.name: legacy.sha(p) for p in Path(source).iterdir() if p.is_file()} == hashes
               for source, hashes in frozen.items())
    legacy.write(dest / 'qualification.json', {'passed': True, 'units': list(sources),
        'native_cook_readback': True, 'rig_contracts': True, 'exports_unchanged': True,
        'native_game_tested': False})
    print('RECENT_UNIT_QUALIFICATION_PASSED', label, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
