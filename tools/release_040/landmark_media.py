"""Fresh Garrison landmark cook and typed native ruined-model integration."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from common import ROOT, OUT, CORE, GUID, guarded, read, run_logged, sha, write
from bindings import ACTORS, GRAPH, STEMS, WORK, private_lists_and_stamps
from lifecycle import install_ruins

sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native
from integration_codec import copy_native_markers, intact_damage_conditions
from garrison_shared import relic_chunky as rc, model_variants as mv, building_project as bp

OLD = OUT.parent / 'release_030'
SOURCE = {
    'pho_minh': ROOT / 'art/exports/landmarks_040/pho_minh_combined',
    'one_pillar': ROOT / 'art/exports/landmarks_040/one_pillar_combined',
}


def inputs():
    result = {}
    for key, folder in SOURCE.items():
        assert folder.is_dir(), folder
        files = {p.name: sha(p) for p in folder.iterdir() if p.is_file()}
        assert {'building.json', 'model.fbx', 'albedo.png', 'normal.png',
                'roughness.png', 'metalness.png'} <= set(files)
        doc = read(folder / 'building.json')
        assert doc['schema'] == 'garrison.building-source/v1' and doc['profile'] == 'english-house'
        names = [row['name'] for row in doc['parts']]
        assert len(names) == len(set(names)) and len(names) >= 3
        handoff = read(OUT / 'landmarks' / key / 'handoff.json')
        assert handoff['export_directory'] == str(folder)
        assert handoff['export_sha256'] == files
        assert sha(handoff['source_blend']) == handoff['source_blend_sha256']
        ruins = handoff['ruin_parts']
        assert ruins == ['garrison_part_0002'] and names == [
            'garrison_part_0000', 'garrison_part_0001', 'garrison_part_0002']
        assert all(row['first_stage'] in range(0, 100, 5) for row in doc['parts'])
        result[key] = {'files': files, 'parts': doc['parts'], 'ruins': ruins}
    return result


def cook(label):
    """Caller holds the shared exclusive native lock and root's cook grant."""
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    frozen = inputs()
    project = OUT / 'art-cook' / label / 'library/Mods/community_040_landmarks'
    assert not project.exists(), 'Use a fresh append-only label'
    project.parent.parent.mkdir(parents=True)
    run_logged(label + '-create', [CORE, 'mod-project', 'create', '--library', project.parent.parent,
                                   '--name', project.name])
    run_logged(label + '-settings', [CORE, 'mod-project', 'settings', '--project', project,
                                     '--live-reload', 'off', '--mod-id', GUID])
    for key, folder in SOURCE.items():
        run_logged(label + '-register-' + key, [CORE, 'mod-project', 'building', '--project', project,
            '--source', folder, '--name', key, '--profile', 'english-house', '--integration', 'script'])
    record = read(project / 'mod-project.json')
    assert record['game_mode']['enabled'] is False and record['game_mode']['live_reload'] is False
    for key, file_info in frozen.items():
        staged = project / 'project/source/art/scenario/garrison/community_040_landmarks/buildings' / key
        for name, digest in file_info['files'].items():
            if name != 'building.json':
                assert sha(staged / name) == digest
    write(OUT / f'landmark-inputs-{label}.json', {'inputs': frozen, 'project': str(project),
                                                  'config_sha256': sha(project / 'mod-project.json')})
    native.WORK, native.PROJECT, native.CACHEWORK = WORK, project, OUT / 'inventory'
    native.cook(project, 'cc040art-' + label)
    receipt = WORK / ('cc040art-' + label + '-cook.json')
    assert inputs() == frozen
    write(OUT / 'art-cook-pointer.json', {'receipt': str(receipt),
                                          'inputs': str(OUT / f'landmark-inputs-{label}.json')})
    return read(receipt)


def put(member, raw, rows):
    target = WORK / 'payload' / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                 'bytes': target.stat().st_size})


def assemble():
    guarded()
    pointer = read(OUT / 'art-cook-pointer.json')
    cooked = read(pointer['receipt'])
    frozen = read(pointer['inputs'])['inputs']
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    assert inputs() == frozen
    back = Path(cooked['readback'])
    graph = read(GRAPH)['landmarks']
    old_media = read(OLD / 'integration/media.json')
    rows, reports, owners = [], [], {}
    for key in ACTORS:
        donor = next(iter(graph[key]['stamps'].values()))['visuals'][0]['model']
        original = native.stock(donor + '.rgm').read_bytes()
        base = f'art/scenario/garrison/community_040_landmarks/buildings/{key}/model'
        final = STEMS[key]
        parts = frozen[key]['parts']
        ruin_names = set(frozen[key]['ruins'])
        healthy_names = {row['name'] for row in parts} - ruin_names
        raw = bp.construction_model((back / (base + '.rgm')).read_bytes(), original,
                                    parts, profile_id='english-house')
        raw, damage = intact_damage_conditions(raw)
        raw, ruins = install_ruins(raw, ruin_names, healthy_names)
        raw, markers = copy_native_markers(raw, original)
        put(final + '.rgm', native.rebase_model(raw, final), rows)
        put(final + '.rrgeom', (back / (base + '.rrgeom')).read_bytes(), rows)
        owner = old_media['native_rgo'][f'art/scenario/cc030/{key}/model']
        assert sha(owner['file']) == owner['sha256'] == sha(native.stock(donor + '.rgo'))
        put(final + '.rgo', Path(owner['file']).read_bytes(), rows)
        owners[final] = {'file': str(WORK / 'payload' / (final + '.rgo')), 'sha256': owner['sha256']}
        material = (back / (base + '.rrmaterial')).read_bytes()
        edits, textures = {}, {}
        for mat in rc.parse(material).roots:
            if mat.tag != b'GMat':
                continue
            name = mat.decoded_name.removesuffix('_collection')
            one = rc.pack_document([rc.pack_chunk(mat.kind, mat.tag, mat.payload,
                                                 name=mat.name, version=mat.version)])
            edits[name] = {}
            for slot, value in mv.material_slots(one)['textures'].items():
                if not value or value == '__default':
                    continue
                member = value.replace('\\', '/').lower()
                assert member.startswith(base.rsplit('/', 1)[0] + '/') and member.endswith('.rrtex')
                private = final.rsplit('/', 1)[0] + '/v040_' + member.rsplit('/', 1)[1]
                edits[name][slot] = private
                textures[private] = back / member
        put(final + '.rrmaterial', native.scoped_material(material, edits), rows)
        for member, path in sorted(textures.items()):
            put(member, path.read_bytes(), rows)
        reports.append({'asset': key, 'model': final, 'stock_lifecycle_owner': donor,
                        'donor_rgo_sha256': owner['sha256'], 'damage': damage,
                        'ruins': ruins, 'markers': markers, 'material_edits': edits})
    lists = private_lists_and_stamps()
    rows.extend(lists['payloads'])
    assert len({r['member'] for r in rows}) == len(rows)
    for row in rows:
        assert sha(row['file']) == row['sha256']
    result = {'status': 'passed', 'payloads': rows, 'models': list(STEMS.values()),
              'reports': reports, 'private_bindings': lists, 'native_rgo': owners,
              'cook': cooked, 'inputs': frozen, 'native_runtime': 'unverified'}
    write(WORK / 'landmark-media.json', result)
    print('LANDMARK_MEDIA_040_ASSEMBLED', len(rows), flush=True)
    return result


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'cook': cook(sys.argv[2])
    elif action == 'assemble': assemble()
    else: raise SystemExit('cook LABEL|assemble')
