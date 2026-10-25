"""Selective 0.5.0 archive composition from the exact completed 0.4.0 SGA."""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from common import ROOT,OUT,WORK,CASTLE,BASELINE,ARCH,CONFIG,KEY,GUID,VERSION,guarded,read,run_logged,sha,write

def listing(archive):
    result=subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,check=True)
    value=json.loads(result.stdout)
    assert value['archive']['verification']['verified']
    assert value['archive']['name'].replace('-','').lower()==GUID.replace('-','').lower()
    paths=[row['path'].replace('\\','/').casefold() for row in value['members']]
    assert len(paths)==len(set(paths)), 'Archive contains duplicate resource paths'
    return value

def unpack(archive,label):
    folder=OUT/'readback'/(label+'-'+sha(archive)[:12])
    if not (folder/'.complete.json').exists():
        assert not folder.exists(),f'Incomplete readback retained: {folder}'
        run_logged('unpack050-'+label,[ARCH,'unpack',archive,'--output',folder])
        write(folder/'.complete.json',{'archive_sha256':sha(archive)})
    assert read(folder/'.complete.json')['archive_sha256']==sha(archive)
    return folder

def payloads():
    assert read(CASTLE/'verification.json')['status']=='passed_offline_and_native_cook'
    rows=[]
    for name in ('landmark-media.json','building-media.json'):
        media=read(CASTLE/'integration'/name)
        assert media['status']=='passed'
        rows.extend(media['payloads'])
    for kind in ('landmarks','details'):
        reference=read(CASTLE/'integration'/(kind+'-reference.json'))
        assert reference['status']=='passed' and sha(reference['archive'])==reference['sha256']
        media_name='landmark-media.json' if kind=='landmarks' else 'building-media.json'
        for row in read(CASTLE/'integration'/media_name)['payloads']:
            assert reference['exact_inputs_sha256'][row['member']]==row['sha256'], row['member']
    binding=read(WORK/'private-bindings.json')
    assert binding['status']=='passed'
    branch_reference=read(CASTLE/'integration/landmarks-branches-reference.json')
    assert branch_reference['status']=='passed' and sha(branch_reference['archive'])==branch_reference['sha256']
    expected={r['model'] for r in binding['branch_variants']}|{r['model'] for r in read(CASTLE/'integration/landmark-media.json')['models']}
    assert {r['model'] for r in branch_reference['model_references']}==expected
    for row in read(CASTLE/'integration/landmark-media.json')['payloads']+[r for r in binding['payloads'] if r['member'].startswith('art/scenario/cc050/')]:
        assert branch_reference['exact_inputs_sha256'][row['member']]==row['sha256'], row['member']
    rows.extend(binding['payloads'])
    pointer=read(OUT/'native-source/current.json')
    assert sha(pointer['receipt'])==pointer['sha256']
    source=read(pointer['receipt']);assert source['status']=='passed'
    assert sha(source['archive'])==source['archive_sha256']
    rows.extend(source['payloads'])
    unique={}
    for row in rows:
        assert sha(row['file'])==row['sha256'],row['member']
        assert row['member'].startswith(('art/scenario/cccastle/','art/scenario/cc050/','art/stamps/cc050/','attrib/')),row['member']
        if row['member'] in unique:assert unique[row['member']]['sha256']==row['sha256']
        unique[row['member']]=row
    return [unique[key] for key in sorted(unique)]

