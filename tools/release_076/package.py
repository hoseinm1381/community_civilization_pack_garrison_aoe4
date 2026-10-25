"""Build 0.7.6 from an explicit completed baseline and verified visual recipe."""
import argparse,zipfile,re,copy
from common import *
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check as identity
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd

def main(recipe,label):
 guard();assert re.fullmatch('[a-z0-9-]{1,20}',label)
 r=read(recipe);base=Path(r['baseline']);assert sha(base)==r['baseline_sha256'];identity(ROOT,base)
 qualification=recipe.parent/'qualification/proof.json';q=read(qualification)
 assert q['status']=='current_official_provenance_and_selector_checks_passed' and q['recipe_sha256']==sha(recipe)
 before=read(base.parent/'verification.json');assert before['sga_sha256']==r['baseline_sha256']
 manifest=Path(r['art_manifest']);assert sha(manifest)==r['art_manifest_sha256'];m=read(manifest)
 for a in m['assets']:
  e=a['source_export'];assert sha(e['source'])==e['source_sha256']
  for name,digest in e['files'].items():assert sha(Path(e['export'])/name)==digest
  d=a['decode'];assert sha(d['manifest'])==d['sha256'] and not d['blockers'] and not d['missing_textures']
 cook=read(OUT/'cooks'/m['cook_label']/'receipt.json');assert sha(cook['archive'])==cook['archive_sha256']
 existing=set(before['member_sha256']);payload=r['payload'];patchmap={p['member']:p for p in r['patches']}
 expected_changes={f'attrib/ebps/vietnam/units/ranged/skirmishers/vn_unit_skirmisher_{a}_vit.rgd' for a in (2,3,4)}|{f'attrib/weapon/vietnam/vn_weapon_skirmisher_{a}_vit.rgd' for a in (2,3,4)}|{'attrib/ebps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.rgd'}
 assert set(payload)&existing==expected_changes
 for member,row in payload.items():
  assert sha(row['file'])==row['sha256']
  assert member in expected_changes or member.startswith('art/scenario/garrison/cc076/') or re.fullmatch(r'attrib/(attachments/attachment_lists|ebps)/vietnam/release_076/vn076_[a-z0-9_]+\.rgd',member)
  if member in expected_changes:
   p=patchmap[member];assert p['donor_sha256']==before['member_sha256'][member]
   doc=rgd.read(Path(row['file']).read_bytes())
   for e in reversed(p['changes']):
    assert e['kind']=='CString' and e['path'].endswith('/$PBGNAME')
    n=rgd.find(doc.nodes,e['path']);assert n.value==e['after'];n.value=e['before']
   assert hashlib.sha256(rgd.write(doc)).hexdigest()==p['donor_sha256']
 # All private PBG references resolve by category and basename in the selected final set.
 allrgds={member:(Path(payload[member]['file']) if member in payload else base.parent/'readback'/member) for member in existing|set(payload) if member.endswith('.rgd')}
 names={}
 for member,p in allrgds.items():
  category='attachments\\attachment_lists' if member.startswith('attrib/attachments/attachment_lists/') else member.split('/')[1]
  names[(category,p.stem)]=member
 guid=CFG['project_guid'].replace('-','');private=[]
 for member,row in payload.items():
  if not member.endswith('.rgd'):continue
  doc=rgd.read(Path(row['file']).read_bytes())
  for path,node in rgd.flatten(doc.nodes):
   if node.kind=='CString' and node.key=='$PBGNAME' and node.value.startswith(guid+':'):
    mapping=rgd.find(doc.nodes,path.rsplit('/',1)[0]+'/$PBGMAP').value
    name=node.value.split(':',1)[1];assert (mapping,name) in names,(member,path,mapping,name)
    private.append({'consumer':member,'path':path,'target':names[mapping,name]})
 out=OUT/'delivery'/label
 if out.exists():raise FileExistsError('Preserve earlier delivery')
 out.mkdir(parents=True)
 write(out/'build-inputs.json',{'recipe_sha256':sha(recipe),'qualification_sha256':sha(qualification),'python':sys.executable,'tools':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'tools/release_076').glob('*.py')},'baseline_sha256':r['baseline_sha256'],'art_manifest_sha256':sha(manifest)})
 def runhere(name,args):return run(name,args,out/'logs')
 mapping=out/'members.txt';mapping.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(payload.items()))+'\n')
 sga=out/'community_civilization_pack.sga'
 runhere('assemble',[CFG['archive_tool'],'set-members',base,mapping,sga,'--alias','data']);identity(ROOT,sga)
 listing=json.loads(runhere('list',[CFG['archive_tool'],'list',sga,'--verify']));mounts={x['path']:x['toc'] for x in listing['members']}
 expected=dict(before['member_sha256']);expected.update({k:v['sha256'] for k,v in payload.items()})
 assert set(expected)==set(mounts)
 assert all(mounts[k]==v for k,v in before['mounts'].items())
 assert all(mounts[k]=='data' for k in set(expected)-existing)
 back=out/'readback';runhere('extract',[CFG['archive_tool'],'extract',sga,back,'--filter',''])
 actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()};assert actual==expected
 for p,h in read(OUT/'source-freeze.json').items():assert sha(p)==h,('active source drift',p)
 for folder,freeze in ((ROOT,ROOT/'output/release_075/baseline/protected.json'),(ROOT.parent/'Community_civilization_pack_normal',ROOT/'output/release_075/baseline/normal.json')):
  for p,h in read(freeze).items():assert sha(folder/p)==h
 assert sha(base)==r['baseline_sha256']
 package_manifest=read(base.parent/'garrison.json');package_manifest['members'][0]['sha256']=sha(sga)
 package_manifest['details'].update(version='0.7.6',updated='2026-10-23',summary='New water buffalo and Dai Viet skirmisher models with age-specific javelins.',description='Includes the completed 0.7.5 building update. New buffalo, three skirmisher bodies, three held javelins and matching projectiles. Balance preserved. Native acceptance pending; custom buffalo supervision loop remains source-only.',changelog='Private visual bindings for all three skirmisher ages and water buffalo; stock throw/hide lifecycle retained. Existing 0.7.5 resources preserved except seven visual-reference records.')
 write(out/'garrison.json',package_manifest)
 evidence={'version':'0.7.6','status':'archive_verified_native_unverified','baseline_sga_sha256':r['baseline_sha256'],'sga_sha256':sha(sga),'archive_namespace':listing['archive']['name'],'recipe':str(recipe),'recipe_sha256':sha(recipe),'changed_members':sorted(expected_changes),'added_members':sorted(set(expected)-existing),'unchanged_members':len(existing)-len(expected_changes),'original_mounts_unchanged':True,'all_existing_gameplay_numeric_fields_unchanged':True,'all_nonvisual_original_fields_exact_reversal':True,'member_sha256':actual,'mounts':mounts,'private_references':private,'native_tested':False,'supervision_animation':'source_only_disabled'}
 write(out/'verification.json',evidence)
 package=out/'community_civilization_pack-0.7.6.zip'
 with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.write(out/'garrison.json','garrison.json');z.write(sga,sga.name)
  z.writestr('START-HERE.txt','Community Civilization Pack 0.7.6\nCredits: hosein81 and chilly5\nImport into Garrison and select Community Civilization Pack as Game Mode and Tuning Pack; choose China and Vietnam. Keep 0.7.5 for rollback. Not installed or native-tested by this build. Custom buffalo supervision loop is source-only and disabled.\n')
  z.write(ROOT/'docs/RELEASE_076_NATIVE_ACCEPTANCE.md','NATIVE-ACCEPTANCE.md')
  z.writestr('EVIDENCE.json',json.dumps({k:v for k,v in evidence.items() if k not in ('member_sha256','mounts','private_references')},indent=2)+'\n')
 with zipfile.ZipFile(package) as z:
  assert z.testzip() is None and len(z.namelist())==5
  assert sum(Path(n).name=='garrison.json' for n in z.namelist())==1
  assert hashlib.sha256(z.read(sga.name)).hexdigest()==sha(sga)
  assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.6'
 write(out/'delivery-proof.json',{'zip':str(package),'zip_sha256':sha(package),'zip_bytes':package.stat().st_size,'sga_sha256':sha(sga),'verified':True,'installed':False})
 print('DELIVERY_VERIFIED',str(package))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('recipe',type=Path);p.add_argument('--label',required=True);a=p.parse_args();main(a.recipe,a.label)
