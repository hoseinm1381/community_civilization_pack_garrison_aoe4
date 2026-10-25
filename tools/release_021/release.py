"""Fresh Garrison art cook and exact visual-only update over accepted 0.2.0."""
import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from common import *

sys.dont_write_bytecode = True
sys.path.append(str(ROOT / 'tools/release_010'))
import integration as native
from integration_codec import (copy_native_markers, copy_native_skeleton_owner,
    intact_damage_conditions, visibility_evidence)
from garrison_shared import relic_chunky as rc, model_variants as mv, building_project as bp

WORK = OUT / 'integration'
native.WORK = WORK
native.CACHEWORK = OUT / 'inventory'
BASELINE = ROOT / 'archives/release_020_user_accepted/community_civilization_pack.sga'
MODELS = {
    'exposed_pit': ('art/scenario/cc010/t1/model', 'art/civilizations/campaign_english/structures/tent/eng_tent_control_a/eng_tent_control_a'),
    'covered_pit': ('art/scenario/cc010/t2/model', 'art/civilizations/campaign_english/structures/tent/eng_tent_control_b/eng_tent_control_b'),
    'ministry': ('art/scenario/cc020/economy_ministry/model', 'art/civilizations/chinese/structures/dynasty_pagoda/chi_dynasty_pagoda_control_age03/chi_dynasty_pagoda_control_age03'),
}
MINISTRY_ACTOR = 'attrib/ebps/vietnam/vn_building_econ_food_control_chi.rgd'

def listing(path):
    data = json.loads(subprocess.run([str(ARCH), 'list', str(path), '--verify'],
        capture_output=True, text=True, check=True).stdout)
    assert data['archive']['verification']['verified']
    assert data['archive']['name'].replace('-', '').lower() == GUID.replace('-', '')
    return data

def unpack(path, label):
    dest = OUT / 'readback' / (label + '-' + sha(path)[:12])
    if not (dest / '.complete.json').exists():
        assert not dest.exists(), f'Incomplete readback retained: {dest}'
        run_logged('unpack-' + label, [ARCH, 'unpack', path, '--output', dest])
        write(dest / '.complete.json', {'sha256': sha(path)})
    assert read(dest / '.complete.json')['sha256'] == sha(path)
    return dest

def sources():
    """Inputs are deliberately separate from all accepted 0.1.0/0.2.0 inputs."""
    return {
        'exposed_pit': ROOT / 'art/exports/traps_021/stake_thicket',
        'covered_pit': ROOT / 'art/exports/traps_021/stake_fan',
        'ministry': ROOT / 'art/exports/buildings_021/ministry',
    }

def source_inputs():
    result = {}
    for key, folder in sources().items():
        assert (folder / 'building.json').is_file(), folder
        result[key] = {p.name: sha(p) for p in folder.iterdir() if p.is_file()}
        assert {'building.json', 'model.fbx', 'albedo.png', 'normal.png', 'roughness.png', 'metalness.png'} <= result[key].keys()
    return result

def editable_inputs():
    result = {}
    for folder in (ROOT / 'art/authoring/traps_021', ROOT / 'art/authoring/buildings_021', ROOT / 'art/recipes/release_021'):
        assert folder.is_dir(), folder
        for path in folder.rglob('*'):
            if path.is_file(): result[path.relative_to(ROOT).as_posix()] = sha(path)
    assert any(p.endswith('.blend') for p in result)
    return result

