"""Rebuild retained older and recent assets; restores only named dependencies."""
import argparse
from common import *
from store import ResourceStore, owned_key


def ensure_prefix(prefixes):
    restored = []
    if not (STORE / 'index.json').exists():
        return restored
    doc = read(STORE / 'index.json')
    store = ResourceStore(STORE / doc['bundle'], doc['files'], ROOTS)
    try:
        for key in store.index:
            if any(key.startswith(prefix) for prefix in prefixes):
                target = ROOTS[key[0]] / key[2:]
                if not target.exists():
                    restored.append(str(store.restore(key)))
    finally:
        store.close()
    return restored


def main(label):
    guard()
    safe_label(label)
    if len(label) > 8:
        raise ValueError('Asset label must be at most eight characters')
    log = OUT / 'asset-qualification' / label
    if log.exists():
        raise FileExistsError('Use a new qualification label')
    log.mkdir(parents=True)
    sources = {p.relative_to(ROOT).as_posix(): sha(p) for p in walk(ROOT / 'assets')}
    prefixes = ['F/output/release_0710/buffalo/art/buffalo/r1/',
                'F/output/release_0710/buffalo/donors.json',
                'F/output/release_079/art/skirmisher2/r3/',
                'F/output/release_079/donors.json']
    specs = read(EXT / 'consolidation_071/geometry-specs.json')
    old = next(x for x in specs if x['model'] == 'archer4')['inputs']
    for field in ('template_body', 'template_project'):
        prefixes.append(owned_key(old[field], ROOTS).rstrip('/') + '/')
    restored = ensure_prefix(prefixes)
    write(log / 'restored-inputs.json', restored)
    run('older-unit', [CFG['python'], '-B', ROOT / 'tools/release_071/qualify_assets.py',
        'unit', '--label', label, '--model', 'archer4'], log, timeout=1800)
    old_receipt = EXT / 'output/release_071' / ('unit-' + label) / 'receipt.json'
    assert read(old_receipt)['passed']
    run('recent-units', [CFG['blender_python'], '-B', ROOT / 'tools/consolidation_080/recent_units.py', label], log, timeout=2100)
    recent = OUT / 'recent-units' / label / 'qualification.json'
    assert read(recent)['passed']
    # Stone branch cooks without the historical default branch's PBG allocation write.
    run('hideout', [CFG['blender_python'], '-B', ROOT / 'tools/release_0710/hideout_run.py',
        'cook', 'stone', label], log, timeout=2100)
    hideout = EXT / 'output/release_0710/hideout' / ('cook-stone-' + label + '.json')
    assert read(hideout)['fresh_native_cook']
    assert all(sha(ROOT / n) == h for n, h in sources.items())
    write(log / 'receipt.json', {'passed': True, 'old_unit': str(old_receipt),
          'recent_units': str(recent), 'building': str(hideout),
          'active_source_unchanged': True, 'restored_inputs': len(restored),
          'native_game_tested': False})
    print('ASSET_QUALIFICATION_PASSED', label, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('label')
    args = p.parse_args()
    if not args.label.replace('-', '').isalnum() or len(args.label) > 8:
        raise ValueError('Invalid qualification label')
    main(args.label)
