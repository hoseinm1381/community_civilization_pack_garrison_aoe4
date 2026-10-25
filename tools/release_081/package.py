"""Assemble visual-only 0.8.1 over exact 0.8.0 owning archive; full readback."""
from common import *
from policy import validate_changes,validate_cook_input,validate_readback
import zipfile,uuid
from integration import preserve_buffalo_markers
sys.path.append(str(ROOT/'tools/release_079'))
from rig_contract import read_contract,validate_contract
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import relic_chunky as rc
def main(label,revision):
    guard();base=OUT/'baseline';frozen=read(base/'inventory.json');archive=Path(frozen['archive']);assert sha(archive)==EXPECTED
    from restore_readback import restore
    restore('baseline')
    sys.path.append(str(ROOT/'tools/release_073'));from check_identity import check
    check(ROOT,archive)
    cook=OUT/'cooks'/label;receipt=read(cook/'receipt.json');assert sha(receipt['archive'])==receipt['archive_sha256']
    fresh=cook/('release-verified-readback-'+uuid.uuid4().hex[:8])
    run('fresh-cook-readback',[CFG['archive_tool'],'extract',receipt['archive'],fresh,'--filter','.'])
    hashes=lambda root:{p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
    validate_readback(hashes(fresh),hashes(cook/'readback'))
    proof=read(cook/'decoded-diagnostic.json')['buffalo'];assert not proof['blockers'] and not proof['missing_textures']
    assert sha(proof['manifest'])==proof['sha256']
    export=read(OUT/'art/buffalo'/revision/'export.json');assert read(OUT/'art/buffalo'/revision/'source-validation.json')['passed']
    validate_cook_input(receipt['records'],revision,sha(OUT/'art/buffalo'/revision/'export.json'),proof['triangles'],export['lod_triangles'])
    assert sha(export['source'])==export['source_sha256'];assert export['files']=={p.name:sha(p) for p in Path(export['export']).iterdir() if p.is_file()}
    root='art/scenario/garrison/cc076/buffalo';new=fresh/root
    validate_contract(read_contract((new/'model.rgm').read_bytes()),export['donor_contract'])
    # Skeleton, bounds markers and all non-mesh model metadata stay byte-exact.
    olddoc=rc.parse((base/'readback'/root/'model.rgm').read_bytes());newdoc=rc.parse((new/'model.rgm').read_bytes())
    a,b=olddoc.roots[0].children,newdoc.roots[0].children
    assert [(c.tag,c.name,c.version) for c in a]==[(c.tag,c.name,c.version) for c in b]
    patched=preserve_buffalo_markers((base/'readback'/root/'model.rgm').read_bytes(),(new/'model.rgm').read_bytes())
    marker_payload=OUT/'payloads/buffalo-v3/model.rgm';marker_payload.parent.mkdir(parents=True,exist_ok=True)
    if marker_payload.exists():assert marker_payload.read_bytes()==patched
    else:marker_payload.write_bytes(patched)
    payload={}
    for p in new.iterdir():
        if p.is_file() and p.suffix!='.rgo':payload[root+'/'+p.name]={'file':str(p),'sha256':sha(p)}
    payload[root+'/model.rgm']={'file':str(marker_payload),'sha256':sha(marker_payload)}
    ministry=read(OUT/'payloads/ministry-v2/receipt.json');allowed=set()
    ministry_export=read(OUT/'art/ministry/r2/receipt.json')
    assert sha(ministry_export['source'])==ministry_export['source_sha256']
    assert ministry_export['export_hashes']=={p.name:sha(p) for p in (EXPORT/'ministry/r2').iterdir() if p.is_file()}
    ministry_cook=read(OUT/'cooks/ministry-v2/receipt.json')
    assert ministry_cook['input_freeze_sha256']==sha(OUT/'cooks/ministry-v2/input-freeze.json')
    assert read(OUT/'cooks/ministry-v2/input-freeze.json')['hashes']==ministry_export['export_hashes']
    for row in ministry['members']:
        assert sha(row['file'])==row['sha256'];allowed.add(row['member']);payload[row['member']]={'file':row['file'],'sha256':row['sha256']}
    payload={k:v for k,v in payload.items() if frozen['members'].get(k)!=v['sha256']}
    validate_changes(set(payload),allowed)
    for name in ('protected.json','normal.json'):
        assert all(sha(p)==h for p,h in read(base/name).items()),'Protected input changed: '+name
    dest=OUT/'delivery/final-v1'
    if dest.exists():raise FileExistsError('Immutable delivery attempt')
    dest.mkdir(parents=True);mapping=dest/'members.txt';mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(payload.items()))+'\n')
    final=dest/'community_civilization_pack.sga'
    run('assemble',[CFG['archive_tool'],'set-members',archive,mapping,final,'--alias','data'],dest/'logs')
    check(ROOT,final);listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',final,'--verify'],dest/'logs'))
    mounts={m['path']:m['toc'] for m in listing['members']};oldmounts={m['path']:m['toc'] for m in frozen['listing']['members']}
    assert all(mounts[k]==v for k,v in oldmounts.items())
    expected=dict(frozen['members']);expected.update({k:v['sha256'] for k,v in payload.items()})
    back=dest/'readback';run('readback',[CFG['archive_tool'],'extract',final,back,'--filter','.'],dest/'logs')
    actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()};assert actual==expected
    # RGO and all animation/actor/attachment/gameplay members are outside allowlist.
    changed={k for k in actual if frozen['members'].get(k)!=actual[k]};assert changed==set(payload)
    validate_changes(changed,allowed)
    manifest=read(ROOT/'output/consolidation_080/delivery/final-v1/garrison.json')
    manifest['details'].update(version='0.8.1',updated='2026-10-24',author='hosein81 and chilly5',summary='Redesigned Vietnamese working buffalo and Ministry herd.',description='New grey-brown buffalo, short fur, farm pack and owner-coloured saddlecloth. Three unladen Ministry buffalo. Native animations and gameplay preserved.',changelog='New buffalo anatomy, materials, work gear and player-colour cloth; three posed Ministry animals. Custom idle/walk sources retained; animal animation export is unqualified. Native acceptance pending.')
    manifest['members'][0]['sha256']=sha(final);write(dest/'garrison.json',manifest)
    (dest/'START-HERE.txt').write_text('Community Civilization Pack Garrison 0.8.1\nCredits: hosein81 and chilly5\nImport manually through Garrison; enable and select the pack and Vietnam game mode.\nNew: natural grey-brown working buffalo, farm pack/hoe/baskets and player-colour saddlecloth; three unladen Ministry buffalo.\nUses original native animations. Custom idle/walk Actions are editable source only: installed exporter does not qualify animal replacement.\nCheck two player colours, idle/walk/turn/stop, construction, Paddy Work/Leave, death, camera distance/LODs and Ministry stages/ruins.\nNative appearance/behaviour, import, save/load and multiplayer are not verified.\nNo installation or publication performed. Exact 0.8.0 rollback is retained.\n',encoding='utf-8')
    package=dest/'community_civilization_pack-0.8.1.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in (dest/'garrison.json',final,dest/'START-HERE.txt'):z.write(p,p.name)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None and set(z.namelist())=={'garrison.json',final.name,'START-HERE.txt'}
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.8.1'
        with z.open(final.name) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha(final)
    write(dest/'verification.json',{'version':'0.8.1','zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),'baseline_sga_sha256':EXPECTED,'member_sha256':actual,'mounts':mounts,'changed':sorted(changed),'added':sorted(set(actual)-set(frozen['members'])),'all_untouched_members_and_mounts_exact':True,'protected_and_normal_unchanged':True,'animations_preserved':True,'native_acceptance':False,'installed':False,'published':False})
    print('081_PACKAGE_VERIFIED',len(changed),str(package))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
