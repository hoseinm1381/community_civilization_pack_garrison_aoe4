"""0.4.0 landmark private list identities, actor bindings and visual stamps."""
from __future__ import annotations

import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ROOT, OUT, CORE, GUID, guarded, read, run_logged, sha, write

sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native
from garrison_shared import rgd
from stamps import clone_visual_stamp

WORK = OUT / 'integration'
PROJECT = WORK / 'library/Mods/community_040_bindings'
OLD = OUT.parent / 'release_030'
OLD_PAYLOAD = OLD / 'integration/payload'
GRAPH = OLD / 'inventory/landmarks.json'
ACTORS = {
    'pho_minh': ('vn_building_landmark_age1_gatehouse_control_chi',),
    'one_pillar': ('vn_building_landmark_age1_vit_one_pilar_pagoda',
                   'vn_building_landmark_age1_headquarters_control_chi'),
}
STEMS = {key: f'art/scenario/cc040/{key}/model' for key in ACTORS}
STAMPS = {key: f'art/stamps/cc040/{key}.bin' for key in ACTORS}
BUILDING_GRAPH = OUT / 'inventory/stock-chinese-buildings.json'
MARKET_DONOR = (r'ebps\races\chinese_ha_01\buildings\building_econ_market_chi_ha_01'
                r'\building_econ_market_control_chi_ha_01')


def building_contracts():
    graph = read(BUILDING_GRAPH)
    assert graph['status'] == 'passed_static_inventory'
    contracts = {}
    for member, info in graph['attachment_lists'].items():
        match = re.search(r'/tier([234])_([^/]+)\.rgd$', member)
        if not match:
            continue
        age = int(match.group(1))
        stem = next((s for s in info['stamps']['default'] if '/civ_chinese/chi_' in s), None)
        assert stem and stem.endswith(f'_0{age}.bin'), member
        family = next((family for family in ('blacksmith', 'stable', 'archery_range', 'market')
                       if f'chi_{family}_age_0{age}.bin' in stem), None)
        assert family, member
        key = f'{family}_age0{age}'
        assert key not in contracts
        contracts[key] = {'source': member.removeprefix('attrib/').removesuffix('.rgd').replace('/', '\\'),
                          'member': member, 'stock_stamp': stem, 'family': family, 'age': age,
                          'name': f'vn040_{key}_visual'}
    assert len(contracts) == 12
    return contracts


def baseline_bytes(relative):
    freeze = read(OUT / 'baseline/freeze-baseline.json')
    record = next(r for r in freeze['active_source_assets']['files'] if r['path'] == relative)
    source = ROOT / 'assets' / relative
    destination = OUT / 'source-baseline' / relative
    if not destination.exists():
        assert sha(source) == record['sha256'], f'Already changed before baseline copy: {relative}'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    assert sha(destination) == record['sha256']
    return destination.read_bytes()


def prepare():
    guarded()
    graph = read(GRAPH)['landmarks']
    if not (PROJECT / 'mod-project.json').exists():
        run_logged('bindings040-create', [CORE, 'mod-project', 'create', '--library', PROJECT.parent.parent,
                                           '--name', PROJECT.name])
    run_logged('bindings040-settings', [CORE, 'mod-project', 'settings', '--project', PROJECT,
                                       '--live-reload', 'off', '--mod-id', GUID])
    existing = {r['name'] for r in read(PROJECT / 'mod-project.json').get('derived_blueprints', [])}
    contracts = building_contracts()
    for key in ACTORS:
        name = f'vn040_{key}_visual'
        if name not in existing:
            run_logged('bindings040-derive-' + key, [CORE, 'mod-project', 'derive', '--project', PROJECT,
                       '--source', graph[key]['principal_source'].replace('\\', '/'), '--name', name])
    for key, recipe in contracts.items():
        if recipe['name'] not in existing:
            run_logged('bindings040-derive-' + key, [CORE, 'mod-project', 'derive', '--project', PROJECT,
                       '--source', recipe['source'].replace('\\', '/'), '--name', recipe['name']])
    if 'vn040_market_actor' not in existing:
        run_logged('bindings040-derive-market-actor', [CORE, 'mod-project', 'derive', '--project', PROJECT,
                   '--source', MARKET_DONOR.replace('\\', '/'), '--name', 'vn040_market_actor'])
    record = read(PROJECT / 'mod-project.json')
    assert record['game_mode']['enabled'] is False and record['game_mode']['live_reload'] is False
    write(WORK / 'binding-recipes.json', {key: {'source': graph[key]['principal_source'],
          'name': f'vn040_{key}_visual'} for key in ACTORS})
    write(WORK / 'building-recipes.json', contracts)
    return {'status': 'prepared', 'project': str(PROJECT)}


