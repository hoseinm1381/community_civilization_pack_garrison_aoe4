"""Private 0.5.0 Castle visual identities and exact-source binding stages.

The Garrison identity project is isolated and never becomes the final pack.
`prepare` performs no cook or Content Editor build. Native operations require
the controller's exclusive grant and native-build.lock.
"""
from __future__ import annotations

import copy
import contextlib
import json
import msvcrt
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, BASELINE, CASTLE, CONFIG, CORE, GUID, NATIVE_LOCK, ROOT, WORK, guarded, read, run_logged, sha, write

sys.path.insert(0, CONFIG['garrison_extension'])
sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native
from garrison_shared import rgd
from garrison_shared import relic_chunky as rc
from integration_codec import copy_native_markers

PROJECT = WORK / 'library/Mods/community_050_visual_bindings'
CONTRACT = CASTLE / 'lifecycle/source-contract.json'
REFERENCE = WORK / 'reference-040-actors.json'
SOURCE_BASE = WORK.parent / 'source-baseline/assets'
GUID32 = GUID.replace('-', '')


@contextlib.contextmanager
def exclusive_native():
    guarded()
    with NATIVE_LOCK.open('r+b') as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError('Shared native-build.lock is busy') from error
        try: yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

ORDINARY = {
    'monastery03': ('civilizations/chinese/buildings/unit_religious_chi/tier3_unit_religious_control_chi',
                    ('vn_building_unit_religious_control_chi',)),
    'monastery04': ('civilizations/chinese/buildings/unit_religious_chi/tier4_unit_religious_control_chi',
                    ('vn_building_unit_religious_control_chi',)),
    'siege_workshop03': ('civilizations/chinese/buildings/unit_siege_chi/tier3_unit_siege_control_chi',
                         ('vn_building_unit_siege_control_chi',)),
    'siege_workshop04': ('civilizations/chinese/buildings/unit_siege_chi/tier4_unit_siege_control_chi',
                         ('vn_building_unit_siege_control_chi',)),
    'keep03': ('civilizations/chinese/buildings/defense_keep_chi/tier3_keep_chi',
               ('vn_building_defense_keep_chi', 'vn_building_defense_keep_2_chi')),
}

LANDMARK_ACTOR = {
    'imperial_citadel': 'vn_building_landmark_age2_imperrial_citadel_vit',
    'resistance_hq': 'vn_building_landmark_age2_headquarter_vit',
}


def specs():
    lifecycle = read(CONTRACT)
    assert lifecycle['status'] == 'passed_static_native_graph'
    rows = {}
    for key, (subpath, actors) in ORDINARY.items():
        rows[key] = {'key': key, 'kind': 'ordinary', 'source': 'attachments/attachment_lists/' + subpath,
                     'actors': list(actors), 'derived_name': 'vn050_' + key + '_visual',
                     'name': 'vn_050_' + key + '_visual'}
    for actor in lifecycle['actors']:
        key = actor['key']
        assert actor['actor'] == LANDMARK_ACTOR[key]
        primary, outskirts = actor['tiers']
        assert len(primary['stamps']) in (1, 4)
        assert len(outskirts['stamps']) >= 12
        for suffix, tier in (('', primary), ('_outskirts', outskirts)):
            name = key + suffix
            rows[name] = {'key': name, 'kind': 'landmark' if not suffix else 'outskirts',
                          'source': 'attachments/attachment_lists/' + tier['reference'].split('attachment_lists\\', 1)[1].replace('\\', '/'),
                          'actors': [actor['actor']], 'derived_name': 'vn050_' + name + '_visual',
                          'name': 'vn_050_' + name + '_visual'}
    assert len(rows) == 9 and len({r['source'] for r in rows.values()}) == 9
    return rows


