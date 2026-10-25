"""Strict 0.8.3 over accepted buffalo-animation owning archive."""
from common import *
from policy import validate_changes,FAMILIES,PREFIX
import zipfile
sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import relic_chunky as rc
sys.path.append(str(ROOT/'tools/release_079'));from rig_contract import read_contract,validate_contract
sys.path.append(str(ROOT/'tools/release_073'));from check_identity import check
def main(label):
    guard();freeze=read(OUT/'baseline/archive.json');baseline=Path(freeze['archive']);assert sha(baseline)==freeze['sha256']==EXPECTED
    assert sha(freeze['zip'])==freeze['zip_sha256'];check(ROOT,baseline)
    cook=OUT/'cooks'/label;receipt=read(cook/'receipt.json');assert receipt['fresh_native_cook'] and not receipt['diagnostic_control'] and sha(receipt['archive'])==receipt['archive_sha256']
    proofs=read(cook/'decoded-proof.json');selection=read(RECIPES/'selection.json');assert set(selection)==FAMILIES
    qa=read(OUT/'source-qa.json');assert qa['passed'] and qa['selection']==selection
    assert qa['cook_sha256']==receipt['archive_sha256']
    assert qa['export_receipt_sha256']=={family:sha(OUT/'art'/family/revision/'export.json') for family,revision in selection.items()}
    dest=OUT/'delivery/final-v2';dest.mkdir(parents=True,exist_ok=False)
    fresh=dest/'fresh-cook-readback';run('fresh-cook-readback',[CFG['archive_tool'],'extract',receipt['archive'],fresh,'--filter','.'],dest/'logs')
    payload={};oldroot=ROOT/'output/release_081/delivery/final-v1/readback'
    for record in receipt['records']:
        family=record['family'];assert selection[family]==record['revision']
        proof=proofs[family];assert not proof['blockers'] and not proof['missing_textures'] and sha(proof['manifest'])==proof['sha256']
        export=read(OUT/'art'/family/record['revision']/'export.json');assert sha(export['source'])==export['source_sha256']
        assert export['files']=={p.name:sha(p) for p in Path(export['export']).iterdir() if p.is_file()}
        rel=record['member_root'];new=fresh/rel;assert {p.name:sha(p) for p in new.iterdir()}=={p.name:sha(p) for p in (cook/'readback'/rel).iterdir()}
        original=(oldroot/rel/'model.rgm').read_bytes();generated=(new/'model.rgm').read_bytes()
        if family.startswith('skirmisher'):validate_contract(read_contract(generated),export['donor_contract'])
        old=rc.parse(original);doc=rc.parse(generated);a,b=old.roots[0].children,doc.roots[0].children
        assert [(x.tag,x.name,x.version) for x in a]==[(x.tag,x.name,x.version) for x in b],family
        geometry_tags={b'SKMS',b'STMS'}
        expected_geometry=b'SKMS' if family.startswith('skirmisher') else b'STMS'
        assert sum(c.tag==expected_geometry for c in b)==1,family
        prior={x.offset:y.payload for x,y in zip(b,a) if x.tag not in geometry_tags}
        patched=rc.rebuild(doc,lambda c:prior.get(c.offset))
        after=rc.parse(patched).roots[0].children
        assert all(x.payload==y.payload for x,y in zip(a,after) if x.tag not in geometry_tags)
        assert [x.payload for x in after if x.tag in geometry_tags]==[x.payload for x in b if x.tag in geometry_tags]
        target=dest/'payload'/rel/'model.rgm';target.parent.mkdir(parents=True);target.write_bytes(patched)
        for path in new.iterdir():
            if path.is_file() and path.suffix!='.rgo':payload[rel+'/'+path.name]={'file':str(target if path.name=='model.rgm' else path),'sha256':sha(target if path.name=='model.rgm' else path)}
    payload={k:v for k,v in payload.items() if freeze['members'].get(k)!=v['sha256']};validate_changes(set(payload))
    for name in ['normal','protected']:
        assert all(sha(p)==h for p,h in read(OUT/f'baseline/{name}.json').items()),name+' preservation drift'
    mapping=dest/'members.txt';mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(payload.items()))+'\n')
    final=dest/'community_civilization_pack.sga';run('assemble',[CFG['archive_tool'],'set-members',baseline,mapping,final,'--alias','data'],dest/'logs');check(ROOT,final)
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',final,'--verify'],dest/'logs'));mounts={m['path']:m['toc'] for m in listing['members']}
    assert all(mounts[k]==v for k,v in freeze['mounts'].items())
    readback=dest/'readback';run('full-readback',[CFG['archive_tool'],'extract',final,readback,'--filter','.'],dest/'logs')
    actual={p.relative_to(readback).as_posix():sha(p) for p in readback.rglob('*') if p.is_file()};expected=dict(freeze['members']);expected.update({k:v['sha256'] for k,v in payload.items()});assert actual==expected
    changed={k for k in actual if freeze['members'].get(k)!=actual[k]};assert changed==set(payload);validate_changes(changed)
    manifest=read(BASE/'garrison.json');manifest['details'].update(version='0.8.3',updated='2026-10-24',author='hosein81 and chilly5',summary='Rebuilt Vietnamese skirmishers and javelins with clear player colours.',description='Redesigned skirmishers II–IV: layered cloth, veteran padding, elite flat armour, broad owner-colour cloth and matching javelins. Includes the accepted working buffalo artwork and custom idle/walk.',changelog='Complete skirmisher clothing/equipment and weapon redesign on native rigs; official Chinese-derived face/hands; improved player-colour coverage. Gameplay unchanged. New skirmisher artwork requires native acceptance.')
    manifest['members'][0]['sha256']=sha(final);write(dest/'garrison.json',manifest)
    (dest/'START-HERE.txt').write_text('Community Civilization Pack Garrison 0.8.3\nCredits: hosein81 and chilly5\nImport manually in Garrison; enable one version and select its tuning pack and Vietnam game mode. Restart the game and use a fresh match.\nNew: skirmishers II/III/IV, broad player-colour cloth, new protection/armour, spare javelins and matching thrown/projectile visuals.\nAccepted buffalo custom idle/walk and 0.8.1 model/Ministry artwork are retained byte-for-byte. Gameplay and skirmisher native animations are unchanged.\nCheck all three ages and upgrades, ordinary/tower training, two player colours, close/far LODs, idle/move/turn/stop, throw/grip/release/projectile flight, work and death.\nFresh native art cook, native decode, source/rig/weight checks, archive identity/member preservation and ZIP integrity passed.\nNew skirmisher in-game appearance, client import, save/load and multiplayer have not been verified.\nNo installation or publication performed. Original 0.8.1 and 0.8.2 pilot ZIPs are preserved.\n',encoding='utf-8')
    package=dest/'community_civilization_pack-0.8.3.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in [dest/'garrison.json',final,dest/'START-HERE.txt']:z.write(path,path.name)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None and set(z.namelist())=={'garrison.json',final.name,'START-HERE.txt'}
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.8.3'
        with z.open(final.name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(final)
    write(dest/'verification.json',{'version':'0.8.3','zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),'baseline_sga_sha256':EXPECTED,'archive_identity':listing['archive']['name'],'member_sha256':actual,'mounts':mounts,'changed':sorted(changed),'added':sorted(set(actual)-set(freeze['members'])),'deleted':[],'untouched_members_exact':len(set(freeze['members'])-changed),'all_original_mounts_exact':True,'normal_and_protected_sources_unchanged':True,'buffalo_animations_preserved':True,'all_gameplay_members_unchanged':True,'native_art_cook':True,'native_decoded_readback':True,'client_import':False,'native_skirmisher_acceptance':False,'save_load':False,'multiplayer':False,'installed':False,'published':False})
    print('083_PACKAGE_VERIFIED',str(package),sha(package),len(changed),flush=True)
if __name__=='__main__':main(sys.argv[1])
