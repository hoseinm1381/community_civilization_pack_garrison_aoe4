"""0.3.0 Ministry placement exception: four floats 16 -> 8 only."""
import copy
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from common import ROOT, OUT, CONFIG, ARCH, EDITOR, GUID, guarded, read, sha, write, run_logged

REL = 'attrib/instances/ebps/vietnam/vn_building_econ_food_control_chi.xml'
MEMBER = 'attrib/ebps/vietnam/vn_building_econ_food_control_chi.rgd'
LANDMARK_MEMBERS = tuple('attrib/ebps/vietnam/' + name + '.rgd' for name in (
    'vn_building_landmark_age1_gatehouse_control_chi',
    'vn_building_landmark_age1_vit_one_pilar_pagoda',
    'vn_building_landmark_age1_headquarters_control_chi'))
WORK = OUT / 'footprint'
ORIGINAL = OUT / 'source-baseline' / REL
BASELINE = ROOT / 'archives/release_021_user_accepted/community_civilization_pack.sga'


def xml_proof(before, after):
    old, new = ET.fromstring(Path(before).read_bytes()), ET.fromstring(Path(after).read_bytes())
    restored = copy.deepcopy(new)
    changes = []
    for tree, expected in ((old, '16'), (new, '8'), (restored, '8')):
        nodes = tree.findall("./list[@name='extensions']/template_reference[@value='ebpextensions\\site_ext']/group[@name='footprint_scale']/float")
        nodes += tree.findall("./variant[@name='campaign']/list[@name='extensions']/template_reference[@value='ebpextensions\\site_ext']/group[@name='footprint_scale']/float")
        assert len(nodes) == 4 and [n.get('name') for n in nodes] == ['x', 'y', 'x', 'y']
        assert all(n.get('value') == expected and n.get('overrideParent') == 'True' for n in nodes)
        if tree is restored:
            for n in nodes: n.set('value', '16')
    assert ET.tostring(restored) == ET.tostring(old), 'Unexpected typed XML modification'
    restored_bytes, count = re.subn(rb'(<group name="footprint_scale">\s*<float name="x" value=")8("[^>]+/>\s*<float name="y" value=")8', rb'\g<1>16\g<2>16', Path(after).read_bytes())
    assert count == 2 and restored_bytes == Path(before).read_bytes(), 'Unapproved source byte change'
    for variant in ('default', 'campaign'):
        for axis in ('x', 'y'): changes.append({'variant': variant, 'property': 'site_ext/footprint_scale/' + axis, 'before': 16, 'after': 8, 'type': 'float'})
    return {'changes': changes, 'all_other_xml_nodes_attributes_text_identical': True, 'all_other_source_bytes_identical': True}


def prepare():
    guarded()
    path = ROOT / 'assets' / REL
    data = path.read_bytes()
    assert ORIGINAL.exists() and sha(ORIGINAL) == read(OUT / 'source-baseline.json')['assets'][REL]['sha256']
    baseline = ORIGINAL.read_bytes()
    updated, count = re.subn(rb'(<group name="footprint_scale">\s*<float name="x" value=")16("[^>]+/>\s*<float name="y" value=")16', rb'\g<1>8\g<2>8', baseline)
    assert count == 2, count
    assert data in (baseline, updated), 'Ministry source drift'
    if data == baseline: path.write_bytes(updated)
    result = verify_source()
    write(WORK / 'source-preservation.json', result)
    return result


