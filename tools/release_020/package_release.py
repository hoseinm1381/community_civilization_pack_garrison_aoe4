"""Make and verify the strict one-manifest Garrison 0.2.0 ZIP."""
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from common import CONFIG, GUID, KEY, OUT, ROOT, VERSION, guarded, read, sha, write
from source_policy import verify as verify_sources

START = '''COMMUNITY CIVILIZATION PACK 0.2.0 — building visuals test

Close Age of Empires IV completely. In Garrison, import this ZIP and enable it.
Select Tuning Pack and Game Mode: Community Civilization Pack.
Choose China, then choose Vietnam in the opening popup. Disable other editions
of this civilization for the isolated test.

Check Barracks and Town Center in Ages I–IV, including existing and newly built
buildings after each age-up, the ordinary and capital Town Centers, construction,
repair, cancel, destruction, two player colours, and near/far views. Check both
farm variants alone and adjacent to other farms; their paddy edges are clearable
and may disappear at shared boundaries. Check Hideout before and after its stone
upgrade, and Economic Ministry construction and damage states. Confirm the
0.1.0 houses and both traps still work, as do ordinary Chinese buildings.

This ZIP has source, cook, archive and package checks. Import, native-match
appearance, and multiplayer behavior have not been verified by those checks.
'''


def _manifest(archive):
    return {'schema': 'garrison.mod/v1', 'bundle_key': KEY,
        'members': [{'mod_key': KEY, 'role': 'tuning', 'path': KEY + '.sga', 'sha256': sha(archive)}],
        'details': {'id': KEY, 'name': CONFIG['display_name'], 'version': VERSION,
                    'summary': 'Vietnamese Barracks, Town Center, farm, Hideout and Economic Ministry visuals',
                    'min_garrison': '0.1.4', 'content_types': ['game-mode', 'tuning-pack'],
                    'updated': datetime.now(timezone.utc).date().isoformat(),
                    'description': 'Private Vietnamese building visuals with original gameplay and 0.1.0 houses/traps retained. Native testing pending.'}}


def validate_manifest(manifest, sga_sha256):
    assert set(manifest) == {'schema', 'bundle_key', 'members', 'details'}
    assert manifest['schema'] == 'garrison.mod/v1' and manifest['bundle_key'] == KEY
    assert manifest['members'] == [{'mod_key': KEY, 'role': 'tuning',
                                    'path': KEY + '.sga', 'sha256': sga_sha256}]
    details = manifest['details']
    assert set(details) == {'id', 'name', 'version', 'summary', 'min_garrison',
                            'content_types', 'updated', 'description'}
    assert details['id'] == KEY and details['name'] == CONFIG['display_name']
    assert details['version'] == VERSION and re.fullmatch(r'\d+\.\d+\.\d+', VERSION)
    assert details['min_garrison'] == '0.1.4'
    assert details['content_types'] == ['game-mode', 'tuning-pack']
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', details['updated'])
    assert all(isinstance(details[key], str) and details[key]
               for key in ('summary', 'description'))
    assert re.fullmatch(r'[0-9a-f]{64}', sga_sha256)


def package(candidate_path):
    guarded()
    candidate_path = Path(candidate_path)
    candidate = read(candidate_path)
    archive = Path(candidate['archive'])
    assert candidate['status'] == 'passed' and sha(archive) == candidate['sha256']
    assert candidate['project_guid'].replace('-', '') == GUID.replace('-', '')
    for name in ('source-preservation.json', 'archive-verification.json', 'release-checks.json'):
        record = read(OUT / name)
        assert record['status'] in ('passed', 'baseline-equivalent-with-known-failures'), name
    for name in ('archive-verification.json', 'release-checks.json'):
        record = read(OUT / name)
        assert record['sga_sha256'] == candidate['sha256'] and record['candidate_sha256'] == sha(candidate_path), name
    source = verify_sources(candidate['source_new_files'])
    assert source['source_assets_sha256'] == read(OUT / 'release-checks.json')['source_assets_sha256']
    destination = OUT / 'package'
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / (KEY + '.sga')
    if target.exists() and sha(target) != sha(archive):
        rollback = ROOT / 'archives' / ('before_020_package_' + sha(target)[:12] + '.sga')
        if not rollback.exists(): shutil.copy2(target, rollback)
    shutil.copy2(archive, target)
    manifest = _manifest(target)
    validate_manifest(manifest, sha(target))
    write(destination / 'garrison.json', manifest)
    (destination / 'START-HERE.txt').write_text(START, encoding='utf-8')
    write(destination / 'EVIDENCE.json', {'project_guid': GUID, 'version': VERSION,
        'sga_sha256': sha(target), 'candidate_receipt_sha256': sha(candidate_path),
        'native_runtime': 'not tested', 'multiplayer': 'not tested',
        'receipts': {name: read(OUT / name) for name in
                     ('source-preservation.json', 'archive-verification.json', 'release-checks.json')}})
    zip_path = OUT / (KEY + '-' + VERSION + '.zip')
    if zip_path.exists():
        rollback = ROOT / 'archives' / (KEY + '-' + VERSION + '-before-' + sha(zip_path)[:12] + '.zip')
        if not rollback.exists(): shutil.copy2(zip_path, rollback)
    temporary = zip_path.with_suffix('.zip.tmp')
    with ZipFile(temporary, 'w', ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(destination.iterdir()):
            if path.is_file(): bundle.write(path, path.name)
    with ZipFile(temporary) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == 4
        assert set(bundle.namelist()) == {KEY + '.sga', 'garrison.json', 'START-HERE.txt', 'EVIDENCE.json'}
        assert bundle.namelist().count('garrison.json') == 1
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == sha(target)
        decoded = json.loads(bundle.read('garrison.json'))
        validate_manifest(decoded, sha(target))
        assert decoded == manifest
    temporary.replace(zip_path)
    result = {'status': 'passed', 'zip': str(zip_path), 'zip_sha256': sha(zip_path),
              'sga': str(target), 'sga_sha256': sha(target), 'candidate': str(candidate_path),
              'version': VERSION, 'manifest_schema': 'garrison.mod/v1', 'native_runtime': 'pending user test'}
    write(OUT / 'package-verification.json', result)
    print('PACKAGE_020_VERIFIED', result['zip_sha256'], result['sga_sha256'])
    return result


def verify_existing(candidate_path):
    guarded()
    candidate = read(candidate_path)
    receipt = read(OUT / 'package-verification.json')
    assert sha(receipt['zip']) == receipt['zip_sha256']
    assert sha(receipt['sga']) == receipt['sga_sha256'] == candidate['sha256']
    with ZipFile(receipt['zip']) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == 4
        assert set(bundle.namelist()) == {KEY + '.sga', 'garrison.json', 'START-HERE.txt', 'EVIDENCE.json'}
        assert all(bundle.namelist().count(name) == 1 for name in bundle.namelist())
        manifest = json.loads(bundle.read('garrison.json'))
        validate_manifest(manifest, candidate['sha256'])
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == candidate['sha256']
        assert json.loads(bundle.read('EVIDENCE.json'))['candidate_receipt_sha256'] == sha(candidate_path)
    print('EXISTING_PACKAGE_020_VERIFIED')
    return receipt


if __name__ == '__main__':
    verify_existing(sys.argv[2]) if sys.argv[1] == '--verify-only' else package(sys.argv[1])
