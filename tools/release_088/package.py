"""Narrow 088: guard Flooded Citadel speed probes and add native Phá»• Minh return interaction."""
import copy,gzip,hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/release_085';DEST=OUT/'final-v2';CFG=json.loads((ROOT/'workspace.json').read_text());sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import rgd
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
TOWER='attrib/ebps/vietnam/buildings/landmarks/feudal/vn_building_landmark_age1_gatehouse_control_chi.rgd';SCAR='scar/vietnam/flooded_citadel.scar'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def run(label,args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace');(OUT/('088-'+label+'.log')).write_text('EXIT '+str(p.returncode)+'\n'+p.stdout+'\n'+p.stderr,encoding='utf-8');assert p.returncode==0,label;return p.stdout
def fields(node):return {n.key:n for n in node.value}
def main():
 check_storage(ROOT,CFG);prior=json.loads((DEST/'verification.json').read_text());assert prior['version']=='0.8.7'
 archive=DEST/'community_civilization_pack.sga';oldzip=DEST/'community_civilization_pack-0.8.7.zip';assert sha(archive)==prior['sga_sha256'] and sha(oldzip)==prior['zip_sha256'];check(ROOT,archive)
 native=json.loads((OUT/'088-native-reference.json').read_text());assert native['native_compile'];reference=Path(native['archive']);freeze=json.loads((OUT/'088-native-input-freeze.json').read_text());assert all(sha(ROOT/k)==v for k,v in freeze['files'].items() if k!='assets/scar/vietnam/flooded_citadel.scar')
 # Native evidence owns the unchanged tuning input; current SCAR has independent Lua/static proof.
 save(OUT/'088-scar-reference-delta.json',{'native_staged_scar_sha256':freeze['files']['assets/scar/vietnam/flooded_citadel.scar'],'final_scar_sha256':sha(ROOT/'assets/scar/vietnam/flooded_citadel.scar'),'native_tuning_inputs_unchanged':True,'native_scar_execution_claimed':False})
 payload=OUT/'088-payload';payload.mkdir(exist_ok=False)
 before=payload/'before-tower.rgd';compiled=payload/'native-tower.rgd'
 run('extract-before',[CFG['archive_tool'],'extract-member',archive,TOWER,before]);run('extract-native',[CFG['archive_tool'],'extract-member',reference,TOWER,compiled])
 raw=before.read_bytes();assert sha(before)==prior['member_sha256'][TOWER];doc=rgd.read(raw);original=copy.deepcopy(doc);index=dict(rgd.flatten(doc.nodes));native_index=dict(rgd.flatten(rgd.read(compiled.read_bytes()).nodes));delta=[]
 for v in ('default','campaign'):
  path=v+'/interactive_object_ext/type_list';target=index[path]
  assert not any(fields(n)['interaction_type'].value=='resource_drop_off' for n in target.value)
  candidate=[n for n in native_index[path].value if fields(n)['interaction_type'].value=='resource_drop_off'];assert len(candidate)==1
  added=copy.deepcopy(candidate[0]);target.value.append(added);delta.append({'op':'append','path':path,'interaction_type':'resource_drop_off'})
 encoded=rgd.write(doc);back=rgd.read(encoded);bi=dict(rgd.flatten(back.nodes))
 for row in delta:
  node=bi[row['path']].value.pop();assert fields(node)['interaction_type'].value=='resource_drop_off'
 assert back.nodes==original.nodes;back.keys=original.keys;assert rgd.write(back)==raw
 modified=payload/'pho-minh.rgd';modified.write_bytes(encoded);source=ROOT/'assets'/SCAR
 oldscar=payload/'before-flooded.scar';run('extract-old-scar',[CFG['archive_tool'],'extract-member',archive,SCAR,oldscar]);assert sha(oldscar)==prior['member_sha256'][SCAR]
 with zipfile.ZipFile(OUT/'088-replaced-members-087.zip','x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.write(before,TOWER);z.write(oldscar,SCAR)
 changes={TOWER:modified,SCAR:source};save(OUT/'088-typed-deltas.json',{'baseline_sga_sha256':prior['sga_sha256'],'changed_members':{k:{'file':str(p),'sha256':sha(p)} for k,p in changes.items()},'tower_changes':delta,'tower_exact_byte_undo':True})
 expected=dict(prior['member_sha256']);expected.update({k:sha(p) for k,p in changes.items()})
 members=OUT/'088-members.txt';members.write_text(''.join(k+'='+str(p)+'\n' for k,p in changes.items()),encoding='utf-8')
 candidate=DEST/'088-candidate.sga';assert not candidate.exists();run('assemble',[CFG['archive_tool'],'set-members',archive,members,candidate,'--alias','data']);check(ROOT,candidate)
 listing=json.loads(run('list',[CFG['archive_tool'],'list',candidate,'--verify']));mounts={m['path']:m['toc'] for m in listing['members']};assert mounts==prior['mounts']
 with tempfile.TemporaryDirectory(prefix='ccp088-readback-') as tmp:
  run('fresh-extract',[CFG['archive_tool'],'extract',candidate,tmp,'--filter','.']);folder=Path(tmp);actual={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()};assert actual==expected
 manifest=json.loads((DEST/'garrison.json').read_text());manifest['members'][0]['sha256']=sha(candidate);manifest['details'].update(version='0.8.8',updated='2026-10-26',summary='Flooded Citadel crash guard and Phá»• Minh resource-return interaction.',description='Prevents unsupported visual/attachment blueprints from reaching the Flooded Citadel speed accessor. Preserves the 30% slow, footprint/range and lifecycle. Adds the native resource-return interaction to Phá»• Minh Tower. Art, compressed audio, selection grouping and per-unit voice cooldowns remain unchanged.',changelog='Fixed Flooded Citadel moving_ext fatal SCAR error and added explicit Phá»• Minh resource drop-off interaction.')
 staged=DEST/'088-garrison.json';save(staged,manifest);note=DEST/'088-START-HERE.txt';note.write_text('Garrison 0.8.8\n\nImport this ordinary Garrison ZIP and select its Tuning Pack and Vietnam Game Mode.\nFlooded Citadel now probes speed only for blueprints verified to have moving_ext. Phá»• Minh Tower has the native resource-return interaction in default/campaign.\nThe slow remains 30% with the same range. All art, compressed voices, independent cooldowns and Skirmisher selection groups remain unchanged.\nOffline regressions, current inheritance checks, real native reference compilation, typed narrow preservation and complete archive/ZIP proof passed. Fresh-game Castle landmark activation and Phá»• Minh food/wood/gold/stone return still require native acceptance; save/load and multiplayer remain separate.\n',encoding='utf-8')
 package=DEST/'community_civilization_pack-0.8.8.zip'
 with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path,name in ((staged,'garrison.json'),(candidate,'community_civilization_pack.sga'),(note,'START-HERE.txt')):
   info=zipfile.ZipInfo(name,(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0x20;z.writestr(info,path.read_bytes(),compresslevel=6)
 size=package.stat().st_size;assert size<=400_000_000,'NOTIFY OWNER: 400 MB ZIP limit exceeded; prior release preserved'
 with zipfile.ZipFile(package) as z:
  assert z.testzip() is None and set(z.namelist())=={'garrison.json','community_civilization_pack.sga','START-HERE.txt'}
  with z.open('community_civilization_pack.sga') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(candidate)
 proof={'version':'0.8.8','zip_bytes':size,'zip_sha256':sha(package),'sga_sha256':sha(candidate),'baseline_sga_sha256':prior['sga_sha256'],'archive_identity':listing['archive']['name'],'member_sha256':actual,'mounts':mounts,'changed':sorted(changes),'added':[],'deleted':[],'all_audio_art_and_other_members_byte_identical':True,'native_reference_compilation':True,'native_validated_instances':native['validated_instances'],'client_import':False,'citadel_runtime':False,'drop_off_runtime':False,'save_load':False,'multiplayer':False,'output_folder_reused':True}
 for name in ('verification.json','garrison.json','START-HERE.txt'):
  backup=DEST/('087-'+name+'.gz');assert not backup.exists();backup.write_bytes(gzip.compress((DEST/name).read_bytes(),mtime=0))
 candidate.replace(archive);staged.replace(DEST/'garrison.json');note.replace(DEST/'START-HERE.txt');save(DEST/'verification.json',proof)
 assert sha(archive)==proof['sga_sha256'] and sha(package)==proof['zip_sha256'];check(ROOT,archive);oldzip.unlink();print('088_DELIVERED',size,proof['zip_sha256'],flush=True)
if __name__=='__main__':main()
