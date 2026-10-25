"""Fresh 0.3.0 art cook and exact selective update over accepted 0.2.1."""
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
from bindings import private_stamp, private_lists, MODEL_STEMS, STAMP_PREFIX, KEEP_SCENERY_IDS
from inventory import ACTORS

WORK = OUT / 'integration'
native.WORK = WORK
native.CACHEWORK = OUT / 'inventory'
BASELINE = ROOT / 'archives/release_021_user_accepted/community_civilization_pack.sga'
MODELS = {
    'exposed_pit': ('art/scenario/cc010/t1/model', 'art/civilizations/campaign_english/structures/tent/eng_tent_control_a/eng_tent_control_a'),
    'covered_pit': ('art/scenario/cc010/t2/model', 'art/civilizations/campaign_english/structures/tent/eng_tent_control_b/eng_tent_control_b'),
    'pho_minh': (MODEL_STEMS['pho_minh'], None),
    'one_pillar': (MODEL_STEMS['one_pillar'], None),
}
from footprint import MEMBER as MINISTRY_ACTOR, LANDMARK_MEMBERS

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
        'exposed_pit': ROOT / 'art/exports/traps_030/stake_thicket',
        'covered_pit': ROOT / 'art/exports/traps_030/stake_fan',
        'pho_minh': ROOT / 'art/exports/landmarks_030/pho_minh',
        'one_pillar': ROOT / 'art/exports/landmarks_030/one_pillar',
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
    for folder in (ROOT / 'art/authoring/traps_030', ROOT / 'art/authoring/landmarks_030', ROOT / 'art/recipes/release_030'):
        assert folder.is_dir(), folder
        for path in folder.rglob('*'):
            if path.is_file(): result[path.relative_to(ROOT).as_posix()] = sha(path)
    assert any(p.endswith('.blend') for p in result)
    return result

def landmark_placement(key, geometry, stamp):
    points = []
    for chunk in rc.walk(rc.load(geometry).roots):
        if chunk.tag != b'GEOB': continue
        count, _, stride, _ = struct.unpack_from('<4I', chunk.payload)
        if stride not in (20, 24, 32) or len(chunk.payload) < 16 + count * stride: continue
        points.extend(struct.unpack_from('<3e', chunk.payload, 16 + i * stride) for i in range(count))
    assert points
    stem = MODELS[key][0]
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
    assert -.1 <= low[1] <= .25, (key, 'ground contact', low)
    assert all(-3.8 <= low[i] <= high[i] <= 3.8 for i in (0, 2)), (key, 'exceeds 8x8 placement art budget', low, high)
    conservative_scaled_span = max(abs(v) for i in (0, 2) for v in (low[i], high[i])) * 1.12
    assert conservative_scaled_span <= 3.95, (key, '112-percent animator scale clearance', conservative_scaled_span)
    result = {'status': 'passed', 'world_min': low, 'world_max': high, 'vertices': len(points),
        'placement_size': [8, 8], 'stamp_transform': transform,
        'conservative_112_percent_half_extent': conservative_scaled_span,
        'geometry_sha256': sha(geometry), 'stamp_sha256': sha(stamp), 'runtime': 'unverified'}
    write(OUT / f'{key}-world-placement.json', result)
    return result

def cook(label):
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    inputs = source_inputs()
    project = OUT / 'art-cook' / label / 'library/Mods/community_030_art'
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
        registered = project / 'project/source/art/scenario/garrison/community_030_art/buildings' / key
        for name, digest in files.items():
            if name != 'building.json': assert sha(registered / name) == digest, (key, name)
    write(OUT / f'inputs-{label}.json', {'inputs': inputs, 'editable_inputs': editable_inputs(), 'project': str(project), 'sha256': sha(project / 'mod-project.json')})
    native.cook(project, 'cc030-' + label)
    receipt = read(WORK / ('cc030-' + label + '-cook.json'))
    assert source_inputs() == inputs
    write(OUT / 'art-cook-pointer.json', {'receipt': str(WORK / ('cc030-' + label + '-cook.json')), 'inputs': str(OUT / f'inputs-{label}.json')})
    return receipt