def ministry_placement(geometry, stamp):
    points = []
    for chunk in rc.walk(rc.load(geometry).roots):
        if chunk.tag != b'GEOB': continue
        count, _, stride, _ = struct.unpack_from('<4I', chunk.payload)
        if stride not in (20, 24, 32) or len(chunk.payload) < 16 + count * stride: continue
        points.extend(struct.unpack_from('<3e', chunk.payload, 16 + i * stride) for i in range(count))
    assert points
    stem = MODELS['ministry'][0]
    visuals = [v for v in native.active_visuals(native.NativeTree(stamp)) if v['model'].replace('\\', '/').lower() == stem]
    assert len(visuals) == 1
    transform = visuals[0]['transform']
    x, y, z, w = transform[:4]
    tx, ty, tz = transform[4:7]
    sx, sy, sz = transform[7:10]
    assert abs(x*x+y*y+z*z+w*w-1) < .002
    world = []
    for a, b, c in points:
        px, py, pz = a*sx, b*sy, c*sz
        ix, iy, iz, iw = w*px+y*pz-z*py, w*py+z*px-x*pz, w*pz+x*py-y*px, -x*px-y*py-z*pz
        world.append((ix*w+iw*-x+iy*-z-iz*-y+tx,
                      iy*w+iw*-y+iz*-x-ix*-z+ty,
                      iz*w+iw*-z+ix*-y-iy*-x+tz))
    low = [min(p[i] for p in world) for i in range(3)]
    high = [max(p[i] for p in world) for i in range(3)]
    assert -.05 <= low[1] <= .15, ('Ministry ground contact', low)
    assert all(-7.95 <= low[i] <= high[i] <= 7.95 for i in (0, 2)), ('Ministry exceeds new 16x16 placement', low, high)
    result = {'status': 'passed', 'world_min': low, 'world_max': high, 'vertices': len(points),
        'placement_size': [16, 16], 'stamp_transform': transform,
        'geometry_sha256': sha(geometry), 'stamp_sha256': sha(stamp), 'runtime': 'unverified'}
    write(OUT / 'ministry-world-placement.json', result)
    return result

def cook(label):
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    inputs = source_inputs()
    project = OUT / 'art-cook' / label / 'library/Mods/community_021_art'
    assert not project.exists(), 'Use a fresh label; prior cook evidence is retained'
    project.parent.parent.mkdir(parents=True)
    run_logged(label + '-create', [CORE, 'mod-project', 'create', '--library', project.parent.parent, '--name', project.name])
    run_logged(label + '-settings', [CORE, 'mod-project', 'settings', '--project', project,
        '--live-reload', 'off', '--mod-id', GUID])
    for key, folder in sources().items():
        run_logged(label + '-register-' + key, [CORE, 'mod-project', 'building', '--project', project,
            '--source', folder, '--name', key, '--profile', 'english-house', '--integration', 'script'])
    record = read(project / 'mod-project.json')
    assert record['game_mode']['enabled'] is False and record['game_mode']['live_reload'] is False
    for key, files in inputs.items():
        registered = project / 'project/source/art/scenario/garrison/community_021_art/buildings' / key
        for name, digest in files.items():
            if name != 'building.json': assert sha(registered / name) == digest, (key, name)
    write(OUT / f'inputs-{label}.json', {'inputs': inputs, 'editable_inputs': editable_inputs(), 'project': str(project), 'sha256': sha(project / 'mod-project.json')})
    native.cook(project, 'cc021-' + label)
    receipt = read(WORK / ('cc021-' + label + '-cook.json'))
    assert source_inputs() == inputs
    write(OUT / 'cook-pointer.json', {'receipt': str(WORK / ('cc021-' + label + '-cook.json')), 'inputs': str(OUT / f'inputs-{label}.json')})
    return receipt

