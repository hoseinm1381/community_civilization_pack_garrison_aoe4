"""Private landmark visual lists, actor references, and native stamp copies."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ROOT, OUT, CORE, GUID, guarded, read, run_logged, sha, write
from inventory import ACTORS, native, rgd
from garrison_shared import relic_chunky as rc

WORK = OUT / 'integration'
PROJECT = WORK / 'library/Mods/community_030_bindings'
STAMP_PREFIX = 'art/stamps/cc030/'
MODEL_STEMS = {key: f'art/scenario/cc030/{key}/model' for key in ACTORS}
KEEP_SCENERY_IDS = {
    'pho_minh': {'11212485802703363496', '12473094573824239852', '16722340478678759900'},
    'one_pillar': {'15902656958373433740', '13024810047402634743', '16676802031648753041',
                   '1473984152880311530', '16002710645850460736', '9842216618339277787',
                   '13341991377591162461', '15302648334181979106', '2530708339084611034',
                   '8483420766015341664', '14860642514211660254'},
}


def put(member, raw, rows):
    target = WORK / 'payload' / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'member': member, 'file': str(target), 'sha256': sha(target), 'bytes': target.stat().st_size})


def prepare():
    guarded()
    graph = read(OUT / 'inventory/landmarks.json')['landmarks']
    assert set(graph) == set(ACTORS)
    if not (PROJECT / 'mod-project.json').exists():
        run_logged('bindings-create', [CORE, 'mod-project', 'create', '--library', PROJECT.parent.parent, '--name', PROJECT.name])
    run_logged('bindings-settings', [CORE, 'mod-project', 'settings', '--project', PROJECT,
                                      '--live-reload', 'off', '--mod-id', GUID])
    record = read(PROJECT / 'mod-project.json')
    existing = {r['name'] for r in record.get('derived_blueprints', [])}
    for key, row in graph.items():
        name = f'vn030_{key}_visual'
        if name not in existing:
            run_logged('bindings-derive-' + key, [CORE, 'mod-project', 'derive', '--project', PROJECT,
                                                  '--source', row['principal_source'].replace('\\', '/'), '--name', name])
    record = read(PROJECT / 'mod-project.json')
    assert record['game_mode']['enabled'] is False and record['game_mode']['live_reload'] is False
    write(WORK / 'binding-recipes.json', {k: {'source': v['principal_source'], 'name': f'vn030_{k}_visual'}
                                          for k, v in graph.items()})
    return {'status': 'prepared', 'project': str(PROJECT)}


def cook_identities(label):
    """Caller must hold the shared exclusive native lock for the full call."""
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    pointer_path = WORK / 'identity-cook-pointer.json'
    if pointer_path.is_file():
        pointer = read(pointer_path)
        assert sha(pointer['receipt']) == pointer['sha256']
        receipt = read(pointer['receipt'])
        assert receipt['status'] == 'passed' and sha(receipt['cook']['archive']) == receipt['cook']['sha256']
        return receipt
    native.WORK = WORK
    native.PROJECT = PROJECT
    native.CACHEWORK = OUT / 'inventory'
    native.cook(PROJECT, 'cc030ids-' + label)
    path = WORK / ('cc030ids-' + label + '-cook.json')
    write(WORK / 'identity-cook-pointer.json', {'receipt': str(path), 'sha256': sha(path)})
    return read(path)


def identities():
    pointer = read(WORK / 'identity-cook-pointer.json')
    assert sha(pointer['receipt']) == pointer['sha256']
    cooked = read(pointer['receipt'])
    assert cooked['status'] == 'passed'
    back = Path(cooked['readback'])
    entries = {}
    for key, recipe in read(WORK / 'binding-recipes.json').items():
        generated = f'attrib/attachments/attachment_lists/garrison/{PROJECT.name}/{recipe["name"]}.rgd'
        source = back / generated
        values = {n.value for _, n in rgd.flatten(rgd.read(source.read_bytes()).nodes) if n.key == 'pbgid'}
        assert len(values) == 1, (key, values)
        identity = next(iter(values))
        private_name = f'vn_030_{key}_visual'
        source_rel = f'attrib/instances/attachments/attachment_lists/vietnam/release_030/{private_name}.xml'
        final = f'attrib/attachments/attachment_lists/vietnam/release_030/{private_name}.rgd'
        target = ROOT / 'assets' / source_rel
        root = ET.Element('instance', version='2', description='Private 0.3.0 landmark visual identity',
                          template=r'attachments\attachment_lists')
        ET.SubElement(root, 'uniqueid', name='pbgid', value=str(identity))
        ET.SubElement(root, 'instance_reference', name='parent_pbg', value=recipe['source'])
        ET.indent(root, space='\t')
        raw = ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'
        if target.exists(): assert target.read_bytes() == raw, target
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        entries[key] = {'key': key, 'pbgid': identity, 'source': source_rel, 'private_name': private_name,
                        'generated': generated, 'generated_sha256': sha(source), 'final': final}
    write(WORK / 'registered-identities.json', entries)
    return entries


def bind_sources():
    guarded()
    entries = identities()
    graph = read(OUT / 'inventory/landmarks.json')['landmarks']
    baseline = read(OUT / 'source-baseline.json')['assets']
    changes = []
    for key, names in ACTORS.items():
        stock = graph[key]['principal_source']
        private = f'attachments\\attachment_lists\\vietnam\\release_030\\{entries[key]["private_name"]}'
        for name in names:
            rel = f'attrib/instances/ebps/vietnam/{name}.xml'
            original = (OUT / 'source-baseline' / rel).read_bytes()
            assert sha(OUT / 'source-baseline' / rel) == baseline[rel]['sha256']
            text = original.decode('utf-8-sig')
            pattern = r'(<instance_reference name="attachments" value=")' + re.escape(stock) + r'("[^>]*/>)'
            updated, count = re.subn(pattern, lambda m: m[1] + private + '" mod="' + GUID.replace('-', '') + '"' + m[2][1:], text)
            assert count >= 1, (name, stock)
            target = ROOT / 'assets' / rel
            encoded = updated.encode('utf-8')
            assert target.read_bytes() in (original, encoded), f'Actor source drift: {rel}'
            target.write_bytes(encoded)
            changes.append({'actor': name, 'private': private, 'replacements': count})
    write(WORK / 'source-bindings.json', {'status': 'passed', 'changes': changes})
    return changes


def private_lists():
    guarded()
    graph = read(OUT / 'inventory/landmarks.json')['landmarks']
    entries = read(WORK / 'registered-identities.json')
    rows, reports = [], []
    for key, info in graph.items():
        original = rgd.read(Path(info['principal_file']).read_bytes())
        edited = copy.deepcopy(original)
        stamps = set(info['stamps'])
        modified = []
        for path, node in rgd.flatten(edited.nodes):
            if node.key == 'pbgid':
                node.value = entries[key]['pbgid']
            elif node.key == 'stamp' and node.kind == 'CString' and node.value:
                value = node.value.replace('\\', '/').lower()
                if value in stamps:
                    node.value = (STAMP_PREFIX + key).replace('/', '\\')
                    modified.append({'path': path, 'from': value, 'to': node.value})
        assert modified and len({m['from'] for m in modified}) == 1, (key, modified)
        restored = copy.deepcopy(edited)
        for path, node in rgd.flatten(restored.nodes):
            if node.key == 'pbgid': node.value = rgd.find(original.nodes, path).value
        for row in modified:
            rgd.find(restored.nodes, row['path']).value = rgd.find(original.nodes, row['path']).value
        assert rgd.write(restored) == rgd.write(original), f'Other list field drift: {key}'
        put(entries[key]['final'], rgd.write(edited), rows)
        reports.append({'key': key, 'pbgid': entries[key]['pbgid'], 'stamp_fields': modified,
                        'all_other_native_fields_preserved': True})
    result = {'status': 'passed', 'payloads': rows, 'reports': reports}
    write(WORK / 'private-lists.json', result)
    return result


def private_stamp(source, destination, old_model, new_model, keep_scenery_ids):
    """Clone native stamp; retain the principal and approved perimeter visuals."""
    tree = native.NativeTree(source)
    memory = bytearray(tree.memory.payload)
    objects = bytearray(tree.chunks[b'ROBJ'].payload)
    creation = bytearray(tree.chunks[b'RNEW'].payload)
    ids = {oid: int.from_bytes(hashlib.sha256(('community030:' + str(destination) + ':' + str(oid)).encode()).digest()[:8], 'little')
           for oid in tree.objects}
    changed = []
    for index, (oid, obj) in enumerate(tree.objects.items()):
        at = 8 + index * 36
        old, tid, address, owner, checksum = struct.unpack_from('<QQQQI', objects, at)
        assert old == oid
        struct.pack_into('<QQQQI', objects, at, ids[oid], tid, address, ids.get(owner, 0), checksum)
        for name, field in obj['fields'].items():
            position = obj['offset'] + int(field.get('Offset')) - tree.memory.payload_offset
            if name == 'm_objectID':
                previous = struct.unpack_from('<Q', memory, position)[0]
                if previous in ids: struct.pack_into('<Q', memory, position, ids[previous])
            if name != 'm_blueprint': continue
            previous = tree.field(obj, field)['text'].replace('\\', '/')
            if previous.lower() != old_model.lower(): continue
            assert obj['type'] == 'VisualStampBlueprint' and field.get('FieldTypeName') == 'util::ReflectString<StdTraits>'
            displacement, length = struct.unpack_from('<qQ', memory, position)
            replacement = new_model.replace('/', '\\').encode()
            assert len(replacement) <= length, (old_model, new_model, length)
            start = position + displacement
            memory[start:start+length] = replacement + b'\0' * (length-len(replacement))
            struct.pack_into('<Q', memory, position+8, len(replacement))
            changed.append(previous)
    assert changed == [old_model], changed
    root = next(o for o in tree.objects.values() if o['type'] == 'StampBlueprint' and not o['owner'])
    field = root['fields']['m_blueprints']
    array = tree.field(root, field)
    kept, removed = [], []
    principal = [v['id'] for v in native.active_visuals(tree) if v['model'].lower() == old_model.lower()]
    assert len(principal) == 1
    keep = set(keep_scenery_ids) | set(principal)
    assert set(keep_scenery_ids) <= {v['id'] for v in native.active_visuals(tree)}
    for i in range(array['count']):
        slot = array['data_address'] + 8*i
        obj = tree.by_offset[slot + struct.unpack('<q', tree.bytes(slot, 8))[0]]
        if obj['type'] == 'VisualStampBlueprint' and str(obj['id']) not in keep:
            removed.append(str(obj['id']))
        else:
            kept.append(obj)
    position = root['offset'] + int(field.get('Offset')) - tree.memory.payload_offset
    struct.pack_into('<II', memory, position+8, len(kept), array['capacity'])
    for i, obj in enumerate(kept):
        slot = array['data_address'] + 8*i
        struct.pack_into('<q', memory, slot-tree.memory.payload_offset, obj['offset']-slot)
    for i in range(len(kept), array['count']):
        struct.pack_into('<q', memory, array['data_address']+8*i-tree.memory.payload_offset, 0)
    for index in range(struct.unpack_from('<Q', creation)[0]):
        at = 8 + 29 * index
        oid = struct.unpack_from('<Q', creation, at)[0]
        struct.pack_into('<Q', creation, at, ids[oid])
    edits = {tree.memory.offset: bytes(memory), tree.chunks[b'ROBJ'].offset: bytes(objects),
             tree.chunks[b'RNEW'].offset: bytes(creation)}
    raw = rc.rebuild(tree.document, lambda chunk: edits.get(chunk.offset))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    final = native.NativeTree(destination)
    before, after = native.active_visuals(tree), native.active_visuals(final)
    selected = [v for v in before if v['id'] in keep]
    assert len(after) == len(selected)
    assert all(a['transform'] == b['transform'] for a, b in zip(selected, after))
    assert [v['model'] for v in after].count(new_model) == 1
    assert [v['model'] for v in after if v['model'] != new_model] == [v['model'] for v in selected if v['model'] != old_model]
    return {'source_sha256': sha(source), 'final_sha256': sha(destination), 'replaced': old_model,
            'visuals_before': len(before), 'visuals_retained': len(after), 'removed_visual_ids': removed,
            'retained_visual_ids': sorted(keep), 'object_count_retained': len(tree.objects) == len(final.objects)}


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': print(json.dumps(prepare(), indent=2))
    elif action == 'cook-identities': print(json.dumps(cook_identities(sys.argv[2]), indent=2))
    elif action == 'bind': bind_sources(); private_lists()
    else: raise SystemExit('prepare|cook-identities LABEL|bind')