def assemble():
    guarded()
    pointer = read(OUT / 'art-cook-pointer.json')
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
        prefix = 'art/scenario/garrison/community_030_art/buildings/' + key
        for path in (back / prefix).iterdir():
            if path.is_file() and path.suffix in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial', '.rrtex'):
                member = path.relative_to(back).as_posix()
                assert sha(path) == sha(fresh / member), member
                compared[member] = sha(path)
    write(WORK / 'fresh-cook-readback.json', {'status': 'passed', 'cook_sha256': cooked['cook']['sha256'], 'members': compared})
    baseline = unpack(BASELINE, 'accepted021')
    graph = read(OUT / 'inventory/landmarks.json')['landmarks']
    rows, reports, owners = [], [], {}
    for key, (final, donor) in MODELS.items():
        base = 'art/scenario/garrison/community_030_art/buildings/' + key + '/model'
        if donor is None:
            stamp_info = next(iter(graph[key]['stamps'].values()))
            donor = stamp_info['visuals'][0]['model']
        # Take lifecycle owner and marker source from the same native stock model.
        original = native.stock(donor + '.rgm').read_bytes()
        parts = read(sources()[key] / 'building.json')['parts']
        raw = bp.construction_model((back / (base + '.rgm')).read_bytes(), original, parts, profile_id='english-house')
        raw, damage = intact_damage_conditions(raw)
        visibility = visibility_evidence(raw, parts)
        raw, markers = (copy_native_skeleton_owner(raw, original, parts) if key == 'covered_pit'
                        else copy_native_markers(raw, original))
        native.put(final + '.rgm', native.rebase_model(raw, final), rows)
        native.put(final + '.rrgeom', (back / (base + '.rrgeom')).read_bytes(), rows)
        if key in ('exposed_pit', 'covered_pit'):
            # Preserve accepted trap lifecycle owner byte for byte.
            assert sha(native.stock(donor + '.rgo')) == sha(baseline / (final + '.rgo'))
            owner = baseline / (final + '.rgo')
        else:
            owner = native.stock(donor + '.rgo')
            native.put(final + '.rgo', owner.read_bytes(), rows)
        owners[final] = {'file': str(owner), 'sha256': sha(owner)}
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
                private = final.rsplit('/', 1)[0] + '/v030_' + member.rsplit('/', 1)[1]
                edits[name][slot] = private
                textures[private] = back / member
        native.put(final + '.rrmaterial', native.scoped_material(material, edits), rows)
        for member, path in sorted(textures.items()): native.put(member, path.read_bytes(), rows)
        reports.append({'asset': key, 'model': final, 'native_owner': donor,
            'rgo_preserved_sha256': sha(owner), 'damage': damage,
            'visibility': visibility, 'markers': markers, 'material_edits': edits})
    # Keep stock landmark construction/scenery records; replace only the one principal visual.
    stamp_reports = []
    for key in ACTORS:
        stem, info = next(iter(graph[key]['stamps'].items()))
        donor = info['visuals'][0]['model']
        member = f'art/stamps/cc030/{key}.bin'
        target = WORK / 'payload' / member
        proof = private_stamp(Path(info['file']), target, donor, MODELS[key][0], KEEP_SCENERY_IDS[key])
        rows.append({'member': member, 'file': str(target), 'sha256': sha(target), 'bytes': target.stat().st_size})
        stamp_reports.append({'key': key, 'source': stem, 'proof': proof})
    lists = private_lists()
    rows.extend(lists['payloads'])
    assert len({r['member'] for r in rows}) == len(rows)
    for row in rows: assert sha(row['file']) == row['sha256']
    placement = {key: landmark_placement(key, WORK / 'payload' / (MODELS[key][0] + '.rrgeom'),
                                         WORK / 'payload' / f'art/stamps/cc030/{key}.bin') for key in ACTORS}
    result = {'status': 'passed', 'payloads': rows, 'models': [v[0] for v in MODELS.values()],
              'reports': reports, 'stamps': stamp_reports, 'lists': lists['reports'],
              'native_rgo': owners, 'placement': placement, 'cook': cooked, 'inputs': read(pointer['inputs'])}
    write(WORK / 'media.json', result)
    print('MEDIA_030_ASSEMBLED', len(rows), flush=True)
    return result

def qualify(label):
    from reference import qualify as run_reference
    return run_reference(label)

