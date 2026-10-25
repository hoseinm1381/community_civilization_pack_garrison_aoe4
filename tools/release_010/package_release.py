"""Package a freshly verified integrated Garrison SGA using its strict v1 schema."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from common import CONFIG, GUID, KEY, OUT, ROOT, check_storage, read, sha, write
from source_policy import verify as verify_sources


START = '''COMMUNITY CIVILIZATION PACK 0.1.0 — houses and traps test

Close Age of Empires IV completely. In Garrison, import this ZIP and enable it.
Select Tuning Pack: Community Civilization Pack.
Select Game Mode: Community Civilization Pack.
Choose China as your civilization; choose Vietnam in the opening popup.
Keep other civilization-mod editions disabled for the first isolated test.

Check houses in Ages I, II, III and IV, including already built houses after age-up,
new houses, both normal and faster/cheaper house commands, construction, repair,
cancel, delete, damaged and destroyed states. Check two player colours and near/far.
Check both existing Explosive Trap actors: construction, completed visuals, attack,
upgrades, effects, death and the preserved four-second timer after first attack.
Confirm ordinary Chinese selection and unrelated civilizations are unchanged.

The house progression is an interpretation of northern Vietnamese village forms.
Trap timber appearance is inspired by medieval Bach Dang stakes; the portable
infantry trap arrangements are game art, not a historically documented mechanism.

This is a Garrison test release. Source/cook/readback/package checks are not native
appearance, runtime or multiplayer proof. No client installation or match was run
as part of building this ZIP. Please test in a fresh match.
'''


def package(candidate_path):
    check_storage(ROOT, CONFIG)
    candidate = read(candidate_path)
    if candidate.get('status') not in ('passed', 'verified'):
        raise ValueError('Integration candidate is not verified')
    archive = Path(candidate['archive'])
    if candidate['sha256'] != sha(archive) or candidate['project_guid'].replace('-', '') != GUID.replace('-', ''):
        raise ValueError('Final integration archive hash/identity mismatch')
    # Require independent source/archive/release test receipts, not merely a cook.
    for name in ('source-preservation.json', 'archive-verification.json', 'release-checks.json'):
        record = read(OUT / name)
        if record.get('status') not in ('passed', 'baseline-equivalent-with-known-failures'):
            raise ValueError(f'Release prerequisite did not pass: {name}')
    for name in ('archive-verification.json', 'release-checks.json'):
        record = read(OUT / name)
        if record.get('sga_sha256') != sha(archive) or record.get('candidate_sha256') != sha(candidate_path):
            raise ValueError(f'Stale release prerequisite: {name}')
    checked = read(OUT / 'release-checks.json')
    current = verify_sources(candidate['source_new_files'])
    if checked.get('source_assets_sha256') != current['source_assets_sha256']:
        raise ValueError('Source assets changed after release checks')
    destination = OUT / 'package'
    destination.mkdir(exist_ok=True)
    target = destination / (KEY + '.sga')
    if target.exists() and sha(target) != sha(archive):
        rollback = ROOT / 'archives' / ('before_010_package_' + sha(target)[:12] + '.sga')
        if not rollback.exists():
            shutil.copy2(target, rollback)
    shutil.copy2(archive, target)
    manifest = {'schema': 'garrison.mod/v1', 'bundle_key': KEY,
        'members': [{'mod_key': KEY, 'role': 'tuning', 'path': target.name, 'sha256': sha(target)}],
        'details': {'id': KEY, 'name': CONFIG['display_name'], 'version': '0.1.0',
            'summary': 'Vietnamese house models for Ages I–IV and two medieval-inspired trap models',
            'min_garrison': '0.1.4', 'content_types': ['game-mode', 'tuning-pack'],
            'updated': datetime.now(timezone.utc).date().isoformat(),
            'description': 'House donor remodels and two scratch stake trap visuals. Existing Vietnam gameplay and private identity preserved; native testing pending.'}}
    write(destination / 'garrison.json', manifest)
    (destination / 'START-HERE.txt').write_text(START, encoding='utf-8')
    evidence = {'project_guid': GUID, 'version': '0.1.0', 'sga_sha256': sha(target),
        'integration_receipt_sha256': sha(candidate_path),
        'native_runtime': 'not tested', 'multiplayer': 'not tested',
        'receipts': {name: read(OUT / name) for name in ('source-preservation.json', 'archive-verification.json', 'release-checks.json')}}
    write(destination / 'EVIDENCE.json', evidence)
    zip_path = OUT / (KEY + '-0.1.0.zip')
    if zip_path.exists():
        backup = ROOT / 'archives' / (KEY + '-0.1.0-before-' + sha(zip_path)[:12] + '.zip')
        if not backup.exists():
            shutil.copy2(zip_path, backup)
    temporary = zip_path.with_suffix('.zip.tmp')
    with ZipFile(temporary, 'w', ZIP_DEFLATED, compresslevel=6) as package_file:
        for path in sorted(destination.iterdir()):
            if path.is_file():
                package_file.write(path, path.name)
    with ZipFile(temporary) as package_file:
        assert package_file.testzip() is None
        assert package_file.namelist().count('garrison.json') == 1
        assert set(package_file.namelist()) == {target.name, 'garrison.json', 'START-HERE.txt', 'EVIDENCE.json'}
        assert hashlib.sha256(package_file.read(target.name)).hexdigest() == sha(target)
        assert json.loads(package_file.read('garrison.json')) == manifest
    temporary.replace(zip_path)
    result = {'status': 'passed', 'zip': str(zip_path), 'zip_sha256': sha(zip_path),
              'sga': str(target), 'sga_sha256': sha(target), 'version': '0.1.0',
              'candidate': str(candidate_path),
              'native_runtime': 'pending user test'}
    write(OUT / 'package-verification.json', result)
    print(json.dumps(result, indent=2))
    return result


def verify_existing(candidate_path):
    check_storage(ROOT, CONFIG)
    candidate = read(candidate_path)
    receipt = read(OUT / 'package-verification.json')
    if sha(receipt['zip']) != receipt['zip_sha256'] or sha(receipt['sga']) != receipt['sga_sha256']:
        raise ValueError('Delivered ZIP/SGA hash changed')
    if receipt['sga_sha256'] != candidate['sha256']:
        raise ValueError('Delivered SGA does not match current candidate')
    with ZipFile(receipt['zip']) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == {KEY+'.sga', 'garrison.json', 'START-HERE.txt', 'EVIDENCE.json'}
        manifest = json.loads(bundle.read('garrison.json'))
        assert manifest['schema'] == 'garrison.mod/v1'
        assert manifest['bundle_key'] == manifest['details']['id'] == KEY
        assert manifest['details']['version'] == '0.1.0'
        assert manifest['members'] == [{'mod_key':KEY,'role':'tuning','path':KEY+'.sga','sha256':candidate['sha256']}]
        assert hashlib.sha256(bundle.read(KEY+'.sga')).hexdigest() == candidate['sha256']
        evidence = json.loads(bundle.read('EVIDENCE.json'))
        assert evidence['integration_receipt_sha256'] == sha(candidate_path)
    print('Existing ZIP/manifest/SGA verification passed')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, default=OUT / 'integration/candidate.json')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    verify_existing(args.candidate) if args.verify_only else package(args.candidate)