def assemble():
    guarded()
    pointer = read(OUT / 'cook-pointer.json')
    cooked = read(pointer['receipt'])
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    assert source_inputs() == read(pointer['inputs'])['inputs']
    assert editable_inputs() == read(pointer['inputs'])['editable_inputs']
    back = Path(cooked['readback'])
    listing(cooked['cook']['archive'])
    # Independently unpack the measured cook before trusting retained readback.
    fresh = unpack(cooked['cook']['archive'], 'fresh-art-cook')
    compared = {}
    for key in MODELS:
        prefix = 'art/scenario/garrison/community_021_art/buildings/' + key
        for path in (back / prefix).iterdir():
            if path.is_file() and path.suffix in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial', '.rrtex'):
                member = path.relative_to(back).as_posix()
                assert sha(path) == sha(fresh / member), member
                compared[member] = sha(path)
    write(WORK / 'fresh-cook-readback.json', {'status': 'passed', 'cook_sha256': cooked['cook']['sha256'], 'members': compared})
    baseline = unpack(BASELINE, 'accepted020')
    rows, reports = [], []
    for key, (final, donor) in MODELS.items():
        base = 'art/scenario/garrison/community_021_art/buildings/' + key + '/model'
        # Take lifecycle owner and marker source from the same official model as 0.2.0.
        original = native.stock(donor + '.rgm').read_bytes()
        parts = read(sources()[key] / 'building.json')['parts']
        raw = bp.construction_model((back / (base + '.rgm')).read_bytes(), original, parts, profile_id='english-house')
        raw, damage = intact_damage_conditions(raw)
        visibility = visibility_evidence(raw, parts)
        raw, markers = (copy_native_skeleton_owner(raw, original, parts) if key == 'covered_pit'
                        else copy_native_markers(raw, original))
        native.put(final + '.rgm', native.rebase_model(raw, final), rows)
        native.put(final + '.rrgeom', (back / (base + '.rrgeom')).read_bytes(), rows)
        # Native RGO is explicitly byte preserved from the accepted release.
        assert sha(native.stock(donor + '.rgo')) == sha(baseline / (final + '.rgo'))
        material = (back / (base + '.rrmaterial')).read_bytes()
        edits, textures = {}, {}
        for mat in rc.parse(material).roots:
            if mat.tag != b'GMat': continue
            name = mat.decoded_name.removesuffix('_collection')
            one = rc.pack_document([rc.pack_chunk(mat.kind, mat.tag, mat.payload, name=mat.name, version=mat.version)])
            edits[name] = {}
            for slot, value in mv.material_slots(one)['textures'].items():
                if not value or value == '__default': continue
                member = value.replace('\\', '/').lower()
                assert member.startswith(base.rsplit('/', 1)[0] + '/') and member.endswith('.rrtex'), member
                # A release-owned prefix avoids stale resources and preserves old rebuild inputs.
                private = final.rsplit('/', 1)[0] + '/v021_' + member.rsplit('/', 1)[1]
                edits[name][slot] = private
                textures[private] = back / member
        native.put(final + '.rrmaterial', native.scoped_material(material, edits), rows)
        for member, path in sorted(textures.items()): native.put(member, path.read_bytes(), rows)
        reports.append({'asset': key, 'model': final, 'native_owner': donor,
            'rgo_preserved_sha256': sha(baseline / (final + '.rgo')), 'damage': damage,
            'visibility': visibility, 'markers': markers, 'material_edits': edits})
    assert len({r['member'] for r in rows}) == len(rows)
    for row in rows: assert sha(row['file']) == row['sha256']
    placement = ministry_placement(WORK / 'payload' / (MODELS['ministry'][0] + '.rrgeom'),
                                   baseline / 'art/stamps/cc020/economy_ministry.bin')
    result = {'status': 'passed', 'payloads': rows, 'models': [v[0] for v in MODELS.values()],
              'reports': reports, 'placement': placement, 'cook': cooked, 'inputs': read(pointer['inputs'])}
    write(WORK / 'media.json', result)
    print('MEDIA_021_ASSEMBLED', len(rows), flush=True)
    return result

def qualify(label):
    """Use the qualified 0.2.0 Reflect procedure with only 0.2.1 paths/evidence."""
    import importlib.util
    # Isolated loading avoids importing the 0.2.0 common/source-policy modules.
    spec = importlib.util.spec_from_file_location('reference021_adapter', ROOT / 'tools/release_020/reference.py')
    module = importlib.util.module_from_spec(spec)
    # Its inventory dependency is a read-only view of native helpers, not 020 state.
    import types
    saved = sys.modules.get('inventory')
    stub = types.ModuleType('inventory'); stub.native = native; sys.modules['inventory'] = stub
    try: spec.loader.exec_module(module)
    finally:
        if saved is None: sys.modules.pop('inventory', None)
        else: sys.modules['inventory'] = saved
    # Adapt the checked procedure mechanically; keep its native assertions intact.
    text = (ROOT / 'tools/release_020/reference.py').read_text(encoding='utf-8')
    start = text.index('def qualify(label):')
    end = text.index("if __name__", start)
    body = text[start:end].replace('cc020ref', 'cc021ref').replace("media-020.json", "media.json")
    body = body.replace("r['member'].startswith('art/scenario/cc020/')", "r['member'].startswith(('art/scenario/cc010/', 'art/scenario/cc020/'))")
    body = body.replace("OUT / 'art-cook/cook-pointer.json'", "OUT / 'cook-pointer.json'")
    body = body.replace("community_020_art/vn020_ministry.rdo", "community_021_art/ministry.rdo")
    body = body.replace('cc020:reference:', 'cc021:reference:').replace('art/stamps/cc020/reference_', 'art/stamps/cc021/reference_')
    body = body.replace('reference-020-', 'reference-021-').replace('FINAL_020_MODELS', 'FINAL_021_MODELS')
    # Lifecycle RGO owners are preserved archive members, not replacement
    # payloads. Stage those exact owners too: native model resolution needs
    # the complete quartet even though only three resources are updated.
    anchor = "    burn = (template / 'source/_default.burnproj').read_text(encoding='utf-8-sig')"
    insertion = """    for model in models:
        donor = next(donor for stem, donor in MODEL_OWNERS.values() if stem == model)
        owner = native.stock(donor + '.rgo')
        assert sha(owner) == PRESERVED_OWNERS[model]
        shutil.copy2(owner, source / (model + '.rgo'))
"""
    assert body.count(anchor) == 1
    body = body.replace(anchor, insertion + anchor)
    module.MODEL_OWNERS = MODELS
    module.PRESERVED_OWNERS = {r['model']: r['rgo_preserved_sha256'] for r in read(WORK / 'media.json')['reports']}
    exec(compile(body, str(ROOT / 'tools/release_020/reference.py') + ':021adapter', 'exec'), module.__dict__)
    return module.qualify('cc021ref' + label.replace('-', ''))

