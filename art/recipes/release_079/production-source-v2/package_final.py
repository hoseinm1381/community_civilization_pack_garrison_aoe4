"""Final art package: allowlisted media only; preserve every other byte and mount."""
import zipfile
from common import *
from rig_contract import read_contract,validate_contract
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check

def main(label):
    guard();baseline=OUT/'baseline';archive=baseline/'community_civilization_pack.sga'
    assert sha(archive)==EXPECTED;check(ROOT,archive)
    before=read(baseline/'verification.json');cook=OUT/'cooks'/label
    receipt=read(cook/'receipt.json');proof=read(cook/'partition-proof.json');decoded=read(cook/'decoded-proof.json')
    assert sha(receipt['archive'])==receipt['archive_sha256']
    expected_families={'buffalo', *{f'{f}{a}' for f in ('skirmisher','javelin','projectile') for a in (2,3,4)}}
    assert {r['family'] for r in receipt['records']}==expected_families
    payload={}
    for row in receipt['records']:
        family=row['family'];export=read(OUT/'art'/family/row['revision']/'export.json')
        assert sha(export['source'])==export['source_sha256']
        assert all(sha(Path(export['export'])/n)==h for n,h in export['files'].items())
        assert sha(OUT/'art'/family/row['revision']/'export.json')==row['export_receipt_sha256']
        assert not decoded[family]['blockers']
        if export['donor_contract']: assert proof[family]['exact_donor_contract']
        assert sha(decoded[family]['manifest'])==decoded[family]['sha256']
        root=cook/'readback'/row['member_root']
        if export['donor_contract']: validate_contract(read_contract((root/'model.rgm').read_bytes()),export['donor_contract'])
        for p in root.iterdir():
            if not p.is_file() or p.suffix=='.rgo': continue
            member=p.relative_to(cook/'readback').as_posix()
            assert member in before['member_sha256'], member
            if family.startswith('javelin') and p.suffix=='.rgm':
                # Preserve the existing, qualified native throw/hide selectors.
                from garrison_shared import relic_chunky as rc
                old=rc.parse((BASE/'readback'/member).read_bytes())
                doc=rc.parse(p.read_bytes())
                prior=next(c for c in rc.walk(old.roots) if c.tag==b'MSBP')
                target=next(c for c in rc.walk(doc.roots) if c.tag==b'MSBP')
                raw=rc.rebuild(doc,lambda c:prior.payload if c.offset==target.offset else None)
                patched=cook/'selector-payload'/family/p.name
                patched.parent.mkdir(parents=True,exist_ok=True);patched.write_bytes(raw);p=patched
            payload[member]={'file':str(p),'sha256':sha(p)}
    ministry=read(OUT/'payloads/ministry-v1/receipt.json')
    for row in ministry['members']:
        assert sha(row['file'])==row['sha256']
        assert row['member'].startswith('art/') and row['member'] not in payload
        payload[row['member']]={'file':row['file'],'sha256':row['sha256']}
    dest=OUT/'delivery/final-v1'
    if dest.exists():raise FileExistsError('Immutable pilot output exists')
    dest.mkdir(parents=True)
    mapping=dest/'members.txt';mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(payload.items()))+'\n')
    final=dest/'community_civilization_pack.sga'
    run('assemble',[CFG['archive_tool'],'set-members',archive,mapping,final,'--alias','data'],dest/'logs')
    check(ROOT,final)
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',final,'--verify'],dest/'logs'))
    mounts={m['path']:m['toc'] for m in listing['members']}
    assert {m:mounts[m] for m in before['mounts']}==before['mounts']
    assert set(mounts)-set(before['mounts'])==set(payload)-set(before['mounts'])
    assert all(mounts[m]=='data' for m in payload)
    expected=dict(before['member_sha256']);expected.update({k:v['sha256'] for k,v in payload.items()})
    back=dest/'readback';run('readback',[CFG['archive_tool'],'extract',final,back,'--filter',''],dest/'logs')
    actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()}
    assert actual==expected
    for name in ('source-hashes.json','normal-hashes.json'):
        assert all(sha(p)==h for p,h in read(baseline/name).items())
    version='0.7.9'
    manifest=read(baseline/'garrison.json')
    manifest['members'][0]['sha256']=sha(final)
    manifest['details'].update(version=version,summary='Rebuilt animated Vietnamese skirmishers and water buffalo.',description='New rigged skirmisher models for Ages II-IV, new water buffalo, corrected javelin orientation and three Ministry decorations. Native donor motions and gameplay preserved.',changelog='New unit geometry and 2K textures; native skeletal LOD contracts; corrected throwing and projectile orientation. Final artwork requires in-game acceptance.')
    write(dest/'garrison.json',manifest)
    instructions="""Community Civilization Pack 0.7.9
Credits: hosein81 and chilly5
Import manually in Garrison and start a fresh Vietnam match.
New art: skirmishers II-IV, water buffalo, javelins/projectiles, three Ministry buffalo.
The earlier pilot's animations passed user testing. Final art is not yet tested in-game.
Check idle, walk, turn, repeated throwing, weapon direction/grip, torch and death.
Check regular/tower training, age upgrades, two player colors and near/far LODs.
Check buffalo construction and Paddy Work/Leave, income, and Ministry lifecycle.
Save/load, multiplayer and performance remain unverified.
No installation, publication or cleanup was performed. Rollback: preserved 0.7.8 ZIP.
"""
    (dest/'START-HERE.txt').write_text(instructions,encoding='utf-8')
    package=dest/f'community_civilization_pack-{version}.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in (dest/'garrison.json',final,dest/'START-HERE.txt'):z.write(p,p.name)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None and len([n for n in z.namelist() if Path(n).name=='garrison.json'])==1
        assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
        assert json.loads(z.read('garrison.json'))['details']['version']==version
    changed=[m for m in expected if m in before['member_sha256'] and expected[m]!=before['member_sha256'][m]]
    write(dest/'verification.json',{'sga_sha256':sha(final),'member_sha256':actual,'mounts':mounts,'changed':changed,'added':sorted(set(expected)-set(before['member_sha256'])),'baseline_sha256':EXPECTED,'all_untouched_members_exact':True,'source_and_normal_unchanged':True,'native_acceptance':False})
    write(dest/'delivery-proof.json',{'zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),'version':version,'verified':True,'installed':False,'final_079_art':True,'changed_members':len(changed),'total_members':len(actual)})
    assert sha(BASE/'community_civilization_pack.sga')==EXPECTED
    print('FINAL_ART_PACKAGE_VERIFIED',str(package),len(changed))

if __name__=='__main__':main(sys.argv[1])
