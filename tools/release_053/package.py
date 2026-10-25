"""Finalize the already compiled 052-C payload as the user-requested 0.5.3.

No native cook, Blender operation, client installation or match test is performed.
Earlier releases and diagnostic receipts are immutable inputs.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import configuration, check_storage

CFG = configuration(ROOT)
EXT = Path(CFG['external_root'])
OUT = EXT / 'output/release_053'
PREV = EXT / 'output/release_052'
KEY = CFG['package_key']
ABILITY = 'attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'
EXPECTED_C = '250145a7ec9acada187dab72c1f3b64f28577fe6db552c427d353a81c744fcdd'
EXPECTED_SGA = 'af202bcb644b4a8c74ff4a598a5374fff7c7a3df47457f3eee5c2195509b6456'


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def write(p, value):
    p = Path(p)
    assert p.resolve().is_relative_to(OUT.resolve()) or p.resolve().is_relative_to((ROOT / 'art/recipes/release_053').resolve())
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def inventory(root):
    result = {}
    root = Path(root)
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in list(dirs):
            p = Path(current) / name
            assert not p.is_symlink() and not p.is_junction(), p
            if name == '__pycache__':
                dirs.remove(name)
        for name in names:
            p = Path(current) / name
            assert not p.is_symlink(), p
            result[p.relative_to(root).as_posix()] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    return result


def preservation(expected_ability):
    check_storage(ROOT, CFG)
    old = read(PREV / 'baseline/freeze.json')['inputs']
    assets = inventory(ROOT / 'assets')
    expected = dict(old['assets'])
    expected[ABILITY] = {'sha256': expected_ability, 'bytes': (ROOT / 'assets' / ABILITY).stat().st_size}
    assert assets == expected, 'Unexpected active source changes'
    assert inventory(CFG['source_root']) == old['normal'], 'Normal edition changed'
    assert inventory(ROOT / 'tests') == old['tests'], 'Historical tests changed'
    assert all(sha(ROOT / p) == digest for p, digest in old['identities'].items())
    additions = {}
    for category in ('art', 'tools'):
        for name, frozen in old[category].items():
            root = ROOT / 'art' / name if category == 'art' else ROOT / 'tools' / name
            now = inventory(root)
            assert all(now.get(p) == meta for p, meta in frozen.items()), (category, name, 'old input changed')
            new = set(now) - set(frozen)
            assert category == 'art' and all(p.startswith(('release_052/', 'release_053/', 'release_060/')) for p in new) or not new
            additions[category + '/' + name] = len(new)
    roots = {p.name for p in (ROOT / 'tools').iterdir() if p.is_dir() and p.name != '__pycache__'}
    assert roots - set(old['tools']) <= {'release_052', 'release_053', 'release_060'}
    return {'status': 'passed', 'active_source_allowlist': [ABILITY], 'normal_edition_exact': True,
            'historical_art_tools_tests_identity_exact': True, 'new_namespace_file_counts': additions,
            'concurrent_060': 'Excluded from release; no files modified by 053'}


def archive_listing(path):
    run = subprocess.run([CFG['archive_tool'], 'list', str(path), '--verify'], capture_output=True, text=True, check=True)
    data = json.loads(run.stdout)
    assert data['archive']['verification']['verified']
    assert data['archive']['name'].replace('-', '').lower() == CFG['project_guid'].replace('-', '').lower()
    names = [r['path'] for r in data['members']]
    assert len(names) == len(set(n.casefold() for n in names))
    return data


def main():
    check_storage(ROOT, CFG)
    assert not (OUT / 'package-verification.json').exists(), 'Preserve completed release'
    test_zip = PREV / (KEY + '-0.5.2-test-c.zip')
    assert sha(test_zip) == EXPECTED_C
    candidate = read(PREV / 'diagnostic-c/receipt.json')
    assert sha(candidate['archive']) == EXPECTED_SGA
    overlay = read(PREV / 'stealth/diagnostic-c/receipt.json')
    assert sha(overlay['overlay']['file']) == overlay['overlay']['sha256']
    source = ROOT / 'assets' / ABILITY
    assert sha(source) == overlay['baseline']['sha256']
    preservation(overlay['baseline']['sha256'])
    native = candidate['native_stealth_source_cook']
    assert native['native_run']['exit_code'] == 0 and native['native_run']['status'] == 'succeeded'
    assert sha(native['archive']) == native['archive_sha256']
    assert native['validated_instances'] == 280 and len(native['compiled_changes']) == 3
    OUT.mkdir(parents=True, exist_ok=True)
    original = OUT / 'baseline' / ABILITY
    original.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, original)
    rollbacks = {}
    for version in ('040', '050', '051'):
        folder = EXT / 'output' / ('release_' + version)
        for p in folder.glob('*.zip'):
            rollbacks[str(p)] = sha(p)
    write(OUT / 'baseline/receipt.json', {'frozen_051': str(PREV / 'baseline/freeze.json'),
          'test_c_sha256': EXPECTED_C, 'source_before': sha(original), 'rollback_zips': rollbacks})
    package = OUT / 'package'
    package.mkdir()
    sga = package / (KEY + '.sga')
    shutil.copy2(candidate['archive'], sga)
    assert sha(sga) == EXPECTED_SGA
    baseline = Path(read(PREV / 'baseline/freeze.json')['baseline_sga'])
    a, b = archive_listing(baseline), archive_listing(sga)
    assert a['archive']['tocs'] == b['archive']['tocs']
    names = {r['path'] for r in a['members']}
    assert names == {r['path'] for r in b['members']} and len(names) == 811
    old_back = PREV / 'diagnostic-a/readback/baseline051'
    new_back = PREV / 'diagnostic-c/readback'
    changed = sorted(n for n in names if sha(old_back / n) != sha(new_back / n))
    assert changed == candidate['changed_members'] and len(changed) == 4
    payloads = []
    for row in candidate['payloads']:
        target = OUT / 'payload' / row['member']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(row['file'], target)
        assert sha(target) == row['sha256'] == sha(new_back / row['member'])
        payloads.append({'member': row['member'], 'file': str(target), 'sha256': sha(target)})
    edit = OUT / 'source-overlay' / ABILITY
    edit.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(overlay['overlay']['file'], edit)
    # Final-release source matches the successfully compiled isolated overlay.
    assert sha(source) == overlay['baseline']['sha256']
    shutil.copy2(edit, source)
    keep = preservation(overlay['overlay']['sha256'])
    assert all(sha(p) == digest for p, digest in rollbacks.items())
    write(OUT / 'preservation.json', keep)
    recipe = {'schema': 'ccp.release053.integration/v1', 'version': '0.5.3', 'base': str(baseline),
              'base_sha256': sha(baseline), 'payloads': payloads, 'source_overlay': str(edit),
              'source_overlay_sha256': sha(edit), 'source_native_receipt': str(PREV / 'stealth/native/rsc03/receipt.json'),
              'material_recipe': str(ROOT / 'art/recipes/release_052/landmarks/options-z1.json'),
              'active_source': str(source), 'live_reload': False}
    write(ROOT / 'art/recipes/release_053/integration.json', recipe)
    evidence = {'schema': 'ccp.release053.evidence/v1', 'version': '0.5.3', 'is_final_release': True,
                'release_basis': 'Existing 052-C compiled payload, finalized at explicit user request without another native test',
                'sga_sha256': sha(sga), 'baseline_sga_sha256': sha(baseline),
                'archive_members': len(names), 'changed_members': changed, 'unchanged_members': 807,
                'added_members': [], 'removed_members': [], 'payloads': payloads,
                'archer_traps_monastery': 'Byte-identical to 0.5.1', 'preservation': keep,
                'source_native_cook': {'status': 'succeeded', 'exit_code': 0, 'validated_instances': 280,
                    'archive_sha256': native['archive_sha256'], 'compiled_changes': native['compiled_changes']},
                'native_match': 'Not performed; user requested final release without a further test gate',
                'runtime_limits': ['Custom landmark material visibility remains unconfirmed in a native match',
                    'Automatic stealth retains its ten-second native graph; continuity remains unconfirmed'],
                'recipe': str(ROOT / 'art/recipes/release_053/integration.json')}
    write(package / 'EVIDENCE.json', evidence)
    with ZipFile(test_zip) as z:
        manifest = json.loads(z.read('garrison.json'))
    manifest['details'].update(version='0.5.3', updated='2026-10-18',
        summary='Castle landmark materials and automatic villager stealth update',
        description='Vietnamese Castle landmark material settings aligned with stock buildings; automatic villager stealth scheduling adjusted. Archer activated stealth, traps and monastery preserved.',
        changelog='Updated both Castle landmark materials and automatic villager stealth scheduling. Preserved activated archer stealth and accepted trap/monastery changes.')
    assert manifest['details']['author'] == 'hosein81 and chilly5'
    assert manifest['members'][0]['sha256'] == sha(sga)
    write(package / 'garrison.json', manifest)
    (package / 'START-HERE.txt').write_text('''COMMUNITY CIVILIZATION PACK 0.5.3
Credits: hosein81 and chilly5

Close AoE4, import this ZIP into Garrison and enable the pack. Select Community
Civilization Pack as both Game Mode and Tuning Pack. Choose China, then Vietnam.

Includes the custom Castle landmark material update and automatic villager
stealth scheduling adjustment. Activated archer stealth, traps and monastery
are unchanged from 0.5.1. This final package supersedes the 0.5.2 diagnostics.

Finalized at the user's request without another in-game acceptance test.
Native compilation and package checks passed; in-game behavior is unverified.
Prior 0.5.1 and 0.4.0 packages remain available for rollback.
''', encoding='utf-8')
    target = OUT / (KEY + '-0.5.3.zip')
    assert not target.exists()
    members = ['garrison.json', KEY + '.sga', 'START-HERE.txt', 'EVIDENCE.json']
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=6) as z:
        for name in members:
            info = ZipInfo(name, date_time=(2026, 10, 18, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o644 << 16
            z.writestr(info, (package / name).read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=6)
    with ZipFile(target) as z:
        assert z.testzip() is None and z.namelist() == members
        assert sum(Path(n).name == 'garrison.json' for n in z.namelist()) == 1
        assert all(z.read(n) == (package / n).read_bytes() for n in members)
    assert sha(test_zip) == EXPECTED_C and all(sha(p) == digest for p, digest in rollbacks.items())
    write(OUT / 'archive-inventory.json', b)
    write(OUT / 'package-verification.json', {'status': 'passed', 'is_final_release': True, 'version': '0.5.3',
          'zip': str(target), 'zip_sha256': sha(target), 'bytes': target.stat().st_size,
          'sga_sha256': sha(sga), 'archive_members': 811, 'changed_members': changed, 'unchanged_members': 807,
          'native_match': evidence['native_match'], 'cleanup': 'No regenerable 053 cook/readback caches created; 052 rebuild dependencies retained',
          'reclaimed_bytes': 0})
    print(json.dumps(read(OUT / 'package-verification.json'), indent=2))


if __name__ == '__main__':
    main()
