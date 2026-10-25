"""Historical test and source-validation gate for the 0.4.0 delivery."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import ROOT, OUT, CONFIG, guarded, read, run_logged, write
from source_policy import verify as verify_source


def run():
    guarded()
    source = verify_source()
    body = '''import io,json,sys,unittest
suite=unittest.defaultTestLoader.discover('tests')
stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
print(stream.getvalue(),file=sys.stderr)
print('RELEASE_TEST_RESULT='+json.dumps({'tests':result.testsRun,'failures':[t.id() for t,d in result.failures],'errors':[t.id() for t,d in result.errors],'skipped':[t.id() for t,d in result.skipped]}))
raise SystemExit(not result.wasSuccessful())
'''
    process = subprocess.run([CONFIG['python'], '-B', '-c', body], cwd=ROOT,
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    (OUT / 'release-tests.log').write_text(process.stdout + '\nSTDERR:\n' + process.stderr, encoding='utf-8')
    tests = json.loads(next(line.split('=', 1)[1] for line in process.stdout.splitlines()
                            if line.startswith('RELEASE_TEST_RESULT=')))
    baseline = read(OUT.parent / 'release_030/release-checks.json')['tests']
    assert tests['tests'] >= baseline['tests']
    assert set(tests['failures']) == set(baseline['failures']) and len(tests['failures']) == 2
    assert not tests['errors'] and not tests['skipped']
    validator = Path(r'C:\Users\RS\.codex\skills\modify-aoe4-tuning-packs\scripts\validate_tuning_pack.py')
    static = run_logged('static-source040', [CONFIG['python'], '-B', validator, ROOT])
    result = {'status': 'baseline-equivalent-with-two-inherited-failures',
              'tests': tests, 'raw_suite_exit_code': process.returncode,
              'static_validation': static, 'source_preservation': source,
              'native_runtime': 'unverified'}
    write(OUT / 'release-checks.json', result)
    return result


if __name__ == '__main__':
    run()
