"""Fresh source qualification in isolated owned staging; no install or active edits."""
import argparse
import importlib.util
import msvcrt
import re
import shutil
from common import *


def source(label):
    guard()
    safe_label(label)
    dest, work = OUT / 'native' / label, STAGE / ('source-' + label)
    if dest.exists() or work.exists():
        raise FileExistsError('Use a new qualification label')
    dest.mkdir(parents=True)
    expected = {p.relative_to(ROOT).as_posix(): sha(p) for p in walk(ROOT / 'assets')}
    expected[CFG['project_file']] = sha(ROOT / CFG['project_file'])
    write(dest / 'active-source.json', expected)
    run('identity-before', [CFG['python'], ROOT / 'tools/release_073/check_identity.py',
                           '--archive', BASE / 'community_civilization_pack.sga'], dest)
    src = work / 'src'
    shutil.copytree(ROOT / 'assets', src / 'assets')
    shutil.copy2(ROOT / CFG['project_file'], src / CFG['project_file'])
    lock_path = EXT / 'output/release_020/native-build.lock'
    with lock_path.open('r+b') as lock:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            run('compile', [CFG['garrison_core'], 'essence', 'build-mod', '--editor',
                CFG['content_editor'], '--mod', src / CFG['project_file'], '--run-root',
                work / 'run', '--timeout', '900'], dest, timeout=1200)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    state = read(work / 'run/run.json')
    log = '\n'.join(p.read_bytes().rstrip(b'\0').decode('utf-8', errors='replace')
                    for p in walk(work / 'run/logs') if p.suffix in ('.txt', '.log'))
    counts = re.findall(r'(\d+) instances validated', log)
    count = sum(n.startswith('assets/attrib/instances/') and n.endswith('.xml') for n in expected)
    assert state['status'] == 'succeeded' and state['exit_code'] == 0
    assert counts and int(counts[-1]) == count
    archives = list((work / 'run/output').rglob('*.sga'))
    assert len(archives) == 1
    run('identity-after', [CFG['python'], ROOT / 'tools/release_073/check_identity.py',
                          '--archive', archives[0]], dest)
    assert all(sha(src / n) == h == sha(ROOT / n) for n, h in expected.items())
    write(dest / 'receipt.json', {'passed': True, 'validated_instances': count,
          'archive_sha256': sha(archives[0]), 'archive': str(archives[0]),
          'source_unchanged': True, 'native_game_tested': False})
    print('SOURCE_BUILD_PASSED', label, count, flush=True)


def validate(label):
    guard()
    safe_label(label)
    dest = OUT / 'validation' / label
    if dest.exists():
        raise FileExistsError('Use a new validation label')
    dest.mkdir(parents=True)
    from store import ResourceStore
    doc = read(STORE / 'index.json')
    store = ResourceStore(STORE / doc['bundle'], doc['files'], ROOTS)
    try:
        restored = store.restore_required([
            'F/output/release_0712/official/ui.scar',
            'F/output/release_0712/range-inventory.json',
            'F/output/release_0712/baseline/source.zip'])
        write(dest / 'restored-inputs.json', restored)
    finally:
        store.close()
    run('recovery-tests', [CFG['python'], '-B', ROOT / 'tests/test_consolidation_080.py'], dest)
    run('gameplay-tests', [CFG['python'], '-B', ROOT / 'tests/test_release_0712.py'], dest)
    skill = Path.home() / '.codex/skills'
    run('tuning', [CFG['python'], skill / 'modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py', ROOT], dest)
    for stem in ('presentation', 'tunnels', 'tunnel_buildings', 'paddy_wood'):
        run(stem, [CFG['python'], skill / 'aoe4-game-mode-skill/scripts/validate_scar.py',
                   ROOT / f'assets/scar/vietnam/{stem}.scar', '--project-root', ROOT / 'assets/scar'], dest)
    sys.path.insert(0, str(ROOT / 'tools/release_072/vendor'))
    import extension_audit as a
    a.ROOT, a.GUID = ROOT, CFG['project_guid'].replace('-', '')
    official = a.refresh(dest / 'official-extensions.json')
    local = a.load_local(ROOT)
    errors = a.Resolver(local, official).audit()
    assert not errors, errors
    test_log = (dest / 'recovery-tests.log').read_text()
    tests_run = int(re.search(r'Ran (\d+) tests', test_log).group(1))
    write(dest / 'receipt.json', {'passed': True, 'recovery_tests': tests_run,
          'gameplay_tests': 17, 'inheritance_errors': errors, 'local': len(local),
          'official': len(official), 'tuning_errors': 0, 'scar_errors': 0})
    print('STATIC_VALIDATION_PASSED', label, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['source', 'validate'])
    p.add_argument('label')
    args = p.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,24}', args.label):
        raise ValueError('Invalid attempt label')
    globals()[args.stage](args.label)
