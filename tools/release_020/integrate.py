"""Private native visual bindings for the approved 0.2.0 buildings.

Stages are explicit. `prepare` and `inventory` do not cook or modify active source.
`cook-identities` requires the root's exclusive native-cook token. `bind` changes
only the approved actor visual references and adds private identity stubs.
"""
import copy
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from common import ARCH, CONFIG, CORE, OUT, ROOT, STAGING, guarded, read, sha, write
from inventory import SOURCES, EXPECTED_STAMPS, native, rgd
from source_policy import CONSUMERS, visual_changes, verify as verify_sources
from garrison_shared import relic_chunky as rc

sys.dont_write_bytecode = True
WORK = OUT / 'integration'
PROJECT = WORK / 'library/Mods/community_020_bindings'
PREFIX = 'art/stamps/cc020/'
MODEL_PREFIX = 'art/scenario/cc020/'

STAMP_TARGETS = {
    **{f'barracks_age0{i}': f'barracks_age0{i}' for i in range(1, 5)},
    **{f'town_center_age0{i}': f'town_center_age0{i}' for i in range(1, 5)},
    'hideout_default': 'hideout_default', 'hideout_stone': 'hideout_stone',
    'economy_ministry': 'economy_ministry',
    **{f'farm_rice_{side}': 'farm_paddy_edge' for side in ('back', 'front', 'left', 'right')},
}

SHELTER_STAMPS = ('hideout_shelter_default', 'hideout_shelter_stone')


def graft_hideout_shelters(data, original):
    """Clone the native Garrison-qualified house stamp node in each outpost branch.

    The Garrison fixed-index experiment established the field schema, but would
    overwrite the campaign scaffolding slot. The typed graft appends at each
    branch's actual end and removes cleanly to recover the donor graph.
    """
    experiment = OUT / 'experiments/hideout-shelter-list/cc020-hideout3q-cook.json'
    cooked = read(experiment)
    assert cooked['status'] == 'passed' and cooked['cook']['sha256'] == '4e9cbc0fbcba8701582c54d8af8dcceb470303c9847b9afab4b407aa69e1b362'
    generated = Path(cooked['readback']) / 'attrib/attachments/attachment_lists/garrison/community_020_bindings/vn020_hideout_visual.rgd'
    qualified = rgd.read(generated.read_bytes())
    attached = []
    for variant in ('default', 'cordoba', 'campaign'):
        for stone in (False, True):
            branch = f'{variant}/attachment_lists/attachment_lists/attachment_list'
            if stone: branch += '[1]'
            branch += '/attachment_list'
            own = rgd.find(data.nodes, branch)
            donor = rgd.find(original.nodes, branch)
            assert own.kind == donor.kind == 'List2'
            before = [node for node in donor.value if node.key == 'stamp_attachment']
            expected = 3 if variant == 'campaign' and not stone else 2
            assert len(before) == expected, (branch, len(before), expected)
            if variant == 'campaign' and not stone:
                assert any(node.key == 'stamp' and node.value.replace('\\', '/').lower() ==
                           'art/stamps/scaffolding/west/west_outpost'
                           for node in before[2].value), 'Campaign scaffolding slot must remain'
            template = rgd.find(qualified.nodes, branch + '/stamp_attachment[2]')
            assert template.kind == 'List' and [n.key for n in template.value] == [
                'stamp', '$REF', 'add_impass_blockers']
            clone = copy.deepcopy(template)
            target = 'hideout_shelter_stone' if stone else 'hideout_shelter_default'
            next(node for node in clone.value if node.key == 'stamp').value = (PREFIX + target).replace('/', '\\')
            assert next(node for node in clone.value if node.key == 'add_impass_blockers').value is False
            own.value.append(clone)
            index = expected
            attached.append({'variant': variant, 'branch': branch, 'slot': index,
                             'stamp': PREFIX + target, 'native_template_sha256': sha(generated)})
    return attached


def run(label, args):
    guarded()
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    log = OUT / (label + '.log'); log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    write(OUT / (label + '-command.json'), {'args': list(map(str, args)), 'exit_code': result.returncode,
                                            'log': str(log)})
    if result.returncode:
        raise RuntimeError(f'{label} exited {result.returncode}; see {log}')
    return result.stdout


