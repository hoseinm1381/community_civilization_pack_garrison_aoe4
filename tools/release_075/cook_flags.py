"""Native compile of reviewed flag placements, with typed readback proof."""
from pathlib import Path
import argparse,hashlib,json,msvcrt,shutil,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
from native_io import visuals
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(placements,label,reflect_only=False,stock_deps=False):
 check_storage(ROOT,CFG)
 poses=json.loads(placements.read_text());prep=json.loads((ROOT/'output/release_075/owner_colour/preparation-v2.json').read_text())
 assert set(poses)=={'citadel','hq','ministry','pho_minh','one_pillar','garden','foundry'}
 work=Path(CFG['external_root'])/'staging/r75'/('flags-'+label);out=ROOT/'output/release_075/owner_colour'/('cook-'+label)
 if work.exists() or out.exists():raise FileExistsError('Retain native attempts')
 template=Path(CFG['external_root'])/'staging/r75/citadel-v1/library/Mods/cc075citadel/project'
 project=work/'project';shutil.copytree(template,project);out.mkdir(parents=True)
 files={};expected={}
 dependencies={}
 if stock_deps:
  for row in prep['stock_resources']:
   src=Path(row['file']);assert sha(src)==row['sha256']
   dst=project/'source'/row['member'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
   assert sha(dst)==row['sha256'];dependencies[row['member']]=row['sha256']
 for family,pose in poses.items():
  assert pose['contact_verified'] is True and pose['support_evidence']
  v=pose['native_translation'];scale=pose['scale'];assert len(v)==3 and 0<scale<=3
  assert abs(v[1]-.1484375*scale-pose['support_native_y'])<.0001
  source=ROOT/'output/release_075/owner_colour/source'/f'{family}.rdo'
  tree=ET.fromstring(source.read_bytes());visual=tree.find('.//DataObject[@Type="VisualStampBlueprint"]')
  for prop in ('m_isSelectable','m_addToPathfinding'):assert visual.find(f'./DataProperty[@Name="{prop}"]').get('Value')=='false'
  # Yaw only; pose quaternion is recorded explicitly rather than inferred from
  # a decorative source transform that could tilt the pole off its base.
  quat=pose.get('native_quaternion',[0,0,0,1]);assert abs(quat[0])+abs(quat[2])<1e-8
  for prop,fields,vals in [('m_translation',('x','y','z'),v),('m_scale',('x','y','z'),[scale]*3),('m_rotation',('x','y','z','s'),quat)]:
   obj=visual.find(f'.//DataProperty[@Name="{prop}"]/DataObject')
   for field,val in zip(fields,vals):obj.find(f'./DataProperty[@Name="{field}"]').set('Value',str(val))
  member=f'art/stamps/garrison/cc075flags/{family}_owner_flag'
  target=project/'source'/(member+'.rdo');target.parent.mkdir(parents=True,exist_ok=True)
  # Match the installed generated RDO writer exactly (no XML declaration).
  ET.indent(tree,space='  ');target.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=False)+b'\n')
  files[member+'.rdo']=sha(target);expected[member+'.bin']=[*quat,*v,*([scale]*3)]
 # The generated prototype has an exact-file Reflect include, not a glob.
 # Extend that proven rule explicitly; mere source presence does not cook it.
 burn=project/'source/_default.burnproj';raw=burn.read_text(encoding='utf-8')
 old='<Includes>art\\stamps\\garrison\\cc075citadel\\citadel.rdo</Includes>'
 assert raw.count(old)==1
 additions=';'.join(k.replace('/','\\') for k in files)
 raw=raw.replace(old,old.replace('</Includes>',';'+additions+'</Includes>'))
 if reflect_only:
  # Keep original namespace prefixes (including QName type attribute values).
  # Drop only generated art burn rules and add an exact seven-source Reflect
  # rule copied from the proven template. Full Content Editor mounts stock art.
  import re
  pattern=r'<BurnRule>.*?</BurnRule>'
  blocks=list(re.finditer(pattern,raw,flags=re.S))
  stamp=next(m.group() for m in blocks if old.split('</Includes>')[0] in m.group())
  replacement=re.sub(r'<Includes>.*?</Includes>',lambda m:'<Includes>'+additions+'</Includes>',stamp,flags=re.S)
  for match in reversed(blocks):
   block=match.group();inc=re.search(r'<Includes>(.*?)</Includes>',block,re.S)
   if inc and inc.group(1).startswith('art\\'):
    raw=raw[:match.start()]+(replacement if 'art\\stamps\\' in inc.group(1) else '')+raw[match.end():]
 burn.write_text(raw,encoding='utf-8');files['_default.burnproj']=sha(burn)
 (out/'input-freeze.json').write_text(json.dumps({'placements':str(placements),'placements_sha256':sha(placements),'source_hashes':files,'validation_only_stock_dependencies':dependencies,'template':'Isolated successful Citadel native art project; none of its actors/models are integrated'},indent=2)+'\n')
 def run(name,args):
  command=list(map(str,args))
  try:p=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1800)
  except subprocess.TimeoutExpired as exc:
   def decoded(value):return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else (value or '')
   (out/(name+'.log')).write_text(decoded(exc.stdout)+'\n'+decoded(exc.stderr),encoding='utf-8')
   (out/(name+'-timeout.json')).write_text(json.dumps({'command':command,'timeout_seconds':exc.timeout,'status':'timeout_outcome_unknown','retained_stdout_stderr':name+'.log'},indent=2)+'\n')
   raise
  (out/(name+'.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
  if p.returncode:raise RuntimeError(name+' failed')
  return p.stdout
 lock=Path(CFG['external_root'])/'output/release_020/native-build.lock'
 with lock.open('r+b') as f:
  msvcrt.locking(f.fileno(),msvcrt.LK_LOCK,1)
  try:run('native',[CFG['garrison_core'],'essence','build-mod','--editor',CFG['content_editor'] if reflect_only else CFG['art_editor'],'--mod',project/'cc075citadel.aoe4mod','--run-root',work/'run','--timeout','1200'])
  finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
 state=json.loads((work/'run/run.json').read_text());assert state['status']=='succeeded' and state['exit_code']==0
 archives=list((work/'run/output').rglob('*.sga'));assert len(archives)==1;archive=archives[0]
 listed=json.loads(run('list',[CFG['archive_tool'],'list',archive,'--verify']));assert listed['archive']['verification']['verified']
 rows=[]
 for member,transform in expected.items():
  target=out/'payload'/member;target.parent.mkdir(parents=True,exist_ok=True)
  run('extract-'+Path(member).stem,[CFG['archive_tool'],'extract-member',archive,member,target])
  tree,v=visuals(target);assert len(v)==1 and v[0]['model']=='art/civilizations/common/flags/flag_rectangle/flag_rectangle'
  assert max(abs(a-b) for a,b in zip(v[0]['transform'],transform))<1e-5
  visual=next(x for x in tree.objects.values() if x['type']=='VisualStampBlueprint')
  for name in ('m_isSelectable','m_addToPathfinding'):
   at=visual['offset']+int(visual['fields'][name].get('Offset'));assert tree.bytes(at,1)==b'\x00'
  rows.append({'member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'transform':v[0]['transform']})
 assert all(sha(project/'source'/name)==digest for name,digest in (files|dependencies).items())
 (out/'receipt.json').write_text(json.dumps({'status':'native_stamp_compile_and_readback_complete_runtime_unverified','archive':str(archive),'archive_sha256':sha(archive),'members':rows,'placements_sha256':sha(placements),'placements':str(placements.resolve()),'editor':CFG['content_editor'] if reflect_only else CFG['art_editor'],'reflect_only':reflect_only,'source_hashes_unchanged':True,'selectable':False,'adds_to_pathfinding':False,'native_tint_lifecycle':'pending final candidate test'},indent=2)+'\n');print('COOKED_FLAG_STAMPS',len(rows))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('placements',type=Path);p.add_argument('--label',default='v1');p.add_argument('--reflect-only',action='store_true');p.add_argument('--stock-deps',action='store_true');a=p.parse_args();main(a.placements,a.label,a.reflect_only,a.stock_deps)