def cook_identities(label):
    """Caller holds the shared release_020 native FileShare.None lock."""
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    pointer = WORK / 'identity-cook-pointer.json'
    if pointer.exists():
        old = read(pointer)
        assert sha(old['receipt']) == old['sha256']
        return read(old['receipt'])
    native.WORK, native.PROJECT, native.CACHEWORK = WORK, PROJECT, OUT / 'inventory'
    native.cook(PROJECT, 'cc040ids-' + label)
    receipt = WORK / ('cc040ids-' + label + '-cook.json')
    write(pointer, {'receipt': str(receipt), 'sha256': sha(receipt)})
    return read(receipt)


def identities():
    guarded()
    pointer = read(WORK / 'identity-cook-pointer.json')
    assert sha(pointer['receipt']) == pointer['sha256']
    cooked = read(pointer['receipt'])
    assert cooked['status'] == 'passed'
    back = Path(cooked['readback'])
    entries = {}
    for key, recipe in read(WORK / 'binding-recipes.json').items():
        generated = f'attrib/attachments/attachment_lists/garrison/{PROJECT.name}/{recipe["name"]}.rgd'
        path = back / generated
        values = {node.value for _, node in rgd.flatten(rgd.read(path.read_bytes()).nodes)
                  if node.key == 'pbgid'}
        assert len(values) == 1
        identity = next(iter(values))
        name = f'vn_040_{key}_visual'
        relative = f'attrib/instances/attachments/attachment_lists/vietnam/release_040/{name}.xml'
        destination = ROOT / 'assets' / relative
        doc = ET.Element('instance', version='2', description='Private 0.4.0 landmark visual identity',
                         template=r'attachments\attachment_lists')
        ET.SubElement(doc, 'uniqueid', name='pbgid', value=str(identity))
        ET.SubElement(doc, 'instance_reference', name='parent_pbg', value=recipe['source'])
        ET.indent(doc, space='\t')
        raw = ET.tostring(doc, encoding='utf-8', xml_declaration=True) + b'\n'
        if destination.exists():
            assert destination.read_bytes() == raw
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        entries[key] = {'pbgid': identity, 'source': relative, 'name': name,
                        'final': f'attrib/attachments/attachment_lists/vietnam/release_040/{name}.rgd'}
    write(WORK / 'registered-identities.json', entries)
    return entries


def register_building_identities():
    guarded()
    pointer = read(WORK / 'identity-cook-pointer.json')
    assert sha(pointer['receipt']) == pointer['sha256']
    cooked = read(pointer['receipt'])
    assert cooked['status'] == 'passed'
    back = Path(cooked['readback'])
    entries = {}
    recipes = read(WORK / 'building-recipes.json')
    for key, recipe in recipes.items():
        generated = (f'attrib/attachments/attachment_lists/garrison/{PROJECT.name}/'
                     f'{recipe["name"]}.rgd')
        path = back / generated
        values = {node.value for _, node in rgd.flatten(rgd.read(path.read_bytes()).nodes)
                  if node.key == 'pbgid'}
        assert len(values) == 1
        identity = next(iter(values))
        name = f'vn_040_{key}_visual'
        relative = f'attrib/instances/attachments/attachment_lists/vietnam/release_040/{name}.xml'
        destination = ROOT / 'assets' / relative
        doc = ET.Element('instance', version='2', description='Private 0.4.0 Vietnamese building visual identity',
                         template=r'attachments\attachment_lists')
        ET.SubElement(doc, 'uniqueid', name='pbgid', value=str(identity))
        ET.SubElement(doc, 'instance_reference', name='parent_pbg', value=recipe['source'])
        ET.indent(doc, space='\t')
        raw = ET.tostring(doc, encoding='utf-8', xml_declaration=True) + b'\n'
        if recipe['family'] == 'market':
            # The Garrison-derived HA01 actor resolves its own generated list
            # identities by GUID:name. Keep one compiled identity per age.
            assert not destination.exists(), f'Remove obsolete provisional identity: {destination}'
            relative = None
            final = generated
        else:
            if destination.exists(): assert destination.read_bytes() == raw
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
            final = f'attrib/attachments/attachment_lists/vietnam/release_040/{name}.rgd'
        entries[key] = dict(recipe, pbgid=identity, source_xml=relative, final=final)
    write(WORK / 'registered-building-identities.json', entries)
    return entries


