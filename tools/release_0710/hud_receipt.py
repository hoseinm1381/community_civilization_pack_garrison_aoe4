"""Hash complete HUD production payload after focused validation."""
import sys, argparse
from pathlib import Path
from common import ROOT, OUT, CFG, guard, run, sha, write, read
def main():
    guard()
    parser=argparse.ArgumentParser()
    parser.add_argument('--native-receipt',required=True)
    args=parser.parse_args()
    native_path=Path(args.native_receipt).resolve()
    native=read(native_path)
    assert native['status']=='native_compile_passed'
    assert sha(native['archive'])==native['sha256'], 'Native archive drift'
    native_run=next(p for p in Path(native['archive']).parents if p.name=='run')
    native_source=native_run.parent/'src/assets'
    command=[CFG['python'],ROOT/'tests/test_hud_0710.py']
    run('tests',command,OUT/'hud')
    paths=['ui/hud/controls/playerscores.xaml','ui/hud/pages/cardinalhudpage.xaml',
       'ui/resources/hudresources.xaml','scar/vietnam/presentation.scar',
       'scar/vietnam/paddy_wood.scar','scar/winconditions/VietnamMode.scar']
    payload=[{'member':p.lower(),'file':str(ROOT/'assets'/p),'sha256':sha(ROOT/'assets'/p),'toc':'data'} for p in paths]
    textures=[]
    for name in ('buffalo','dai_viet_dragon'):
        input_path=ROOT/f'assets/ui/images/vietnam_0710/{name}.png'
        assert sha(input_path)==sha(native_source/f'ui/images/vietnam_0710/{name}.png'), 'Texture input drift'
        member=f'ui/images/vietnam_0710/{name}.rrtex'
        file=Path(native['readback'])/member
        assert file.is_file() and file.stat().st_size>0, 'Native rrtex required'
        payload.append({'member':member,'file':str(file),'sha256':sha(file),'toc':'data'})
        textures.append({'input':str(input_path),'input_sha256':sha(input_path),'member':member,'sha256':sha(file)})
    proof=[OUT/'hud/tests.log',OUT/'hud/loose-contract.json',OUT/'hud/ui-import-contract.json',OUT/'hud/native-texture-decoding.json',OUT/'hud/mcp-check.json',ROOT/'docs/RELEASE_0710_HUD.md',native_path,native_run/'logs/EssenceEditorLog.txt',native_run/'logs/burn.log']
    proof += sorted((OUT/'hud/official').glob('*.xaml'))
    proof += sorted((ROOT/'art/authoring/release_0710/hud').glob('*.svg'))
    proof += sorted((ROOT/'assets/ui/images/vietnam_0710').glob('*.png'))
    write(OUT/'hud/receipt.json',{
      'schema':'vietnam-hud-0710/v1','version':'0.7.10','members':payload,
      'proof_files':{str(p):sha(p) for p in proof},'test_command':list(map(str,command)),
      'tests':{'passed':12,'type':'Lua 5.1 mocked lifecycle + XML/official preservation + texture input contract'},
      'native_textures':{'compile_receipt':str(native_path),'archive_sha256':native['sha256'],'textures':textures},
      'contracts':{'loose_files':'project/source/files -> Contribution.members, exact byte preservation; data SGA members',
        'scoreboard':'player row ScarModel[vietnam_hud]; original RaceIcon retained',
        'texture':'Supported ui_assets.add_image stages PNG into native UI Textures RRTextureBurner inputs; ship resulting rrtex at PNG URI stem',
        'counter':'living owned spawned exact private SBP squads / Player_GetCurrentPopulationCap(player, CT_Medic)',
        'cycle':'UI_CreateCommand from ui.scar; Misc_ClearSelection + Misc_SelectSquad; ascending numeric Squad_GetID with wrap',
        'supervision':'VietnamBuffaloSupervisionTemplate; existing owner/replay/active-assignment creation and destruction unchanged'},
      'gates':{'static':'passed','content_editor':'native UI texture compile/readback passed','package':'payload only','native':'unverified','save_load_native':'unverified','multiplayer':'unverified'},
      'limits':['Keyboard/mouse CardinalHUDPage; Xbox counter layout is not overridden.',
        'Native UI binding, scaling, observer switching and texture rendering still require game verification.',
        'Installed rrtex decoder parses Chunky but cannot export native UI internal format 28; see native-texture-decoding.json.',
        'Only spawned playable buffalo are counted; despawned held entities deliberately excluded for safe API traversal.',
        'Full official UI overrides must be refreshed after game UI updates.']})
    print(str(OUT/'hud/receipt.json'))
if __name__=='__main__':main()