def prepare():
    guarded()
    freeze = read(WORK.parent / 'baseline/freeze-baseline.json')
    assert freeze['status'] == 'immutable_pre_050_baseline'
    assert sha(BASELINE) == freeze['accepted_release_040']['embedded_sga']['sha256']
    assert read(REFERENCE)['accepted_archive_sha256'] == sha(BASELINE)
    recipes = specs()
    if not (PROJECT / 'mod-project.json').exists():
        run_logged('bindings050-create', [CORE, 'mod-project', 'create', '--library', PROJECT.parent.parent,
                                           '--name', PROJECT.name])
    run_logged('bindings050-settings', [CORE, 'mod-project', 'settings', '--project', PROJECT,
                                       '--live-reload', 'off', '--mod-id', GUID])
    current = read(PROJECT / 'mod-project.json')
    existing = {r['name'] for r in current.get('derived_blueprints', [])}
    for key, recipe in recipes.items():
        if recipe['derived_name'] not in existing:
            run_logged('bindings050-derive-' + key, [CORE, 'mod-project', 'derive',
                       '--project', PROJECT, '--source', recipe['source'],
                       '--name', recipe['derived_name']])
    current = read(PROJECT / 'mod-project.json')
    assert current['game_mode']['enabled'] is False and current['game_mode']['live_reload'] is False
    write(WORK / 'binding-recipes.json', {
        'schema': 'ccp.release050.binding-recipes/v1', 'status': 'prepared',
        'project': str(PROJECT), 'project_guid': GUID, 'recipes': recipes,
        'accepted_archive_sha256': sha(BASELINE),
    })
    print('BINDINGS050_PREPARED', len(recipes), PROJECT, flush=True)
    return recipes


def cook_identities(label):
    """Run only after controller grant; also take shared native-build.lock."""
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label), label
    pointer = WORK / 'identity-cook-pointer.json'
    assert not pointer.exists(), 'Identity cook already registered; preserve its PBG IDs'
    recipes = read(WORK / 'binding-recipes.json')
    assert recipes['status'] == 'prepared'
    with exclusive_native():
        native.WORK, native.PROJECT, native.CACHEWORK = WORK, PROJECT, WORK
        native.cook(PROJECT, 'cc050ids-' + label)
    receipt = WORK / ('cc050ids-' + label + '-cook.json')
    cooked = read(receipt)
    assert cooked['status'] == 'passed'
    write(pointer, {'receipt': str(receipt), 'sha256': sha(receipt),
                    'canonical_project': str(PROJECT),
                    'canonical_config_sha256': sha(PROJECT / 'mod-project.json')})
    print('BINDINGS050_IDENTITIES_COOKED', label, sha(receipt), flush=True)
    return cooked


def identity_xml(pbgid, parent, description):
    doc = ET.Element('instance', version='2', description=description,
                     template=r'attachments\attachment_lists')
    ET.SubElement(doc, 'uniqueid', name='pbgid', value=str(pbgid))
    ET.SubElement(doc, 'instance_reference', name='parent_pbg', value=parent)
    ET.indent(doc, space='\t')
    return ET.tostring(doc, encoding='utf-8', xml_declaration=True) + b'\n'


def identity_records():
    pointer = read(WORK / 'identity-cook-pointer.json')
    assert sha(pointer['receipt']) == pointer['sha256']
    cooked = read(pointer['receipt'])
    assert cooked['status'] == 'passed'
    back = Path(cooked['readback'])
    entries = {}
    for key, recipe in read(WORK / 'binding-recipes.json')['recipes'].items():
        generated = (f'attrib/attachments/attachment_lists/garrison/{PROJECT.name}/'
                     f'{recipe["derived_name"]}.rgd')
        compiled = back / generated
        assert compiled.is_file(), compiled
        values = {n.value for _, n in rgd.flatten(rgd.read(compiled.read_bytes()).nodes)
                  if n.key == 'pbgid'}
        assert len(values) == 1
        pbgid = next(iter(values))
        relative = (f'attrib/instances/attachments/attachment_lists/vietnam/release_050/'
                    f'{recipe["name"]}.xml')
        entries[key] = {**recipe, 'pbgid': pbgid, 'source_xml': relative,
                        'member': f'attrib/attachments/attachment_lists/vietnam/release_050/{recipe["name"]}.rgd',
                        'generated_member': generated,
                        'identity_source_sha256': sha(compiled)}
    assert len({row['pbgid'] for row in entries.values()}) == len(entries) == 9
    return entries