def compose(label):
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}',label)
    from source_policy import verify as verify_source
    assert verify_source()['status']=='passed'
    freeze=read(OUT/'baseline/freeze-baseline.json')
    assert sha(BASELINE)==freeze['accepted_release_040']['embedded_sga']['sha256']
    rows=payloads()
    folder=OUT/'candidates'/label;assert not folder.exists();folder.mkdir(parents=True)
    target=folder/(KEY+'.sga');current=BASELINE
    groups=[('data',[r for r in rows if r['member'].startswith('art/')]),
            ('attrib',[r for r in rows if r['member'].startswith('attrib/')])]
    for index,(alias,selected) in enumerate(groups):
        assert selected
        mapping=folder/(alias+'-members.txt')
        mapping.write_text(''.join(r['member']+'='+r['file']+'\n' for r in selected),encoding='utf-8')
        destination=target if index==len(groups)-1 else folder/(alias+'-stage.sga')
        run_logged('compose050-'+label+'-'+alias,[ARCH,'set-members',current,mapping,destination,'--alias',alias])
        current=destination
    value={'status':'passed','archive':str(target),'sha256':sha(target),
           'baseline_sha256':sha(BASELINE),'payloads':rows,'project_guid':GUID,
           'art_verification_sha256':sha(CASTLE/'verification.json'),
           'binding_receipt_sha256':sha(WORK/'private-bindings.json'),
           'native_source_receipt_sha256':read(OUT/'native-source/current.json')['sha256']}
    write(OUT/'candidate.json',value)
    print('RELEASE050_COMPOSED',len(rows),sha(target));return value

def verify():
    guarded()
    from source_policy import verify as verify_source
    assert verify_source()['status']=='passed'
    candidate=read(OUT/'candidate.json');archive=Path(candidate['archive'])
    assert sha(archive)==candidate['sha256'] and sha(BASELINE)==candidate['baseline_sha256']
    assert payloads()==candidate['payloads'],'Candidate payloads no longer match registered inputs'
    a,b=listing(BASELINE),listing(archive)
    assert a['archive']['tocs']==b['archive']['tocs']
    before,after=unpack(BASELINE,'baseline040'),unpack(archive,'candidate050')
    old={r['path'] for r in a['members']};new={r['path'] for r in b['members']}
    assert old<=new
    mapped={r['member']:r for r in candidate['payloads']}
    changed={p for p in old if sha(before/p)!=sha(after/p)}
    assert changed==set(mapped)&old,(sorted(changed^(set(mapped)&old)))
    assert new-old==set(mapped)-old
    for member,row in mapped.items():assert sha(after/member)==row['sha256'],member
    # The source compile may regenerate unrelated files. Only explicitly allowed
    # visual actor/list payloads are composed; every other 040 member stays exact.
    result={'status':'passed','sga_sha256':sha(archive),'baseline_sha256':sha(BASELINE),
            'baseline_members':len(old),'final_members':len(new),'changed':sorted(changed),
            'added':sorted(new-old),'untouched_members':len(old-changed),
            'all_other_members_byte_identical':True,'unique_resource_paths':True,'native_runtime':'not tested'}
    write(OUT/'archive-verification.json',result)
    print('RELEASE050_ARCHIVE_VERIFIED',len(changed),'changed',len(new-old),'added',len(old-changed),'untouched')
    return result

START='''COMMUNITY CIVILIZATION PACK 0.5.0 — Vietnamese Castle Age buildings

Import this ZIP through Garrison with the game closed. Select Community
Civilization Pack as Game Mode and Tuning Pack. Choose China in the lobby,
then Vietnam at the opening choice. Credits: hosein81 and chilly5.

New art: Imperial Citadel, Resistance Headquarters, Castle/Imperial monastery
and siege workshop, and the shared keep. The completed 0.4.0 pack is the baseline.

Native acceptance is pending. Test both landmarks: build, damage, destroy,
wait past collapse cleanup, select persistent ruins, repair, interrupt/resume,
and destroy again. Check landmark victory accounting, player colours, adjacent
buildings and paths, production exits, construction, and alternate/campaign art.
Review EVIDENCE.json for shader qualification and other limitations.

Rollback: close the game and reimport the preserved 0.4.0 ZIP.
'''

