"""Verified narrow 087 typed overlay on accepted 086; compact in-place delivery."""
import copy,gzip,hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/release_085';DEST=OUT/'final-v2'
cfg=json.loads((ROOT/'workspace.json').read_text());sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
TOWER='attrib/ebps/vietnam/buildings/landmarks/feudal/vn_building_landmark_age1_gatehouse_control_chi.rgd'
DONOR='attrib/ebps/vietnam/buildings/hideouts/vn_building_defense_outpost_chi.rgd'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def run(label,args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace')
 (OUT/('087-'+label+'.log')).write_text('EXIT '+str(p.returncode)+'\n'+p.stdout+'\n'+p.stderr,encoding='utf-8')
 if p.returncode:raise RuntimeError(label)
 return p.stdout
def get(archive,member,filename):
 target=OUT/'087-inputs'/filename
 if not target.exists():run('extract-'+filename,[cfg['archive_tool'],'extract-member',archive,member,target])
 return target
def mapping(doc):return dict(rgd.flatten(doc.nodes))
def main():
 check_storage(ROOT,cfg)
 prior=json.loads((DEST/'verification.json').read_text());assert prior['version']=='0.8.6'
 archive=DEST/'community_civilization_pack.sga';oldzip=DEST/'community_civilization_pack-0.8.6.zip'
 assert sha(archive)==prior['sga_sha256'] and sha(oldzip)==prior['zip_sha256'];check(ROOT,archive)
 native=json.loads((OUT/'087-native-reference.json').read_text());assert native['native_compile'];reference=Path(native['archive'])
 freeze=json.loads((OUT/'087-native-input-freeze.json').read_text())
 assert all(sha(ROOT/k)==v and sha(Path(freeze['staged_root'])/k)==v for k,v in freeze['files'].items())
 allow=sorted([TOWER,*[m for m in prior['member_sha256'] if m.startswith('attrib/sbps/vietnam/units/ranged/skirmishers/')]])
 assert len(allow)==7
 donor=rgd.read(get(archive,DONOR,'donor-hideout.rgd').read_bytes());dm=mapping(donor)
 assert sha(OUT/'087-inputs/donor-hideout.rgd')==prior['member_sha256'][DONOR]
 payload=OUT/'087-payload';payload.mkdir(exist_ok=False);changes=[];expected=dict(prior['member_sha256'])
 with zipfile.ZipFile(OUT/'086-replaced-rgd-rollback.zip','x',zipfile.ZIP_DEFLATED,compresslevel=9) as rollback:
  for member in allow:
   orig=get(archive,member,'before-'+member.replace('/','__'));original=orig.read_bytes();assert sha(orig)==prior['member_sha256'][member]
   rollback.writestr(member,original)
   doc=rgd.read(original);before=copy.deepcopy(doc);index=mapping(doc)
   ref=rgd.read(get(reference,member,'native-'+sha(reference)[:12]+'-'+member.replace('/','__')).read_bytes());rm=mapping(ref)
   log=[]
   if member==TOWER:
    for variant in ('default','campaign'):
     root=index[variant];assert not any(n.key=='resource_drop_off_ext' for n in root.value)
     added=copy.deepcopy(dm[variant+'/resource_drop_off_ext'])
     # Actual fresh native compilation agrees with the working Hideout contract.
     assert added==rm[variant+'/resource_drop_off_ext']
     root.value.append(added);log.append({'op':'append','path':variant+'/resource_drop_off_ext'})
     tags=index[variant+'/type_ext/unit_type_list'];oldvalues=[n.value for n in tags.value]
     for value in ('resource_drop_off','economy_building'):
      assert value not in oldvalues
      dn=copy.deepcopy(next(n for n in dm[variant+'/type_ext/unit_type_list'].value if n.value==value))
      assert dn in rm[variant+'/type_ext/unit_type_list'].value
      tags.value.append(dn);log.append({'op':'append','path':variant+'/type_ext/unit_type_list','value':value})
   else:
    for path,node in index.items():
     if path.endswith('/squad_ui_ext/race_list/race_data/info/selection_group'):
      assert node.kind=='CString' and node.value=='archer'
      assert rm[path].value=='vn_skirmisher'
      node.value='vn_skirmisher';log.append({'op':'set','path':path,'before':'archer','after':'vn_skirmisher'})
    assert len(log)==(1 if 'vn_tower_train_' in member else 2)
   encoded=rgd.write(doc);reread=rgd.read(encoded);ri=mapping(reread)
   # Undo ONLY the logged narrow edits on the serialized readback, prove every other byte exact.
   for row in reversed(log):
    if row['op']=='set':ri[row['path']].value=row['before']
    elif row['path'].endswith('/resource_drop_off_ext'):
     root=ri[row['path'].split('/')[0]];root.value.remove(ri[row['path']])
    else:
     tail=ri[row['path']].value.pop();assert tail.value==row['value']
   assert reread.nodes==before.nodes,member+' failed structural undo'
   # The codec retains newly registered dictionary keys after node removal.
   # Restore only that dictionary metadata before proving exact original bytes.
   reread.keys=copy.deepcopy(before.keys)
   assert rgd.write(reread)==original,member+' failed exact byte undo'
   target=payload/(member.replace('/','__'));target.write_bytes(encoded);expected[member]=sha(target)
   changes.append({'member':member,'file':str(target),'before_sha256':prior['member_sha256'][member],'after_sha256':sha(target),'changes':log,'exact_byte_undo':True})
 save(OUT/'087-typed-deltas.json',{'baseline_sga_sha256':prior['sga_sha256'],'native_reference':native,'changes':changes})
 members=OUT/'087-members.txt';members.write_text(''.join(c['member']+'='+c['file']+'\n' for c in changes),encoding='utf-8')
 candidate=DEST/'087-candidate.sga';assert not candidate.exists()
 run('assemble',[cfg['archive_tool'],'set-members',archive,members,candidate,'--alias','data']);check(ROOT,candidate)
 listing=json.loads(run('list',[cfg['archive_tool'],'list',candidate,'--verify']));mounts={m['path']:m['toc'] for m in listing['members']};assert mounts==prior['mounts']
 with tempfile.TemporaryDirectory(prefix='garrison087-') as tmp:
  folder=Path(tmp).resolve();assert folder.is_relative_to(Path(tempfile.gettempdir()).resolve()) and folder.name.startswith('garrison087-')
  run('fresh-extract',[cfg['archive_tool'],'extract',candidate,folder,'--filter','.'])
  actual={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()};assert actual==expected
 manifest=json.loads((DEST/'garrison.json').read_text());manifest['members'][0]['sha256']=sha(candidate)
 manifest['details'].update(version='0.8.7',updated='2026-10-25',summary='PhÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¢ Minh Tower resource drop-off and separate Skirmisher selection group.',description='PhÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¢ Minh Tower accepts food, wood, gold and stone like the Hideout. Skirmishers have their own selection group across all ages and tower-trained variants. Existing voices, independent cooldowns, artwork and other gameplay are preserved.',changelog='Fixed PhÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¢ Minh Tower resource drop-off and Skirmisher selection grouping.')
 staged=DEST/'087-garrison.json';save(staged,manifest)
 note=DEST/'087-START-HERE.txt';note.write_text('Garrison 0.8.7\n\nImport this ordinary Garrison ZIP and select its Tuning Pack and Vietnam Game Mode.\nPhÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¢ Minh Tower accepts food, wood, gold and stone like the Hideout. Skirmishers use their own selection group at every age, including tower-trained squads.\nExisting compressed dialogue, per-unit cooldowns, pain/death sounds and artwork remain unchanged.\nSource regressions, fresh official inheritance audit, real Content Editor reference compilation, typed delta preservation and full archive/ZIP proof passed. Import, native drop-off pathing, mixed-selection UI, save/load and multiplayer remain game acceptance gates.\n',encoding='utf-8')
 package=DEST/'community_civilization_pack-0.8.7.zip'
 with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path,name in ((staged,'garrison.json'),(candidate,'community_civilization_pack.sga'),(note,'START-HERE.txt')):z.write(path,name)
 size=package.stat().st_size
 assert size<=400_000_000,'NOTIFY USER: 400 MB exceeded; old release retained'
 with zipfile.ZipFile(package) as z:
  assert z.testzip() is None and set(z.namelist())=={'garrison.json','community_civilization_pack.sga','START-HERE.txt'}
  with z.open('community_civilization_pack.sga') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(candidate)
  assert z.read('garrison.json')==staged.read_bytes()
 proof=dict(version='0.8.7',zip_bytes=size,zip_sha256=sha(package),sga_sha256=sha(candidate),baseline_sga_sha256=prior['sga_sha256'],archive_identity=listing['archive']['name'],member_sha256=actual,mounts=mounts,changed=allow,added=[],deleted=[],all_audio_art_scar_members_byte_identical=True,voice_regeneration=False,native_source_reference_compilation=True,native_validated_instances=native['validated_instances'],native_import=False,native_drop_off=False,native_selection_ui=False,save_load=False,multiplayer=False,output_folder_reused=True)
 staged_proof=DEST/'087-verification.json';save(staged_proof,proof)
 for filename in ('verification.json','garrison.json','START-HERE.txt'):
  backup=DEST/('086-'+filename+'.gz');assert not backup.exists();backup.write_bytes(gzip.compress((DEST/filename).read_bytes(),mtime=0))
 # Replace only after all proof passed. Retain 084 independent rollback + compact 086 deltas.
 candidate.replace(archive);staged.replace(DEST/'garrison.json');note.replace(DEST/'START-HERE.txt');staged_proof.replace(DEST/'verification.json')
 assert sha(archive)==proof['sga_sha256'] and sha(package)==proof['zip_sha256'];check(ROOT,archive)
 oldzip.unlink();print('087_VERIFIED_REPLACEMENT',size,proof['zip_sha256'],flush=True)
if __name__=='__main__':main()
