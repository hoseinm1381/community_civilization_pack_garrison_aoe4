"""Exact 0.3.0 source preservation with enumerated 0.4.0 visual edits."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ROOT, OUT, GUID, guarded, read, sha, write
from bindings import ACTORS, BUILDING_ACTORS, MARKET_DONOR, building_contracts

ASSETS = ROOT / 'assets'
FREEZE = OUT / 'baseline/freeze-baseline.json'
OLD_MARKET = MARKET_DONOR
NEW_MARKET = r'ebps\vietnam\release_040\vn_040_market_actor'


def _source_files():
    result = {}
    for path in ASSETS.rglob('*'):
        if path.is_symlink() or path.is_junction():
            raise RuntimeError(f'Unexpected source link: {path}')
        if path.is_file(): result[path.relative_to(ASSETS).as_posix()] = path
    return result


def _replace(raw, old, new, count):
    assert raw.count(old) == count, (old, raw.count(old), count)
    return raw.replace(old, new)


def _identity_xml(identity, parent, description, template):
    doc = ET.Element('instance', version='2', description=description, template=template)
    ET.SubElement(doc, 'uniqueid', name='pbgid', value=str(identity))
    ET.SubElement(doc, 'instance_reference', name='parent_pbg', value=parent)
    ET.indent(doc, space='\t')
    return ET.tostring(doc, encoding='utf-8', xml_declaration=True) + b'\n'


def expected_actor(relative, original, landmark_entries, building_entries):
    text = original.decode('utf-8-sig')
    if relative.startswith('attrib/instances/ebps/vietnam/'):
        actor = Path(relative).stem
        for key, names in ACTORS.items():
            if actor in names:
                old = f'attachments\\attachment_lists\\vietnam\\release_030\\vn_030_{key}_visual'
                new = f'attachments\\attachment_lists\\vietnam\\release_040\\{landmark_entries[key]["name"]}'
                assert text.count(old) == 2
                return text.replace(old, new).encode('utf-8')
        family = next((f for f, name in BUILDING_ACTORS.items() if name == actor), None)
        if family:
            for age in (2, 3, 4):
                entry = building_entries[f'{family}_age0{age}']
                old = f'value="{entry["source"]}"'
                new = (f'value="attachments\\attachment_lists\\vietnam\\release_040\\'
                       f'vn_040_{family}_age0{age}_visual" mod="{GUID.replace("-", "")}"')
                text = _replace(text, old, new, 2)
            return text.encode('utf-8')
    if relative.startswith('attrib/instances/sbps/vietnam/vn_unit_villager_'):
        old = f'value="{OLD_MARKET}"'
        new = f'value="{NEW_MARKET}" mod="{GUID.replace("-", "")}"'
        return _replace(text, old, new, 2).encode('utf-8')
    if relative == 'locdb/community_civilization_pack_en.csv':
        replacements = read(OUT / 'integration/credits.json')['exact_replacements']
        for old, new in replacements.items():
            text = _replace(text, old, new, 1)
        return text.encode('utf-8')
    raise AssertionError(f'Unrecognized source edit: {relative}')


def verify():
    guarded()
    freeze = read(FREEZE)
    assert freeze['schema'] == 'community-civilization-pack/release-040-freeze/v1'
    for item in freeze['release_030'].values():
        assert sha(item['path']) == item['sha256']
    old = {r['path']: r for r in freeze['active_source_assets']['files']}
    now = _source_files()
    assert set(old) <= set(now)
    landmark_entries = read(OUT / 'integration/registered-identities.json')
    building_entries = read(OUT / 'integration/registered-building-identities.json')
    market = read(OUT / 'integration/registered-market-actor.json')
    added_expected = {row['source'] for row in landmark_entries.values()}
    added_expected |= {row['source_xml'] for row in building_entries.values() if row['source_xml']}
    added_expected.add(market['source'])
    assert set(now) - set(old) == added_expected, sorted(set(now) - set(old) ^ added_expected)
    expected_additions = {}
    landmark_recipes = read(OUT / 'integration/binding-recipes.json')
    for key, row in landmark_entries.items():
        expected_additions[row['source']] = _identity_xml(row['pbgid'], landmark_recipes[key]['source'],
            'Private 0.4.0 landmark visual identity', r'attachments\attachment_lists')
    for row in building_entries.values():
        if row['source_xml']:
            expected_additions[row['source_xml']] = _identity_xml(row['pbgid'], row['source'],
                'Private 0.4.0 Vietnamese building visual identity', r'attachments\attachment_lists')
    expected_additions[market['source']] = _identity_xml(market['pbgid'], market['donor'],
        'Private 0.4.0 HA01 market actor identity', 'ebps')
    assert set(expected_additions) == added_expected
    assert len({r['pbgid'] for r in landmark_entries.values()} |
               {r['pbgid'] for r in building_entries.values()} | {market['pbgid']}) == 15
    for rel, expected in expected_additions.items():
        assert now[rel].read_bytes() == expected, f'Unexpected new identity bytes: {rel}'
    changed_expected = {
        *(f'attrib/instances/ebps/vietnam/{actor}.xml' for names in ACTORS.values() for actor in names),
        *(f'attrib/instances/ebps/vietnam/{actor}.xml' for actor in BUILDING_ACTORS.values()),
        'attrib/instances/sbps/vietnam/vn_unit_villager_1_chi.xml',
        'attrib/instances/sbps/vietnam/vn_unit_villager_3_chi.xml',
        'locdb/community_civilization_pack_en.csv',
    }
    assert len(changed_expected) == 9
    changed = {}
    for rel, item in old.items():
        actual = sha(now[rel])
        if actual == item['sha256']: continue
        assert rel in changed_expected, f'Unexpected source edit: {rel}'
        snapshot = OUT / 'source-baseline' / rel
        assert sha(snapshot) == item['sha256'], rel
        expected = expected_actor(rel, snapshot.read_bytes(), landmark_entries, building_entries)
        assert now[rel].read_bytes() == expected, f'Non-allowlisted bytes: {rel}'
        changed[rel] = actual
    assert set(changed) == changed_expected, sorted(changed_expected - set(changed))
    result = {'status': 'passed', 'freeze_sha256': sha(FREEZE), 'old_count': len(old),
              'added': sorted(added_expected), 'changed': changed,
              'untouched_source_bytes_identical': True, 'native_runtime': 'unverified'}
    write(OUT / 'source-policy.json', result)
    return result


if __name__ == '__main__':
    verify()