def transform_actor(relative, original, entries):
    """One exact visual-reference rewrite from frozen 0.4.0 source bytes."""
    text = original.decode('utf-8-sig')
    actor = Path(relative).stem
    changes = []
    if actor == 'vn_building_unit_religious_control_chi':
        # The installed editor silently ignores inherited-item overrides for
        # this actor. Keep its accepted 0.4 source byte-identical; native_source
        # applies and proves four exact compiled visual-reference leaves.
        assert 'tier_ext' not in text and text.count('<list name="extensions">') == 2
        changes.append({'kind': 'compiled-visual-overlay-only', 'branches': ['default', 'campaign'],
                        'tiers': [3, 4]})
    else:
        selected = {key: row for key, row in entries.items() if actor in row['actors']}
        assert selected, actor
        for key, row in selected.items():
            old = row['source'].replace('/', '\\')
            new = f'attachments\\attachment_lists\\vietnam\\release_050\\{row["name"]}'
            pattern = r'(<instance_reference name="attachments" value=")' + re.escape(old) + r'("[^>]*/>)'
            replacement = lambda m: m[1] + new + f'" mod="{GUID32}"' + m[2][1:]
            text, count = re.subn(pattern, replacement, text)
            expected = 3 if row['kind'] in ('landmark', 'outskirts') else 2
            assert count == expected, (relative, key, count, expected)
            changes.append({'key': key, 'from': old, 'to': new, 'count': count})
    return text.encode('utf-8'), changes


def register_and_bind_sources():
    guarded()
    freeze = read(WORK.parent / 'baseline/freeze-baseline.json')
    assert freeze['status'] == 'immutable_pre_050_baseline'
    entries = identity_records()
    for key, row in entries.items():
        relative = row['source_xml']
        target = ROOT / 'assets' / relative
        data = identity_xml(row['pbgid'], row['source'].replace('/', '\\'),
                            'Private 0.5.0 Vietnamese Castle visual identity')
        if target.exists():
            assert target.read_bytes() == data, relative
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        row['source_sha256'] = sha(target)
    assert len(entries) == 9
    actor_rows = []
    actors = sorted({actor for row in entries.values() for actor in row['actors']})
    assert len(actors) == 6
    for actor in actors:
        relative = f'attrib/instances/ebps/vietnam/{actor}.xml'
        frozen = SOURCE_BASE / relative
        target = ROOT / 'assets' / relative
        assert frozen.is_file()
        original = frozen.read_bytes()
        expected, changes = transform_actor(relative, original, entries)
        assert target.read_bytes() in (original, expected), f'Unexpected active source drift: {relative}'
        target.write_bytes(expected)
        actor_rows.append({'actor': actor, 'source': relative, 'before_sha256': sha(frozen),
                           'after_sha256': sha(target), 'changes': changes})
    write(WORK / 'registered-identities.json', {'status': 'passed', 'entries': entries})
    write(WORK / 'source-bindings.json', {'status': 'passed', 'actors': actor_rows,
                                        'visual_only_source_delta': True})
    print('BINDINGS050_SOURCE_REGISTERED', len(entries), len(actor_rows), flush=True)
    return entries


def _payload(member, raw, rows):
    assert member.startswith(('attrib/attachments/attachment_lists/vietnam/release_050/',
                              'art/stamps/cc050/', 'art/scenario/cc050/')), member
    target = WORK / 'payload' / member
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, member
    else:
        target.write_bytes(raw)
    row = {'member': member, 'file': str(target), 'sha256': sha(target), 'bytes': len(raw)}
    if member not in {r['member'] for r in rows}: rows.append(row)
    return target