def package():
    audit=verify()
    from checks import run
    checks=run()
    candidate=read(OUT/'candidate.json');folder=OUT/'package';folder.mkdir(exist_ok=True)
    target=folder/(KEY+'.sga')
    if target.exists():assert sha(target)==candidate['sha256']
    else:shutil.copy2(candidate['archive'],target)
    manifest={'schema':'garrison.mod/v1','bundle_key':KEY,
        'members':[{'mod_key':KEY,'role':'tuning','path':KEY+'.sga','sha256':sha(target)}],
        'details':{'id':KEY,'name':CONFIG['display_name'],'version':VERSION,
            'summary':'Vietnamese Castle Age landmarks, monasteries, siege workshops and keep',
            'min_garrison':'0.1.4','content_types':['game-mode','tuning-pack'],'updated':'2026-10-17',
            'author':'hosein81 and chilly5',
            'description':'Castle Age visual update based on completed 0.4.0. Native import and match acceptance pending.'}}
    write(folder/'garrison.json',manifest);(folder/'START-HERE.txt').write_text(START,encoding='utf-8')
    pointer=read(OUT/'native-source/current.json')
    evidence={'version':VERSION,'project_guid':GUID,'baseline':'completed 0.4.0',
              'active_visual_bindings_applied':True,
              'asset_preparation_receipts_scope':'Historical isolated asset-stage records; applied 0.5.0 operations are in bindings and native_source below.',
              'archive':audit,'checks':checks,'asset_verification':read(CASTLE/'verification.json'),
              'lifecycle_contract':read(CASTLE/'lifecycle/model-contract.json'),
              'bindings':read(WORK/'private-bindings.json'),'native_source':read(pointer['receipt']),
              'retained_native_visual_policy':read(ROOT/'art/recipes/release_050/retained-native-visuals.json'),
              'external_normal_observation':read(OUT/'baseline/normal-concurrent-observation.json'),
              'branch_reference_cook':read(CASTLE/'integration/landmarks-branches-reference.json'),
              'benchmark':read(CASTLE/'budget/castle-stock-landmark-budget.json'),
              'landmarks':{key:read(CASTLE/'landmarks'/key/'handoff.json') for key in ('imperial_citadel','resistance_hq')},
              'native_runtime':'not tested','client_import':'not performed'}
    colour=CASTLE/'owner-colour/verification.json'
    if colour.exists():evidence['owner_colour']=read(colour)
    write(folder/'EVIDENCE.json',evidence)
    destination=OUT/(KEY+'-'+VERSION+'.zip')
    names=('garrison.json',KEY+'.sga','START-HERE.txt','EVIDENCE.json')
    if destination.exists():
        with ZipFile(destination) as bundle:
            assert bundle.testzip() is None and bundle.namelist()==list(names)
            assert all(bundle.read(name)==(folder/name).read_bytes() for name in names),'Preserve previous package before repackaging'
    else:
        temporary=destination.with_suffix('.zip.tmp');assert not temporary.exists()
        with ZipFile(temporary,'w',ZIP_DEFLATED,compresslevel=6) as bundle:
            for name in names:
                info=ZipInfo(name,date_time=(2026,10,17,0,0,0));info.create_system=3;info.external_attr=0o644<<16
                bundle.writestr(info,(folder/name).read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=6)
        with ZipFile(temporary) as bundle:
            assert bundle.testzip() is None and bundle.namelist()==list(names)
            assert json.loads(bundle.read('garrison.json'))==manifest
            assert hashlib.sha256(bundle.read(KEY+'.sga')).hexdigest()==sha(target)
        temporary.replace(destination)
    result={'status':'passed','version':VERSION,'zip':str(destination),'zip_sha256':sha(destination),
            'sga':str(target),'sga_sha256':sha(target),'bytes':destination.stat().st_size,
            'native_runtime':'not tested','client_import':'not performed'}
    write(OUT/'package-verification.json',result)
    print('RELEASE050_PACKAGE_VERIFIED',sha(destination));return result

if __name__=='__main__':
    action=sys.argv[1]
    if action=='compose':compose(sys.argv[2])
    elif action=='verify':verify()
    elif action=='package':package()
    else:raise SystemExit('compose LABEL|verify|package')