def compose(label):
    guarded()
    media = read(WORK / 'media.json')
    reference = read(WORK / 'reference-cook.json')
    import footprint
    art_rows = media['payloads']
    rows = art_rows + [footprint.compiled_payload()]
    assert reference['status'] == 'passed'
    assert reference['exact_inputs_sha256'] == {r['member']: r['sha256'] for r in art_rows}
    target = OUT / 'candidates' / label / (KEY + '.sga')
    assert not target.exists()
    target.parent.mkdir(parents=True)
    write(target.parent / 'visual-allowlist.json', media)
    current = BASELINE
    for alias, selected in (('data', art_rows), ('attrib', rows[-1:])):
        mapping = WORK / f'members-{label}-{alias}.txt'
        mapping.write_text(''.join(r['member'] + '=' + r['file'] + '\n' for r in selected), encoding='utf-8')
        destination = target if alias == 'attrib' else target.parent / 'art-stage.sga'
        run_logged('compose-' + label + '-' + alias, [ARCH, 'set-members', current, mapping, destination, '--alias', alias])
        current = destination
    receipt = {'status': 'passed', 'archive': str(target), 'sha256': sha(target),
        'baseline_sha256': sha(BASELINE), 'payloads': rows, 'reference': reference,
        'media_sha256': sha(WORK / 'media.json'), 'project_guid': GUID}
    write(OUT / 'candidate.json', receipt)
    return receipt

def verify():
    guarded()
    candidate = read(OUT / 'candidate.json')
    inputs = read(read(OUT / 'cook-pointer.json')['inputs'])
    assert source_inputs() == inputs['inputs'] and editable_inputs() == inputs['editable_inputs']
    archive = Path(candidate['archive'])
    assert sha(archive) == candidate['sha256'] and sha(BASELINE) == candidate['baseline_sha256']
    before_index, after_index = listing(BASELINE), listing(archive)
    assert before_index['archive']['tocs'] == after_index['archive']['tocs']
    before, after = unpack(BASELINE, 'accepted020'), unpack(archive, 'candidate021')
    old = {r['path'] for r in before_index['members']}
    new = {r['path'] for r in after_index['members']}
    assert old <= new
    payloads = {r['member']: r for r in candidate['payloads']}
    changes = {m for m in old if sha(before / m) != sha(after / m)}
    expected = {stem + ext for stem, donor in MODELS.values() for ext in ('.rgm', '.rrgeom', '.rrmaterial')} | {MINISTRY_ACTOR}
    assert changes == expected, (changes, expected)
    assert new - old == set(payloads) - old
    assert all(m in expected or any(m.startswith(stem.rsplit('/', 1)[0] + '/v021_') and m.endswith('.rrtex') for stem, _ in MODELS.values()) for m in payloads)
    for member, row in payloads.items(): assert sha(after / member) == row['sha256']
    import footprint
    actor_proof = footprint.compiled_proof(before / MINISTRY_ACTOR, after / MINISTRY_ACTOR)
    footprint.verify_source()
    visited = {MINISTRY_ACTOR}
    for stem, _ in MODELS.values():
        for ext in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial'):
            path = after / (stem + ext); assert path.is_file(); rc.load(path)
            if ext != '.rgo': visited.add(stem + ext)
        doc = rc.load(after / (stem + '.rgm'))
        bana = [c for c in rc.walk(doc.roots) if c.tag == b'BANA']
        assert len(bana) == 1 and rc.read_lp_string(bana[0].payload, 0)[0].replace('\\', '/') == stem
        for mat in rc.load(after / (stem + '.rrmaterial')).roots:
            if mat.tag != b'GMat': continue
            raw = rc.pack_document([rc.pack_chunk(mat.kind, mat.tag, mat.payload, name=mat.name, version=mat.version)])
            for value in mv.material_slots(raw)['textures'].values():
                if not value or value == '__default': continue
                member = value.replace('\\', '/').lower()
                if not member.endswith('.rrtex'): member += '.rrtex'
                assert member in payloads and (after / member).is_file(), member
                visited.add(member)
    assert visited == set(payloads), ('Unvisited payload', set(payloads) ^ visited)
    placement = ministry_placement(after / (MODELS['ministry'][0] + '.rrgeom'),
                                   after / 'art/stamps/cc020/economy_ministry.bin')
    result = {'status': 'passed', 'sga_sha256': sha(archive), 'baseline_sha256': sha(BASELINE),
        'baseline_members': len(old), 'final_members': len(new), 'changed': sorted(changes),
        'added': sorted(new - old), 'untouched_members': len(old - changes),
        'nonvisual_exception': actor_proof, 'all_other_nonvisual_members_byte_identical': True,
        'all_bindings_and_stamps_byte_identical': True,
        'ministry_placement': placement,
        'all_payloads_typed_visited': True, 'native_runtime': 'pending user test'}
    write(OUT / 'archive-verification.json', result)
    print('ARCHIVE_021_VERIFIED', len(changes), len(new - old), len(old - changes), flush=True)
    return result