def _model_map():
    building = read(CASTLE / 'integration/building-media.json')
    landmark = read(CASTLE / 'integration/landmark-media.json')
    assert building['status'] == landmark['status'] == 'passed'
    models = {}
    for row in building['models'] + landmark['models']:
        key = row['key'].removeprefix('vn_').replace('_age0', '0')
        models[key] = row['model']
    assert len(models) == 12
    return models, {r['member']: r for r in building['payloads'] + landmark['payloads']}


def _branch_variant(rows, source_media, model, stock_owner):
    """A branch-specific marker/RGO owner with the already qualified visual mesh."""
    assert model == 'art/scenario/cccastle/imperial_citadel/model'
    branch = 'art/scenario/cc050/imperial_citadel_campaign/model'
    official = native.stock(stock_owner + '.rgm').read_bytes()
    primary_owner = native.stock('art/civilizations/chinese/structures/wonder_greatwall_mp/wonder_greatwall_mp.rgm').read_bytes()
    conditions = lambda raw: [c.payload for c in rc.walk(rc.parse(raw).roots) if c.tag == b'CNBP']
    assert conditions(primary_owner) == conditions(official), 'Branch lifecycle conditions differ'
    source = Path(source_media[model + '.rgm']['file'])
    raw, marker_proof = copy_native_markers(source.read_bytes(), official)
    primary_authored_conditions = conditions(source.read_bytes())
    assert len(primary_authored_conditions) == 6
    branch_model = _payload(branch + '.rgm', native.rebase_model(raw, branch), rows)
    assert conditions(branch_model.read_bytes()) == primary_authored_conditions
    native_rgo = native.stock(stock_owner + '.rgo')
    branch_rgo = _payload(branch + '.rgo', native_rgo.read_bytes(), rows)
    assert branch_rgo.read_bytes() == native_rgo.read_bytes()
    for suffix in ('.rrgeom', '.rrmaterial'):
        _payload(branch + suffix, Path(source_media[model + suffix]['file']).read_bytes(), rows)
    return branch, {'model': branch, 'branch_native_owner': stock_owner,
                    'branch_native_rgo_sha256': sha(native.stock(stock_owner + '.rgo')),
                    'native_marker_copy': marker_proof,
                    'branch_cnbp_payloads_identical_to_primary_stock': True,
                    'authored_six_cnbp_payloads_byte_identical_to_primary': True,
                    'branch_native_rgo_byte_identical': True,
                    'authored_selector_predicates_retained': True,
                    'fresh_native_reference': 'pending'}


def _source_stamp(path):
    return native.stock(path.replace('\\', '/') + '.bin')


def _main_stamp(source_stamp, target_stamp, new_model, *, remove_decor=False):
    origin = _source_stamp(source_stamp)
    tree = native.NativeTree(origin)
    visuals = native.active_visuals(tree)
    assert visuals
    owners = [v for v in visuals if v['model'].startswith('art/civilizations/chinese/') or
              v['model'].startswith('art/civilizations/chinese_ha_01/')]
    if new_model.endswith('/model') and new_model.startswith(('art/scenario/cccastle/',
                                                              'art/scenario/cc050/')):
        owner = next(v for v in owners if '/structures/' in v['model'])
    else: raise AssertionError(new_model)
    removed = [v['id'] for v in visuals if remove_decor and v['id'] != owner['id'] and
               '/debris/' not in v['model']]
    output = WORK / 'payload' / (target_stamp + '.bin')
    report = native.private_stamp(origin, output, {owner['model']: new_model}, removed)
    final = native.active_visuals(native.NativeTree(output))
    assert sum(v['model'] == new_model for v in final) == 1
    assert len(final) == len(visuals) - len(removed)
    report['reviewed_visual_removals'] = [
        {'id': v['id'], 'model': v['model'], 'transform': v['transform'],
         'reason': ('vegetation clearance for authored full compound'
                    if '/bush' in v['model'] or '/hedge' in v['model'] or '/flower' in v['model']
                    else 'stock healthy dressing replaced by authored full compound')}
        for v in visuals if v['id'] in removed]
    report['retained_ruin_debris_visual_ids'] = [
        v['id'] for v in final if '/debris/' in v['model']]
    return report


