"""Fresh official inheritance and installed validators before native assembly."""
import xml.etree.ElementTree as E,re
from common import *

def main():
    guard();out=OUT/'validation';out.mkdir(parents=True,exist_ok=True)
    run('source-policy',[CFG['blender_python'],'-B',ROOT/'tools/release_0712/source_policy.py'],out)
    run('tests',[CFG['python'],'-B',ROOT/'tests/test_release_0712.py'],out)
    test_count=int(re.search(r'Ran (\d+) tests', (out/'tests.log').read_text()).group(1))
    sys.path.insert(0,str(ROOT/'tools/release_072/vendor'));import extension_audit as a
    a.ROOT=ROOT;a.GUID=CFG['project_guid'].replace('-','')
    official=a.refresh(out/'official-extensions.json');local=a.load_local(ROOT)
    errors=a.Resolver(local,official).audit();write(out/'inheritance.json',{'errors':errors,'local':len(local),'official':len(official)})
    assert not errors,errors
    skill=Path.home()/'.codex/skills'
    run('tuning',[CFG['python'],skill/'modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py',ROOT],out)
    for stem in ('presentation','tunnels','tunnel_buildings'):
        run(stem,[CFG['python'],skill/'aoe4-game-mode-skill/scripts/validate_scar.py',ROOT/f'assets/scar/vietnam/{stem}.scar','--project-root',ROOT],out)
    for name in ('aoe4-game-mode-skill','modify-aoe4-tuning-packs'):
        run(name+'-self-test',[CFG['python'],skill/name/'scripts/self_test.py'],out)
    for name in read(OUT/'source-policy.json')['changed']:
        if name.endswith(('.xml','.xaml')):E.parse(ROOT/name)
    write(out/'receipt.json',{'passed':True,'source_policy_sha256':sha(OUT/'source-policy.json'),
        'tests_passed':test_count,'tuning_errors':0,'scar_errors':0,'inheritance_errors':0,'native_game_tested':False})
    print('STATIC_VALIDATION_PASSED')

if __name__=='__main__':main()