def compose(label):
    guarded()
    media = read(WORK / 'media.json')
    reference = read(WORK / 'reference-cook.json')
    import footprint
    media_rows = media['payloads']
    actor_rows = footprint.compiled_payload()
    rows = media_rows + actor_rows
    assert reference['status'] == 'passed'
    assert reference['exact_inputs_sha256'] == {r['member']: r['sha256'] for r in media_rows
                                                 if r['member'].startswith(('art/scenario/cc010/', 'art/scenario/cc030/'))}
    target = OUT / 'candidates' / label / (KEY + '.sga')
    assert not target.exists()
    target.parent.mkdir(parents=True)
    write(target.parent / 'visual-allowlist.json', media)
    current = BASELINE
    for alias, selected in (('data', [r for r in rows if r['member'].startswith('art/')]),
                            ('attrib', [r for r in rows if r['member'].startswith('attrib/')])):
        mapping = WORK / f'members-{label}-{alias}.txt'
        mapping.write_text(''.join(r['member'] + '=' + r['file'] + '\n' for r in selected), encoding='utf-8')
        destination = target if alias == 'attrib' else target.parent / 'art-stage.sga'
        assert not destination.exists(), f'Preserve prior composition output: {destination}'
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
    inputs = read(read(OUT / 'art-cook-pointer.json')['inputs'])
    assert source_inputs() == inputs['inputs'] and editable_inputs() == inputs['editable_inputs']
    archive = Path(candidate['archive'])
    assert sha(archive) == candidate['sha256'] and sha(BASELINE) == candidate['baseline_sha256']
    before_index, after_index = listing(BASELINE), listing(archive)
    assert before_index['archive']['tocs'] == after_index['archive']['tocs']
    before, after = unpack(BASELINE, 'accepted021'), unpack(archive, 'candidate030')
    old = {r['path'] for r in before_index['members']}
    new = {r['path'] for r in after_index['members']}
    assert old <= new
    payloads = {r['member']: r for r in candidate['payloads']}
    assert len(payloads) == len(candidate['payloads'])
    changes = {m for m in old if sha(before / m) != sha(after / m)}
    expected = {MODELS[key][0] + ext for key in ('exposed_pit', 'covered_pit')
                for ext in ('.rgm', '.rrgeom', '.rrmaterial')}
    expected |= {MINISTRY_ACTOR, *LANDMARK_MEMBERS}
    assert changes == expected, (changes, expected)
    assert new - old == set(payloads) - old
    assert set(payloads) - old <= new
    for member, row in payloads.items():
        assert sha(after / member) == row['sha256'], member
    import footprint
    from garrison_shared import rgd
    source_proof = footprint.verify_source()
    actor_proofs = {MINISTRY_ACTOR: footprint.compiled_proof(before / MINISTRY_ACTOR, after / MINISTRY_ACTOR)}
    actor_proofs.update({m: footprint.landmark_compiled_proof(before / m, after / m) for m in LANDMARK_MEMBERS})
    visited = set(actor_proofs)
    media = read(WORK / 'media.json')
    for stem in media['models']:
        for ext in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial'):
            path = after / (stem + ext)
            assert path.is_file(), path
            rc.load(path)
            if stem.startswith('art/scenario/cc010/') and ext == '.rgo':
                assert sha(path) == sha(before / (stem + '.rgo'))
            else:
                visited.add(stem + ext)
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
                assert member.startswith(stem.rsplit('/', 1)[0] + '/v030_'), member
                assert member in payloads and (after / member).is_file(), member
                visited.add(member)
    # The new private stamp and list resources must resolve to the new model stems.
    graph = read(OUT / 'inventory/landmarks.json')['landmarks']
    for key in ACTORS:
        stamp = f'art/stamps/cc030/{key}.bin'
        tree = native.NativeTree(after / stamp)
        visuals = native.active_visuals(tree)
        assert visuals[0]['model'].replace('\\', '/') == MODEL_STEMS[key]
        prior = next(iter(graph[key]['stamps'].values()))['visuals']
        selected = [v for v in prior if v['id'] in KEEP_SCENERY_IDS[key]]
        assert len(visuals) == 1 + len(selected)
        assert [v['model'] for v in visuals[1:]] == [v['model'] for v in selected]
        visited.add(stamp)
        entry = read(WORK / 'registered-identities.json')[key]
        list_member = entry['final']
        fields = dict(rgd.flatten(rgd.read((after / list_member).read_bytes()).nodes))
        assert any(n.key == 'stamp' and str(n.value).replace('\\', '/').lower() == STAMP_PREFIX + key
                   for n in fields.values())
        visited.add(list_member)
    assert visited == set(payloads), ('Unvisited payload', set(payloads) ^ visited)
    placement = {key: landmark_placement(key, after / (MODEL_STEMS[key] + '.rrgeom'),
                                         after / f'art/stamps/cc030/{key}.bin') for key in ACTORS}
    # The existing Ministry visual must be byte-for-byte identical to accepted 0.2.1.
    ministry = [m for m in old if m.startswith('art/scenario/cc020/economy_ministry/')]
    assert ministry and all(sha(before / m) == sha(after / m) for m in ministry)
    result = {'status': 'passed', 'sga_sha256': sha(archive), 'baseline_sha256': sha(BASELINE),
        'baseline_members': len(old), 'final_members': len(new), 'changed': sorted(changes),
        'added': sorted(new - old), 'untouched_members': len(old - changes),
        'actor_proofs': actor_proofs, 'source_proof': source_proof,
        'all_other_nonvisual_members_byte_identical': True,
        'ministry_visual_members_byte_identical': len(ministry),
        'landmark_placement': placement, 'all_payloads_typed_visited': True,
        'native_runtime': 'pending user match'}
    write(OUT / 'archive-verification.json', result)
    print('ARCHIVE_030_VERIFIED', len(changes), len(new - old), len(old - changes), flush=True)
    return result
