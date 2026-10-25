"""Strict 051 source allowlist, inherited failures, and protected-input checks."""
import io,json,subprocess,sys
from common import *
from freeze import verify,files
def source_policy():
    guarded();frozen=read(OUT/'baseline/freeze.json')['assets'];current=files(ROOT/'assets')
    expected=read(OUT/'traps/source-changes.json')['changed']
    assert not(set(frozen)-set(current))
    changes={p:r['sha256'] for p,r in current.items() if p not in frozen or r!=frozen[p]}
    assert changes==expected,('Unexpected source changes',changes,expected)
    for name in ('vn_building_bambo_outpost_chi','vn_building_defense_outpost_bambo_chi'):
        p='attrib/instances/ebps/vietnam/'+name+'.xml';assert current[p]==frozen[p]
    result={'status':'passed','changed':changes,'untouched_assets_byte_identical':True,'normal_edition':'unchanged since051freeze'}
    write(OUT/'source-policy.json',result);return result
def run(label):
    verify();source=source_policy()
    import landmark_visibility as landmark
    for row in read(OUT/'landmarks/receipt.json')['payloads']:
        frozen=OUT/'landmarks/baseline'/row['member']
        assert sha(row['file'])==row['sha256']
        landmark.regression(frozen.read_bytes(),Path(row['file']).read_bytes())
    import monastery_verify
    monastery_verify.main()
    body="""import io,json,sys,unittest
s=io.StringIO();r=unittest.TextTestRunner(stream=s,verbosity=1).run(unittest.defaultTestLoader.discover('tests'))
print(s.getvalue(),file=sys.stderr)
print('RESULT='+json.dumps({'tests':r.testsRun,'failures':[t.id() for t,d in r.failures],'errors':[t.id() for t,d in r.errors],'skipped':[t.id() for t,d in r.skipped]}))
"""
    p=subprocess.run([CONFIG['python'],'-B','-c',body],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    log=OUT/'logs'/('tests051-'+label+'.log');assert not log.exists();log.write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    tests=json.loads(next(line[7:] for line in p.stdout.splitlines() if line.startswith('RESULT=')))
    prior=read(PRIOR/'release-checks.json')['tests']
    assert tests['tests']>=prior['tests']+5
    assert set(tests['failures'])==set(prior['failures']) and len(tests['failures'])==2 and not tests['errors'] and not tests['skipped'],tests
    # The shared Lua fixture gains only a native API stub, no changed assertions.
    old=(OUT/'baseline/test_runtime_repairs.py').read_text()
    expected=old.replace('function Entity_GetBlueprint(e) return e.bp end','function Entity_GetBlueprint(e) return e.bp end\nfunction Entity_ConvertBlueprint(e,bp) e.bp=bp;e.conversions=(e.conversions or 0)+1 end')
    assert (ROOT/'tests/test_runtime_repairs.py').read_text()==expected
    static=run_logged('static051-'+label,[CONFIG['python'],'-B',Path.home()/'.codex/skills/modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py',ROOT])
    scar=run_logged('scar051-'+label,[CONFIG['python'],'-B',Path.home()/'.codex/skills/aoe4-game-mode-skill/scripts/validate_scar.py',ROOT/'assets/scar/vietnam/traps.scar','--project-root',ROOT])
    result={'status':'passed_with_two_inherited_weapon_parity_failures','tests':tests,'tests_log':str(log),'static_log':static,'scar_log':scar,'source':source,'native_match':'pending'}
    write(OUT/'checks.json',result);print('CHECKS051_PASSED',tests['tests']);return result
if __name__=='__main__':run(sys.argv[1])
