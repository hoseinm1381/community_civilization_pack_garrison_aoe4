"""Build strict diagnostic ZIPs over frozen 0.8.1, with one owning-resource edit."""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
check_storage(ROOT,CFG)
OUT=ROOT/'output/release_082_animation';DEST=OUT/'delivery-v1';DEST.mkdir(parents=True,exist_ok=False)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def run(label,args):
    p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
    (DEST/(label+'.log')).write_text(subprocess.list2cmdline(list(map(str,args)))+'\nEXIT '+str(p.returncode)+'\n'+p.stdout+p.stderr)
    assert p.returncode==0,(label,p.stderr)
    return p.stdout
base=ROOT/'output/release_081/delivery/final-v1';freeze=read(base/'verification.json');baseline=base/'community_civilization_pack.sga'
assert sha(baseline)==freeze['sga_sha256']=='a295752f63ad8bcf62b1ca323d0a60c1084d6f6c3c4f380ab52421324ca17a10'
assert sha(base/'community_civilization_pack-0.8.1.zip')==freeze['zip_sha256']=='75963810d5b241680fad90ff5b4c4f81cb0ba37f550c3b2e65b103f0250fd3e0'
sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
check(ROOT,baseline)
listing=json.loads(run('baseline-list',[CFG['archive_tool'],'list',baseline,'--verify']))
old_mounts={m['path']:m['toc'] for m in listing['members']}
assert set(old_mounts)==set(freeze['member_sha256'])
for name in ['normal.json','protected.json']:
    original=read(ROOT/'output/release_081/baseline'/name)
    assert all(sha(path)==wanted for path,wanted in original.items()),name
recipe=read(OUT/'integration-v2/recipe.json');encoded=read(OUT/'encoded-v3/receipt.json')
qa=read(OUT/'qa-v2/proof.json');assert qa['rig_bones']==45
assert qa['motions']['walk']['maximum_native_reference_world_ankle_target_stance_drift']<.01
for record in recipe['records']:assert sha(record['file'])==record['sha256']
attachment=recipe['attachment'];stem=recipe['new_animator']
allowed_new={stem+ext for ext in ['.rgm','.rgo','.rootmotion','.rhka']}
receipts=[]
for label,number in [('idle',1),('idle-walk',2)]:
    version='0.8.2-pilot.'+str(number);folder=DEST/label;folder.mkdir()
    proof=encoded[label];assert sha(proof['path'])==proof['sha256']
    assert all(c['independent_sample_readback'] for c in proof['clips'])
    payload={r['member']:r['file'] for r in recipe['records']};payload[stem+'.rhka']=proof['path']
    assert set(payload)==allowed_new|{attachment}
    mapping=folder/'members.txt';mapping.write_text('\n'.join(member+'='+str(path) for member,path in payload.items())+'\n')
    final=folder/'community_civilization_pack.sga'
    run(label+'-assemble',[CFG['archive_tool'],'set-members',baseline,mapping,final,'--alias','data'])
    check(ROOT,final)
    final_listing=json.loads(run(label+'-verify',[CFG['archive_tool'],'list',final,'--verify']))
    mounts={m['path']:m['toc'] for m in final_listing['members']}
    assert all(mounts[path]==toc for path,toc in old_mounts.items())
    assert all(mounts[path]=='data' for path in allowed_new)
    back=folder/'readback';run(label+'-readback',[CFG['archive_tool'],'extract',final,back,'--filter','.'])
    actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()}
    expected=dict(freeze['member_sha256']);expected.update({name:sha(path) for name,path in payload.items()})
    assert actual==expected
    changed={k for k in freeze['member_sha256'] if actual[k]!=freeze['member_sha256'][k]}
    assert changed=={attachment}
    assert set(actual)-set(freeze['member_sha256'])==allowed_new
    assert not set(freeze['member_sha256'])-set(actual)
    manifest=read(base/'garrison.json');assert manifest['bundle_key']=='community_civilization_pack'
    manifest['details'].update(version=version,updated='2026-10-24',summary='Buffalo native '+label+' animation qualification trial.',
        description='Diagnostic candidate: new buffalo idle'+(' and planted walking cycle' if number==2 else '')+'. Existing model, gameplay, other animation clips, Ministry and normal edition preserved. Native in-game acceptance pending.',
        changelog='Private cattle animator and independently decoded native motion. Test idle candidate first; then test idle+walk in a fresh game process. No installation or publication performed.')
    manifest['members'][0]['sha256']=sha(final)
    (folder/'garrison.json').write_text(json.dumps(manifest,indent=2)+'\n')
    instructions=('Community Civilization Pack '+version+' — BUFFALO ANIMATION TRIAL\n'
        'Import this ZIP manually in Garrison. Same bundle/GUID as 0.8.1; enable only one version.\n'
        'Restart the game after changing candidates; select this tuning pack and the Vietnam game mode. Use a fresh match.\n'
        'Test order: pilot.1 (idle only), then pilot.2 (idle + walk) after accepting idle.\n'
        'Idle: watch the head/neck lower, ears flick, and tail sway; move, stop, and check that idle resumes.\n'
        'Walk candidate: order a long ordinary walk, turn, stop/restart; check the four-leg gait, planted hooves and pack stability.\n'
        'Only navigation\\idle_01'+(' and navigation\\walk_01' if number==2 else '')+' are replaced. Other idle variants, trot/run, work and death remain native.\n'
        'Check two player colours, near/far LODs, Paddy Work/Leave, death and the Ministry herd.\n'
        'Offline encoding, native decoder readback, source deformation, archive identity, member preservation and ZIP checks passed.\n'
        'Native game playback/transitions, client import, save/load and multiplayer are not verified.\n'
        'Rollback: re-import the preserved original 0.8.1 ZIP and restart the game.\n'
        'Credits: hosein81 and chilly5.\n')
    (folder/'START-HERE.txt').write_text(instructions,encoding='utf-8')
    package=folder/('community_civilization_pack-'+version+'.zip')
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in [folder/'garrison.json',final,folder/'START-HERE.txt']:archive.write(path,path.name)
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())=={'garrison.json','community_civilization_pack.sga','START-HERE.txt'}
        assert json.loads(archive.read('garrison.json'))['details']['version']==version
        with archive.open(final.name) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha(final)
    receipt={'version':version,'zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),
             'baseline_sga_sha256':sha(baseline),'changed':sorted(changed),'added':sorted(allowed_new),'deleted':[],
             'untouched_original_members_exact':len(freeze['member_sha256'])-1,'all_original_mounts_exact':True,
             'archive_identity':final_listing['archive']['name'],'encoder':proof,'member_sha256':actual,
             'root_motion_rgo_events_skeletons_preserved':True,'normal_and_protected_081_inputs_unchanged':True,
             'native_model_cook':'existing 0.8.1 geometry unchanged; new motions written directly as native RHKA, no FBX or XML burn',
             'native_runtime':False,'client_import':False,'save_load':False,'multiplayer':False,'installed':False,'published':False}
    (folder/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');receipts.append(receipt)
    print('CANDIDATE_PACKAGE_VERIFIED',version,str(package),flush=True)
(DEST/'receipts.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='member_sha256'} for r in receipts],indent=2))
