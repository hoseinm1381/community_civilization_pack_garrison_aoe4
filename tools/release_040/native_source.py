"""Content Editor compilation of the exact 0.4.0 source delta."""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from common import ROOT, OUT, CONFIG, ARCH, EDITOR, GUID, guarded, read, run_logged, sha, write
from source_policy import verify as verify_source

sys.path.insert(0, str(ROOT / 'tools/release_010'))
from garrison_shared import rgd
import integration as native

BASELINE = ROOT / 'archives/release_030_user_accepted/community_civilization_pack.sga'
WORK = OUT / 'native-source'
ACTORS = (
    'vn_building_landmark_age1_gatehouse_control_chi',
    'vn_building_landmark_age1_vit_one_pilar_pagoda',
    'vn_building_landmark_age1_headquarters_control_chi',
    'vn_building_tech_unit_infantry_control_chi',
    'vn_building_unit_cavalry_control_chi',
    'vn_building_unit_ranged_control_chi',
)
MEMBERS = tuple(f'attrib/ebps/vietnam/{name}.rgd' for name in ACTORS) + tuple(
    f'attrib/sbps/vietnam/vn_unit_villager_{age}_chi.rgd' for age in (1, 3))
LOCALE = 'en/en.ucs'
MARKET = 'attrib/ebps/vietnam/release_040/vn_040_market_actor.rgd'


