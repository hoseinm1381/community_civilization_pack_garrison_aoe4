"""In-place functional Persia import and current release orchestration.

The exact owning archive is the preservation authority; a source burn is only
the reference for the newly added Persia resources. Never broad-overlay Vietnam.
"""
import argparse,csv,hashlib,io,json,os,re,subprocess,sys,xml.etree.ElementTree as E,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/current'
NG='a743d7d1d7534cf78817e29d8ded7366'
GUID='b7fcea91257b408fb9e8ae4d8bc402e1'
VERSION='0.9.0'
CFG=json.loads((ROOT/'workspace.json').read_text(encoding='utf-8'))

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def run(label,args):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace')
    (OUT/(label+'.log')).write_text('EXIT '+str(result.returncode)+'\n'+result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(label+' failed; see '+str(OUT/(label+'.log')))
    return result.stdout

def extract(member,target,archive=None):
    archive=archive or Path(json.loads((OUT/'baseline.json').read_text())['archive'])
    target=Path(target);expected=json.loads((OUT/'baseline.json').read_text())['members'].get(member)
    if target.exists():
        if expected and sha(target)==expected:return target
        raise ValueError('Existing extraction differs: '+str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    run('extract-'+target.name,[CFG['archive_tool'],'extract-member',archive,member,target])
    if expected:assert sha(target)==expected,member
    return target

def translated(data):return data.replace(NG.encode(),GUID.encode())

def import_source(source):
    sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
    check_storage(ROOT,CFG)
    baseline=json.loads((OUT/'baseline.json').read_text())
    assert sha(baseline['archive'])==baseline['archive_sha256']
    inputs={}
    for p in sorted((source/'assets/attrib/instances').glob('*/persia/ps_*.xml')):
        rel=p.relative_to(source);target=ROOT/rel;data=translated(p.read_bytes())
        assert not target.exists() or target.read_bytes()==data,'Existing Persian edit: '+str(target)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);inputs[rel.as_posix()]=sha(p)
    assert len(inputs)==281
    for p in (source/'assets/ui/icons/persia').rglob('*.png'):
        target=ROOT/p.relative_to(source);assert not target.exists() or sha(target)==sha(p)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
    for p in (source/'assets/scar/persia').glob('*.scar'):
        target=ROOT/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(translated(p.read_bytes()))
    (ROOT/'assets/scar/vietnam/selection_core.scar').write_bytes((source/'assets/scar/vietnam/selection_core.scar').read_bytes())
    # Keep the current packaged voice-owned precache and scripts as editable
    # source, so subsequent native burns do not drop their imports.
    for member in ('scar/vietnam/prematch_precache.scar','scar/vietnam/voices_084.scar','scar/vietnam/voice_bank_084.scar','scar/garrison/garrison.scar'):
        original=extract(member,OUT/'inputs'/member)
        target=ROOT/'assets'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(original.read_bytes())
    mode=translated((source/'assets/scar/winconditions/VietnamMode.scar').read_bytes()).decode('utf-8-sig').replace('\r\n','\n')
    mode=mode.replace('import("vietnam/lifecycle.scar")','import("vietnam/lifecycle.scar")\nimport("vietnam/presentation.scar")\nimport("vietnam/voices_084.scar")')
    mode=mode.replace('function VietnamMode_RefreshDynastyUI()\n','function VietnamMode_RefreshDynastyUI()\n    VietnamPresentation_Update()\n')
    mode=mode.replace('    PersiaLifecycle_Start(state.civilizations)\n','    PersiaLifecycle_Start(state.civilizations)\n    VietnamPresentation_Start()\n    VietnamVoice_Start(state.civilizations)\n')
    mode=mode.replace('    VietnamPaddyWood_RestoreUI()\n','    VietnamPaddyWood_RestoreUI()\n    VietnamPresentation_Restore()\n    VietnamVoice_Stop()\n    if state.selection ~= nil and state.selection.closed and not state.ending then\n        VietnamVoice_Start(state.civilizations)\n    end\n')
    mode=mode.replace('    VietnamInitialization_Cleanup()\n','    VietnamVoice_Stop()\n    VietnamInitialization_Cleanup()\n')
    mode=mode.replace('    PersiaLifecycle_Cleanup()\n','    PersiaLifecycle_Cleanup()\n    VietnamPresentation_Cleanup()\n')
    mode=mode.replace('revision=20261023-runtime-v12','revision=20261026-persia-garrison-090')
    (ROOT/'assets/scar/winconditions/VietnamMode.scar').write_text(mode,encoding='utf-8',newline='\n')
    locale=ROOT/'assets/locdb/community_civilization_pack_en.csv';raw=locale.read_bytes();bom=raw.startswith(b'\xef\xbb\xbf')
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline='')));columns=list(rows[0]);existing={r['ID']:r for r in rows}
    donor=list(csv.DictReader((source/'assets/locdb/Community_Civilization_Pack_Normal_en.csv').open(encoding='utf-8-sig',newline='')))
    for row in donor:
        if int(row['ID'])>=5000 or row['ID'] in ('1104','1105','1107','1109','1110','1111'):
            row=dict(row);row['Text']=row['Text'].replace('Community Civilization Pack Normal','Community Civilization Pack')
            assert row['ID'] not in existing or existing[row['ID']]==row,'Conflicting locale ID '+row['ID']
            if row['ID'] not in existing:rows.append(row);existing[row['ID']]=row
    existing['1002']['Text']='Community Civilization Pack.\\r\\n- Select China: choose China or Vietnam.\\r\\n- Select Delhi: choose Delhi or Persia.\\r\\n- 30-second choice; timeout keeps your original civilization.\\r\\nCredits: hosein81 and chilly5.'
    existing['1010']['Text']='Community Civilization Pack initialized. No eligible Chinese or Delhi human with the required tuning data was detected; ordinary civilizations remain active.'
    text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=columns,lineterminator='\r\n' if b'\r\n' in raw else '\n');writer.writeheader();writer.writerows(rows)
    locale.write_bytes((b'\xef\xbb\xbf' if bom else b'')+text.getvalue().encode('utf-8'))
    ledger=json.loads(translated((source/'docs/persia-import.json').read_bytes()))
    ledger['normal_source_guid']=NG;ledger['normal_source_head']=baseline['normal_head'];ledger['normal_input_sha256']=inputs
    save(ROOT/'docs/persia-import.json',ledger)
    save(OUT/'import.json',{'version':VERSION,'instances':len(inputs),'icons':27,'locale_rows':len(rows),'garrison_guid':GUID,'normal_inputs':inputs,'no_normal_edits':True})
    print('Imported Persia:',len(inputs),'instances;',len(rows),'locale rows')

