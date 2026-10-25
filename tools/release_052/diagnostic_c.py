"""Combine two independently bounded candidates for native acceptance testing."""
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from common import *
from diagnostic_a import listing
from landmark_options_probe import prove

RUN=OUT/'diagnostic-c'

def main():
    guard();assert sha(BASELINE)==SGA051_SHA and sha(ZIP051)==ZIP051_SHA
    assert not (RUN/'receipt.json').exists(),'Preserve completed test builds'
    material=read(OUT/'landmarks/options-z1/receipt.json')
    pointer=read(OUT/'stealth/native/current.json');assert sha(pointer['file'])==pointer['sha256']
    native=read(pointer['file'])
    assert native['status']=='passed_native_source_compile' and native['native_run']['status']=='succeeded'
    assert native['native_run']['exit_code']==0 and sha(native['archive'])==native['archive_sha256']
    rows=material['payloads']+native['payloads'];assert len(rows)==len({r['member'] for r in rows})==4
    for r in rows:assert sha(r['file'])==r['sha256']
    original=OUT/'diagnostic-a/readback/baseline051';assert original.is_dir()
    assert read(OUT/'diagnostic-a/receipt.json')['baseline_sga_sha256']==SGA051_SHA
    for r in material['payloads']:
        assert sha(original/r['member'])==r['baseline_sha256']
        prove((original/r['member']).read_bytes(),Path(r['file']).read_bytes())
    RUN.mkdir(parents=True,exist_ok=True)
    current=BASELINE;candidate=RUN/(KEY+'.sga')
    for alias,selected in [('data',material['payloads']),('attrib',native['payloads'])]:
        mapping=RUN/(alias+'.txt');mapping.write_text(''.join(r['member']+'='+r['file']+'\n' for r in selected),encoding='utf-8')
        target=candidate if alias=='attrib' else RUN/'data-stage.sga';assert not target.exists()
        command('compose-diagnostic-c-'+alias,[ARCH,'set-members',current,mapping,target,'--alias',alias]);current=target
    a,b=listing(BASELINE),listing(candidate);assert a['archive']['tocs']==b['archive']['tocs']
    names={m['path'] for m in a['members']};assert names=={m['path'] for m in b['members']}
    back=RUN/'readback';assert not back.exists()
    command('unpack-diagnostic-c',[ARCH,'unpack',candidate,'--output',back])
    changes={m for m in names if sha(original/m)!=sha(back/m)};assert changes=={r['member'] for r in rows}
    for r in rows:assert sha(back/r['member'])==r['sha256']
    archer='attrib/abilities/vietnam/vn_activate_stealth_for_archer.rgd'
    assert archer in names and sha(original/archer)==sha(back/archer)
    for m in read(OUT/'diagnostic-a/receipt.json')['changed_members']:assert sha(original/m)==sha(back/m)
    verify_frozen()
    result={'status':'passed_test_package_preparation','diagnostic':'C','version':'0.5.2','is_final_release':False,
        'purpose':'Custom landmark material and automatic villager stealth candidate for native testing',
        'baseline_sga_sha256':SGA051_SHA,'archive':str(candidate),'archive_sha256':sha(candidate),
        'changed_members':sorted(changes),'unchanged_members':len(names)-len(changes),'added_members':[],
        'all_other_members_byte_identical':True,'payloads':rows,'native_stealth_source_cook':native,
        'source_overlay':read(OUT/'stealth/diagnostic-c/receipt.json'),
        'landmark_material':material,'archer_ability_byte_identical':True,'accepted_traps_monastery_byte_identical':True,
        'custom_landmark_stamps_and_geometry':'exact051; no stock-model diagnosticA stamp changes included',
        'active_source':'untouched; one-XML overlay is editable in052 inputs until native acceptance',
        'native_test':'pending user model visibility, continuous automatic stealth, range/HQ lifecycle and archer control'}
    write(RUN/'receipt.json',result)
    folder=RUN/'package';folder.mkdir()
    with ZipFile(ZIP051) as z:manifest=json.loads(z.read('garrison.json'))
    manifest['members'][0]['sha256']=result['archive_sha256']
    manifest['details'].update({'version':'0.5.2','updated':'2026-10-18','summary':'TEST C - custom Castle landmarks and automatic villager stealth',
        'description':'Native acceptance candidate. Custom landmark material option corrected to stock building convention; passive villager stealth scheduling adjusted. Archer activation, traps and monastery unchanged. Final release awaits native results.'})
    write(folder/'garrison.json',manifest);write(folder/'EVIDENCE.json',result)
    text='''COMMUNITY CIVILIZATION PACK 0.5.2 - TEST C
Credits: hosein81 and chilly5

THIS SUPERSEDES TEST B FOR TESTING BOTH FIX CANDIDATES TOGETHER.
It restores the custom Vietnamese landmark designs with the same material-only
change as B, and adds the isolated native-compiled automatic-stealth candidate.
Archer activated stealth, traps and monastery remain exactly unchanged.
This is an acceptance test build; final 0.5.2 is still pending native results.

Close AoE4, import this ZIP into Garrison, enable the pack, select it as Game Mode
and Tuning Pack, then start fresh matches as China -> Vietnam.

1. Build Resistance Headquarters. Check the custom model stays visible after
   completion at5000/5000HP without relying on selection outline.
2. Keep a stationary villager safely inside the HQ range for at least45seconds,
   away from enemy detectors. Check for rapid flicker and drops every10seconds.
3. Walk outside and back inside33m; destroy the last HQ and check removal.
   Test gathering, combat and enemy detectors separately from idle flicker.
4. Confirm the archer's activated stealth still works as before.
5. In a second fresh match, build Imperial Citadel and check completed visibility.
6. If both models render, also check destruction, selectable persistent ruins,
   interrupted/resumed repair, player colours, access and landmark victory.

Please report: HQ custom model visible? Citadel custom model visible?
Villager stable for45seconds? Range exit/reentry and HQ loss work?
Archer activated stealth unchanged?

Stealth retains its native10-second graph; the candidate changes only passive
self-disable, cooldown and queue settings. Continuous stealth is not yet proven.
The exact old0.5.1 delivery and test A/B are preserved for comparison/rollback.
'''
    (folder/'START-HERE.txt').write_text(text,encoding='utf-8')
    sources={'garrison.json':folder/'garrison.json',KEY+'.sga':candidate,'START-HERE.txt':folder/'START-HERE.txt','EVIDENCE.json':folder/'EVIDENCE.json'}
    target=OUT/(KEY+'-0.5.2-test-c.zip');assert not target.exists()
    with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in sources.items():
            info=ZipInfo(name,date_time=(2026,10,18,0,0,0));info.create_system=3;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=6)
    with ZipFile(target) as z:
        assert z.testzip() is None and z.namelist()==list(sources)
        assert all(z.read(n)==p.read_bytes() for n,p in sources.items())
    write(RUN/'package-verification.json',{'status':'passed','zip':str(target),'zip_sha256':sha(target),'bytes':target.stat().st_size,
        'sga_sha256':result['archive_sha256'],'native_test':'pending user acceptance','is_final_release':False})
    print('TEST_C_READY',sha(target),flush=True)

if __name__=='__main__':main()