def _detail_stamp(key, model, rows):
    source_name = 'detail_' + re.sub(r'0([34])$', r'_age0\1', key)
    source = (CASTLE / 'integration/readback-ccnext-rdet01-a950fc203176/art/stamps/garrison/'
              'community_castle_next_details' / (source_name + '.bin'))
    assert source.is_file(), source
    visuals = native.active_visuals(native.NativeTree(source))
    assert len(visuals) == 1 and visuals[0]['model'].endswith('/' + source_name + '/model')
    stamp = 'art/stamps/cc050/' + key + '_detail'
    target = WORK / 'payload' / (stamp + '.bin')
    report = native.private_stamp(source, target, {visuals[0]['model']: model})
    _payload(stamp + '.bin', target.read_bytes(), rows)
    return stamp, report


def _outskirts_stamp(source_stamp, target_stamp):
    origin = _source_stamp(source_stamp)
    visuals = native.active_visuals(native.NativeTree(origin))
    # This marker is a native outskirt consumer; only foliage gets suppressed.
    removed = [v['id'] for v in visuals if not v['model'].endswith('/outskirt_marker')]
    output = WORK / 'payload' / (target_stamp + '.bin')
    report = native.private_stamp(origin, output, {}, removed)
    assert all(v['model'].endswith('/outskirt_marker') for v in
               native.active_visuals(native.NativeTree(output)))
    report['reviewed_visual_removals'] = [
        {'id': v['id'], 'model': v['model'], 'transform': v['transform'],
         'reason': 'stock outskirts vegetation suppressed for authored full compound'}
        for v in visuals if v['id'] in removed]
    report['retained_outskirt_marker_ids'] = [
        v['id'] for v in native.active_visuals(native.NativeTree(output))]
    return report


