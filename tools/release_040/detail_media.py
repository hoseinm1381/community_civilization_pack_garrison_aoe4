"""Cook authored building frontage details and attach them with native stamp lists."""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

from common import ROOT, OUT, CORE, GUID, guarded, read, run_logged, sha, write
from bindings import WORK, building_contracts

sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native
from integration_codec import intact_damage_conditions
from garrison_shared import relic_chunky as rc, rgd, model_variants as mv

HANDOFF = ROOT / 'art/recipes/release_040/building-details-source.json'
DETAIL = OUT / 'details'
PROJECT_NAME = 'community_040_details'
FAMILIES = ('blacksmith', 'stable', 'archery_range', 'market')


def inputs():
    handoff = read(HANDOFF)
    assert len(handoff['models']) == 12
    keys = {(family, age) for family in FAMILIES for age in (2, 3, 4)}
    assert {(r['family'], r['age']) for r in handoff['models']} == keys
    for row in handoff['models']:
        folder = Path(row['export_directory'])
        files = {p.name: sha(p) for p in folder.iterdir() if p.is_file()}
        assert files == row['export_sha256']
        assert {'building.json', 'model.fbx', 'albedo.png', 'normal.png',
                'roughness.png', 'metalness.png'} <= set(files)
        assert sha(row['editable_blend']) == row['editable_blend_sha256']
        doc = read(folder / 'building.json')
        assert doc['schema'] == 'garrison.building-source/v1' and doc['profile'] == 'english-house'
        assert [p['name'] for p in doc['parts']] == [f'garrison_part_{i:04d}' for i in range(3)]
        assert [p['first_stage'] for p in doc['parts']] == [0, 40, 80]
        row['parts'] = doc['parts']
    return handoff


def cook(label):
    """Caller holds the shared exclusive native-cook lock."""
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    frozen = inputs()
    project = DETAIL / 'cook' / label / 'library/Mods' / PROJECT_NAME
    assert not project.exists()
    project.parent.parent.mkdir(parents=True, exist_ok=True)
    run_logged('details-' + label + '-create', [CORE, 'mod-project', 'create',
               '--library', project.parent.parent, '--name', PROJECT_NAME])
    run_logged('details-' + label + '-settings', [CORE, 'mod-project', 'settings',
               '--project', project, '--live-reload', 'off', '--mod-id', GUID])
    for row in frozen['models']:
        key = f"detail_{row['family']}_age0{row['age']}"
        run_logged('details-' + label + '-' + key, [CORE, 'mod-project', 'building',
                   '--project', project, '--source', row['export_directory'],
                   '--name', key, '--profile', 'english-house', '--integration', 'script'])
    config = read(project / 'mod-project.json')
    assert not config['game_mode']['enabled'] and not config['game_mode']['live_reload']
    assert inputs() == frozen
    write(DETAIL / ('inputs-' + label + '.json'), {'handoff': frozen, 'project': str(project),
                                                  'config_sha256': sha(project / 'mod-project.json')})
    native.WORK, native.PROJECT, native.CACHEWORK = DETAIL, project, OUT / 'inventory'
    native.cook(project, 'cc040details-' + label)
    receipt = DETAIL / ('cc040details-' + label + '-cook.json')
    assert inputs() == frozen
    write(DETAIL / 'cook-pointer.json', {'receipt': str(receipt),
                                        'inputs': str(DETAIL / ('inputs-' + label + '.json'))})
    return read(receipt)


def put(member, raw, rows):
    target = WORK / 'payload' / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                 'bytes': target.stat().st_size})


def put_override(member, raw, rows):
    target = DETAIL / 'payload' / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                 'bytes': target.stat().st_size})


