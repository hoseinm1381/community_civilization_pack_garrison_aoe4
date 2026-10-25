"""Selective 051 archive, strict package, and confined readback cleanup."""
import hashlib,json,re,shutil,subprocess,sys
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from common import *
def listing(archive):
    x=json.loads(subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,check=True).stdout)
    assert x['archive']['verification']['verified']
    assert x['archive']['name'].replace('-','').lower()==GUID.replace('-','').lower()
    paths=[m['path'].replace('\\','/').casefold() for m in x['members']];assert len(paths)==len(set(paths))
    return x
def payloads():
    rows=[]
    for kind in ('landmarks','monastery'):
        receipt=read(OUT/kind/'receipt.json');rows.extend(receipt['payloads'])
    p=read(OUT/'native-source/current.json');assert sha(p['file'])==p['sha256'];native=read(p['file']);assert native['status']=='passed'
    assert sha(native['archive'])==native['archive_sha256'];rows.extend(native['payloads'])
    assert len(rows)==len({r['member'] for r in rows})==14
    for r in rows:assert sha(r['file'])==r['sha256']
    return sorted(rows,key=lambda r:r['member'])
def unpack(archive,label):
    folder=OUT/'readback'/(label+'-'+sha(archive)[:12]);marker=folder/'.complete.json'
    if not marker.exists():
        assert not folder.exists(),'Incomplete readback retained'
        run_logged('unpack051-'+folder.name,[ARCH,'unpack',archive,'--output',folder]);write(marker,{'sha256':sha(archive)})
    assert read(marker)['sha256']==sha(archive);return folder
def compose(label):
    from checks import source_policy
    source_policy();assert sha(BASELINE)==SGA050_SHA
    root=OUT/'candidates'/label;assert not root.exists();root.mkdir(parents=True)
    target=root/(KEY+'.sga');rows=payloads();current=BASELINE
    for alias,selected in [('data',[r for r in rows if r['member'].startswith(('art/','scar/'))]),('attrib',[r for r in rows if r['member'].startswith('attrib/')])]:
        mapping=root/(alias+'.txt');mapping.write_text(''.join(r['member']+'='+r['file']+'\n' for r in selected),encoding='utf-8')
        destination=target if alias=='attrib' else root/'data-stage.sga'
        run_logged('compose051-'+label+'-'+alias,[ARCH,'set-members',current,mapping,destination,'--alias',alias]);current=destination
    write(OUT/'candidate.json',{'status':'passed','archive':str(target),'sha256':sha(target),'baseline_sha256':SGA050_SHA,'payloads':rows});print('COMPOSED051',sha(target))
def verify():
    guarded();c=read(OUT/'candidate.json');assert sha(c['archive'])==c['sha256'] and sha(BASELINE)==SGA050_SHA
    assert payloads()==c['payloads']
    a,b=listing(BASELINE),listing(c['archive']);assert a['archive']['tocs']==b['archive']['tocs']
    before,after=unpack(BASELINE,'baseline050'),unpack(c['archive'],'candidate051')
    old={m['path'] for m in a['members']};new={m['path'] for m in b['members']};assert old<=new
    mapped={r['member']:r for r in c['payloads']}
    changed={p for p in old if sha(before/p)!=sha(after/p)}
    assert changed==(old&set(mapped)) and new-old==set(mapped)-old
    for p,r in mapped.items():assert sha(after/p)==r['sha256']
    v={'status':'passed','baseline_sha256':SGA050_SHA,'sga_sha256':c['sha256'],'baseline_members':len(old),'final_members':len(new),'changed':sorted(changed),'added':sorted(new-old),'untouched_members':len(old-changed),'all_other_members_byte_identical':True,'unique_resource_paths':True}
    write(OUT/'archive-verification.json',v);print('ARCHIVE051_VERIFIED',len(changed),len(new-old),len(old-changed));return v
