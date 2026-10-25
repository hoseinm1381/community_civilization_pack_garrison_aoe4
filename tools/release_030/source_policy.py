"""Immutable 0.2.1 source comparison with the narrow 0.3.0 visual allowance."""
from __future__ import annotations

import copy
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ROOT, OUT, CONFIG, guarded, read, sha, write

BASELINE = OUT / 'source-baseline.json'
ASSETS = ROOT / 'assets'
MINISTRY = 'attrib/instances/ebps/vietnam/vn_building_econ_food_control_chi.xml'
LANDMARK_TO_PRIVATE = {
    'attrib/instances/ebps/vietnam/vn_building_landmark_age1_gatehouse_control_chi.xml': 'vn_030_pho_minh_visual',
    'attrib/instances/ebps/vietnam/vn_building_landmark_age1_vit_one_pilar_pagoda.xml': 'vn_030_one_pillar_visual',
    'attrib/instances/ebps/vietnam/vn_building_landmark_age1_headquarters_control_chi.xml': 'vn_030_one_pillar_visual',
}
LANDMARKS = set(LANDMARK_TO_PRIVATE)
NEW_IDENTITIES = {
    f'attrib/instances/attachments/attachment_lists/vietnam/release_030/{name}.xml'
    for name in set(LANDMARK_TO_PRIVATE.values())
}
IDENTITY_PARENTS = {
    'pho_minh': r'attachments\attachment_lists\civilizations\english\buildings\campaign\york_wooden_castle_eng',
    'one_pillar': r'attachments\attachment_lists\civilizations\chinese_ha_01\buildings\tier1_landmark_1b_chi_ha',
}
VISUAL_ACTORS = LANDMARKS


def _files():
    for path in ASSETS.rglob('*'):
        if path.is_symlink() or path.is_junction():
            raise RuntimeError(f'Unexpected link in source: {path}')
        if path.is_file():
            yield path


def capture():
    guarded()
    if BASELINE.exists():
        raise FileExistsError(f'Immutable source baseline already exists: {BASELINE}')
    rows = {p.relative_to(ASSETS).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in _files()}
    assert len(rows) >= 289 and MINISTRY in rows and LANDMARKS <= rows.keys()
    accepted = ROOT / 'archives/release_021_user_accepted/community_civilization_pack.sga'
    assert accepted.is_file()
    for rel in sorted(LANDMARKS | {MINISTRY}):
        target = OUT / 'source-baseline' / rel
        assert not target.exists(), target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ASSETS / rel, target)
        assert sha(target) == rows[rel]['sha256']
    record = {'schema': 'community.release030.source-baseline/v1', 'status': 'frozen',
              'accepted_021_sga_sha256': sha(accepted), 'project_sha256': sha(ROOT / CONFIG['project_file']),
              'assets': rows}
    write(BASELINE, record)
    return {'status': 'frozen', 'files': len(rows), 'sga_sha256': record['accepted_021_sga_sha256']}


def _walk(before, after, path='root'):
    if before.tag != after.tag or len(before) != len(after) or before.text != after.text or before.tail != after.tail:
        raise AssertionError(f'XML structure/text drift: {path}')
    a, b = dict(before.attrib), dict(after.attrib)
    edits = []
    visual = before.tag == 'instance_reference' and before.get('name') == 'attachments'
    footprint = before.tag == 'float' and before.get('name') in ('x', 'y') and 'footprint_scale' in path
    if visual:
        for k in ('value', 'mod'): a.pop(k, None); b.pop(k, None)
    if footprint:
        a.pop('value', None); b.pop('value', None)
    assert a == b, f'Unapproved XML attribute drift: {path}: {a} -> {b}'
    if before.attrib != after.attrib:
        if visual:
            assert after.get('mod') == CONFIG['project_guid'].replace('-', '')
            assert after.get('value', '').startswith('attachments\\attachment_lists\\vietnam\\release_030\\')
        elif footprint:
            assert before.get('value') == '16' and after.get('value') == '8'
        else:
            raise AssertionError(f'Unexpected XML edit: {path}')
        edits.append({'path': path, 'before': before.attrib, 'after': after.attrib})
    for i, (left, right) in enumerate(zip(before, after)):
        edits.extend(_walk(left, right, f'{path}/{left.get("name", left.tag)}[{i}]'))
    return edits


def verify():
    guarded()
    frozen = read(BASELINE)
    assert frozen['schema'] == 'community.release030.source-baseline/v1'
    assert sha(ROOT / CONFIG['project_file']) == frozen['project_sha256']
    assert sha(ROOT / 'archives/release_021_user_accepted/community_civilization_pack.sga') == frozen['accepted_021_sga_sha256']
    now = {p.relative_to(ASSETS).as_posix(): p for p in _files()}
    old = frozen['assets']
    added = set(now) - set(old)
    assert set(old) <= set(now)
    assert added == NEW_IDENTITIES, added
    registered = read(OUT / 'integration/registered-identities.json')
    assert {row['source'] for row in registered.values()} == NEW_IDENTITIES
    assert set(registered) == set(IDENTITY_PARENTS)
    for key, entry in registered.items():
        identity = ET.parse(now[entry['source']]).getroot()
        assert identity.tag == 'instance' and identity.attrib == {
            'version': '2', 'description': 'Private 0.3.0 landmark visual identity',
            'template': r'attachments\attachment_lists'}
        assert len(identity) == 2
        assert identity[0].tag == 'uniqueid' and identity[0].attrib == {
            'name': 'pbgid', 'value': str(entry['pbgid'])}
        assert identity[1].tag == 'instance_reference' and identity[1].attrib == {
            'name': 'parent_pbg', 'value': IDENTITY_PARENTS[key]}
    changed = {}
    for rel, row in old.items():
        if sha(now[rel]) == row['sha256']:
            continue
        assert rel in VISUAL_ACTORS or rel == MINISTRY, f'Unapproved source change: {rel}'
        baseline_copy = OUT / 'source-baseline' / rel
        assert baseline_copy.is_file() and sha(baseline_copy) == row['sha256'], rel
        edits = _walk(ET.fromstring(baseline_copy.read_bytes()), ET.fromstring(now[rel].read_bytes()))
        assert edits, f'Byte drift without typed edit: {rel}'
        if rel == MINISTRY:
            assert len(edits) == 4 and all('footprint_scale' in e['path'] for e in edits), edits
        else:
            expected = 'attachments\\attachment_lists\\vietnam\\release_030\\' + LANDMARK_TO_PRIVATE[rel]
            assert len(edits) == 2, (rel, edits)
            assert all(e['before'].get('name') == 'attachments' and
                       e['after'].get('name') == 'attachments' and
                       e['after'].get('value') == expected for e in edits), (rel, edits)
        changed[rel] = edits
    assert MINISTRY in changed and changed.keys() & LANDMARKS == LANDMARKS
    return {'status': 'passed', 'baseline_sha256': sha(BASELINE), 'old_files': len(old),
            'added': sorted(added), 'changed': changed,
            'all_other_source_bytes_identical': True}


if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'capture':
        result = capture()
    elif sys.argv[1] == 'verify':
        result = verify()
    else:
        raise SystemExit('capture|verify')
    print(json.dumps(result, indent=2))
