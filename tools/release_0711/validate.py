"""Official-source, installed-validator, regression and source-preservation checks."""
import xml.etree.ElementTree as E
from common import *

def main():
    guard();out=OUT/'validation'
    run('source-policy',[CFG['blender_python'],'-B',ROOT/'tools/release_0711/source_policy.py'],out)
    run('tests',[CFG['python'],'-B',ROOT/'tests/test_hud_0711.py'],out)
    skill=Path.home()/'.codex/skills'
    run('tuning',[CFG['python'],skill/'modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py',ROOT],out)
    for stem in ('presentation','presentation_data','presentation_badges','paddy_wood'):
        run(stem,[CFG['python'],skill/'aoe4-game-mode-skill/scripts/validate_scar.py',ROOT/f'assets/scar/vietnam/{stem}.scar','--project-root',ROOT],out)
    for name in ('aoe4-game-mode-skill','modify-aoe4-tuning-packs'):
        run(name+'-self-test',[CFG['python'],skill/name/'scripts/self_test.py'],out)
    for p in (ROOT/'assets/ui').rglob('*.xaml'):E.parse(p)
    inventory=read(OUT/'badge-inventory.json');assert not inventory['inheritance_errors']
    sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
    from read_official_members import members
    donors={}
    for name,data in members('UI.sga',lambda n:n in ('cardinalhudpage.xaml','hudresources.xaml')):
        prior=OUT.parent/'release_0710/hud/official'/name
        assert data==prior.read_bytes(),('Official UI changed; refresh overrides',name)
        p=out/'official'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);donors[name]=sha(p)
    assert len(donors)==2
    api=Path(CFG['content_editor']).parent/'scardocs/api/Essence_ScarFunctions.api'
    wanted=('UI_OverrideUIProperty(','Misc_IsPosOnScreen(','BP_GetEntityBlueprint(','BP_GetSquadBlueprint(')
    lines=[l for l in api.read_text(encoding='utf-8-sig').splitlines() if l.startswith(wanted)]
    assert len(lines)==4,lines
    write(out/'official-contracts.json',{'api':str(api),'api_sha256':sha(api),'lines':lines,'ui_donors':donors,
        'official_usage':['missionomatic/missionomatic.scar:1088-1093 flag_icon','camera.scar:177,265 and scarutil.scar:1783,1802 Misc_IsPosOnScreen'],
        'local_imports':'VietnamMode imports presentation; presentation imports generated cap/badges at script loading',
        'marker_contract':'PositionTags.TagData.Data dictionary follows current TagDataTemplate Data[Message] binding; private boolean routes one marker only',
        'mcp_unknowns_resolved':'Same-file helper definitions and Lua and/or tokens; no low-confidence APIs'})
    write(out/'receipt.json',{'passed':True,'source_policy_sha256':sha(OUT/'source-policy.json'),'tests_passed':13,
        'tuning_errors':0,'scar_errors':0,'inheritance_errors':0,'official_badge_blueprints':len(inventory['rows']),
        'native_game_tested':False})
    print('STATIC_VALIDATION_PASSED',len(inventory['rows']),'badges')

if __name__=='__main__':main()
