"""0.2.1 explicit Ministry placement exception; immutable 0.2.0 baseline retained."""
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
WORK = OUT / 'footprint'
ORIGINAL = WORK / 'source-baseline' / REL
BASELINE = ROOT / 'archives/release_020_user_accepted/community_civilization_pack.sga'


def xml_proof(before, after):
    old, new = ET.fromstring(Path(before).read_bytes()), ET.fromstring(Path(after).read_bytes())
    restored = copy.deepcopy(new)
    changes = []
    for tree, expected in ((old, '8'), (new, '16'), (restored, '16')):
        nodes = tree.findall("./list[@name='extensions']/template_reference[@value='ebpextensions\\site_ext']/group[@name='footprint_scale']/float")
        nodes += tree.findall("./variant[@name='campaign']/list[@name='extensions']/template_reference[@value='ebpextensions\\site_ext']/group[@name='footprint_scale']/float")
        assert len(nodes) == 4 and [n.get('name') for n in nodes] == ['x', 'y', 'x', 'y']
        assert all(n.get('value') == expected and n.get('overrideParent') == 'True' for n in nodes)
        if tree is restored:
            for n in nodes: n.set('value', '8')
    assert ET.tostring(restored) == ET.tostring(old), 'Unexpected typed XML modification'
    restored_bytes, count = re.subn(rb'(<group name="footprint_scale">\s*<float name="x" value=")16("[^>]+/>\s*<float name="y" value=")16', rb'\g<1>8\g<2>8', Path(after).read_bytes())
    assert count == 2 and restored_bytes == Path(before).read_bytes(), 'Unapproved source byte change'
    for variant in ('default', 'campaign'):
        for axis in ('x', 'y'): changes.append({'variant': variant, 'property': 'site_ext/footprint_scale/' + axis, 'before': 8, 'after': 16, 'type': 'float'})
    return {'changes': changes, 'all_other_xml_nodes_attributes_text_identical': True, 'all_other_source_bytes_identical': True}


def prepare():
    guarded()
    path = ROOT / 'assets' / REL
    data = path.read_bytes()
    assert sha(path) == read(OUT / 'baseline-freeze.json')['active_source_assets']['files'][REL]['sha256']
    ET.fromstring(data)
    ORIGINAL.parent.mkdir(parents=True, exist_ok=True)
    assert not ORIGINAL.exists() or sha(ORIGINAL) == sha(path)
    ORIGINAL.write_bytes(data)
    updated, count = re.subn(rb'(<group name="footprint_scale">\s*<float name="x" value=")8("[^>]+/>\s*<float name="y" value=")8', rb'\g<1>16\g<2>16', data)
    assert count == 2, count
    path.write_bytes(updated)
    result = verify_source()
    write(WORK / 'source-preservation.json', result)
    return result