def register_market_actor_identity():
    cooked = read(read(WORK / 'identity-cook-pointer.json')['receipt'])
    generated = f'attrib/ebps/garrison/{PROJECT.name}/vn040_market_actor.rgd'
    values = {node.value for _, node in rgd.flatten(rgd.read(
        (Path(cooked['readback']) / generated).read_bytes()).nodes) if node.key == 'pbgid'}
    assert len(values) == 1
    identity = next(iter(values))
    relative = 'attrib/instances/ebps/vietnam/release_040/vn_040_market_actor.xml'
    target = ROOT / 'assets' / relative
    doc = ET.Element('instance', version='2', description='Private 0.4.0 HA01 market actor identity',
                     template='ebps')
    ET.SubElement(doc, 'uniqueid', name='pbgid', value=str(identity))
    ET.SubElement(doc, 'instance_reference', name='parent_pbg', value=MARKET_DONOR)
    ET.indent(doc, space='\t')
    raw = ET.tostring(doc, encoding='utf-8', xml_declaration=True) + b'\n'
    if target.exists(): assert target.read_bytes() == raw
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    result = {'source': relative, 'member': 'attrib/ebps/vietnam/release_040/vn_040_market_actor.rgd',
              'generated': generated, 'pbgid': identity,
              'donor': MARKET_DONOR}
    write(WORK / 'registered-market-actor.json', result)
    return result


def bind_sources():
    guarded()
    entries = identities()
    changes = []
    for key, names in ACTORS.items():
        old = f'attachments\\attachment_lists\\vietnam\\release_030\\vn_030_{key}_visual'
        new = f'attachments\\attachment_lists\\vietnam\\release_040\\{entries[key]["name"]}'
        for name in names:
            relative = f'attrib/instances/ebps/vietnam/{name}.xml'
            original = baseline_bytes(relative)
            text = original.decode('utf-8-sig')
            pattern = r'(<instance_reference name="attachments" value=")' + re.escape(old) + r'(" mod="[0-9a-f]{32}"[^>]*/>)'
            updated, count = re.subn(pattern, lambda m: m[1] + new + m[2], text)
            assert count >= 1, (relative, old)
            encoded = updated.encode('utf-8')
            target = ROOT / 'assets' / relative
            assert target.read_bytes() in (original, encoded), f'Unexpected actor drift: {relative}'
            target.write_bytes(encoded)
            changes.append({'actor': relative, 'replacements': count, 'from': old, 'to': new})
    write(WORK / 'source-bindings.json', {'status': 'passed', 'changes': changes})
    return changes


def payload(member, raw, rows):
    target = WORK / 'payload' / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'member': member, 'file': str(target), 'sha256': sha(target), 'bytes': target.stat().st_size})


def private_lists_and_stamps():
    guarded()
    entries = read(WORK / 'registered-identities.json')
    rows, reports = [], []
    for key in ACTORS:
        old_member = f'attrib/attachments/attachment_lists/vietnam/release_030/vn_030_{key}_visual.rgd'
        original = rgd.read((OLD_PAYLOAD / old_member).read_bytes())
        edited = copy.deepcopy(original)
        changed_stamps = []
        for path, node in rgd.flatten(edited.nodes):
            if node.key == 'pbgid':
                node.value = entries[key]['pbgid']
            elif node.key == 'stamp' and node.kind == 'CString' and node.value:
                old = node.value.replace('\\', '/').lower()
                if old == f'art/stamps/cc030/{key}':
                    node.value = STAMPS[key].removesuffix('.bin').replace('/', '\\')
                    changed_stamps.append(path)
        assert changed_stamps
        payload(entries[key]['final'], rgd.write(edited), rows)
        old_model = f'art/scenario/cc030/{key}/model'
        source = OLD_PAYLOAD / f'art/stamps/cc030/{key}.bin'
        destination = WORK / 'payload' / STAMPS[key]
        stamp = clone_visual_stamp(source, destination, old_model, STEMS[key],
                                   visual_scale=2.5 if key == 'one_pillar' else 1)
        rows.append({'member': STAMPS[key], 'file': str(destination),
                     'sha256': sha(destination), 'bytes': destination.stat().st_size})
        reports.append({'key': key, 'list': entries[key]['final'],
                        'stamp_fields': changed_stamps, 'stamp': stamp})
    result = {'status': 'passed', 'payloads': rows, 'reports': reports}
    write(WORK / 'private-lists-stamps.json', result)
    return result