def checks():
    guarded()
    # The immutable 0.2.0 freeze stays intact; 021 admits only the approved footprint edit.
    import footprint
    preservation = footprint.verify_source()
    body = '''import io,json,sys,unittest
suite=unittest.defaultTestLoader.discover('tests')
stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
print(stream.getvalue(),file=sys.stderr)
print('RELEASE_TEST_RESULT='+json.dumps({'tests':result.testsRun,'failures':[t.id() for t,d in result.failures],'errors':[t.id() for t,d in result.errors],'skipped':[t.id() for t,d in result.skipped]}))
raise SystemExit(not result.wasSuccessful())
'''
    process = subprocess.run([CONFIG['python'], '-B', '-c', body], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (OUT / 'release-tests.log').write_text(process.stdout + '\nSTDERR:\n' + process.stderr, encoding='utf-8')
    tests = json.loads(next(line.split('=', 1)[1] for line in process.stdout.splitlines() if line.startswith('RELEASE_TEST_RESULT=')))
    baseline = read(EXTERNAL / 'output/release_020/release-checks.json')['tests']
    assert tests['tests'] >= baseline['tests'] and set(tests['failures']) == set(baseline['failures'])
    assert not tests['errors'] and not tests['skipped']
    validator = Path(r'C:\Users\RS\.codex\skills\modify-aoe4-tuning-packs\scripts\validate_tuning_pack.py')
    command = run_logged('static-source', [CONFIG['python'], '-B', validator, ROOT])
    result = {'status': 'baseline-equivalent-with-known-failures', 'tests': tests,
        'raw_suite_exit_code': process.returncode, 'static_validation': command,
        'source_and_prior_art': preservation, 'native_runtime': 'pending user test'}
    write(OUT / 'release-checks.json', result)
    print('CHECKS_021_PASSED', tests['tests'], 'tests; inherited failures', len(tests['failures']), flush=True)
    return result

START = '''COMMUNITY CIVILIZATION PACK 0.2.1 — pit traps and Ministry refinement

Close AoE4. Import this ZIP into Garrison and enable it. Select Community
Civilization Pack in BOTH Game Mode and Tuning Pack. Choose China in the lobby,
then Vietnam in the opening selection. Do not select companion_tuning_pack or
Vietnam v2 as the tuning pack for this game mode. Disable other editions for an
isolated test. If blueprints are reported unavailable, check the match setup.

Check both pit traps on different terrain and slopes, before/after upgrades,
construction, attacks, destruction and four-second expiry. Pit depth is visual;
terrain is not excavated. Check Ministry construction, repair, damage/destruction,
research, worker-elephant production and emergence, pen clearance, two player
colours and near/far views. All three yard elephants are decorative and static.
The Ministry placement area is enlarged from 8x8 to 16x16 to fit the compound;
its costs, research and production are unchanged. Test placement near other
buildings, production exits and worker paths around the compound.
Confirm existing houses and all other 0.2.0 buildings remain unchanged.

Rollback: close AoE4 and reimport the accepted 0.2.0 ZIP through Garrison.
Build/cook/readback/package checks are separate from native-match acceptance.
No client installation or game match is performed by this release command.
'''

def package():
    audit = verify()
    checked = checks()
    candidate = read(OUT / 'candidate.json')
    folder = OUT / 'package'
    folder.mkdir(exist_ok=True)
    target = folder / (KEY + '.sga')
    if target.exists(): assert sha(target) == candidate['sha256'], 'Keep prior package; use a new release directory'
    else: shutil.copy2(candidate['archive'], target)
    manifest = {'schema': 'garrison.mod/v1', 'bundle_key': KEY,
        'members': [{'mod_key': KEY, 'role': 'tuning', 'path': KEY + '.sga', 'sha256': sha(target)}],
        'details': {'id': KEY, 'name': CONFIG['display_name'], 'version': VERSION,
            'summary': 'Two pit-trap designs and a weathered Ministry compound with three large decorative elephants',
            'min_garrison': '0.1.4', 'content_types': ['game-mode', 'tuning-pack'],
            'updated': datetime.now(timezone.utc).date().isoformat(),
            'description': 'New pit visuals and Ministry compound. Only the Ministry placement footprint changes; costs, research, production and unrelated buildings retained. Native testing pending.'}}
    write(folder / 'garrison.json', manifest)
    (folder / 'START-HERE.txt').write_text(START, encoding='utf-8')
    evidence = {'version': VERSION, 'project_guid': GUID, 'sga_sha256': sha(target),
        'archive': audit, 'checks': checked, 'reference_cook': read(WORK / 'reference-cook.json'),
        'native_footprint_build': read(read(OUT / 'footprint/current.json')['receipt']),
        'native_runtime': 'pending user test', 'multiplayer': 'not tested'}
    write(folder / 'EVIDENCE.json', evidence)
    destination = OUT / (KEY + '-' + VERSION + '.zip')
    temporary = destination.with_suffix('.zip.tmp')
    with ZipFile(temporary, 'w', ZIP_DEFLATED, compresslevel=6) as bundle:
        for name in ('garrison.json', KEY + '.sga', 'START-HERE.txt', 'EVIDENCE.json'): bundle.write(folder / name, name)
    with ZipFile(temporary) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == len(set(bundle.namelist())) == 4
        assert bundle.namelist().count('garrison.json') == 1
        assert json.loads(bundle.read('garrison.json')) == manifest
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == sha(target)
    temporary.replace(destination)
    receipt = {'status': 'passed', 'version': VERSION, 'zip': str(destination),
        'zip_sha256': sha(destination), 'zip_bytes': destination.stat().st_size,
        'sga': str(target), 'sga_sha256': sha(target), 'native_runtime': 'pending user test'}
    write(OUT / 'package-verification.json', receipt)
    print('PACKAGE_021_VERIFIED', receipt['zip'], receipt['zip_sha256'], flush=True)
    return receipt

def verify_package():
    verify(); checks()
    receipt = read(OUT / 'package-verification.json')
    assert sha(receipt['zip']) == receipt['zip_sha256']
    assert sha(receipt['sga']) == receipt['sga_sha256']
    with ZipFile(receipt['zip']) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == {'garrison.json', KEY + '.sga', 'START-HERE.txt', 'EVIDENCE.json'}
        assert len(bundle.namelist()) == 4
        manifest = json.loads(bundle.read('garrison.json'))
        assert manifest['schema'] == 'garrison.mod/v1' and manifest['details']['version'] == VERSION
        assert manifest['bundle_key'] == KEY and manifest['members'][0]['sha256'] == receipt['sga_sha256']
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == receipt['sga_sha256']
    print('PACKAGE_021_REPEAT_VERIFIED', flush=True)

if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'cook': cook(sys.argv[2])
    elif action == 'assemble': assemble()
    elif action == 'qualify': qualify(sys.argv[2])
    elif action == 'compose': compose(sys.argv[2])
    elif action == 'verify': verify()
    elif action == 'package': package()
    elif action == 'checks': checks()
    elif action == 'verify-only': verify_package()
    elif action == 'rebuild':
        cook(sys.argv[2]); assemble(); qualify(sys.argv[2]); compose(sys.argv[2]); package()
    else: raise SystemExit('cook|assemble|qualify|compose|verify|package|verify-only|rebuild')
