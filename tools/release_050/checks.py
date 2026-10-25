"""0.5.0 checks against the frozen completed 0.4.0, with no game claims."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from common import CONFIG, ROOT, OUT, guarded, read, write, run_logged

def run():
    guarded()
    from source_policy import verify
    source=verify()
    assert source['status']=='passed'
    run_logged('freeze050-post-edit',[CONFIG['blender_python'],'-B',ROOT/'tools/release_050/freeze_baseline.py','--verify-post-edit'])
    body='''import io,json,sys,unittest
suite=unittest.defaultTestLoader.discover('tests')
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
print(stream.getvalue(),file=sys.stderr)
print('RELEASE_TEST_RESULT='+json.dumps({'tests':result.testsRun,'failures':[t.id() for t,d in result.failures],'errors':[t.id() for t,d in result.errors],'skipped':[t.id() for t,d in result.skipped]}))
raise SystemExit(not result.wasSuccessful())
'''
    process=subprocess.run([CONFIG['python'],'-B','-c',body],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (OUT/'release-tests.log').write_text(process.stdout+'\nSTDERR:\n'+process.stderr,encoding='utf-8')
    tests=json.loads(next(line.split('=',1)[1] for line in process.stdout.splitlines() if line.startswith('RELEASE_TEST_RESULT=')))
    baseline=read(OUT.parent/'release_040/release-checks.json')['tests']
    assert tests['tests']>=baseline['tests']
    assert set(tests['failures'])==set(baseline['failures']) and len(tests['failures'])==2,tests
    assert not tests['errors'] and not tests['skipped'],tests
    validator=Path(r'C:\Users\RS\.codex\skills\modify-aoe4-tuning-packs\scripts\validate_tuning_pack.py')
    static=run_logged('static-source050',[CONFIG['python'],'-B',validator,ROOT])
    from reference_contracts import ACTORS
    loading=(ROOT/'assets/scar/vietnam/prematch_precache.scar').read_text(encoding='utf-8')
    guid=CONFIG['project_guid'].replace('-','')
    assert all(guid+':'+actor in loading for actor in ACTORS)
    result={'status':'baseline-equivalent-with-two-inherited-failures','tests':tests,
            'raw_suite_exit_code':process.returncode,'source_preservation':source,
            'static_validation':static,'native_runtime':'not tested'}
    result['prematch_actor_coverage']={'actors':list(ACTORS),'all_six_preloaded_by_existing_unchanged_scar':True}
    result['identity_guard_fixture']='Uses unchanged wood camp because keep now has authorized visual bindings; exact comparison and deliberate nonidentity-mutation rejection are retained. Original test preserved under baseline/test_workspace-pre050-fixture.py.'
    write(OUT/'release-checks.json',result)
    print('RELEASE050_CHECKS',tests['tests'],'tests; two inherited weapon-parity failures')
    return result

if __name__=='__main__':run()