def checks():
    guarded()
    # Compare against immutable accepted 0.2.1 source and release evidence.
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
    baseline = read(EXTERNAL / 'output/release_021/release-checks.json')['tests']
    assert tests['tests'] >= baseline['tests'] and set(tests['failures']) == set(baseline['failures'])
    assert not tests['errors'] and not tests['skipped']
    validator = Path(r'C:\Users\RS\.codex\skills\modify-aoe4-tuning-packs\scripts\validate_tuning_pack.py')
    command = run_logged('static-source', [CONFIG['python'], '-B', validator, ROOT])
    result = {'status': 'baseline-equivalent-with-known-failures', 'tests': tests,
        'raw_suite_exit_code': process.returncode, 'static_validation': command,
        'source_and_prior_art': preservation, 'native_runtime': 'pending user test'}
    write(OUT / 'release-checks.json', result)
    print('CHECKS_030_PASSED', tests['tests'], 'tests; inherited failures', len(tests['failures']), flush=True)
    return result

START = '''COMMUNITY CIVILIZATION PACK 0.3.0 — traps and first-age landmarks

Close AoE4. Import this ZIP into Garrison and enable it. Select Community
Civilization Pack in BOTH Game Mode and Tuning Pack. Choose China in the lobby,
then Vietnam in the opening selection. Do not select companion_tuning_pack or
Vietnam v2 as the tuning pack for this game mode. Disable other editions for an
isolated test. If blueprints are reported unavailable, check the match setup.

Check both pit traps on different terrain and slopes, before/after upgrades,
construction, attacks, destruction and four-second expiry. Check Pho Minh and
One Pillar from their first-age choices, including the alternate headquarters
actor, in construction, completed, damaged and destroyed states. Check near/far
views, two player colours, unit paths and production. The Ministry has its old
8x8 placement footprint and its 0.2.1 hall, storage and three static elephants.
Confirm existing houses and all other 0.2.1 buildings remain unchanged.

Rollback: close AoE4 and reimport the accepted 0.2.1 ZIP through Garrison.
Build/cook/readback/package checks are separate from native-match acceptance.
No client installation or game match is performed by this release command.
'''