def package():
    sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
    baseline=json.loads((OUT/'baseline.json').read_text())
    assert sha(baseline['archive'])==baseline['archive_sha256']
    work=Path(CFG['external_root'])/'staging/current/native'
    state=json.loads((work/'run.json').read_text())
    assert state['status']=='succeeded' and state['exit_code']==0,'A completed native burn is required'
    logs='\n'.join(p.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace') for p in (work/'logs').glob('*') if p.is_file())
    counts=re.findall(r'(\d+) instances validated',logs);assert counts and int(counts[-1])==658,counts
    assert 'EssenceEditor.exe Error:' not in logs
    expected_inputs=json.loads((OUT/'native-inputs.json').read_text())
    assert all(sha(ROOT/k)==v for k,v in expected_inputs.items()),'Source changed after burn started'
    natives=list((work/'output').rglob('*.sga'));assert len(natives)==1;native=natives[0];check(ROOT,native)
    listing=json.loads(run('native-list',[CFG['archive_tool'],'list',native,'--verify']))
    assert listing['archive']['verification']['verified']
    candidates=[m['path'] for m in listing['members']]
    private=[k for k in candidates if k.startswith('attrib/') and '/persia/' in k and k.endswith('.rgd')]
    icons=[k for k in candidates if k.startswith('ui/icons/persia/')]
    locales=[m['path'] for m in listing['members'] if m['toc']=='locale' and m['path'].endswith('.ucs')]
    assert len(private)==281 and len(icons)==27 and len(locales)==1,(len(private),len(icons),locales)
    payload=OUT/'payload';changes={}
    sys.path.insert(0,str(ROOT/'tools/compact'))
    from native_payloads import refresh_native_member
    for member in private+icons+locales:
        target=payload/member
        refresh_native_member(native,member,target,lambda archive,key,dest:
            run('native-member-'+str(len(changes)),[CFG['archive_tool'],'extract-member',archive,key,dest]))
        changes[member]=target
    scar={
        'scar/winconditions/vietnammode.scar':ROOT/'assets/scar/winconditions/VietnamMode.scar',
        'scar/vietnam/selection_core.scar':ROOT/'assets/scar/vietnam/selection_core.scar',
        'scar/vietnam/flooded_citadel.scar':ROOT/'assets/scar/vietnam/flooded_citadel.scar',
    }
    scar.update({'scar/persia/'+p.name:p for p in (ROOT/'assets/scar/persia').glob('*.scar')})
    changes.update(scar)
    expected=dict(baseline['members']);expected.update({k:sha(v) for k,v in changes.items()})
    current=Path(baseline['archive']);steps=[]
    for alias in ('attrib','data'):
        group={k:p for k,p in changes.items() if bool(k.startswith('attrib/'))==bool(alias=='attrib')}
        manifest=OUT/('members-'+alias+'.txt');manifest.write_bytes(''.join(k+'='+str(p)+'\n' for k,p in sorted(group.items())).encode('utf-8'))
        target=OUT/('attrib-current.sga' if alias=='attrib' else 'community_civilization_pack.sga')
        assert not target.exists(),'Current output already exists; verify/reuse it before rebuilding'
        run('assemble-'+alias,[CFG['archive_tool'],'set-members',current,manifest,target,'--alias',alias])
        current=target;steps.append({'alias':alias,'members':{k:{'path':str(p),'sha256':sha(p)} for k,p in sorted(group.items())}})
    check(ROOT,current)
    final_listing=json.loads(run('final-list',[CFG['archive_tool'],'list',current,'--verify']))
    mounts={m['path']:m['toc'] for m in final_listing['members']}
    assert final_listing['archive']['verification']['verified']
    assert all(mounts[k]==v for k,v in baseline['mounts'].items())
    assert all(v=='attrib' for k,v in mounts.items() if k.startswith('attrib/'))
    readback=ROOT/'.local/current-readback';readback.mkdir(parents=True,exist_ok=True)
    assert not any(readback.iterdir()),'Readback folder is not empty'
    run('fresh-extract',[CFG['archive_tool'],'extract',current,readback,'--filter','.'])
    actual={p.relative_to(readback).as_posix():sha(p) for p in readback.rglob('*') if p.is_file()}
    assert actual==expected,'Final member bytes differ from explicit delta'
    # Native compiled reference closure and identity collision checks.
    sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import rgd
    available={(k.split('/')[1],Path(k).stem) for k in actual if k.startswith('attrib/') and k.endswith('.rgd')}
    identities={};own_references=0
    for member in actual:
        if not (member.startswith('attrib/') and member.endswith('.rgd')):continue
        doc=rgd.read((readback/member).read_bytes())
        ids={n.value for _,n in rgd.flatten(doc.nodes) if n.key=='pbgid'}
        for identity in ids:
            assert identity not in identities or identities[identity]==member,('PBG collision',identity,member)
            identities[identity]=member
        for path,node in rgd.flatten(doc.nodes):
            if node.kind not in ('List','List2'):continue
            fields={n.key:n.value for n in node.value if n.kind not in ('List','List2')}
            name=fields.get('$PBGNAME','');category=fields.get('$PBGMAP','').split('\\')[0]
            if isinstance(name,str) and name.startswith(GUID+':'):
                assert (category,name.split(':',1)[1]) in available,(member,path,fields)
                own_references+=1
    original=json.loads((ROOT/'output/release_085/final-v2/garrison.json').read_text())
    original['members'][0]['sha256']=sha(current)
    original['details'].update(version=VERSION,updated='2026-10-26',summary='Adds Persia alongside Delhi while preserving Vietnam art, voices and gameplay.',description='Select China for China or Vietnam; select Delhi Sultanate for Delhi or Persia. One shared 30-second choice, defaulting to the original civilization. Full Persian roster with Divans, dynasties, Caravanserais, unique units and landmarks. Existing stock Persian visuals; complete new Persian art is the next milestone.',changelog='Functional Persia port and combined selection; preserves Garrison 0.8.8 Vietnam resources and extends the safe Flooded Citadel movement admission set.')
    save(OUT/'garrison.json',original)
    (OUT/'START-HERE.txt').write_text('Community Civilization Pack '+VERSION+'\n\nImport this ZIP into Garrison. Select its Tuning Pack and Vietnam Game Mode.\nSelect China for China/Vietnam or Delhi Sultanate for Delhi/Persia.\nUse a standard Dark Age human start. AI keeps its native civilization.\nExisting Persian stock visuals are retained; custom Persian art is the next milestone.\nSource/tests/native burn/archive/package checks are separate from game acceptance.\nFresh-match roster/landmarks/repair/save/load/multiplayer remain to be tested.\n',encoding='utf-8',newline='\n')
    package=OUT/('community_civilization_pack-'+VERSION+'.zip');assert not package.exists()
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in ('garrison.json','community_civilization_pack.sga','START-HERE.txt'):
            info=zipfile.ZipInfo(name,(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0x20
            with (OUT/name).open('rb') as src,z.open(info,'w') as dst:
                import shutil;shutil.copyfileobj(src,dst,1024*1024)
    assert package.stat().st_size<=400_000_000,'Owner notification required: 400 MB package limit exceeded'
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert sum(Path(n).name=='garrison.json' for n in z.namelist())==1
        with z.open('community_civilization_pack.sga') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(current)
    changed=sorted(k for k in baseline['members'] if expected[k]!=baseline['members'][k]);added=sorted(set(expected)-set(baseline['members']))
    proof={'version':VERSION,'zip_bytes':package.stat().st_size,'zip_sha256':sha(package),'sga_sha256':sha(current),'baseline_sga_sha256':baseline['archive_sha256'],'archive_identity':GUID,'member_sha256':actual,'mounts':mounts,'changed':changed,'added':added,'deleted':[],'unchanged_original_members':len(baseline['members'])-len(changed),'native_reference_compilation':True,'native_validated_instances':658,'resolved_own_references':own_references,'serialized_pbg_values':len(identities),'client_import':False,'native_match':False,'save_load':False,'multiplayer':False}
    save(OUT/'verification.json',proof);save(OUT/'delta.json',{'steps':steps,'native_archive_sha256':sha(native),'native_archive':str(native),'native_validated_instances':658,'source_hashes':expected_inputs})
    print('CURRENT_PACKAGE_VERIFIED',VERSION,len(actual),package.stat().st_size,sha(package),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    i=s.add_parser('import');i.add_argument('--source',type=Path,required=True)
    s.add_parser('package')
    a=p.parse_args()
    if a.command=='import':import_source(a.source.resolve())
    elif a.command=='package':package()

if __name__=='__main__':main()
