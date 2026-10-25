"""Release gate: 0.1.0 source/art intact, historical test failures only, static XML valid."""
import json
import re
import subprocess
import sys
from pathlib import Path
from common import CONFIG, OUT, ROOT, guarded, read, sha, write
from source_policy import CONSUMERS, verify as verify_sources
from guard_source_contract import verify as verify_source_graph
from freeze_art import verify as verify_accepted_art

BODY = r'''
import io,json,sys,unittest
suite=unittest.defaultTestLoader.discover('tests')
stream=io.StringIO()
result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
print(stream.getvalue(),file=sys.stderr)
print('RELEASE_TEST_RESULT='+json.dumps({'tests':result.testsRun,
    'failures':[t.id() for t,d in result.failures], 'errors':[t.id() for t,d in result.errors],
    'skipped':[t.id() for t,d in result.skipped]}),flush=True)
raise SystemExit(not result.wasSuccessful())
'''


def verify(candidate_path):
    frozen = guarded()
    candidate_path = Path(candidate_path)
    candidate = read(candidate_path)
    identities = read(OUT / 'integration/registered-identities.json')
    source = verify_sources([row['source'] for row in identities])
    graph_guard = verify_source_graph()
    assert graph_guard['source_assets_sha256'] == source['source_assets_sha256']
    assert candidate['candidate_source_build']['source_preservation']['source_assets_sha256'] == source['source_assets_sha256']
    precache_path = ROOT / 'assets/scar/vietnam/prematch_precache.scar'
    precache = precache_path.read_text(encoding='utf-8')
    entity_block = re.search(r'local entities\s*=\s*\{(.*?)\}', precache, re.S)
    assert entity_block is not None, 'Missing prematch entity loading table'
    queued = set(re.findall(r'"([0-9a-f]{32}:[^"]+)"', entity_block[1]))
    required = {CONFIG['project_guid'].replace('-', '') + ':' + name for name in CONSUMERS}
    assert required <= queued, ('Missing building precache', required - queued)
    assert 'Scar_AddInit(VietnamPrecache_Init)' in precache
    assert 'Scar_PrecachePrematchResource(BP_GetEntityBlueprint(name))' in precache
    art = verify_accepted_art()
    normal = Path(CONFIG['source_root'])
    expected = read(ROOT / 'docs/preparation/normal-before.json')
    actual = {p.relative_to(normal).as_posix(): p for p in normal.rglob('*') if p.is_file()}
    if set(actual) != set(expected) or any(sha(actual[name]) != row['sha256'] for name, row in expected.items()):
        raise ValueError('Preserved normal edition changed')
    process = subprocess.run([CONFIG['python'], '-B', '-c', BODY], cwd=ROOT,
                             capture_output=True, text=True, encoding='utf-8', errors='replace')
    (OUT / 'release-tests.log').write_text(process.stdout + '\nSTDERR:\n' + process.stderr, encoding='utf-8')
    matches = [line for line in process.stdout.splitlines() if line.startswith('RELEASE_TEST_RESULT=')]
    assert len(matches) == 1
    tests = json.loads(matches[0].split('=', 1)[1])
    expected_failures = {f"test_legacy_trap_tunnel.OriginalTuningParityTests.test_native_tunneling_and_weapon_data_match_original (name='{name}')"
        for name in ('vn_weapon_outpost_handcannon_bambo_alarm_chi', 'vn_weapon_outpost_handcannon_bambo_chi')}
    if tests['errors'] or tests['skipped'] or set(tests['failures']) != expected_failures:
        raise ValueError(f'New test regression: {tests}')
    baseline_tests = read(OUT / 'baseline-tests.json')
    assert baseline_tests['accepted_baseline'] and tests['tests'] >= 68
    installed = Path(r'C:\Users\RS\.codex\skills\modify-aoe4-tuning-packs\scripts\validate_tuning_pack.py')
    assert installed.exists()
    static = subprocess.run([CONFIG['python'], '-B', str(installed), str(ROOT)],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    (OUT / 'release-static.log').write_text(static.stdout + static.stderr, encoding='utf-8')
    assert static.returncode == 0, 'Static tuning validation failed'
    summary = re.search(r'Validated (\d+) pack\(s\), (\d+) instance\(s\): (\d+) error\(s\), (\d+) warning\(s\), (\d+) info', static.stdout)
    assert summary, 'Could not parse static summary'
    result = {'status': 'baseline-equivalent-with-known-failures', 'tests': tests,
              'raw_suite_exit_code': process.returncode, 'static_exit_code': static.returncode,
              'static_summary': dict(zip(('packs', 'instances', 'errors', 'warnings', 'info'), map(int, summary.groups()))),
              'candidate_sha256': sha(candidate_path), 'sga_sha256': candidate['sha256'],
              'source_assets_sha256': source['source_assets_sha256'], 'normal_files_unchanged': len(expected),
              'accepted_010_art_files_unchanged': art['files_unchanged'], 'native_runtime': 'unverified'}
    result['loading_coverage'] = {'status': 'passed', 'actors': sorted(required),
                                'prematch_source_sha256': sha(precache_path),
                                'evidence': 'Static unchanged prematch hook and entity table; native loading remains a user gate.'}
    write(OUT / 'release-checks.json', result)
    print('RELEASE_020_CHECKS', result['tests']['tests'], 'tests; historical failures', len(expected_failures))
    return result


if __name__ == '__main__':
    verify(sys.argv[1])
