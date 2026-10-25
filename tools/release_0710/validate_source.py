"""Current official inheritance, tuning and presentation static verification."""
import importlib.util
from common import *

def main():
    guard();out=OUT/'validation';out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
    spec=importlib.util.spec_from_file_location('audit0710',ROOT/'tools/release_072/vendor/extension_audit.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    audit.ROOT=ROOT;audit.GUID=CFG['project_guid'].replace('-','')
    official=audit.refresh(out/'official-extensions.json')
    local=audit.load_local(ROOT)
    errors=audit.Resolver(local,official).audit()
    write(out/'inheritance.json',{'official_blueprints':len(official),'local_blueprints':len(local),'errors':errors})
    if errors:raise ValueError('Inherited extensions failed; see inheritance.json')
    skill=Path.home()/'.codex/skills'
    tuning=run('tuning',[CFG['python'],skill/'modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py',ROOT],out)
    for path in ('scar/vietnam/presentation.scar','scar/vietnam/paddy_wood.scar','scar/winconditions/VietnamMode.scar'):
        p=ROOT/'assets'/path
        if p.exists():run(p.stem+'-scar',[CFG['python'],skill/'aoe4-game-mode-skill/scripts/validate_scar.py',p,'--project-root',ROOT],out)
    write(out/'static-receipt.json',{'source_policy_sha256':sha(out/'source-policy.json'),'inheritance_errors':0,'official_blueprints':len(official),'tuning_passed':True,'scar_static_passed':True,'native_game_tested':False})
    print('STATIC_VALIDATION_PASSED',len(official),len(local))

if __name__=='__main__':main()