def prepare():
    guarded()
    graph = read(OUT / 'inventory/native-graph.json')
    assert graph['status'] == 'official source inventory' and set(graph['attachments']) == set(SOURCES)
    if not (PROJECT / 'mod-project.json').exists():
        run('prepare-020-create', [CORE, 'mod-project', 'create', '--library', WORK / 'library', '--name', PROJECT.name])
    run('prepare-020-settings', [CORE, 'mod-project', 'settings', '--project', PROJECT,
                                 '--live-reload', 'off', '--mod-id', CONFIG['project_guid']])
    project = read(PROJECT / 'mod-project.json')
    existing = {row['name'] for row in project.get('derived_blueprints', [])}
    for name, source in SOURCES.items():
        private = f'vn020_{name}_visual'
        if private not in existing:
            run(f'prepare-020-derive-{name}', [CORE, 'mod-project', 'derive', '--project', PROJECT,
                                               '--source', source.replace('\\', '/'), '--name', private])
    project = read(PROJECT / 'mod-project.json')
    assert project['game_mode']['enabled'] is False and project['game_mode']['live_reload'] is False
    derived = {row['name']: row['source'] for row in project['derived_blueprints']}
    assert all(derived[f'vn020_{key}_visual'].replace('/', '\\') == ref for key, ref in SOURCES.items())
    write(WORK / 'derived-contracts.json', [{'key': key, 'source': ref, 'name': f'vn020_{key}_visual'}
                                            for key, ref in SOURCES.items()])
    print('PRIVATE_ATTACHMENT_RECIPES_READY', len(SOURCES))


def cook_identities(label):
    """Must be called only after the root grants an exclusive native-cook token."""
    guarded()
    assert re.fullmatch(r'cc020-[a-z0-9-]{2,32}', label)
    native.WORK = WORK
    native.PROJECT = PROJECT
    native.cook(PROJECT, label)
    write(WORK / 'identity-cook-pointer.json', {'label': label,
                                                  'receipt': str(WORK / (label + '-cook.json'))})


def register_identities():
    guarded()
    pointer = read(WORK / 'identity-cook-pointer.json')
    cook = read(pointer['receipt'])
    back = Path(cook['readback'])
    entries = []
    for contract in read(WORK / 'derived-contracts.json'):
        key, generated_name = contract['key'], contract['name']
        name = generated_name.replace('vn020_', 'vn_020_', 1)
        assert name.startswith('vn_020_') and generated_name.startswith('vn020_')
        generated = f'attrib/attachments/attachment_lists/garrison/{PROJECT.name}/{generated_name}.rgd'
        cooked = back / generated
        assert cooked.is_file(), generated
        values = {node.value for _, node in rgd.flatten(rgd.read(cooked.read_bytes()).nodes) if node.key == 'pbgid'}
        assert len(values) == 1, (generated_name, values)
        identity = next(iter(values))
        source = f'attrib/instances/attachments/attachment_lists/vietnam/release_020/{name}.xml'
        target = ROOT / 'assets' / source
        root = ET.Element('instance', version='2', description='Garrison-owned 0.2.0 visual identity; full native list in approved integration payload.', template=r'attachments\attachment_lists')
        ET.SubElement(root, 'uniqueid', name='pbgid', value=str(identity))
        ET.SubElement(root, 'instance_reference', name='parent_pbg', value=contract['source'])
        ET.indent(root, space='\t')
        raw = ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'
        if target.exists() and target.read_bytes() != raw:
            raise ValueError(f'Private identity drift: {target}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        entries.append({'key': key, 'name': name, 'generated_name': generated_name,
                        'source': source, 'pbgid': identity,
                        'generated_member': generated, 'generated_sha256': sha(cooked),
                        'final_member': f'attrib/attachments/attachment_lists/vietnam/release_020/{name}.rgd'})
    write(WORK / 'registered-identities.json', entries)
    print('PRIVATE_IDENTITIES_REGISTERED', len(entries))
    return entries