BUILDING_ACTORS = {
    'blacksmith': 'vn_building_tech_unit_infantry_control_chi',
    'stable': 'vn_building_unit_cavalry_control_chi',
    'archery_range': 'vn_building_unit_ranged_control_chi',
}


def bind_building_sources():
    guarded()
    entries = register_building_identities()
    register_market_actor_identity()
    changes = []
    for family, actor in BUILDING_ACTORS.items():
        relative = f'attrib/instances/ebps/vietnam/{actor}.xml'
        before = baseline_bytes(relative)
        text = before.decode('utf-8-sig')
        total = 0
        for age in (2, 3, 4):
            recipe = entries[f'{family}_age0{age}']
            old = recipe['source']
            new = (f'attachments\\attachment_lists\\vietnam\\release_040\\'
                   f'vn_040_{family}_age0{age}_visual')
            pattern = r'(<instance_reference name="attachments" value=")' + re.escape(old) + r'("[^>]*/>)'
            text, count = re.subn(pattern, lambda m: m[1] + new + f'" mod="{GUID.replace("-", "")}"' + m[2][1:], text)
            assert count == 2, (relative, old, count)
            total += count
        encoded = text.encode('utf-8')
        target = ROOT / 'assets' / relative
        assert target.read_bytes() in (before, encoded), relative
        target.write_bytes(encoded)
        changes.append({'actor': relative, 'tier_ref_edits': total})
    old = MARKET_DONOR
    new = r'ebps\vietnam\release_040\vn_040_market_actor'
    for actor in ('vn_unit_villager_1_chi', 'vn_unit_villager_3_chi'):
        relative = f'attrib/instances/sbps/vietnam/{actor}.xml'
        before = baseline_bytes(relative)
        text = before.decode('utf-8-sig')
        pattern = r'(<instance_reference name="ebp" value=")' + re.escape(old) + r'("[^>]*/>)'
        text, count = re.subn(pattern, lambda m: m[1] + new + f'" mod="{GUID.replace("-", "")}"' + m[2][1:], text)
        assert count == 2, (relative, count)
        encoded = text.encode('utf-8')
        target = ROOT / 'assets' / relative
        assert target.read_bytes() in (before, encoded), relative
        target.write_bytes(encoded)
        changes.append({'actor': relative, 'market_ref_edits': count})
    write(WORK / 'building-source-bindings.json', {'status': 'passed', 'changes': changes})
    return changes