def assemble():
    """Pure private resource assembly; no native cook and no active source writes."""
    guarded()
    entries = read(WORK / 'registered-identities.json')['entries']
    models, source_media = _model_map()
    native.CACHEWORK = WORK / 'reference-stock'
    rows, reports, variants = [], {}, []
    campaign_owner = 'art/civilizations/chinese/structures/wonder_greatwall/wonder_greatwall'
    campaign_model, variant = _branch_variant(rows, source_media, models['imperial_citadel'], campaign_owner)
    variants.append(variant)
    for key, entry in entries.items():
        source = native.stock('attrib/' + entry['source'] + '.rgd')
        original = rgd.read(source.read_bytes())
        changed = copy.deepcopy(original)
        stamp_map, stamp_reports, slots = {}, [], []
        for path, node in rgd.flatten(changed.nodes):
            if node.key != 'stamp' or not node.value: continue
            source_stamp = node.value.replace('\\', '/')
            if key.endswith('_outskirts'):
                stamp_key = key + '_' + source_stamp.rsplit('/', 1)[-1]
                private = 'art/stamps/cc050/' + stamp_key
                if source_stamp not in stamp_map:
                    stamp_reports.append(_outskirts_stamp(source_stamp, private))
                    _payload(private + '.bin', (WORK / 'payload' / (private + '.bin')).read_bytes(), rows)
                    stamp_map[source_stamp] = private
            elif source_stamp.startswith('art/stamps/civ_chinese/'):
                branch = ('campaign' if key == 'imperial_citadel' and
                          source_stamp.endswith('chi_wonder_great_wall') else 'default')
                private = 'art/stamps/cc050/' + key + '_base_' + branch
                if source_stamp not in stamp_map:
                    selected = campaign_model if branch == 'campaign' else models[key]
                    stamp_reports.append(_main_stamp(source_stamp, private, selected,
                                                     remove_decor=entry['kind'] == 'landmark'))
                    _payload(private + '.bin', (WORK / 'payload' / (private + '.bin')).read_bytes(), rows)
                    stamp_map[source_stamp] = private
            else: continue  # Stock construction/destroyed stamps remain exact.
            node.value = stamp_map[source_stamp].replace('/', '\\')
            slots.append({'path': path, 'source': source_stamp, 'private': stamp_map[source_stamp]})
        assert stamp_map, key
        if entry['kind'] == 'ordinary':
            detail_key = 'detail_' + key
            detail_model = models[detail_key]
            detail_stamp, report = _detail_stamp(key, detail_model, rows)
            stamp_reports.append(report)
            for branch in ('default', 'cordoba', 'campaign'):
                list_path = branch + '/attachment_lists/attachment_lists/attachment_list/attachment_list'
                selected = rgd.find(changed.nodes, list_path)
                original_list = rgd.find(original.nodes, list_path)
                assert selected.kind == 'List2' and len(selected.value) == len(original_list.value)
                template = copy.deepcopy(selected.value[0])
                assert template.key == 'stamp_attachment'
                assert next(n.value for n in template.value if n.key == 'add_impass_blockers') is False
                next(n for n in template.value if n.key == 'stamp').value = detail_stamp.replace('/', '\\')
                selected.value.append(template)
        else:
            assert entry['kind'] in ('landmark', 'outskirts')
        assert entry['member'].startswith('attrib/attachments/')
        pid = rgd.find(changed.nodes, 'default/pbgid')
        pid.value = entry['pbgid']
        restored = copy.deepcopy(changed)
        if entry['kind'] == 'ordinary':
            for branch in ('default', 'cordoba', 'campaign'):
                selected = rgd.find(restored.nodes,
                    branch + '/attachment_lists/attachment_lists/attachment_list/attachment_list')
                selected.value.pop()
        prior_fields = dict(rgd.flatten(original.nodes))
        changed_stamp_paths = {s['path'] for s in slots}
        for path, node in rgd.flatten(restored.nodes):
            if path == 'default/pbgid' or path in changed_stamp_paths:
                node.value = prior_fields[path].value
        assert rgd.write(restored) == rgd.write(original), ('Nonvisual list drift', key)
        target = _payload(entry['member'], rgd.write(changed), rows)
        reread = rgd.read(target.read_bytes())
        assert rgd.find(reread.nodes, 'default/pbgid').value == entry['pbgid']
        reports[key] = {'source_list': entry['source'], 'source_sha256': sha(source),
                        'private_list': entry['member'], 'private_sha256': sha(target),
                        'rewired_visual_stamps': slots, 'private_stamp_proofs': stamp_reports,
                        'stock_nonvisual_stamps_retained': True,
                        'all_other_list_bytes_identical_after_visual_reversal': True,
                        'native_runtime': 'unverified'}
    assert len(reports) == 9 and len({r['member'] for r in rows}) == len(rows)
    report = {'schema': 'ccp.release050.private-bindings/v1', 'status': 'passed',
              'payloads': rows, 'bindings': reports, 'branch_variants': variants,
              'accepted_archive_sha256': sha(BASELINE),
              'active_source_binding_status': read(WORK / 'source-bindings.json')['status'],
              'native_runtime': 'unverified'}
    write(WORK / 'private-bindings.json', report)
    print('BINDINGS050_PRIVATE_PAYLOADS', len(rows), flush=True)
    return report


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': prepare()
    elif action == 'cook-identities': cook_identities(sys.argv[2])
    elif action == 'bind-sources': register_and_bind_sources()
    elif action == 'assemble': assemble()
    else: raise SystemExit('prepare|cook-identities LABEL|bind-sources|assemble')
