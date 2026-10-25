"""Assemble an explicit seven-family selection over immutable 0.7.4 bytes."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'tools/release_073'))
from workspace_support import check_storage
from check_identity import check as identity
from verify_preservation import check as preserved
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(selection,label):
 assert re.fullmatch('[a-z0-9-]{1,16}',label)
 check_storage(ROOT,CFG);preserved();identity(ROOT)
 selected=json.loads(selection.read_text());families={'citadel','hq','ministry','pho_minh','one_pillar','garden','foundry'}
 assert set(selected['models'])==families
 assert set(selected['sources'])==families
 base=ROOT/'output/release_075/baseline/community_civilization_pack.sga';before=json.loads((ROOT/'output/release_075/baseline/package-members.json').read_text())
 assert sha(base)==before['sga_sha256']
 out=ROOT/'output/release_075/candidates'/label
 if out.exists():raise FileExistsError('Retain prior candidates')
 payload={};recipes={}
 def add(member,file,digest):
  assert sha(file)==digest,(member,'payload drift')
  if member in payload:assert payload[member]['sha256']==digest
  payload[member]={'file':str(file),'sha256':digest}
 for family,path in selected['models'].items():
  p=Path(path);r=json.loads(p.read_text());assert r['family']==family and r['status']=='isolated_payload_static_checks_passed_runtime_unverified'
  final=selected['sources'][family]
  blend=Path(final['blend']);assert sha(blend)==final['blend_sha256'],(family,'editable source drift')
  cook_path=Path(final['cook_receipt']);assert sha(cook_path)==r['cook_receipt_sha256'],(family,'payload cook provenance')
  cook=json.loads(cook_path.read_text());assert cook['family']==family and cook['status']=='fresh_native_cook_and_readback_complete_runtime_unverified'
  freeze_path=cook_path.parent/'input-freeze.json';assert sha(freeze_path)==cook['input_freeze_sha256']
  freeze=json.loads(freeze_path.read_text());exports=Path(final['export_directory'])
  assert exports.resolve()==Path(freeze['source']).resolve(),(family,'wrong export revision')
  assert freeze['hashes']==final['export_sha256'],(family,'final export selection differs from native cook')
  assert all(sha(exports/n)==h for n,h in final['export_sha256'].items()),(family,'export drift')
  assert sha(Path(cook['archive']))==cook['archive_sha256'],(family,'native cook archive drift')
  recipes[str(cook_path)]=sha(cook_path);recipes[str(freeze_path)]=sha(freeze_path)
  recipes[str(p)]=sha(p)
  for m in r['members']:add(m['member'],Path(m['file']),m['sha256'])
 flags=Path(selected['flags']);r=json.loads(flags.read_text());assert r['status']=='native_stamp_compile_and_readback_complete_runtime_unverified'
 expected_flags={f'art/stamps/garrison/cc075flags/{f}_owner_flag.bin' for f in families}
 assert len(r['members'])==7 and {m['member'] for m in r['members']}==expected_flags
 placements=Path(selected['flag_placements']);assert sha(placements)==r['placements_sha256']==selected['flag_placements_sha256']
 poses=json.loads(placements.read_text());assert set(poses)==families
 for family,pose in poses.items():
  assert sha(Path(pose['support_evidence']))==pose['support_evidence_sha256'],(family,'flag support evidence drift')
  assert pose['contact_verified'] is True and abs(pose['contact_error'])<.0001
 recipes[str(flags)]=sha(flags);recipes[str(placements)]=sha(placements)
 for m in r['members']:add(m['member'],Path(m['file']),m['sha256'])
 prep=ROOT/'output/release_075/owner_colour/preparation-v2.json';p=json.loads(prep.read_text());recipes[str(prep)]=sha(prep)
 for m in p['attachment_candidates']:
  assert m['removal_restores_exact_original'] is True
  add(m['member'],Path(m['file']),m['after_sha256'])
 # Only the enumerated private bodies, new private textures, seven visual lists
 # and seven flag stamps are permitted. No actor or existing lifecycle RGO.
 graph=json.loads((ROOT/'output/release_075/inspection/current-consumers.json').read_text())
 allowed_models={s+ext for f in families for s in graph['families'][f]['all_variant_models'] for ext in ('.rgm','.rrgeom','.rrmaterial')}
 allowed_lists=set(p['allowed_changed_members']);allowed_stamps=set(p['allowed_added_members'])
 for member in payload:
  assert member in allowed_models|allowed_lists|allowed_stamps or (member.startswith('art/scenario/cc075/') and member.endswith('.rrtex')),member
 out.mkdir(parents=True)
 (out/'recipe-freeze.json').write_text(json.dumps({'selection':str(selection),'selection_sha256':sha(selection),'recipes':recipes,'payload':payload},indent=2)+'\n')
 def run(name,args):
  command=list(map(str,args))
  try:p=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=900)
  except subprocess.TimeoutExpired as error:
   def decoded(value):return value.decode('utf-8','replace') if isinstance(value,bytes) else (value or '')
   (out/(name+'.log')).write_text('COMMAND '+subprocess.list2cmdline(command)+'\nTIMEOUT 900 seconds\n'+decoded(error.stdout)+'\n'+decoded(error.stderr),encoding='utf-8')
   raise
  (out/(name+'.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');assert p.returncode==0,(name,p.returncode)
  return p.stdout
 mapping=out/'members.txt';mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(payload.items()))+'\n',encoding='utf-8')
 sga=out/'community_civilization_pack.sga';run('assemble',[CFG['archive_tool'],'set-members',base,mapping,sga,'--alias','data'])
 listing=json.loads(run('verify',[CFG['archive_tool'],'list',sga,'--verify']));assert listing['archive']['verification']['verified'];identity(ROOT,sga)
 mounts={m['path']:m['toc'] for m in listing['members']};expected=dict(before['member_sha256']);expected.update({k:v['sha256'] for k,v in payload.items()})
 assert set(mounts)==set(expected) and all(mounts[k]==v for k,v in before['mounts'].items())
 assert all(mounts[k]=='data' for k in set(expected)-set(before['member_sha256']))
 back=out/'readback';run('readback',[CFG['archive_tool'],'extract',sga,back,'--filter',''])
 actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()};assert actual==expected
 changed=sorted(k for k,v in before['member_sha256'].items() if expected[k]!=v);added=sorted(set(expected)-set(before['member_sha256']))
 assert set(changed)<=set(payload);assert all(k in allowed_models|allowed_lists for k in changed)
 preserved();assert sha(base)==before['sga_sha256']
 manifest=json.loads((ROOT/'output/release_074/delivery/garrison.json').read_text())
 manifest['members'][0]['sha256']=sha(sga)
 manifest['details'].update(version='0.7.5',updated='2026-10-23',summary='Seven Vietnamese building visual upgrade candidate.',description='Revised editable building art and native stock owner-colour flag attachments. Gameplay and unrelated packaged resources preserved from 0.7.4. Visual target and native acceptance remain pending.',changelog='Visual revisions to Ministry, Pho Minh, One Pillar, Citadel, Headquarters, Garden and Foundries. Native import, two player colours and full building lifecycle tests required.')
 (out/'garrison.json').write_text(json.dumps(manifest,indent=2)+'\n')
 evidence={'version':'0.7.5','status':'verified_package_review_candidate','baseline_sga_sha256':before['sga_sha256'],'sga_sha256':sha(sga),'archive_namespace':listing['archive']['name'],'changed_members':changed,'added_members':added,'unchanged_members':len(before['member_sha256'])-len(changed),'unchanged_original_mounts':True,'gameplay_actor_bytes_unchanged':True,'native_import_tested':False,'native_match_tested':False,'visual_9_to_10_target_accepted':False,'member_sha256':actual,'mounts':mounts}
 (out/'verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
 package=out/'community_civilization_pack-0.7.5.zip'
 with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.write(out/'garrison.json','garrison.json');z.write(sga,sga.name)
  z.writestr('START-HERE.txt','Community Civilization Pack 0.7.5 review candidate\nCredits: hosein81 and chilly5\n\nKeep 0.7.4 for rollback. Import this ZIP into Garrison; select the pack as both Game Mode and Tuning Pack, then China and Vietnam.\nThis package is not a claim of native testing or achievement of the 9–10 visual target.\n')
  z.write(ROOT/'docs/RELEASE_075_NATIVE_ACCEPTANCE.md','NATIVE-ACCEPTANCE.md')
  z.writestr('EVIDENCE.json',json.dumps({k:v for k,v in evidence.items() if k not in ('member_sha256','mounts')},indent=2)+'\n')
 with zipfile.ZipFile(package) as z:
  assert z.testzip() is None and len(z.namelist())==5
  assert hashlib.sha256(z.read(sga.name)).hexdigest()==sha(sga)
  assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.5'
 (out/'delivery-proof.json').write_text(json.dumps({'zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(sga),'zip_bytes':package.stat().st_size,'verified':True},indent=2)+'\n');print(package)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('selection',type=Path);p.add_argument('--label',default='review-v1');a=p.parse_args();main(a.selection,a.label)