def package(label):
    audit=verify();reference=read(OUT/'reference/receipt.json');candidate=read(OUT/'candidate.json')
    assert reference['status']=='passed' and reference['candidate_sha256']==candidate['sha256']
    assert sha(reference['archive'])==reference['archive_sha256']
    from checks import run
    checks=run(label)
    monastery=read(OUT/'monastery/receipt.json')
    monastery['status']='passed_source_readback_and_integrated_native_reference'
    monastery['native_reference_cook']={'status':'passed','receipt':str(OUT/'reference/receipt.json'),'sha256':sha(OUT/'reference/receipt.json'),'candidate_sha256':candidate['sha256'],'qualification':reference['qualification']}
    write(OUT/'monastery/receipt.json',monastery)
    folder=OUT/'package';folder.mkdir(exist_ok=True);sga=folder/(KEY+'.sga')
    if sga.exists():assert sha(sga)==candidate['sha256']
    else:shutil.copy2(candidate['archive'],sga)
    manifest={'schema':'garrison.mod/v1','bundle_key':KEY,'members':[{'mod_key':KEY,'role':'tuning','path':KEY+'.sga','sha256':sha(sga)}],
        'details':{'id':KEY,'name':CONFIG['display_name'],'version':VERSION,'summary':'Trap completion conversion and focused Castle building repairs','min_garrison':'0.1.4','content_types':['game-mode','tuning-pack'],'updated':'2026-10-17','author':'hosein81 and chilly5','description':'0.5.1 based on verified 0.5.0; import and native match acceptance pending.'}}
    start='''COMMUNITY CIVILIZATION PACK 0.5.1\nCredits: hosein81 and chilly5\n\nImport through Garrison with the game closed. Select Community Civilization Pack\nas both Game Mode and Tuning Pack, choose China, then Vietnam at the opening choice.\n\nTrap construction keeps path blockers; completed traps convert to passable children.\nBoth Castle landmarks have repaired completed-state selectors. Both monastery tiers\nrestore donor-shaped roofs and remove the oversized added canopy/frame.\n\nNative acceptance is PENDING. Build/damage/destroy/select persistent ruins/repair\nboth landmarks, interrupt/resume and destroy again. Check landmark victory, player\ncolours, every monastery tier, adjacency and production access. Test trap construction\nwith one/multiple builders, friendly/enemy infantry/cavalry/elephants/siege passage\nafter completion, attack detection and the non-resetting four-second lifetime.\n\nRollback: close game and import the preserved 0.5.0 ZIP (reported broken art),\nor use the retained 0.4.0 rollback. Do not confuse offline checks with native proof.\n'''
    write(folder/'garrison.json',manifest);(folder/'START-HERE.txt').write_text(start,encoding='utf-8')
    pointer=read(OUT/'native-source/current.json')
    evidence={'version':VERSION,'project_guid':GUID,'archive':audit,'checks':checks,'native_source':read(pointer['file']),'native_reference':reference,'landmarks':read(OUT/'landmarks/receipt.json'),'monastery':read(OUT/'monastery/receipt.json'),'baseline_freeze_sha256':sha(OUT/'baseline/freeze.json'),'normal_edition':'unchanged','client_import':'not performed','native_match':'pending user testing'}
    write(folder/'EVIDENCE.json',evidence)
    names=['garrison.json',KEY+'.sga','START-HERE.txt','EVIDENCE.json'];target=OUT/(KEY+'-'+VERSION+'.zip');assert not target.exists(),'Keep previous package before repackaging'
    temporary=target.with_suffix('.zip.tmp');assert not temporary.exists()
    with ZipFile(temporary,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for name in names:
            info=ZipInfo(name,date_time=(2026,10,17,0,0,0));info.create_system=3;info.external_attr=0o644<<16
            z.writestr(info,(folder/name).read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=6)
    with ZipFile(temporary) as z:
        assert z.testzip() is None and z.namelist()==names
        assert all(z.read(n)==(folder/n).read_bytes() for n in names)
    temporary.replace(target)
    result={'status':'passed','zip':str(target),'zip_sha256':sha(target),'bytes':target.stat().st_size,'sga':str(sga),'sga_sha256':sha(sga),'native_match':'pending user testing','client_import':'not performed'}
    write(OUT/'package-verification.json',result);print('PACKAGE051_VERIFIED',result['zip_sha256'])
if __name__=='__main__':
    action=sys.argv[1]
    if action=='compose':compose(sys.argv[2])
    elif action=='verify':verify()
    elif action=='package':package(sys.argv[2])