def package():
    audit = verify()
    from trap_audit import audit as audit_traps
    candidate = read(OUT / 'candidate.json')
    trap_visual = audit_traps(unpack(BASELINE, 'accepted021'), unpack(candidate['archive'], 'candidate030'))
    checked = checks()
    mcp_path = OUT / 'traps/mcp-inspection.json'
    assert sha(mcp_path) == 'f2637ae98d8dfd2b436cf3a1c33ce87315e29c9eb661adae3adde881b3cc4e26'
    trap_mcp = read(mcp_path)
    assert trap_mcp['status'] == 'passed' and trap_mcp['claim_released'] is True
    assert trap_mcp['source_hashes_unchanged_after_live_inspection'] is True
    assert all(sha(ROOT / member) == digest for member, digest in trap_mcp['source_export_sha256'].items())
    frozen_inputs = read(read(OUT / 'art-cook-pointer.json')['inputs'])['inputs']
    handoffs = {}
    for key in ('pho_minh', 'one_pillar'):
        path = OUT / 'landmarks' / key / 'handoff.json'
        handoff = read(path)
        assert handoff['name'] == key and handoff['export_sha256'] == frozen_inputs[key]
        assert sha(handoff['source_blend']) == handoff['source_blend_sha256']
        handoffs[key] = {'sha256': sha(path), 'receipt': handoff}
    budget_path = OUT / 'budget/stock-budget.json'
    budget = read(budget_path)
    assert budget['status'] == 'qualified_static_drawgraph_budget'
    assert budget['method']['selector_evidence_sha256'] == sha(OUT / 'inventory/stock-completed-budget.json')
    assert {row['id']: row['completed_healthy_lod0_triangles'] for row in budget['assets']} == {
        'academy': 59496, 'gate': 98762, 'aachen': 90258}
    reviews = {'trap_mcp': {'sha256': sha(mcp_path), 'receipt': trap_mcp},
               'landmark_handoffs': handoffs,
               'stock_budget': {'sha256': sha(budget_path), 'receipt': budget}}
    folder = OUT / 'package'
    folder.mkdir(exist_ok=True)
    target = folder / (KEY + '.sga')
    if target.exists(): assert sha(target) == candidate['sha256'], 'Keep prior package; use a new release directory'
    else: shutil.copy2(candidate['archive'], target)
    manifest = {'schema': 'garrison.mod/v1', 'bundle_key': KEY,
        'members': [{'mod_key': KEY, 'role': 'tuning', 'path': KEY + '.sga', 'sha256': sha(target)}],
        'details': {'id': KEY, 'name': CONFIG['display_name'], 'version': VERSION,
            'summary': 'Natural pit-trap camouflage and Vietnamese first-age Pho Minh and One Pillar landmarks',
            'min_garrison': '0.1.4', 'content_types': ['game-mode', 'tuning-pack'],
            'updated': datetime.now(timezone.utc).date().isoformat(),
            'description': 'New trap camouflage and two first-age landmark visuals. Ministry placement returns to 8x8 with its 0.2.1 model retained. Gameplay and other buildings remain unchanged. Native testing pending.'}}
    write(folder / 'garrison.json', manifest)
    (folder / 'START-HERE.txt').write_text(START, encoding='utf-8')
    evidence = {'version': VERSION, 'project_guid': GUID, 'sga_sha256': sha(target),
        'archive': audit, 'trap_material_readback': trap_visual, 'review_receipts': reviews,
        'checks': checked,
        'reference_cook': read(WORK / 'reference-cook.json'),
        'native_footprint_build': read(read(OUT / 'footprint/current.json')['receipt']),
        'native_runtime': 'pending user test', 'multiplayer': 'not tested'}
    write(folder / 'EVIDENCE.json', evidence)
    destination = OUT / (KEY + '-' + VERSION + '.zip')
    temporary = destination.with_suffix('.zip.tmp')
    assert not temporary.exists(), f'Unreviewed temporary delivery exists: {temporary}'
    with ZipFile(temporary, 'w', ZIP_DEFLATED, compresslevel=6) as bundle:
        for name in ('garrison.json', KEY + '.sga', 'START-HERE.txt', 'EVIDENCE.json'): bundle.write(folder / name, name)
    with ZipFile(temporary) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == len(set(bundle.namelist())) == 4
        assert bundle.namelist().count('garrison.json') == 1
        assert json.loads(bundle.read('garrison.json')) == manifest
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == sha(target)
    if destination.exists():
        assert sha(destination) == sha(temporary), f'Existing delivery differs; preserve and review: {destination}'
        temporary.unlink()
    else:
        temporary.replace(destination)
    receipt = {'status': 'passed', 'version': VERSION, 'zip': str(destination),
        'zip_sha256': sha(destination), 'zip_bytes': destination.stat().st_size,
        'sga': str(target), 'sga_sha256': sha(target), 'native_runtime': 'pending user test'}
    write(OUT / 'package-verification.json', receipt)
    print('PACKAGE_030_VERIFIED', receipt['zip'], receipt['zip_sha256'], flush=True)
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
        evidence = json.loads(bundle.read('EVIDENCE.json'))
        reviews = evidence['review_receipts']
        assert reviews['trap_mcp']['sha256'] == sha(OUT / 'traps/mcp-inspection.json')
        assert reviews['stock_budget']['sha256'] == sha(OUT / 'budget/stock-budget.json')
        assert all(row['sha256'] == sha(OUT / 'landmarks' / key / 'handoff.json')
                   for key, row in reviews['landmark_handoffs'].items())
    print('PACKAGE_030_REPEAT_VERIFIED', flush=True)

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
    elif action == 'candidate':
        cook(sys.argv[2]); assemble(); qualify(sys.argv[2]); compose(sys.argv[2])
    else: raise SystemExit('cook|assemble|qualify|compose|verify|package|verify-only|rebuild')
