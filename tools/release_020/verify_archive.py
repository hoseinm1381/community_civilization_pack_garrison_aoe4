"""Independent byte and typed-graph audit of the 0.2.0 candidate archive."""
import json
import subprocess
import sqlite3
from functools import lru_cache
import sys
from pathlib import Path
from common import ARCH, CONFIG, GUID, OUT, ROOT, guarded, read, sha, write
from inventory import SOURCES, EXPECTED_STAMPS, native, rgd
from source_policy import CONSUMERS
from garrison_shared import relic_chunky as rc, model_variants as mv

sys.dont_write_bytecode = True
WORK = OUT / 'integration'
BASELINE = ROOT / 'archives/release_010_user_accepted/community_civilization_pack.sga'


def listing(path):
    result = subprocess.run([str(ARCH), 'list', str(path), '--verify'], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', check=True)
    data = json.loads(result.stdout)
    assert data['archive']['verification']['verified']
    assert data['archive']['name'].replace('-', '').lower() == GUID.replace('-', '').lower()
    return {entry['path'].lower(): entry for entry in data['members']}


def unpack(path, label):
    output = OUT / 'verification-readback' / (label + '-' + sha(path)[:16])
    marker = output / '.readback-complete.json'
    if not marker.exists():
        if output.exists(): raise ValueError(f'Incomplete readback retained at {output}')
        result = subprocess.run([str(ARCH), 'unpack', str(path), '--output', str(output)],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode: raise RuntimeError(result.stdout + result.stderr)
        write(marker, {'archive': str(path), 'sha256': sha(path)})
    assert read(marker)['sha256'] == sha(path)
    return output


def compiled_actor_proof(before, after, name, source_map, final_map):
    member = f'attrib/ebps/vietnam/{name}.rgd'
    old = rgd.read((before / member).read_bytes())
    new = rgd.read((after / member).read_bytes())
    restored = rgd.read((after / member).read_bytes())
    a, b = dict(rgd.flatten(old.nodes)), dict(rgd.flatten(new.nodes))
    assert a.keys() == b.keys(), (name, 'compiled shape changed')
    changes = []
    for path, original in a.items():
        node = b[path]
        if original.kind == 'CString' and original.key == '$PBGNAME' and path.endswith(('/attachments/$PBGNAME', '/animator_attachments/$PBGNAME')):
            key = source_map.get(original.value)
            if key and key in final_map[name]:
                target = GUID.replace('-', '') + ':' + final_map[name][key]
                assert node.value == target, (name, path, node.value, target)
                rgd.find(restored.nodes, path).value = original.value
                changes.append({'path': path, 'from': original.value, 'to': target})
    if not changes or rgd.write(restored) != rgd.write(old):
        raise ValueError(f'Unexpected compiled gameplay delta: {name}')
    return {'member': member, 'visual_changes': changes, 'all_other_compiled_fields_identical': True}


def private_binding_proof(after, graph, identities):
    records = []
    binding_contract = {row['key']: row for row in read(WORK / 'private-bindings.json')['attachments']}
    for key, official in graph['attachments'].items():
        row = identities[key]
        target = after / row['final_member']
        original = rgd.read(Path(official['file']).read_bytes())
        current = rgd.read(target.read_bytes())
        restored = rgd.read(target.read_bytes())
        a, b = dict(rgd.flatten(original.nodes)), dict(rgd.flatten(current.nodes))
        extras = set(b) - set(a)
        assert not (set(a) - set(b))
        appended = binding_contract[key]['shelter_appends']
        if key == 'hideout':
            assert len(appended) == 6
            expected_extra = {item['branch'] + f"/stamp_attachment[{item['slot']}]" + suffix
                for item in appended for suffix in ('', '/stamp', '/$REF', '/add_impass_blockers')}
            assert extras == expected_extra, ('unexpected native Hideout shape', extras ^ expected_extra)
            assert {(item['variant'], item['slot'], item['stamp']) for item in appended} == {
                ('default', 2, 'art/stamps/cc020/hideout_shelter_default'),
                ('default', 2, 'art/stamps/cc020/hideout_shelter_stone'),
                ('cordoba', 2, 'art/stamps/cc020/hideout_shelter_default'),
                ('cordoba', 2, 'art/stamps/cc020/hideout_shelter_stone'),
                ('campaign', 3, 'art/stamps/cc020/hideout_shelter_default'),
                ('campaign', 2, 'art/stamps/cc020/hideout_shelter_stone')}
            for item in appended:
                prefix = item['branch'] + f"/stamp_attachment[{item['slot']}]"
                assert b[prefix + '/stamp'].value.replace('\\', '/').lower() == item['stamp']
                assert b[prefix + '/$REF'].value == 'options\\attachment_types\\stamp_attachment'
                assert b[prefix + '/add_impass_blockers'].value is False
                assert (after / (item['stamp'] + '.bin')).is_file()
                removed = rgd.find(restored.nodes, item['branch']).value.pop()
                assert removed.key == 'stamp_attachment'
            campaign = 'campaign/attachment_lists/attachment_lists/attachment_list/attachment_list/stamp_attachment[2]/stamp'
            assert a[campaign].value == b[campaign].value == r'art\stamps\scaffolding\west\west_outpost'
        else:
            assert not extras and not appended, key
        stamps = []
        for path in a:
            node = b[path]
            old = a[path]
            if node.key == 'pbgid':
                assert node.value == row['pbgid']
                rgd.find(restored.nodes, path).value = old.value
            elif node.kind == 'CString' and node.key == 'stamp' and old.value != node.value:
                original_stem = old.value.replace('\\', '/').lower()
                stamp_key = next((k for k, v in EXPECTED_STAMPS.items() if v == original_stem), None)
                assert stamp_key and node.value.replace('\\', '/').lower() == f'art/stamps/cc020/{stamp_key}'
                assert (after / f'art/stamps/cc020/{stamp_key}.bin').is_file()
                rgd.find(restored.nodes, path).value = old.value
                stamps.append(stamp_key)
        assert stamps and rgd.write(restored) == rgd.write(original), key
        records.append({'member': row['final_member'], 'stamp_references': stamps,
                        'private_shelter_stamps': appended,
                        'all_other_compiled_fields_identical': True})
    return records


def private_media_closure(after, candidate, binding_rows):
    """Resolve every private and retained official visual terminal from all variants."""
    native.CACHEWORK = OUT / 'inventory'
    visited, official, stamp_checks = {}, {}, []
    private_stamps = {f'art/stamps/cc020/{key}' for key in candidate['stamp_model_targets']}
    stamp_stems = set()
    for row in binding_rows:
        doc = rgd.read((after / row['member']).read_bytes())
        for path, node in rgd.flatten(doc.nodes):
            if node.kind != 'CString' or not node.value: continue
            value = node.value.replace('\\', '/').lower()
            if node.key == 'stamp': stamp_stems.add(value)
            elif node.key == 'parent_animator' and value:
                for suffix in ('.rgm', '.rgo'):
                    member = value + suffix
                    assert native.stock(member).is_file(), (row['member'], path, value)
                    official[member] = read(OUT / 'inventory/official-index.json')[member]
    assert private_stamps <= stamp_stems
    all_models = set()
    for stem in sorted(stamp_stems):
        member = stem + '.bin'
        if stem.startswith('art/stamps/cc020/'):
            path = after / member
            assert path.is_file(), member
            visited[member] = sha(path)
        else:
            path = native.stock(member)
            official[member] = read(OUT / 'inventory/official-index.json')[member]
        visuals = native.active_visuals(native.NativeTree(path))
        models = {row['model'].replace('\\', '/').lower() for row in visuals}
        all_models |= models
        if stem in private_stamps:
            key = stem.rsplit('/', 1)[1]
            expected = {'art/scenario/cc020/' + target + '/model'
                        for target in candidate['stamp_model_targets'][key]}
            assert expected <= models, (key, expected, models)
            private = sorted(model for model in models if model.startswith('art/scenario/cc020/'))
            assert set(private) == expected, (key, private, expected)
            stamp_checks.append({'member': member, 'private_visuals': private,
                                 'active_visual_count': len(visuals)})
    for stem in sorted(all_models):
        private = stem.startswith('art/scenario/cc020/')
        doc = rc.load(after / (stem + '.rgm') if private else native.stock(stem + '.rgm'))
        marker = False
        if not private and not any(c.tag in (b'MSCL', b'GEOB') for c in rc.walk(doc.roots)):
            # Native behavior-only models have RGM/RGO but no render geometry.
            # Admit this only when the installed authoritative asset index also
            # confirms both geometry and material are absent; private models
            # must always supply their complete resource set.
            with sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro', uri=True) as database:
                marker = all(database.execute(
                    'select 1 from resolved_assets where lower(logical_path)=?',
                    (stem + suffix,)).fetchone() is None for suffix in ('.rrgeom', '.rrmaterial'))
        suffixes = ('.rgm', '.rgo') if marker else ('.rgm', '.rgo', '.rrgeom', '.rrmaterial')
        for suffix in suffixes:
            member = stem + suffix
            if private:
                path = after / member
                assert path.is_file(), member
                visited[member] = sha(path)
            else:
                path = native.stock(member)
                official[member] = read(OUT / 'inventory/official-index.json')[member]
        if private:
            bana = [c for c in rc.walk(doc.roots) if c.tag == b'BANA']
            assert len(bana) == 1
            name, _ = rc.read_lp_string(bana[0].payload, 0)
            assert name.replace('\\', '/').lower() == stem
        if marker:
            assert not any(c.tag in (b'MSCL', b'GEOB') for c in rc.walk(doc.roots))
            continue
        material = rc.load(after / (stem + '.rrmaterial') if private else native.stock(stem + '.rrmaterial'))
        for root in material.roots:
            if root.tag != b'GMat': continue
            raw = rc.pack_document([rc.pack_chunk(root.kind, root.tag, root.payload,
                                                  name=root.name, version=root.version)])
            for slot, value in mv.material_slots(raw)['textures'].items():
                if not value or value == '__default': continue
                member = value.replace('\\', '/').lower()
                if not member.endswith('.rrtex'): member += '.rrtex'
                if member.startswith('art/scenario/cc020/'):
                    path = after / member
                    assert path.is_file(), member
                    visited[member] = sha(path)
                else:
                    assert native.stock(member).is_file(), member
                    official[member] = read(OUT / 'inventory/official-index.json')[member]
    for member, record in official.items():
        assert sha(record['file']) == record['sha256']
        archive = Path(record['archive']['path'])
        stat = archive.stat()
        assert stat.st_size == record['archive']['size'] and stat.st_mtime_ns == record['archive']['mtime_ns']
    return stamp_checks, visited, official


def verify(candidate_path):
    frozen = guarded()
    candidate_path = Path(candidate_path)
    candidate = read(candidate_path)
    archive = Path(candidate['archive'])
    assert candidate['status'] == 'passed' and sha(archive) == candidate['sha256']
    assert sha(BASELINE) == frozen['accepted_release_010']['sga_sha256']
    prior, final = listing(BASELINE), listing(archive)
    assert set(prior) <= set(final), '0.1.0 archive member dropped'
    before, after = unpack(BASELINE, 'accepted-010'), unpack(archive, 'candidate-020')
    changed = [member for member in prior if sha(before / prior[member]['path']) != sha(after / final[member]['path'])]
    expected = {f'attrib/ebps/vietnam/{name}.rgd' for name in CONSUMERS}
    assert set(changed) == expected, ('Existing archive allowlist mismatch', changed)
    new = sorted(set(final) - set(prior))
    assert all(member.startswith(('art/scenario/cc020/', 'art/stamps/cc020/', 'attrib/attachments/attachment_lists/vietnam/release_020/vn_020_'))
               for member in new), ('Private namespace escaped', new)
    assert set(new) == set(candidate['new_members'])
    graph = read(OUT / 'inventory/native-graph.json')
    identities = {row['key']: row for row in read(OUT / 'integration/registered-identities.json')}
    # Native RGD $PBGNAME stores the leaf identity, rather than the editable
    # XML's full category path. Keep both supported representations explicit.
    source_map = {source: key for key, source in SOURCES.items()}
    for key, source in SOURCES.items():
        leaf = source.replace('/', '\\').rsplit('\\', 1)[-1]
        assert leaf not in source_map or source_map[leaf] == key
        source_map[leaf] = key
    final_map = {name: {key: identities[key]['name'] for key in graph['consumers'][name]['matching_private_sources']}
                 for name in CONSUMERS}
    actors = [compiled_actor_proof(before, after, name, source_map, final_map) for name in CONSUMERS]
    bindings = private_binding_proof(after, graph, identities)
    # Resolve each official asset once per audit. The closure's final loop still
    # rehashes every terminal and checks its owning archive fingerprint.
    stock_resolver = native.stock
    native.stock = lru_cache(maxsize=None)(stock_resolver)
    try:
        stamps, media, official = private_media_closure(after, candidate, bindings)
    finally:
        native.stock = stock_resolver
    visited = {row['member'] for row in bindings} | {row['member'] for row in stamps} | set(media)
    assert set(new) == visited, ('unvisited private archive member', sorted(set(new) ^ visited))
    for row in candidate['payloads']:
        assert sha(after / row['member']) == row['sha256'], row['member']
    result = {'status': 'passed', 'baseline_sha256': sha(BASELINE), 'sga_sha256': sha(archive),
              'candidate_sha256': sha(candidate_path), 'baseline_members': len(prior),
              'final_members': len(final), 'changed_existing_members': sorted(changed),
              'unchanged_existing_member_count': len(prior)-len(changed),
              'new_members': new, 'compiled_actors': actors, 'private_bindings': bindings,
              'private_stamps': stamps, 'private_media_sha256': media,
              'official_terminal_resources': official,
              'all_new_members_typed_visited': True,
              'all_other_010_members_byte_identical': True, 'native_runtime': 'unverified'}
    write(OUT / 'archive-verification.json', result)
    print('ARCHIVE_020_VERIFIED', len(prior), len(final), len(changed), len(new))
    return result


if __name__ == '__main__':
    verify(Path(sys.argv[1]))