def verify_source():
    import importlib.util
    spec = importlib.util.spec_from_file_location('release030_source_policy', Path(__file__).with_name('source_policy.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    all_source = module.verify()
    proof = xml_proof(ORIGINAL, ROOT / 'assets' / REL)
    return {'status': 'passed', 'source_policy': all_source, 'source_exception': proof,
            'source_assets_sha256': {p.relative_to(ROOT / 'assets').as_posix(): sha(p)
                for p in (ROOT / 'assets').rglob('*') if p.is_file()}}


def compiled_proof(before_file, after_file):
    sys.path.append(str(ROOT / 'tools/release_010'))
    import integration
    from garrison_shared import rgd
    old = rgd.read(Path(before_file).read_bytes())
    new = rgd.read(Path(after_file).read_bytes())
    restored = copy.deepcopy(new)
    a, b = dict(rgd.flatten(old.nodes)), dict(rgd.flatten(new.nodes))
    assert a.keys() == b.keys(), 'Compiled node paths changed'
    changes = []
    for path, left in a.items():
        right = b[path]
        assert left.kind == right.kind and left.key == right.key
        if left.kind not in ('List', 'List2') and left.value != right.value:
            assert path in {v + '/site_ext/footprint_scale/' + axis for v in ('default', 'campaign') for axis in ('x', 'y')}, path
            assert left.value == 16 and right.value == 8, (path, left.value, right.value)
            assert left.kind == 'Float', (path, left.kind)
            rgd.find(restored.nodes, path).value = left.value
            changes.append({'path': path, 'type': left.kind, 'before': left.value, 'after': right.value})
    assert len(changes) == 4, changes
    assert rgd.write(restored) == rgd.write(old), 'Unexpected compiled actor difference'
    return {'status': 'passed', 'changes': changes, 'all_other_typed_fields_and_serialized_bytes_identical': True,
            'before_sha256': sha(before_file), 'after_sha256': sha(after_file)}


def landmark_compiled_proof(before_file, after_file):
    sys.path.append(str(ROOT / 'tools/release_010'))
    from garrison_shared import rgd
    old = rgd.read(Path(before_file).read_bytes())
    new = rgd.read(Path(after_file).read_bytes())
    a, b = dict(rgd.flatten(old.nodes)), dict(rgd.flatten(new.nodes))
    assert a.keys() == b.keys()
    restored = copy.deepcopy(new)
    changes = []
    for path, left in a.items():
        right = b[path]
        assert left.kind == right.kind and left.key == right.key
        if left.kind not in ('List', 'List2') and left.value != right.value:
            assert '/attachments/' in path and left.key in ('$PBGNAME', '$PBGMAP'), (path, left.value, right.value)
            if left.key == '$PBGNAME':
                assert str(right.value).startswith(GUID.replace('-', '') + ':vn_030_'), (path, right.value)
            else:
                assert right.value == r'attachments\attachment_lists', (path, right.value)
            rgd.find(restored.nodes, path).value = left.value
            changes.append({'path': path, 'before': left.value, 'after': right.value, 'type': left.kind})
    assert changes and rgd.write(restored) == rgd.write(old), 'Unapproved compiled landmark actor change'
    return {'status': 'passed', 'changes': changes, 'all_other_typed_fields_and_serialized_bytes_identical': True,
            'before_sha256': sha(before_file), 'after_sha256': sha(after_file)}


def compile_candidate(label):
    """Caller must hold release_020/native-build.lock FileShare.None for entire call."""
    assert re.fullmatch(r'[a-z][a-z0-9-]{2,25}', label)
    proof = verify_source()
    run = WORK / 'runs' / label
    assert not run.exists(), 'Append-only native build label required'
    source = run / 'source'
    source.mkdir(parents=True)
    shutil.copytree(ROOT / 'assets', source / 'assets')
    shutil.copy2(ROOT / CONFIG['project_file'], source / CONFIG['project_file'])
    command = run_logged('footprint-' + label, [EDITOR, '-rtm', '--safe_settings', '--do_not_restore',
        '--quiet_crash_report', '--no_source_control', '--log_path', run / 'native-logs',
        '--build_mod', source / CONFIG['project_file'], '--build_path', run / 'build', '--no_burn_window',
        '--burn_cache_type', 'Local', '--burn_max_threads', '1', '--burn_platform', 'PC',
        '--burn_log_path', run / 'burn.log', '--intermediate_path', run / 'intermediate'], cwd=EDITOR.parent, timeout=1800)
    return finish(label, proof, command)


def finish(label, proof=None, command=None):
    """Finish a successful native invocation without repeating its build."""
    assert re.fullmatch(r'[a-z][a-z0-9-]{2,25}', label)
    proof = proof or verify_source()
    run = WORK / 'runs' / label
    source = run / 'source'
    command = command or read(OUT / 'logs' / ('footprint-' + label + '.json'))
    assert command['exit_code'] == 0
    log = Path(command['log']).read_text(encoding='utf-8', errors='replace')
    errors = [l for l in log.splitlines() if 'EssenceEditor.exe Error:' in l or 'System does not support' in l]
    missing = [l for l in log.splitlines() if str(source).lower() in l.lower() and ("doesn't exist" in l or 'does not exist' in l)]
    validated = re.findall(r'(\d+) instances validated', log)
    expected_instances = len(list((source / 'assets/attrib/instances').rglob('*.xml')))
    assert expected_instances >= 255
    assert not errors and not missing and validated and int(validated[-1]) == expected_instances, (errors, missing, validated)
    archives = list((run / 'build').rglob('*.sga'))
    assert len(archives) == 1
    archive = archives[0]
    listing = json.loads(subprocess.run([str(ARCH), 'list', str(archive), '--verify'], capture_output=True, text=True, check=True).stdout)
    assert listing['archive']['verification']['verified']
    assert listing['archive']['name'].replace('-', '').lower() == GUID.replace('-', '').lower()
    payloads, proofs = [], {}
    for member in (MEMBER, *LANDMARK_MEMBERS):
        target = run / 'payload' / member
        before = run / 'baseline' / member
        for arc, dest in ((archive, target), (BASELINE, before)):
            dest.parent.mkdir(parents=True, exist_ok=True)
            extraction = dest if not dest.exists() else dest.with_suffix('.resume.rgd')
            if extraction.exists(): raise RuntimeError('Prior incomplete resume evidence retained: ' + str(extraction))
            subprocess.run([str(ARCH), 'extract-member', str(arc), member, str(extraction)], check=True, capture_output=True)
            if extraction != dest: assert sha(extraction) == sha(dest), 'Previously extracted member differs'
        proofs[member] = (compiled_proof(before, target) if member == MEMBER else landmark_compiled_proof(before, target))
        payloads.append({'member': member, 'file': str(target), 'sha256': sha(target), 'bytes': target.stat().st_size})
    assert proof == verify_source()
    assert {p.relative_to(source / 'assets').as_posix(): sha(p) for p in (source / 'assets').rglob('*') if p.is_file()} == proof['source_assets_sha256']
    result = {'schema': 'community.release030.footprint-native/v1', 'status': 'passed', 'label': label,
              'archive': str(archive), 'sha256': sha(archive), 'native_validated_instances': expected_instances,
              'command': command, 'source_preservation': proof, 'compiled_actor_proofs': proofs,
              'payloads': payloads,
              'runtime': 'pending user placement and production test'}
    write(run / 'receipt.json', result)
    write(WORK / 'current.json', {'receipt': str(run / 'receipt.json'), 'sha256': sha(run / 'receipt.json')})
    return result


def compiled_payload():
    pointer = read(WORK / 'current.json')
    assert sha(pointer['receipt']) == pointer['sha256']
    receipt = read(pointer['receipt'])
    assert receipt['status'] == 'passed' and receipt['native_validated_instances'] >= 255
    assert receipt['source_preservation'] == verify_source()
    assert sha(receipt['archive']) == receipt['sha256']
    rows = receipt['payloads']
    assert {r['member'] for r in rows} == {MEMBER, *LANDMARK_MEMBERS}
    for row in rows:
        assert sha(row['file']) == row['sha256'] and Path(row['file']).stat().st_size == row['bytes']
    run = Path(pointer['receipt']).parent
    for row in rows:
        member = row['member']
        proof = compiled_proof(run / 'baseline' / member, row['file']) if member == MEMBER else landmark_compiled_proof(run / 'baseline' / member, row['file'])
        assert proof == receipt['compiled_actor_proofs'][member]
    return rows


if __name__ == '__main__':
    if sys.argv[1] == 'prepare': result = prepare()
    elif sys.argv[1] == 'verify-source': result = verify_source()
    elif sys.argv[1] == 'compile': result = compile_candidate(sys.argv[2])
    elif sys.argv[1] == 'finish': result = finish(sys.argv[2])
    elif sys.argv[1] == 'payload': result = compiled_payload()
    else: raise ValueError('Expected verify-source, compile LABEL, or payload')
    if sys.argv[1] == 'verify-source':
        print(json.dumps({key: result[key] for key in ('status', 'source_exception')}, indent=2))
    elif sys.argv[1] in ('compile', 'finish'):
        print(json.dumps({key: result[key] for key in ('status', 'label', 'archive',
            'sha256', 'native_validated_instances', 'payloads')}, indent=2))
    else:
        print(json.dumps(result, indent=2))