def assemble():
    guarded()
    pointer = read(DETAIL / 'cook-pointer.json')
    cooked = read(pointer['receipt'])
    frozen = read(pointer['inputs'])['handoff']
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    assert inputs() == frozen
    back = Path(cooked['readback'])
    media = read(WORK / 'building-media.json')
    assert media['status'] == 'passed'
    existing = {r['member']: r for r in media['payloads']}
    contracts = building_contracts()
    identities = read(WORK / 'registered-building-identities.json')
    rows, overrides, reports = [], [], []
    native.CACHEWORK = OUT / 'inventory'
    for row in frozen['models']:
        key = f"{row['family']}_age0{row['age']}"
        name = 'detail_' + key
        base = f'art/scenario/garrison/{PROJECT_NAME}/buildings/{name}/model'
        stock_model = row['stock_model_stem']
        assert stock_model == next(m['donor'] for m in media['models'] if
                                   m['family'] == row['family'] and m['age'] == row['age'])
        raw, damage = intact_damage_conditions((back / (base + '.rgm')).read_bytes())
        # Every native selector carries construction/healthy/damage predicates;
        # no geometry is selected for ruins, so the detail disappears on death.
        from lifecycle import _pairs, _selector, _conditions
        _, pairs = _pairs(raw)
        parts = {part for s, _ in pairs for part in _selector(s)[1]}
        assert parts == {p['name'] for p in row['parts']}
        assert all(not any(condition[-1] == 'ruins' for condition in _conditions(c)) for _, c in pairs)
        put(base + '.rgm', raw, rows)
        for extension in ('.rgo', '.rrgeom', '.rrmaterial'):
            put(base + extension, (back / (base + extension)).read_bytes(), rows)
        material = (back / (base + '.rrmaterial')).read_bytes()
        for mat in rc.parse(material).roots:
            if mat.tag != b'GMat': continue
            one = rc.pack_document([rc.pack_chunk(mat.kind, mat.tag, mat.payload,
                                                 name=mat.name, version=mat.version)])
            for value in mv.material_slots(one)['textures'].values():
                if not value or value == '__default': continue
                member = value.replace('\\', '/').lower()
                if not member.endswith('.rrtex'): member += '.rrtex'
                assert member.startswith(base.rsplit('/', 1)[0] + '/')
                if member not in {r['member'] for r in rows}:
                    put(member, (back / member).read_bytes(), rows)
        stamp = f'art/stamps/garrison/{PROJECT_NAME}/{name}.bin'
        stamp_path = back / stamp
        visuals = native.active_visuals(native.NativeTree(stamp_path))
        assert len(visuals) == 1 and visuals[0]['model'].replace('\\', '/') == base
        put(stamp, stamp_path.read_bytes(), rows)
        assert identities[key]['member'] == contracts[key]['member']
        original = existing[identities[key]['final']]
        source = rgd.read(Path(original['file']).read_bytes())
        modified = copy.deepcopy(source)
        changed = []
        for variant in ('default', 'cordoba', 'campaign'):
            path = (variant + '/attachment_lists/attachment_lists/attachment_list/'
                    'attachment_list')
            selected = rgd.find(modified.nodes, path)
            assert selected.kind == 'List2'
            expected = 3 if variant == 'campaign' else 2
            assert len(selected.value) == expected
            template = copy.deepcopy(selected.value[0])
            assert template.key == 'stamp_attachment'
            assert next(n.value for n in template.value if n.key == 'add_impass_blockers') is False
            next(n for n in template.value if n.key == 'stamp').value = stamp.removesuffix('.bin').replace('/', '\\')
            selected.value.append(template)
            changed.append({'variant': variant, 'slot': expected, 'stamp': stamp})
        restored = copy.deepcopy(modified)
        for variant in ('default', 'cordoba', 'campaign'):
            path = variant + '/attachment_lists/attachment_lists/attachment_list/attachment_list'
            rgd.find(restored.nodes, path).value.pop()
        assert rgd.write(restored) == rgd.write(source), key
        put_override(identities[key]['final'], rgd.write(modified), overrides)
        reports.append({'key': key, 'detail_model': base, 'detail_stamp': stamp,
                        'damage': damage, 'additional_stamp_slots': changed,
                        'stock_destruction_and_campaign_stamps_preserved': True,
                        'model_ruins_geometry_empty': True,
                        'native_runtime': 'unverified'})
    assert len(reports) == 12 and len(overrides) == 12
    assert len({r['member'] for r in rows}) == len(rows)
    result = {'status': 'passed', 'models': reports, 'payloads': rows,
              'list_overrides': overrides, 'cook': cooked,
              'native_runtime': 'unverified'}
    write(WORK / 'building-details-media.json', result)
    return result


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'cook': cook(sys.argv[2])
    elif action == 'assemble': assemble()
    else: raise SystemExit('cook LABEL|assemble')