def extract(archive, member, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists(), destination
    run_logged('extract-' + member.replace('/', '-') + '-' + sha(archive)[:8],
               [ARCH, 'extract-member', archive, member, destination])


def compiled_visual_proof(before, after, *, squad=False):
    old, new = rgd.read(before.read_bytes()), rgd.read(after.read_bytes())
    left, right = dict(rgd.flatten(old.nodes)), dict(rgd.flatten(new.nodes))
    assert left.keys() == right.keys()
    restored, edits = copy.deepcopy(new), []
    for path, node in left.items():
        current = right[path]
        assert (node.kind, node.key) == (current.kind, current.key)
        if node.kind in ('List', 'List2') or node.value == current.value: continue
        assert node.key in ('$PBGNAME', '$PBGMAP'), (path, node.value, current.value)
        if squad:
            assert 'market_actor' in str(current.value) or node.key == '$PBGMAP', path
        else:
            assert 'vn_040_' in str(current.value) or node.key == '$PBGMAP', path
        rgd.find(restored.nodes, path).value = node.value
        edits.append({'path': path, 'before': node.value, 'after': current.value})
    assert edits and rgd.write(restored) == rgd.write(old)
    return {'edits': edits, 'all_other_compiled_fields_byte_identical': True,
            'baseline_sha256': sha(before), 'new_sha256': sha(after)}


def market_identity_proof(compiled):
    """Tie the source-compiled HA01 child to the final private visual actor."""
    registration = read(OUT / 'integration/registered-market-actor.json')
    assert registration['member'] == MARKET
    native.CACHEWORK = OUT / 'inventory'
    donor = native.stock('attrib/' + registration['donor'].replace('\\', '/') + '.rgd')
    payload = OUT / 'integration/payload' / MARKET
    def leaves(path):
        return {key: (node.kind, node.value) for key, node in rgd.flatten(rgd.read(path.read_bytes()).nodes)
                if not isinstance(node.value, list)}
    stock, source, final = leaves(donor), leaves(compiled), leaves(payload)
    assert stock.keys() == source.keys() == final.keys()
    identity = [p for p in source if p.endswith('/pbgid')]
    assert len(identity) == 1 and source[identity[0]][1] == final[identity[0]][1] == registration['pbgid']
    parent_name = 'default/parent_pbg/$PBGNAME'
    parent_map = 'default/parent_pbg/$PBGMAP'
    assert source[parent_name][1] == registration['donor'].rsplit('\\', 1)[-1]
    assert source[parent_map][1] == 'ebps'
    assert final[parent_name] == stock[parent_name] and final[parent_map] == stock[parent_map]
    tiers = read(OUT / 'integration/registered-building-identities.json')
    identity_cook = read(read(OUT / 'integration/identity-cook-pointer.json')['receipt'])
    expected_tiers = {}
    registered_tier_ids = {}
    for age, index in ((2, ''), (3, '[1]'), (4, '[2]')):
        path = f'default/tier_ext/tier_group_list/tier_group/tier{index}/attachments/$PBGNAME'
        expected_tiers[path] = GUID.replace('-', '') + f':vn040_market_age0{age}_visual'
        tier = tiers[f'market_age0{age}']
        registered_tier_ids[f'market_age0{age}'] = tier['pbgid']
        member = tier['final']
        assert member.startswith('attrib/attachments/attachment_lists/garrison/community_040_bindings/')
        for candidate in (Path(identity_cook['readback']) / member,
                          OUT / 'integration/payload' / member):
            record = leaves(candidate)
            assert record['default/pbgid'][1] == tier['pbgid'], (member, candidate)
        detail_override = OUT / 'details/payload' / member
        if detail_override.exists():
            assert leaves(detail_override)['default/pbgid'][1] == tier['pbgid'], member
    for path in source:
        if path in identity or path in (parent_name, parent_map):
            continue
        assert source[path] == stock[path], ('Compiled market donor drift', path)
        if path in expected_tiers:
            assert final[path] == (source[path][0], expected_tiers[path])
        else:
            assert final[path] == source[path], ('Final market gameplay drift', path)
    return {'compiled_identity_sha256': sha(compiled), 'donor_sha256': sha(donor),
            'final_payload_sha256': sha(payload), 'pbgid': registration['pbgid'],
            'private_tiers': expected_tiers, 'registered_market_tier_pbgids': registered_tier_ids,
            'all_nonvisual_donor_fields_preserved': True}


def attachment_identity_proof(archive, extraction_root):
    """Read the Content Editor output for every new source attachment identity."""
    landmarks = read(OUT / 'integration/registered-identities.json')
    buildings = read(OUT / 'integration/registered-building-identities.json')
    entries = list(landmarks.values()) + [row for row in buildings.values() if row['source_xml']]
    assert len(entries) == 11
    result = {}
    for row in entries:
        member = row['final']
        compiled = extraction_root / member
        if not compiled.exists():
            compiled.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(ARCH), 'extract-member', str(archive), member, str(compiled)],
                           capture_output=True, check=True)
        native.CACHEWORK = OUT / 'inventory'
        leaves = {path: node.value for path, node in rgd.flatten(rgd.read(compiled.read_bytes()).nodes)
                  if not isinstance(node.value, list)}
        assert leaves['default/pbgid'] == row['pbgid'], member
        parent = (read(OUT / 'integration/binding-recipes.json')[
            next(key for key, value in landmarks.items() if value is row)]['source']
            if row in landmarks.values() else row['source'])
        assert leaves['default/parent_pbg/$PBGNAME'] == parent.rsplit('\\', 1)[-1], member
        assert leaves['default/parent_pbg/$PBGMAP'] == r'attachments\attachment_lists', member
        final = OUT / 'integration/payload' / member
        final_leaves = {path: node.value for path, node in rgd.flatten(rgd.read(final.read_bytes()).nodes)
                        if not isinstance(node.value, list)}
        assert final_leaves['default/pbgid'] == row['pbgid'], member
        result[member] = {'compiled_sha256': sha(compiled), 'final_sha256': sha(final),
                          'pbgid': row['pbgid'], 'parent': parent}
    return result


def compile(label):
    """Caller holds the shared release_020 native FileShare.None lock."""
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    source_proof = verify_source()
    run = WORK / 'runs' / label
    assert not run.exists(), 'Use a fresh append-only label'
    source = run / 'source'
    source.mkdir(parents=True)
    shutil.copytree(ROOT / 'assets', source / 'assets')
    shutil.copy2(ROOT / CONFIG['project_file'], source / CONFIG['project_file'])
    command = run_logged('native-source-' + label, [EDITOR, '-rtm', '--safe_settings',
        '--do_not_restore', '--quiet_crash_report', '--no_source_control',
        '--log_path', run / 'native-logs', '--build_mod', source / CONFIG['project_file'],
        '--build_path', run / 'build', '--no_burn_window', '--burn_cache_type', 'Local',
        '--burn_max_threads', '1', '--burn_platform', 'PC', '--burn_log_path', run / 'burn.log',
        '--intermediate_path', run / 'intermediate'], cwd=EDITOR.parent, timeout=1800)
    return finish(label, source_proof, command)