def private_building_lists_and_stamps():
    guarded()
    native.CACHEWORK = OUT / 'inventory'
    entries = read(WORK / 'registered-building-identities.json')
    rows, reports = [], []
    for key, entry in entries.items():
        source = native.stock(entry['member'])
        assert sha(source) == read(BUILDING_GRAPH)['attachment_lists'][entry['member']]['sha256']
        original = rgd.read(source.read_bytes())
        edited = copy.deepcopy(original)
        count = 0
        private_stamp = f'art/stamps/cc040/{key}.bin'
        for _, node in rgd.flatten(edited.nodes):
            if node.key == 'pbgid': node.value = entry['pbgid']
            elif node.key == 'stamp' and node.kind == 'CString' and node.value.replace('\\', '/').lower() == entry['stock_stamp'].removesuffix('.bin'):
                node.value = private_stamp.removesuffix('.bin').replace('/', '\\')
                count += 1
        assert count == 3, (key, count)
        restored = copy.deepcopy(edited)
        original_fields = dict(rgd.flatten(original.nodes))
        for path, node in rgd.flatten(restored.nodes):
            if node.key == 'pbgid' or (node.key == 'stamp' and node.kind == 'CString' and
                node.value.replace('\\', '/').lower() == private_stamp.removesuffix('.bin')):
                node.value = original_fields[path].value
        assert rgd.write(restored) == rgd.write(original), f'Nonvisual list drift: {key}'
        payload(entry['final'], rgd.write(edited), rows)
        source_stamp = native.stock(entry['stock_stamp'])
        donor = read(ROOT / 'art/recipes/release_040/buildings-donors.json')
        model = next(r['logical_path'].removesuffix('.rgm') for r in donor['models']
                     if r['family'] == entry['family'] and r['age'] == entry['age'])
        final_model = f'art/scenario/cc040/{key}/model'
        target = WORK / 'payload' / private_stamp
        report = clone_visual_stamp(source_stamp, target, model, final_model)
        rows.append({'member': private_stamp, 'file': str(target), 'sha256': sha(target),
                     'bytes': target.stat().st_size})
        reports.append({'key': key, 'list_stamp_edits': count, 'stamp': report,
                        'all_other_list_fields_byte_identical': True,
                        'destruction_and_campaign_entries_preserved': True})
    result = {'status': 'passed', 'payloads': rows, 'reports': reports}
    write(WORK / 'private-building-lists-stamps.json', result)
    return result


def private_market_actor():
    """Retain HA01 gameplay fields, changing identity and three visual lists."""
    guarded()
    native.CACHEWORK = OUT / 'inventory'
    stock_path = native.stock('attrib/' + MARKET_DONOR.replace('\\', '/') + '.rgd')
    donor = rgd.read(stock_path.read_bytes())
    cooked = read(read(WORK / 'identity-cook-pointer.json')['receipt'])
    generated = f'attrib/ebps/garrison/{PROJECT.name}/vn040_market_actor.rgd'
    member = 'attrib/ebps/vietnam/release_040/vn_040_market_actor.rgd'
    candidate = rgd.read((Path(cooked['readback']) / generated).read_bytes())
    prior = [(p, n.kind, n.value) for p, n in rgd.flatten(donor.nodes) if not isinstance(n.value, list)]
    current = [(p, n.kind, n.value) for p, n in rgd.flatten(candidate.nodes) if not isinstance(n.value, list)]
    assert len(prior) == len(current)
    expected = {'pbgid', '$PBGNAME', '$PBGMAP'}
    changed = [(a[0], a[2], b[2]) for a, b in zip(prior, current) if a != b]
    assert all(a[0] == b[0] and a[1] == b[1] for a, b in zip(prior, current))
    assert len(changed) == 6 and all(p.rsplit('/', 1)[-1].split('[')[0] in expected for p, _, _ in changed), changed
    # Garrison creates a self-contained derived EBP, clearing its parent. The
    # parent link is retained for donor parity without changing flattened data.
    for path, old, new in changed:
        if path.endswith('parent_pbg/$PBGNAME') or path.endswith('parent_pbg/$PBGMAP'):
            rgd.find(candidate.nodes, path).value = old
    remaining = [(p, n.value) for p, n in rgd.flatten(candidate.nodes)
                 if not isinstance(n.value, list)]
    after = [(p, a, b) for (p, _, a), (_, b) in zip(prior, remaining) if a != b]
    assert len(after) == 4, after
    assert sum(p.endswith('/pbgid') for p, _, _ in after) == 1
    assert sum(p.endswith('/$PBGNAME') for p, _, _ in after) == 3
    rows = []
    payload(member, rgd.write(candidate), rows)
    result = {'status': 'passed', 'member': member, 'payload': rows[0],
              'donor_sha256': sha(stock_path), 'changed_fields': after,
              'nonvisual_gameplay_fields_preserved': True}
    write(WORK / 'private-market-actor.json', result)
    return result


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': print(json.dumps(prepare(), indent=2))
    elif action == 'cook-identities': print(json.dumps(cook_identities(sys.argv[2]), indent=2))
    elif action == 'bind': bind_sources(); private_lists_and_stamps()
    elif action == 'bind-buildings': bind_building_sources(); private_building_lists_and_stamps(); private_market_actor()
    else: raise SystemExit('prepare|cook-identities LABEL|bind')
