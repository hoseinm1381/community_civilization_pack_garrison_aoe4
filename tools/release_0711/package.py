"""Assemble six presentation members over frozen 0710; verify every byte/mount."""
import argparse, shutil, zipfile
from common import *
from patch import CHANGED
sys.path.insert(0,str(ROOT/'tools/release_0710'))
from package_policy import merge_payloads,verify_inventory,verify_static_source
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check

def preserve():
    for name in ('normal-hashes.json','protected-0710-inputs.json'):
        assert all(sha(p)==h for p,h in read(OUT/'baseline'/name).items()),name
    proof=read(OUT/'baseline/delivery-proof.json')
    assert sha(BASE/'community_civilization_pack.sga')==EXPECTED
    assert sha(proof['zip'])==proof['zip_sha256']

def main(label,native_label):
    guard();preserve();frozen=OUT/'baseline';source=read(OUT/'source-policy.json')
    assert source['passed'] and all(sha(ROOT/p)==h for p,h in source['current_hashes'].items())
    static=read(OUT/'validation/receipt.json');verify_static_source(static,sha(OUT/'source-policy.json'))
    assert static['passed'] and static['tests_passed']==13
    native_path=OUT/f'native/{native_label}/receipt.json';native=read(native_path)
    assert native['status']=='native_compile_passed' and sha(native['archive'])==native['sha256']
    assert native['source_policy_sha256']==sha(OUT/'source-policy.json')
    native_inputs=read(native_path.parent/'inputs.json')
    baseline=read(frozen/'verification.json')
    inventory=read(OUT/'badge-inventory.json')
    for row in inventory['rows']:
        assert 'attrib/'+row['key'].replace('\\','/')+'.rgd' in baseline['member_sha256']
    # Read the actual packaged native squad requirement as well as the XML source.
    sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import rgd
    capmember='attrib/sbps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.rgd'
    doc=rgd.read((BASE/'readback'/capmember).read_bytes())
    caps=[n.value for _,n in rgd.flatten(doc.nodes) if n.key=='max_squad_cap']
    assert caps==[read(OUT/'cap-source.json')['default']]*2,caps
    names=sorted(set(CHANGED)|{'assets/scar/vietnam/presentation_data.scar','assets/scar/vietnam/presentation_badges.scar'})
    rows=[]
    for name in names:
        member=name.removeprefix('assets/').lower();p=ROOT/name
        assert native_inputs[name]==sha(p),('Native source drift',name)
        # Native burner copies SCAR; XAML uses the qualified Garrison loose-UI
        # route and is checked by XML parsers and final archive readback.
        if member.startswith('scar/'):
            assert sha(Path(native['readback'])/member)==sha(p),('Native SCAR readback mismatch',member)
        rows.append({'member':member,'file':str(p),'sha256':sha(p),'toc':'data'})
    payload=merge_payloads([rows])
    proofs=[OUT/'source-policy.json',OUT/'cap-source.json',OUT/'badge-inventory.json',OUT/'mcp-check.json',OUT/'validation/receipt.json',OUT/'validation/official-contracts.json',OUT/'validation/dotnet-xml.json',native_path]
    rebuild=[p for p in (ROOT/'tools/release_0711').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    rebuild += [ROOT/'tests/test_hud_0711.py',ROOT/'tools/build_release_0711.ps1']
    RECIPES.mkdir(parents=True,exist_ok=True)
    write(RECIPES/'integration.json',{'version':'0.7.11','baseline_sha256':EXPECTED,'members':rows,
        'proof_files':{str(p):sha(p) for p in proofs},'rebuild_inputs':{str(p):sha(p) for p in rebuild},
        'native_receipt':str(native_path),'native_game_tested':False})
    dest=OUT/'delivery'/label;dest.mkdir(parents=True,exist_ok=False)
    check(ROOT,frozen/'community_civilization_pack.sga')
    mapping=dest/'members.txt';mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(payload.items()))+'\n',encoding='utf-8')
    final=dest/'community_civilization_pack.sga'
    run('assemble',[CFG['archive_tool'],'set-members',frozen/'community_civilization_pack.sga',mapping,final,'--alias','data'],dest/'logs')
    check(ROOT,final)
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',final,'--verify'],dest/'logs'))
    mounts={m['path']:m['toc'] for m in listing['members']}
    back=dest/'readback';run('readback',[CFG['archive_tool'],'extract',final,back,'--filter',''],dest/'logs')
    actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()}
    verify_inventory(baseline['member_sha256'],baseline['mounts'],actual,mounts,payload)
    preserve()
    manifest=read(frozen/'garrison.json');manifest['members'][0]['sha256']=sha(final)
    manifest['details'].update(version='0.7.11',updated='2026-10-24',
        summary='Quiet farm-work markers, corrected buffalo cap and Vietnamese badges.',
        description='Small steady farm-work icon visible only on camera. Buffalo counter displays the native squad limit as whole numbers. Vietnamese units and buildings use the Dai Viet dragon civilization badge.',
        changelog='Fix tutorial-arrow/off-screen supervision notifier and incorrect medic-pool cap display. Apply private Vietnamese civilization badges. Native match acceptance pending.')
    write(dest/'garrison.json',manifest)
    (dest/'START-HERE.txt').write_text('''Community Civilization Pack Garrison 0.7.11
Credits: hosein81 and chilly5
Import this ZIP through Garrison, enable the mod and select the required tuning pack/game mode. Start a fresh match.
Changes: quiet 14px farm-work icon, no tutorial arrow or off-screen locator; integer buffalo count/current native squad limit; Dai Viet dragon badges on private Vietnamese units/buildings.
The count/click cycling and all gameplay/art remain preserved. China keeps its native badges. No installation, publication or cleanup was performed.
Native cook and package verification passed; native visual rendering, save/load and multiplayer require separate testing. Verify repeated camera pans, Work/Leave, 0/15 and 8/15 counter displays, unit/building tooltips and mixed China/Vietnam players.
Retain 0.7.10 as rollback. Detailed source/verification receipts remain under release_0711 in the development workspace.
''',encoding='utf-8')
    package=dest/'community_civilization_pack-0.7.11.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in (dest/'garrison.json',final,dest/'START-HERE.txt'):z.write(p,p.name)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'garrison.json','community_civilization_pack.sga','START-HERE.txt'}
        assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.11'
    changed=sorted(p for p in actual if p in baseline['member_sha256'] and actual[p]!=baseline['member_sha256'][p])
    added=sorted(set(actual)-set(baseline['member_sha256']));assert len(changed)==4 and len(added)==2
    write(dest/'verification.json',{'sga_sha256':sha(final),'member_sha256':actual,'mounts':mounts,
        'changed':changed,'added':added,'all_untouched_members_exact':True,'all_tuning_and_art_preserved':True,
        'normal_and_0710_preserved':True,'baseline_sha256':EXPECTED,'integration_sha256':sha(RECIPES/'integration.json'),
        'native_game_tested':False})
    write(dest/'delivery-proof.json',{'version':'0.7.11','zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),
        'verified':True,'changed_members':len(changed),'added_members':len(added),'total_members':len(actual),
        'badge_blueprints':len(inventory['rows']),'buffalo_cap':caps[0],'installed':False,'native_game_tested':False})
    print('PACKAGE_VERIFIED',package,len(changed),len(added))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',default='final-v1');p.add_argument('--native-label',default='v1');a=p.parse_args();main(a.label,a.native_label)
