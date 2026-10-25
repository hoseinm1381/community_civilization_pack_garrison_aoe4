"""Strict 0.4.0 selective native archive composition and Garrison delivery."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from common import ROOT, OUT, ARCH, CONFIG, KEY, GUID, VERSION, guarded, read, run_logged, sha, write
from source_policy import verify as verify_source

BASELINE = ROOT / 'archives/release_030_user_accepted/community_civilization_pack.sga'
WORK = OUT / 'integration'


def listing(archive):
    result = subprocess.run([str(ARCH), 'list', str(archive), '--verify'],
                            capture_output=True, text=True, check=True)
    index = json.loads(result.stdout)
    assert index['archive']['verification']['verified']
    assert index['archive']['name'].replace('-', '').lower() == GUID.replace('-', '').lower()
    return index


def unpack(archive, label):
    destination = OUT / 'readback' / (label + '-' + sha(archive)[:12])
    if not (destination / '.complete.json').exists():
        assert not destination.exists(), f'Incomplete readback retained: {destination}'
        run_logged('unpack040-' + label, [ARCH, 'unpack', archive, '--output', destination])
        write(destination / '.complete.json', {'archive_sha256': sha(archive)})
    assert read(destination / '.complete.json')['archive_sha256'] == sha(archive)
    return destination


def market_compiled_identity_proof():
    from native_source import MARKET, market_identity_proof, attachment_identity_proof
    pointer = read(OUT / 'native-source/current.json')
    assert sha(pointer['receipt']) == pointer['sha256']
    native = read(pointer['receipt'])
    compiled = Path(pointer['receipt']).parent / 'compiled-identity' / MARKET
    assert sha(native['archive']) == native['archive_sha256']
    audit = OUT / 'native-source/market-audit' / native['archive_sha256'] / MARKET
    if not audit.exists():
        audit.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(ARCH), 'extract-member', native['archive'], MARKET, str(audit)],
                       capture_output=True, check=True)
    assert sha(audit) == sha(compiled)
    proof = market_identity_proof(compiled)
    if MARKET in native['compiled_proofs']:
        assert all(proof[key] == value for key, value in native['compiled_proofs'][MARKET].items())
    attachments = attachment_identity_proof(native['archive'],
        Path(pointer['receipt']).parent / 'compiled-identity')
    if 'compiled_attachment_identities' in native:
        assert native['compiled_attachment_identities'] == attachments
    proof['compiled_attachment_identities'] = attachments
    return proof


def payloads():
    from art_qa import verify as verify_art_qa
    assert verify_art_qa()['status'] == 'passed_offline_qa'
    landmark = read(WORK / 'landmark-media.json')
    buildings = read(WORK / 'building-media.json')
    details = read(WORK / 'building-details-media.json')
    reference = read(WORK / 'reference-cook.json')
    detail_reference = read(WORK / 'detail-reference-cook.json')
    native_pointer = read(OUT / 'native-source/current.json')
    assert sha(native_pointer['receipt']) == native_pointer['sha256']
    native = read(native_pointer['receipt'])
    market_compiled_identity_proof()
    assert landmark['status'] == buildings['status'] == details['status'] == native['status'] == reference['status'] == detail_reference['status'] == 'passed'
    assert reference['exact_inputs_sha256'] == {r['member']: r['sha256'] for r in landmark['payloads']
        if r['member'].startswith('art/scenario/cc040/')}
    assert detail_reference['exact_inputs_sha256'] == {r['member']: r['sha256'] for r in details['payloads']
        if r['member'].startswith('art/scenario/garrison/community_040_details/')}
    overrides = {r['member']: r for r in details['list_overrides']}
    assert len(overrides) == 12
    base_buildings = [r for r in buildings['payloads'] if r['member'] not in overrides]
    assert len(buildings['payloads']) - len(base_buildings) == 12
    rows = landmark['payloads'] + base_buildings + details['payloads'] + list(overrides.values()) + native['payloads']
    assert len({row['member'] for row in rows}) == len(rows)
    for row in rows:
        assert sha(row['file']) == row['sha256']
    locale = next(row for row in native['payloads'] if row['member'] == 'en/en.ucs')
    locale_raw = Path(locale['file']).read_bytes()
    for required in ('hosein81', 'chilly5', 'youtube.com/@aoe4kingdom', 'youtube.com/@ChillyEmpire'):
        assert required.encode('utf-16le') in locale_raw, required
    return rows


def compose(label):
    guarded()
    assert verify_source()['status'] == 'passed'
    assert read(WORK / 'reference-cook.json')['status'] == 'passed'
    assert read(OUT / 'landmark-lifecycle-contract.json')['status'] == 'passed_static_native_graph'
    rows = payloads()
    target = OUT / 'candidates' / label / (KEY + '.sga')
    assert not target.exists()
    target.parent.mkdir(parents=True)
    current = BASELINE
    for alias, selected in (
        ('data', [r for r in rows if r['member'].startswith('art/')]),
        ('attrib', [r for r in rows if r['member'].startswith('attrib/')]),
        ('locale', [r for r in rows if r['member'].startswith('en/')]),
    ):
        assert selected, alias
        mapping = target.parent / (alias + '-members.txt')
        mapping.write_text(''.join(r['member'] + '=' + r['file'] + '\n' for r in selected), encoding='utf-8')
        destination = target if alias == 'locale' else target.parent / (alias + '-stage.sga')
        run_logged('compose040-' + label + '-' + alias,
                   [ARCH, 'set-members', current, mapping, destination, '--alias', alias])
        current = destination
    receipt = {'status': 'passed', 'archive': str(target), 'sha256': sha(target),
               'baseline_sha256': sha(BASELINE), 'payloads': rows,
               'reference_sha256': sha(WORK / 'reference-cook.json'),
               'detail_reference_sha256': sha(WORK / 'detail-reference-cook.json'),
               'native_source_sha256': read(OUT / 'native-source/current.json')['sha256'],
               'project_guid': GUID}
    write(OUT / 'candidate.json', receipt)
    return receipt


def verify():
    guarded()
    candidate = read(OUT / 'candidate.json')
    archive = Path(candidate['archive'])
    assert sha(archive) == candidate['sha256']
    assert sha(BASELINE) == candidate['baseline_sha256']
    assert verify_source()['status'] == 'passed'
    before_index, after_index = listing(BASELINE), listing(archive)
    assert before_index['archive']['tocs'] == after_index['archive']['tocs']
    before, after = unpack(BASELINE, 'accepted030'), unpack(archive, 'candidate040')
    old = {r['path'] for r in before_index['members']}
    new = {r['path'] for r in after_index['members']}
    assert old <= new
    rows = candidate['payloads']
    mapped = {r['member']: r for r in rows}
    assert len(mapped) == len(rows)
    changed = {member for member in old if sha(before / member) != sha(after / member)}
    expected_changed = {member for member in mapped if member in old}
    assert changed == expected_changed, (sorted(changed ^ expected_changed), sorted(changed))
    assert new - old == set(mapped) - old
    for member, row in mapped.items():
        assert sha(after / member) == row['sha256'], member
    # Every existing non-allowlisted member is compared byte-for-byte above.
    # Require the current private lifecycle selectors and model pointers too.
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'tools/release_010'))
    import integration as native
    from garrison_shared import relic_chunky as rc
    for key in ('pho_minh', 'one_pillar'):
        stamp = after / f'art/stamps/cc040/{key}.bin'
        visuals = native.active_visuals(native.NativeTree(stamp))
        assert visuals[0]['model'].replace('\\', '/') == f'art/scenario/cc040/{key}/model'
        rc.load(after / f'art/scenario/cc040/{key}/model.rgm')
    result = {'status': 'passed', 'sga_sha256': sha(archive),
              'baseline_sha256': sha(BASELINE), 'baseline_members': len(old),
              'final_members': len(new), 'changed': sorted(changed),
              'added': sorted(new - old), 'untouched_members': len(old - changed),
              'all_other_members_byte_identical': True,
              'native_runtime': 'pending client import and fresh match'}
    write(OUT / 'archive-verification.json', result)
    return result


START = '''COMMUNITY CIVILIZATION PACK 0.4.0 — Vietnamese buildings and landmark ruins

Close Age of Empires IV. Import this ZIP through Garrison. Select Community
Civilization Pack as both Game Mode and Tuning Pack. Choose China in the lobby,
then Vietnam at the opening choice. Disable other editions for an isolated test.

Test Pho Minh Tower and One Pillar Pagoda after destruction: their native ruins
should persist, remain selectable, and accept repair. Inspect the One Pillar
whole visual compound at 2.5x, including its yard decorations, and check
placement, paths, production, player colour, damage, construction, and campaign
variants. Check blacksmith, stable, archery range, and market in Ages II–IV.

Rollback: close the game and reimport the accepted 0.3.0 ZIP through Garrison.
Native import, lobby, match, and multiplayer checks are separate user gates.
'''


def package():
    audit = verify()
    from checks import run as run_checks
    checks = run_checks()
    target_folder = OUT / 'package'
    target_folder.mkdir(parents=True, exist_ok=True)
    candidate = read(OUT / 'candidate.json')
    target = target_folder / (KEY + '.sga')
    if target.exists(): assert sha(target) == candidate['sha256']
    else: shutil.copy2(candidate['archive'], target)
    manifest = {'schema': 'garrison.mod/v1', 'bundle_key': KEY,
        'members': [{'mod_key': KEY, 'role': 'tuning', 'path': KEY + '.sga', 'sha256': sha(target)}],
        'details': {'id': KEY, 'name': CONFIG['display_name'], 'version': VERSION,
            'summary': 'Vietnamese building remodels, scaled One Pillar Pagoda, and native Feudal landmark ruins',
            'min_garrison': '0.1.4', 'content_types': ['game-mode', 'tuning-pack'],
            'updated': '2026-10-17',
            'author': 'hosein81 and chilly5',
            'description': 'Building and landmark visual update. Credits: hosein81 and chilly5. Native match verification pending.'}}
    write(target_folder / 'garrison.json', manifest)
    (target_folder / 'START-HERE.txt').write_text(START, encoding='utf-8')
    one_pillar = read(OUT / 'landmarks/one_pillar/handoff.json')
    stamp_proofs = read(WORK / 'private-lists-stamps.json')['reports']
    assert one_pillar['healthy_scale'] == 2.5
    assert len(next(row['stamp']['scaled_decorative_visuals'] for row in stamp_proofs
                    if row['key'] == 'one_pillar')) == 11
    evidence = {'version': VERSION, 'project_guid': GUID,
                'archive': audit, 'checks': checks,
                'landmark_lifecycle': read(WORK / 'landmark-media.json')['reports'],
                'landmark_native_graph': read(OUT / 'landmark-lifecycle-contract.json'),
                'landmark_bindings': stamp_proofs,
                'landmark_handoffs': {key: read(OUT / 'landmarks' / key / 'handoff.json')
                                      for key in ('pho_minh', 'one_pillar')},
                'building_models': read(WORK / 'building-media.json')['models'],
                'building_details': read(WORK / 'building-details-media.json')['models'],
                'building_art_qa_binding': read(OUT / 'buildings/details/art-qa-binding.json'),
                'building_contact_audit': read(OUT / 'buildings/details/contact-audit.json'),
                'building_textured_preview': read(OUT / 'buildings/details/textured-composite-validation.json'),
                'reference_cook': read(WORK / 'reference-cook.json'),
                'detail_reference_cook': read(WORK / 'detail-reference-cook.json'),
                'native_source': read(read(OUT / 'native-source/current.json')['receipt']),
                'market_compiled_identity': market_compiled_identity_proof(),
                'native_runtime': 'pending user test'}
    write(target_folder / 'EVIDENCE.json', evidence)
    destination = OUT / (KEY + '-' + VERSION + '.zip')
    names = ('garrison.json', KEY + '.sga', 'START-HERE.txt', 'EVIDENCE.json')
    if destination.exists():
        with ZipFile(destination) as existing:
            assert existing.testzip() is None
            assert existing.namelist() == list(names)
            assert all(existing.read(name) == (target_folder / name).read_bytes() for name in names), (
                'Existing ZIP differs from current manifest/evidence; archive it before repackaging')
        receipt = {'status': 'passed', 'version': VERSION, 'zip': str(destination),
                   'zip_sha256': sha(destination), 'sga': str(target),
                   'sga_sha256': sha(target), 'native_runtime': 'pending user test'}
        write(OUT / 'package-verification.json', receipt)
        return receipt
    temporary = destination.with_suffix('.zip.tmp')
    assert not temporary.exists()
    with ZipFile(temporary, 'w', ZIP_DEFLATED, compresslevel=6) as bundle:
        for name in names:
            info = ZipInfo(name, date_time=(2026, 10, 17, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o644 << 16
            bundle.writestr(info, (target_folder / name).read_bytes(),
                            compress_type=ZIP_DEFLATED, compresslevel=6)
    with ZipFile(temporary) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == len(set(bundle.namelist())) == 4
        assert json.loads(bundle.read('garrison.json')) == manifest
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == sha(target)
    temporary.replace(destination)
    receipt = {'status': 'passed', 'version': VERSION, 'zip': str(destination),
               'zip_sha256': sha(destination), 'sga': str(target),
               'sga_sha256': sha(target), 'native_runtime': 'pending user test'}
    write(OUT / 'package-verification.json', receipt)
    return receipt


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'compose': compose(sys.argv[2])
    elif action == 'verify': verify()
    elif action == 'package': package()
    else: raise SystemExit('compose LABEL|verify|package')
