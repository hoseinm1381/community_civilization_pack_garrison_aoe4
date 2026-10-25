"""One-axis native probe: authored landmarks, building material option Z=1."""
import shutil
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from common import *
from diagnostic_a import listing
from landmark_options_probe import prove

RUN=OUT/'diagnostic-b'

def main():
    guard();assert sha(BASELINE)==SGA051_SHA and sha(ZIP051)==ZIP051_SHA
    assert not (RUN/'receipt.json').exists(),'Keep completed probe builds'
    material=read(OUT/'landmarks/options-z1/receipt.json');rows=material['payloads']
    assert len(rows)==3
    original=OUT/'diagnostic-a/readback/baseline051'
    assert original.is_dir() and read(OUT/'diagnostic-a/receipt.json')['baseline_sga_sha256']==SGA051_SHA
    for row in rows:
        assert sha(original/row['member'])==row['baseline_sha256']
        assert sha(row['file'])==row['sha256']
        prove((original/row['member']).read_bytes(),Path(row['file']).read_bytes())
    RUN.mkdir(parents=True,exist_ok=True)
    mapping=RUN/'members.txt';mapping.write_text(''.join(r['member']+'='+r['file']+'\n' for r in rows),encoding='utf-8')
    candidate=RUN/(KEY+'.sga')
    if not candidate.exists():command('compose-diagnostic-b',[ARCH,'set-members',BASELINE,mapping,candidate,'--alias','data'])
    a,b=listing(BASELINE),listing(candidate)
    assert a['archive']['tocs']==b['archive']['tocs']
    names={m['path'] for m in a['members']};assert names=={m['path'] for m in b['members']}
    back=RUN/'readback'
    if not back.exists():command('unpack-diagnostic-b',[ARCH,'unpack',candidate,'--output',back])
    changed={m for m in names if sha(original/m)!=sha(back/m)}
    assert changed=={r['member'] for r in rows}
    for r in rows:assert sha(back/r['member'])==r['sha256']
    # This starts from 051, not diagnostic A: all custom model stamps return
    # byte-identically, while the already-failed selector edit remains controlled.
    for m in read(OUT/'diagnostic-a/receipt.json')['changed_members']:
        assert sha(back/m)==sha(original/m)
    verify_frozen()
    result={'status':'passed_diagnostic_package_preparation','diagnostic':'B','version':'0.5.2',
            'purpose':'Custom landmark material one-field native comparison; NOT final release',
            'baseline_sga_sha256':SGA051_SHA,'archive':str(candidate),'archive_sha256':sha(candidate),
            'changed_members':sorted(changed),'unchanged_members':len(names)-len(changed),
            'all_other_members_byte_identical':True,'payloads':rows,
            'material_receipt_sha256':sha(OUT/'landmarks/options-z1/receipt.json'),
            'only_edit':'options Float4 Z 0.0->1.0 in structure and structure_collection; six ASCII bytes total',
            'geometry_selectors_rgo_stamps_gameplay':'unchanged from051; authored designs restored from diagnosticA',
            'archer_activated_stealth':'byte-identical to051, confirmed good by user',
            'villager_auto_stealth':'unchanged in this rendering-only probe; separate investigation ongoing',
            'native_test':'pending user visibility comparison','is_final_release':False}
    write(RUN/'receipt.json',result)
    folder=RUN/'package';folder.mkdir()
    with ZipFile(ZIP051) as z:manifest=json.loads(z.read('garrison.json'))
    manifest['members'][0]['sha256']=result['archive_sha256']
    manifest['details'].update({'version':'0.5.2','summary':'DIAGNOSTIC B - custom Castle landmark material comparison',
        'description':'Custom Vietnamese designs restored. Only the building material options Z value changes; rendering acceptance pending. Automatic villager-stealth fix is not included in this isolated model test.'})
    write(folder/'garrison.json',manifest);write(folder/'EVIDENCE.json',result)
    text='''COMMUNITY CIVILIZATION PACK 0.5.2 - DIAGNOSTIC B
Credits: hosein81 and chilly5

THIS IS THE CUSTOM-MODEL MATERIAL TEST, NOT THE FINAL RELEASE.
The original custom Vietnamese Citadel and Headquarters designs are restored.
Only one material option changes to match stock building materials. Gameplay,
archer activated stealth, traps and monastery remain byte-identical to 0.5.1.
Villager auto-stealth is unchanged in this isolated rendering test.

Close AoE4, import this ZIP, enable the pack, select it as Game Mode and Tuning
Pack, and start fresh matches as China -> Vietnam.

Build Headquarters in one match and Citadel in another. After each is completed
at 5000/5000 HP, check normal visibility without relying on selection outlines.
Report: Headquarters custom model visible? Citadel custom model visible?
If visible, also note whether player colour appears and whether damage/destruction
leaves recognizable, selectable ruins that villagers can repair.

The preserved diagnostic A stock-model comparison and 0.5.1 ZIP remain available.
Final 0.5.2 will follow the successful native model test and automatic-stealth repair.
'''
    (folder/'START-HERE.txt').write_text(text,encoding='utf-8')
    sources={'garrison.json':folder/'garrison.json',KEY+'.sga':candidate,'START-HERE.txt':folder/'START-HERE.txt','EVIDENCE.json':folder/'EVIDENCE.json'}
    target=OUT/(KEY+'-0.5.2-diagnostic-b.zip');assert not target.exists()
    with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in sources.items():
            info=ZipInfo(name,date_time=(2026,10,17,0,0,0));info.create_system=3;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=6)
    with ZipFile(target) as z:
        assert z.testzip() is None and z.namelist()==list(sources)
        assert all(z.read(n)==p.read_bytes() for n,p in sources.items())
    write(RUN/'package-verification.json',{'status':'passed','zip':str(target),'zip_sha256':sha(target),'bytes':target.stat().st_size,
        'sga_sha256':result['archive_sha256'],'native_test':'pending user comparison','is_final_release':False})
    print('DIAGNOSTIC_B_READY',sha(target),flush=True)

if __name__=='__main__':main()
