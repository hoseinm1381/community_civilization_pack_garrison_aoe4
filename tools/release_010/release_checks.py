"""Release-aware checks retain raw inherited failures and reject new regressions."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from common import CONFIG, OUT, ROOT, check_storage, read, sha, write
from source_policy import verify as verify_sources
from workspace_support import check_identity

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
    check_storage(ROOT, CONFIG)
    candidate = read(candidate_path)
    sources = verify_sources(candidate['source_new_files'])
    compiled_sources = candidate['candidate_source_build']['source_preservation']['source_assets_sha256']
    if compiled_sources != sources['source_assets_sha256']:
        raise ValueError('Current source differs from the candidate compiled source snapshot')
    identity = check_identity(ROOT, CONFIG)
    normal = Path(CONFIG['source_root'])
    original = read(ROOT / 'docs/preparation/normal-before.json')
    actual = {p.relative_to(normal).as_posix() for p in normal.rglob('*') if p.is_file()}
    if actual != set(original) or any(sha(normal/p) != row['sha256'] for p,row in original.items()):
        raise ValueError('Normal edition changed')
    process = subprocess.run([sys.executable,'-B','-c',BODY],cwd=ROOT,capture_output=True,
                             text=True,encoding='utf-8',errors='replace')
    (OUT/'release-tests.log').write_text(process.stdout+'\nSTDERR:\n'+process.stderr,encoding='utf-8')
    lines=[line for line in process.stdout.splitlines() if line.startswith('RELEASE_TEST_RESULT=')]
    if len(lines)!=1:
        raise ValueError('Could not parse raw test result')
    tests=json.loads(lines[0].split('=',1)[1])
    expected={f"test_legacy_trap_tunnel.OriginalTuningParityTests.test_native_tunneling_and_weapon_data_match_original (name='{name}')"
        for name in ('vn_weapon_outpost_handcannon_bambo_alarm_chi','vn_weapon_outpost_handcannon_bambo_chi')}
    if tests['errors'] or tests['skipped'] or set(tests['failures'])!=expected:
        write(OUT/'release-checks.json',{'status':'failed','tests':tests,'raw_suite_exit_code':process.returncode})
        raise ValueError(f'New source test regression; inspect release-tests.log: {tests}')
    validator=Path(r'C:\Users\RS\.codex\skills\modify-aoe4-tuning-packs\scripts\validate_tuning_pack.py')
    static=subprocess.run([sys.executable,'-B',str(validator),str(ROOT)],capture_output=True,
                          text=True,encoding='utf-8',errors='replace')
    (OUT/'release-static.log').write_text(static.stdout+static.stderr,encoding='utf-8')
    if static.returncode:
        raise ValueError('Tuning static validation failed')
    summary = re.search(r'Validated (\d+) pack\(s\), (\d+) instance\(s\): (\d+) error\(s\), (\d+) warning\(s\), (\d+) info', static.stdout)
    if not summary:
        raise ValueError('Could not parse static validation summary')
    result={'status':'baseline-equivalent-with-known-failures','tests':tests,
        'candidate_sha256':sha(candidate_path),'sga_sha256':candidate['sha256'],
        'source_assets_sha256':sources['source_assets_sha256'],
        'raw_suite_exit_code':process.returncode,'normal_files_unchanged':len(original),
        'identity':identity,'static_exit_code':static.returncode,'gameplay_source_guard':'passed',
        'static_summary':dict(zip(('packs','instances','errors','warnings','info'),map(int,summary.groups()))),
        'changed_existing_source_files':len(sources['changed_existing_source']),
        'runtime':'not tested'}
    write(OUT/'release-checks.json',result)
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,default=OUT/'integration/candidate.json')
    verify(parser.parse_args().candidate)
