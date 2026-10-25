"""Metadata-only 0.8.0 package: never substitute a source-only native archive."""
import hashlib
import shutil
import zipfile
from common import *


def verify_package(path, expected_zip, expected_native):
    if sha(path) != expected_zip:
        raise ValueError('Current delivery ZIP hash changed')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != 3 or set(names) != {'garrison.json', 'community_civilization_pack.sga', 'START-HERE.txt'} or z.testzip() is not None:
            raise ValueError('Delivery ZIP layout/CRC failed')
        manifest = json.loads(z.read('garrison.json'))
        key = 'community_civilization_pack'
        if (manifest.get('schema') != 'garrison.mod/v1' or manifest.get('bundle_key') != key
                or manifest.get('details', {}).get('version') != '0.8.0'
                or manifest['details'].get('id') != key
                or manifest['details'].get('author') != 'hosein81 and chilly5'
                or manifest.get('members') != [{'mod_key': key, 'role': 'tuning',
                    'path': key + '.sga', 'sha256': expected_native}]):
            raise ValueError('Delivery metadata contract failed')
        with z.open(key + '.sga') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != expected_native:
                raise ValueError('Embedded native archive differs from accepted 0.7.12')
    return manifest


def package(label):
    guard()
    safe_label(label)
    frozen = read(TX / 'active-source-freeze.json')
    assert all(sha(ROOT / name) == digest for name, digest in frozen.items()), \
        '0.8.0 is a preservation release; source edits require a new changed-resource release policy'
    archive = BASE / 'community_civilization_pack.sga'
    assert sha(archive) == EXPECTED
    run('identity-package-' + label, [CFG['python'], ROOT / 'tools/release_073/check_identity.py',
                                    '--archive', archive])
    dest = OUT / 'delivery' / label
    if dest.exists():
        raise FileExistsError('Immutable delivery exists: ' + str(dest))
    dest.mkdir(parents=True)
    manifest = read(BASE / 'garrison.json')
    manifest['details'].update(version='0.8.0', updated='2026-10-24',
        summary='Garrison development consolidation; preserves 0.7.12 game content.',
        description='All 0.7.12 gameplay, visuals, HUD and animations preserved. '
                    'Editable assets and recovery inputs retained for continued development.',
        changelog='Storage and rebuild consolidation only. No gameplay or visual changes.')
    manifest['members'][0]['sha256'] = EXPECTED
    write(dest / 'garrison.json', manifest)
    text = ('Community Civilization Pack Garrison 0.8.0\nCredits: hosein81 and chilly5\n'
            'Storage and rebuild consolidation. Game archive is byte-identical to 0.7.12.\n'
            'Import through Garrison, enable the pack and select its tuning pack and Vietnam game mode.\n'
            'Development: see docs/DEVELOPMENT_080.md in the retained workspace.\n'
            'No installation or publication performed. Runtime, save/load and multiplayer checks remain separate.\n')
    (dest / 'START-HERE.txt').write_text(text, encoding='utf-8')
    path = dest / 'community_civilization_pack-0.8.0.zip'
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, source in [('garrison.json', dest / 'garrison.json'),
                             ('community_civilization_pack.sga', archive),
                             ('START-HERE.txt', dest / 'START-HERE.txt')]:
            info = zipfile.ZipInfo(name, (2026, 10, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            with source.open('rb') as inp, z.open(info, 'w') as output:
                shutil.copyfileobj(inp, output, 1024 * 1024)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {'garrison.json', 'community_civilization_pack.sga', 'START-HERE.txt'}
        assert json.loads(z.read('garrison.json'))['details']['version'] == '0.8.0'
        with z.open('community_civilization_pack.sga') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == EXPECTED
    verify_package(path, EXPECTED_ZIP, EXPECTED)
    listing = json.loads(run('list-package-' + label,
        [CFG['archive_tool'], 'list', archive, '--verify']))
    before = read(BASE / 'verification.json')
    assert {m['path']: m['toc'] for m in listing['members']} == before['mounts']
    write(dest / 'verification.json', before | {'version': '0.8.0', 'changed': [],
          'added': [], 'baseline_sha256': EXPECTED, 'archive_byte_identical': True})
    proof = {'version': '0.8.0', 'zip': str(path), 'zip_sha256': sha(path),
             'sga_sha256': EXPECTED, 'verified': True, 'members': len(before['mounts']),
             'changed_members': 0, 'all_mounts_preserved': True,
             'installed': False, 'published': False, 'native_game_tested': False}
    write(dest / 'delivery-proof.json', proof)
    print('PACKAGE_VERIFIED', json.dumps(proof), flush=True)
    return proof


if __name__ == '__main__':
    package(sys.argv[1])