def finish(label, source_proof=None, command=None):
    guarded()
    run = WORK / 'runs' / label
    source = run / 'source'
    source_proof = source_proof or verify_source()
    command = command or read(OUT / 'logs' / ('native-source-' + label + '.json'))
    assert command['exit_code'] == 0
    log = Path(command['log']).read_text(encoding='utf-8', errors='replace')
    errors = [line for line in log.splitlines() if 'EssenceEditor.exe Error:' in line or 'System does not support' in line]
    missing = [line for line in log.splitlines() if str(source).lower() in line.lower() and
               ("doesn't exist" in line or 'does not exist' in line)]
    counts = re.findall(r'(\d+) instances validated', log)
    expected_instances = len(list((source / 'assets/attrib/instances').rglob('*.xml')))
    assert not errors and not missing and counts and int(counts[-1]) == expected_instances, (errors, missing, counts)
    archives = list((run / 'build').rglob('*.sga'))
    assert len(archives) == 1
    archive = archives[0]
    listing = json.loads(subprocess.run([str(ARCH), 'list', str(archive), '--verify'],
                                 capture_output=True, text=True, check=True).stdout)
    assert listing['archive']['verification']['verified']
    assert listing['archive']['name'].replace('-', '').lower() == GUID.replace('-', '').lower()
    rows, proofs = [], {}
    market_compiled = run / 'compiled-identity' / MARKET
    extract(archive, MARKET, market_compiled)
    proofs[MARKET] = market_identity_proof(market_compiled)
    attachment_proofs = attachment_identity_proof(archive, run / 'compiled-identity')
    for member in (*MEMBERS, LOCALE):
        target, prior = run / 'payload' / member, run / 'baseline' / member
        extract(archive, member, target)
        extract(BASELINE, member, prior)
        if member != LOCALE:
            proofs[member] = compiled_visual_proof(prior, target, squad='/sbps/' in member)
        else:
            assert sha(prior) != sha(target)
            locale_raw = target.read_bytes()
            assert b'h\x00o\x00s\x00e\x00i\x00n\x008\x001\x00' in locale_raw
            assert b'c\x00h\x00i\x00l\x00l\x00y\x005\x00' in locale_raw
            for link in ('youtube.com/@aoe4kingdom', 'youtube.com/@ChillyEmpire'):
                assert link.encode('utf-16le') in locale_raw
            proofs[member] = {'changed_from_credit_source': True, 'baseline_sha256': sha(prior),
                              'new_sha256': sha(target), 'author_credits_and_links_present': True}
        rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                     'bytes': target.stat().st_size})
    assert source_proof == verify_source()
    assert {p.relative_to(source / 'assets').as_posix(): sha(p)
            for p in (source / 'assets').rglob('*') if p.is_file()} == {
            p.relative_to(ROOT / 'assets').as_posix(): sha(p)
            for p in (ROOT / 'assets').rglob('*') if p.is_file()}
    receipt = {'status': 'passed', 'source_policy': source_proof,
               'native_validated_instances': expected_instances, 'command': command,
               'archive': str(archive), 'archive_sha256': sha(archive),
               'payloads': rows, 'compiled_proofs': proofs,
               'compiled_attachment_identities': attachment_proofs, 'runtime': 'unverified'}
    write(run / 'receipt.json', receipt)
    write(WORK / 'current.json', {'receipt': str(run / 'receipt.json'),
                                 'sha256': sha(run / 'receipt.json')})
    return receipt


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'compile': compile(sys.argv[2])
    elif action == 'finish': finish(sys.argv[2])
    else: raise SystemExit('compile LABEL|finish LABEL')
