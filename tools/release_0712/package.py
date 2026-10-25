"""Guarded 0712 assembly over exact delivered 0711, with every-member readback."""
import argparse,shutil,zipfile
from common import *
from attributes import assemble
sys.path.insert(0,str(ROOT/'tools/release_0710'))
from package_policy import merge_payloads,verify_inventory,verify_static_source
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check

def preserve():
    for name in ('normal-hashes.json','protected-0711-inputs.json'):
        assert all(sha(p)==h for p,h in read(OUT/'baseline'/name).items()),name
    old=read(OUT/'baseline/delivery-proof.json')
    assert sha(BASE/'community_civilization_pack.sga')==EXPECTED
    assert sha(old['zip'])==old['zip_sha256']

def main(label,native_label):
    guard();preserve();source=read(OUT/'source-policy.json')
    assert source['passed'] and all(sha(ROOT/p)==h for p,h in source['current_hashes'].items())
    static=read(OUT/'validation/receipt.json');verify_static_source(static,sha(OUT/'source-policy.json'))
    assert static['passed'] and static['tests_passed']>=17
    native_path=OUT/f'native/{native_label}/receipt.json';native=read(native_path)
    assert native['source_policy_sha256']==sha(OUT/'source-policy.json')
    inputs=read(native_path.parent/'inputs.json')
    assert all(inputs[p]==sha(ROOT/p) for p in source['changed'])
    rows=assemble(native_label)
    for name in source['changed']:
        if name.startswith('assets/attrib/'):continue
        member=name.removeprefix('assets/').lower();p=ROOT/name
        if member.startswith('scar/'):
            assert sha(Path(native['readback'])/member)==sha(p),('Native SCAR drift',member)
        rows.append({'member':member,'file':str(p),'sha256':sha(p),'toc':'data'})
    payload=merge_payloads([rows]);assert len(payload)==44
    xml=read(OUT/'validation/dotnet-xml.json');assert xml['passed'] and xml['source_policy_sha256']==sha(OUT/'source-policy.json')
    proofs=[OUT/'source-policy.json',OUT/'patch-receipt.json',OUT/'range-inventory.json',OUT/'attribute-proof.json',
        OUT/'validation/receipt.json',OUT/'validation/dotnet-xml.json',OUT/'validation/tests.log',OUT/'validation/inheritance.json',
        OUT/'mcp-check.json',OUT/'mcp-resolution.json',OUT/'native-before-tunnel.log',OUT/'official/donors.json',native_path]
    for p in proofs:assert p.exists(),p
    rebuild=[p for p in (ROOT/'tools/release_0712').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    rebuild += [ROOT/'tests/test_release_0712.py',ROOT/'tools/build_release_0712.ps1']
    RECIPES.mkdir(parents=True,exist_ok=True)
    write(RECIPES/'integration.json',{'version':'0.7.12','baseline_sha256':EXPECTED,'members':rows,
        'proof_files':{str(p):sha(p) for p in proofs},'rebuild_inputs':{str(p):sha(p) for p in rebuild},
        'native_label':native_label,'actual_influence_increase_metres':2,'native_game_tested':False})
    dest=OUT/'delivery'/label;dest.mkdir(parents=True,exist_ok=False)
    archive=OUT/'baseline/community_civilization_pack.sga';check(ROOT,archive)
    for toc in ('attrib','data'):
        selected={k:v for k,v in payload.items() if v['toc']==toc}
        mapping=dest/(toc+'-members.txt');mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(selected.items()))+'\n',encoding='utf-8')
        target=dest/(toc+'-assembly.sga')
        run('assemble-'+toc,[CFG['archive_tool'],'set-members',archive,mapping,target,'--alias',toc],dest/'logs');archive=target
    final=dest/'community_civilization_pack.sga';shutil.copyfile(archive,final);check(ROOT,final)
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',final,'--verify'],dest/'logs'))
    mounts={m['path']:m['toc'] for m in listing['members']}
    back=dest/'readback';run('readback',[CFG['archive_tool'],'extract',final,back,'--filter',''],dest/'logs')
    actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()}
    before=read(OUT/'baseline/verification.json');verify_inventory(before['member_sha256'],before['mounts'],actual,mounts,payload)
    preserve()
    manifest=read(OUT/'baseline/garrison.json');manifest['members'][0]['sha256']=sha(final)
    manifest['details'].update(version='0.7.12',updated='2026-10-24',
        summary='Skirmisher timing, clickable buffalo counter, visible work icons and expanded influence.',
        description='Skirmisher wind-up +0.25s and reload -0.25s. Buffalo counter selects and focuses the next owned buffalo. Larger steady work icons. Vietnam influence and tunnel network reach +2m. Nearby ground clicks select eligible tunnel exits within 8m of building edges.',
        changelog='Correct counter click availability and player-handle lookup. Enlarge work marker to 48px. Apply authorized actual/display influence extension. Skip invalid tunnel neighbours when choosing the nearest eligible exit. Native match acceptance pending.')
    write(dest/'garrison.json',manifest)
    (dest/'START-HERE.txt').write_text('''Community Civilization Pack Garrison 0.7.12
Credits: hosein81 and chilly5
Import through Garrison, enable the mod and select the required tuning pack and Vietnam game mode. Start a fresh match.
Changes: skirmisher wind-up 0.50s / reload 1.125s; click the buffalo count to select and focus the next living owned buffalo; steady 48px work marker, hidden off camera; Vietnam actual influence/display and scripted network reach increased 2m; tunnel ground clicks accepted within 8m of a valid owned completed connected building's footprint edge.
All other gameplay/art, normal edition and exact 0.7.11 rollback are preserved. No installation, publication or cleanup was performed.
Native build/readback and package proof are separate from in-game UI/transport validation. Check mixed China/Vietnam, all skirmisher tiers, repeated counter clicks, working buffalo, camera pans, influence/placement, nearby exit clicks, save/load and multiplayer.
''',encoding='utf-8')
    package=dest/'community_civilization_pack-0.7.12.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in (dest/'garrison.json',final,dest/'START-HERE.txt'):z.write(p,p.name)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'garrison.json','community_civilization_pack.sga','START-HERE.txt'}
        assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.12'
    changed=sorted(p for p in actual if p in before['member_sha256'] and actual[p]!=before['member_sha256'][p])
    added=sorted(set(actual)-set(before['member_sha256']));assert len(changed)==44 and not added
    write(dest/'verification.json',{'sga_sha256':sha(final),'member_sha256':actual,'mounts':mounts,'changed':changed,'added':added,
        'all_untouched_members_exact':True,'normal_and_prior_inputs_preserved':True,'baseline_sha256':EXPECTED,
        'integration_sha256':sha(RECIPES/'integration.json'),'native_game_tested':False})
    write(dest/'delivery-proof.json',{'version':'0.7.12','zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),
        'verified':True,'changed_members':len(changed),'added_members':0,'total_members':len(actual),
        'actual_influence_increase_metres':2,'installed':False,'native_game_tested':False})
    print('PACKAGE_VERIFIED',package,len(changed))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',default='final-v1');p.add_argument('--native-label',default='v2');a=p.parse_args();main(a.label,a.native_label)