def bind_sources():
    guarded()
    identities = read(WORK / 'registered-identities.json')
    mapping = {SOURCES[row['key']]: row['name'] for row in identities}
    frozen = STAGING / 'baseline_source/assets/attrib/instances/ebps/vietnam'
    changes = []
    for name in CONSUMERS:
        path = ROOT / f'assets/attrib/instances/ebps/vietnam/{name}.xml'
        before = (frozen / (name + '.xml')).read_bytes()
        text = before.decode('utf-8-sig')
        edits = []
        def replace(match):
            value = re.search(r'value="([^"]+)"', match[0]).group(1)
            if value not in mapping:
                return match[0]
            target = 'attachments\\attachment_lists\\vietnam\\release_020\\' + mapping[value]
            updated = match[0].replace('value="' + value + '"',
                                       'value="' + target + '" mod="' + CONFIG['project_guid'].replace('-', '') + '"')
            edits.append({'before': value, 'after': target})
            return updated
        changed = re.sub(r'<instance_reference name="(?:attachments|animator_attachments)"[^>]+/>', replace, text)
        if not edits:
            raise ValueError(f'No visual list bound in {name}')
        encoded = changed.encode('utf-8')
        current = path.read_bytes()
        if current not in (before, encoded):
            visual_changes(before, current)
        if current != encoded:
            path.write_bytes(encoded)
        changes.append({'name': name, 'source': str(path), 'attachment_changes': edits})
    proof = verify_sources([row['source'] for row in identities])
    write(WORK / 'source-bindings.json', {'status': 'passed', 'actors': changes,
                                          'source_new_files': [row['source'] for row in identities],
                                          'preservation': proof})
    print('PRIVATE_ACTORS_BOUND', len(changes))


def payload(member, data, rows):
    path = WORK / 'payload' / member
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    rows.append({'member': member, 'file': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size})


def bind_private_lists():
    guarded()
    graph = read(OUT / 'inventory/native-graph.json')
    identities = {row['key']: row for row in read(WORK / 'registered-identities.json')}
    rows, contracts = [], []
    for key, info in graph['attachments'].items():
        original = rgd.read(Path(info['file']).read_bytes())
        data = copy.deepcopy(original)
        altered = []
        for path, node in rgd.flatten(data.nodes):
            if node.key == 'pbgid':
                node.value = identities[key]['pbgid']
            elif node.kind == 'CString' and node.key == 'stamp':
                value = node.value.replace('\\', '/').lower()
                stem_key = next((name for name, stem in EXPECTED_STAMPS.items() if stem == value), None)
                if stem_key is not None and (stem_key == key or
                    (key == 'hideout' and stem_key.startswith('hideout_')) or
                    (key == 'farm_outskirts' and stem_key.startswith('farm_rice_'))):
                    node.value = (PREFIX + stem_key).replace('/', '\\')
                    altered.append({'path': path, 'before': value, 'after': node.value})
        expected = 6 if key == 'hideout' else 12 if key == 'farm_outskirts' else 3
        if len(altered) != expected:
            raise ValueError(f'Incomplete default/cordoba/campaign stamp coverage: {key}, {len(altered)} != {expected}')
        appended = graft_hideout_shelters(data, original) if key == 'hideout' else []
        restored = copy.deepcopy(data)
        for path, node in rgd.flatten(restored.nodes):
            if node.key == 'pbgid': node.value = rgd.find(original.nodes, path).value
        for edit in altered:
            rgd.find(restored.nodes, edit['path']).value = rgd.find(original.nodes, edit['path']).value
        for item in appended:
            node = rgd.find(restored.nodes, item['branch'])
            removed = node.value.pop()
            assert removed.key == 'stamp_attachment'
        if rgd.write(restored) != rgd.write(original):
            raise ValueError(f'Nonvisual compiled list field changed: {key}')
        raw = rgd.write(data)
        payload(identities[key]['final_member'], raw, rows)
        contracts.append({'key': key, 'pbgid': identities[key]['pbgid'],
                          'changed_stamp_fields': altered, 'shelter_appends': appended,
                          'other_compiled_fields_preserved': True})
    write(WORK / 'private-bindings.json', {'status': 'passed', 'payloads': rows,
                                           'attachments': contracts, 'runtime': 'unverified'})
    print('PRIVATE_NATIVE_LISTS_BOUND', len(rows))


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'prepare': prepare()
    elif command == 'cook-identities': cook_identities(sys.argv[2])
    elif command == 'register': register_identities()
    elif command == 'bind': register_identities(); bind_sources(); bind_private_lists()
    else: raise SystemExit(f'Unknown stage: {command}')