def verify_source():
    guarded()
    frozen_path = OUT / 'baseline-freeze.json'
    frozen = read(frozen_path)
    assert frozen['schema'] == 'community-civilization-pack.release-021-baseline-freeze/v1'
    assets = ROOT / 'assets'
    sys.path.insert(0, str(ROOT / 'tools/release_021'))
    from freeze_baseline import safe_files
    expected = frozen['active_source_assets']['files']
    assert len(expected) == 289
    assert {p.relative_to(assets).as_posix() for p in safe_files(assets)} == set(expected)
    assert sha(ORIGINAL) == expected[REL]['sha256'], 'Original XML must match immutable freeze'
    for rel, record in expected.items():
        if rel != REL: assert sha(assets / rel) == record['sha256'], rel
    proof = xml_proof(ORIGINAL, assets / REL)
    for base, entries in frozen['preserved_art_manifests'].items():
        if base == 'output/release_020/accepted-art-baseline.json':
            assert sha(ROOT / base) == entries['sha256']
            continue
        folder = ROOT / base
        assert {p.relative_to(folder).as_posix() for p in safe_files(folder)} == set(entries), base
        for rel, row in entries.items(): assert sha(folder / rel) == row['sha256'], (base, rel)
    project = frozen['active_project_file']
    assert sha(project['path']) == project['sha256']
    normal = frozen['normal_source_verification']
    assert sha(normal['baseline_receipt']) == normal['baseline_receipt_sha256']
    normal_files = read(normal['baseline_receipt'])
    assert len(normal_files) == 484
    assert {p.relative_to(Path(normal['source_root'])).as_posix() for p in safe_files(Path(normal['source_root']))} == set(normal_files), 'Preserved normal edition inventory changed'
    for rel, row in normal_files.items(): assert sha(Path(normal['source_root']) / rel) == row['sha256'], rel
    for row in list(frozen['rollback_copies'].values()) + list(frozen['receipt_copies'].values()):
        assert sha(row['archive_copy']) == row['sha256']
    assert sha(BASELINE) == frozen['sga_sha256']
    return {'status': 'passed', 'baseline_freeze_sha256': sha(frozen_path), 'exception_source': REL,
            'source_assets_sha256': {r: sha(assets / r) for r in expected}, 'source_assets_checked': len(expected),
            'normal_files_checked': len(normal_files), 'source_exception': proof,
            'all_other_source_art_project_normal_rollback_hashes_preserved': True}


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
        if left.kind != 'List' and left.value != right.value:
            assert path in {v + '/site_ext/footprint_scale/' + axis for v in ('default', 'campaign') for axis in ('x', 'y')}, path
            assert left.value == 8 and right.value == 16, (path, left.value, right.value)
            assert left.kind == 'Float', (path, left.kind)
            rgd.find(restored.nodes, path).value = left.value
            changes.append({'path': path, 'type': left.kind, 'before': left.value, 'after': right.value})
    assert len(changes) == 4, changes
    assert rgd.write(restored) == rgd.write(old), 'Unexpected compiled actor difference'
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
    assert len(list((source / 'assets/attrib/instances').rglob('*.xml'))) == 255
    assert not errors and not missing and validated and int(validated[-1]) == 255, (errors, missing, validated)
    archives = list((run / 'build').rglob('*.sga'))
    assert len(archives) == 1
    archive = archives[0]
    listing = json.loads(subprocess.run([str(ARCH), 'list', str(archive), '--verify'], capture_output=True, text=True, check=True).stdout)
    assert listing['archive']['verification']['verified']
    assert listing['archive']['name'].replace('-', '').lower() == GUID.replace('-', '').lower()
    target = run / 'payload' / MEMBER
    before = run / 'baseline' / MEMBER
    for arc, dest in ((archive, target), (BASELINE, before)):
        dest.parent.mkdir(parents=True, exist_ok=True)
        extraction = dest if not dest.exists() else dest.with_suffix('.resume.rgd')
        if extraction.exists(): raise RuntimeError('Prior incomplete resume evidence retained: ' + str(extraction))
        subprocess.run([str(ARCH), 'extract-member', str(arc), MEMBER, str(extraction)], check=True, capture_output=True)
        if extraction != dest: assert sha(extraction) == sha(dest), 'Previously extracted member differs'
    typed = compiled_proof(before, target)
    assert proof == verify_source()
    assert {p.relative_to(source / 'assets').as_posix(): sha(p) for p in (source / 'assets').rglob('*') if p.is_file()} == proof['source_assets_sha256']
    result = {'schema': 'community.release021.footprint-native/v1', 'status': 'passed', 'label': label,
              'archive': str(archive), 'sha256': sha(archive), 'native_validated_instances': 255,
              'command': command, 'source_preservation': proof, 'compiled_actor_proof': typed,
              'payload': {'member': MEMBER, 'file': str(target), 'sha256': sha(target), 'bytes': target.stat().st_size},
              'runtime': 'pending user placement and production test'}
    write(run / 'receipt.json', result)
    write(WORK / 'current.json', {'receipt': str(run / 'receipt.json'), 'sha256': sha(run / 'receipt.json')})
    return result


def compiled_payload():
    pointer = read(WORK / 'current.json')
    assert sha(pointer['receipt']) == pointer['sha256']
    receipt = read(pointer['receipt'])
    assert receipt['status'] == 'passed' and receipt['native_validated_instances'] == 255
    assert receipt['source_preservation'] == verify_source()
    assert sha(receipt['archive']) == receipt['sha256']
    row = receipt['payload']
    assert row['member'] == MEMBER and sha(row['file']) == row['sha256']
    assert Path(row['file']).stat().st_size == row['bytes']
    run = Path(pointer['receipt']).parent
    assert compiled_proof(run / 'baseline' / MEMBER, row['file']) == receipt['compiled_actor_proof']
    return row


if __name__ == '__main__':
    if sys.argv[1] == 'prepare': result = prepare()
    elif sys.argv[1] == 'verify-source': result = verify_source()
    elif sys.argv[1] == 'compile': result = compile_candidate(sys.argv[2])
    elif sys.argv[1] == 'finish': result = finish(sys.argv[2])
    elif sys.argv[1] == 'payload': result = compiled_payload()
    else: raise ValueError('Expected verify-source, compile LABEL, or payload')
    if sys.argv[1] == 'verify-source':
        print(json.dumps({key: result[key] for key in ('status', 'exception_source',
            'source_assets_checked', 'normal_files_checked', 'source_exception',
            'all_other_source_art_project_normal_rollback_hashes_preserved')}, indent=2))
    elif sys.argv[1] in ('compile', 'finish'):
        print(json.dumps({key: result[key] for key in ('status', 'label', 'archive',
            'sha256', 'native_validated_instances', 'payload')}, indent=2))
    else:
        print(json.dumps(result, indent=2))
