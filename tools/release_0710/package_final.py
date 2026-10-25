"""Assemble reviewed 0710 payloads over exact accepted 079; preserve mounts."""
import argparse
import shutil
import zipfile
from common import *
from package_policy import merge_payloads, verify_inventory, verify_static_source
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check

def preserve():
    baseline=OUT/'baseline'
    for key in ('normal-hashes.json','protected-079-inputs.json'):
        for p,h in read(baseline/key).items():
            if sha(p)!=h:raise ValueError('Protected input changed: '+p)
    if sha(BASE/'community_civilization_pack.sga')!=EXPECTED:raise ValueError('Accepted baseline changed')
    prior=read(baseline/'delivery-proof.json')
    if sha(prior['zip'])!=prior['zip_sha256']:raise ValueError('Accepted rollback ZIP changed')

def main(label):
    guard();preserve();baseline=OUT/'baseline';archive=baseline/'community_civilization_pack.sga'
    assert sha(archive)==EXPECTED;check(ROOT,archive)
    integration=read(RECIPES/'integration.json')
    assert integration['version']=='0.7.10' and integration['reviewed'] is True
    groups=[]
    for item in integration['payload_receipts']:
        assert sha(item['file'])==item['sha256']
        receipt=read(item['file'])
        for p,h in receipt.get('proof_files',{}).items():assert sha(p)==h,('Stale proof',p)
        groups.append(receipt['members'])
    for p,h in integration['rebuild_input_hashes'].items():assert sha(p)==h,('Changed reviewed rebuild input',p)
    payload=merge_payloads(groups)
    before=read(baseline/'verification.json')
    source=read(OUT/'validation/source-policy.json')
    assert source['passed'] is True
    assert all(sha(ROOT/k)==v for k,v in source['current_hashes'].items())
    static=read(OUT/'validation/static-receipt.json')
    verify_static_source(static,sha(OUT/'validation/source-policy.json'))
    assert static['tuning_passed'] and static['scar_static_passed'] and static['inheritance_errors']==0
    dest=OUT/'delivery'/label;dest.mkdir(parents=True,exist_ok=False)
    current=archive
    for toc in ('attrib','data'):
        selected={k:v for k,v in payload.items() if v['toc']==toc}
        if not selected:continue
        mapping=dest/(toc+'-members.txt')
        mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(selected.items()))+'\n',encoding='utf-8')
        target=dest/(toc+'-assembly.sga')
        run('assemble-'+toc,[CFG['archive_tool'],'set-members',current,mapping,target,'--alias',toc],dest/'logs')
        current=target
    final=dest/'community_civilization_pack.sga';shutil.copyfile(current,final)
    check(ROOT,final)
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',final,'--verify'],dest/'logs'))
    mounts={m['path']:m['toc'] for m in listing['members']}
    back=dest/'readback'
    run('readback',[CFG['archive_tool'],'extract',final,back,'--filter',''],dest/'logs')
    actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()}
    verify_inventory(before['member_sha256'],before['mounts'],actual,mounts,payload)
    preserve()
    manifest=read(baseline/'garrison.json');manifest['members'][0]['sha256']=sha(final)
    manifest['details'].update(version='0.7.10',updated='2026-10-24',
        summary='Buffalo fur, fortified Hideout and Vietnam HUD improvements.',
        description='Sparse buffalo fur, reinforced timber fortified Hideout, quiet farm-work marker, Dai Viet scoreboard emblem and buffalo counter with click cycling. Gameplay preserved.',
        changelog='New visual assets and Vietnam-only HUD. Influence display resize omitted: no independent visual range contract qualified. Native acceptance pending.')
    write(dest/'garrison.json',manifest)
    instructions='''Community Civilization Pack Garrison 0.7.10
Credits: hosein81 and chilly5
Manual import: import this ZIP in Garrison, enable it and select the required tuning pack/game mode in the lobby. Start a fresh match.
Changes: sparse buffalo fur including Ministry decorations; reinforced fortified Hideout; quiet farm supervision icon; gold Dai Viet dragon scoreboard flag; buffalo total/current-cap counter. Click cycles living owned buffalo without issuing orders.
Omitted by approved fallback: +/-2m influence display adjustment. Actual influence and gameplay remain unchanged.
Cook, readback and package verification are not native gameplay acceptance. Test mixed China/Vietnam players, HUD scales, cycle selection, Work/Leave, model motion and LOD, building upgrades/construction/destruction/repair. Save/load and multiplayer remain separate unverified gates.
Rollback: retain the accepted 0.7.9 ZIP. No installation, publication or cleanup was performed.
'''
    (dest/'START-HERE.txt').write_text(instructions,encoding='utf-8')
    package=dest/'community_civilization_pack-0.7.10.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in (dest/'garrison.json',final,dest/'START-HERE.txt'):z.write(p,p.name)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'garrison.json',final.name,'START-HERE.txt'}
        assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.10'
    changed=sorted(k for k in actual if k in before['member_sha256'] and actual[k]!=before['member_sha256'][k])
    added=sorted(set(actual)-set(before['member_sha256']))
    write(dest/'verification.json',{'baseline_sha256':EXPECTED,'sga_sha256':sha(final),'member_sha256':actual,'mounts':mounts,
        'changed':changed,'added':added,'all_untouched_members_exact':True,'normal_and_079_inputs_unchanged':True,
        'source_policy':sha(OUT/'validation/source-policy.json'),'integration':sha(RECIPES/'integration.json'),
        'influence_resize':'omitted','native_acceptance':False})
    write(dest/'delivery-proof.json',{'zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),'version':'0.7.10',
        'verified':True,'installed':False,'changed_members':len(changed),'added_members':len(added),'total_members':len(actual),
        'influence_resize':'omitted','native_game_tested':False})
    print('PACKAGE_VERIFIED',package,len(changed),len(added))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='final-v1');a=parser.parse_args();main(a.label)
