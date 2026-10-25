"""Immutable diagnostic package: only four existing RGM/RRGEOM pairs may change."""
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
    expected_families={'buffalo','skirmisher2','skirmisher3','skirmisher4'}
    assert {r['family'] for r in receipt['records']}==expected_families
    payload={}
    for row in receipt['records']:
        family=row['family'];export=read(OUT/'art'/family/row['revision']/'export.json')
        assert sha(export['source'])==export['source_sha256']
        assert all(sha(Path(export['export'])/n)==h for n,h in export['files'].items())
        assert sha(OUT/'art'/family/row['revision']/'export.json')==row['export_receipt_sha256']
        assert proof[family]['exact_donor_contract'] and not decoded[family]['blockers']
        assert sha(decoded[family]['manifest'])==decoded[family]['sha256']
        root=cook/'readback'/row['member_root']
        validate_contract(read_contract((root/'model.rgm').read_bytes()),export['donor_contract'])
        # Material and texture dependencies must remain byte-identical. RGO is
        # intentionally retained from baseline, not replaced by the scaffold.
        for p in root.iterdir():
            if not p.is_file():continue
            member=p.relative_to(cook/'readback').as_posix()
            if p.suffix in ('.rgm','.rrgeom'):
                assert member in before['member_sha256'];payload[member]={'file':str(p),'sha256':sha(p)}
            elif p.suffix!='.rgo':
                assert sha(p)==before['member_sha256'].get(member),(member,'unexpected media drift')
    assert len(payload)==8
    dest=OUT/'delivery/motion-pilot-1'
    if dest.exists():raise FileExistsError('Immutable pilot output exists')
    dest.mkdir(parents=True)
    mapping=dest/'members.txt';mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(payload.items()))+'\n')
    final=dest/'community_civilization_pack.sga'
    run('assemble',[CFG['archive_tool'],'set-members',archive,mapping,final,'--alias','data'],dest/'logs')
    check(ROOT,final)
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',final,'--verify'],dest/'logs'))
    mounts={m['path']:m['toc'] for m in listing['members']}
    assert mounts==before['mounts']
    expected=dict(before['member_sha256']);expected.update({k:v['sha256'] for k,v in payload.items()})
    back=dest/'readback';run('readback',[CFG['archive_tool'],'extract',final,back,'--filter',''],dest/'logs')
    actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()}
    assert actual==expected
    for name in ('source-hashes.json','normal-hashes.json'):
        assert all(sha(p)==h for p,h in read(baseline/name).items())
    version='0.7.9-pilot.1'
    manifest=read(baseline/'garrison.json')
    manifest['members'][0]['sha256']=sha(final)
    manifest['details'].update(version=version,summary='Animation qualification pilot; existing artwork retained.',description='Repairs native skeleton partitions and skirmisher skeletal LOD weights. Diagnostic candidate for movement, throwing, and death testing before the 0.7.9 art rebuild. Gameplay and Ministry remain unchanged.',changelog='Restore donor skeleton partitions; fold distant skirmisher weights to native ancestors. Native testing pending.')
    write(dest/'garrison.json',manifest)
    instructions='''Community Civilization Pack 0.7.9-pilot.1
Credits: hosein81 and chilly5
ANIMATION TEST ONLY - existing 0.7.8 artwork is intentionally retained.
This is not the completed 0.7.9 art rebuild. Do not judge new art from this pilot.

Import manually in Garrison, select its Game Mode and Tuning Pack, then China/Vietnam.
Start a fresh match. Do not use an old save for this gate.
1. Move a buffalo, stop it, and observe legs, head and tail rather than sliding.
2. Train a skirmisher, move/stop/turn, repeatedly attack a target, and observe throwing.
3. Upgrade skirmishers through Ages III and IV; test near and far zoom and death.
Report which unit/age/action still freezes, stretches, disappears, or slides.
Work/Leave and construction commands should retain existing behavior; no new work clip is added.
Rollback: preserved community_civilization_pack-0.7.8.zip.
'''
    (dest/'START-HERE.txt').write_text(instructions,encoding='utf-8')
    package=dest/f'community_civilization_pack-{version}.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in (dest/'garrison.json',final,dest/'START-HERE.txt'):z.write(p,p.name)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None and len([n for n in z.namelist() if Path(n).name=='garrison.json'])==1
        assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
        assert json.loads(z.read('garrison.json'))['details']['version']==version
    changed=[m for m in expected if expected[m]!=before['member_sha256'][m]]
    write(dest/'verification.json',{'sga_sha256':sha(final),'member_sha256':actual,'mounts':mounts,'changed':changed,'added':[],'baseline_sha256':EXPECTED,'all_untouched_members_exact':True,'source_and_normal_unchanged':True,'native_acceptance':False})
    write(dest/'delivery-proof.json',{'zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),'version':version,'verified':True,'installed':False,'final_079_art':False,'changed_members':len(changed),'total_members':len(actual)})
    assert sha(BASE/'community_civilization_pack.sga')==EXPECTED
    print('MOTION_PILOT_VERIFIED',str(package),len(changed))

if __name__=='__main__':main(sys.argv[1])
