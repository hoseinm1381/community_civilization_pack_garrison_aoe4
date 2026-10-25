"""Cook only explicitly selected art exports into a disposable art-source project."""
import re,shutil,msvcrt,xml.etree.ElementTree as ET
from common import *
from inventory import official
def main(selection,label):
 guard()
 if not re.fullmatch('[a-z0-9-]{1,12}',label):raise ValueError('Unsafe label')
 dest=OUT/'cooks'/label;library=STAGE/label;key='cc076art';project=library/'Mods'/key
 if dest.exists() or library.exists():raise FileExistsError('Preserve previous cook attempt')
 dest.mkdir(parents=True);library.mkdir(parents=True)
 source=project/'project/source';core=CFG['garrison_core']
 run('create',[core,'mod-project','create','--library',library,'--name',key],dest)
 run('settings',[core,'mod-project','settings','--project',project,'--live-reload','off'],dest)
 cfg=read(project/'mod-project.json')
 assert not cfg['game_mode']['enabled'] and not cfg['game_mode'].get('live_reload',False)
 template=RECIPES/'art-burn-rules.xml'
 old='__MODEL_PATH__'
 rules=[b for b in re.findall(r'<BurnRule>.*?</BurnRule>',template.read_text(),re.S) if old in b]
 assert len(rules)==4
 burn=source/'_default.burnproj';text=burn.read_text();records=[]
 for family,revision in selection.items():
  exp=EXPORT/family/revision;receipt=read(OUT/'art'/family/revision/'export.json')
  assert receipt['files']=={p.name:sha(p) for p in exp.iterdir() if p.is_file()}
  rel='art/scenario/garrison/cc076/'+family;body=source/rel;body.mkdir(parents=True)
  for name in receipt['files']:shutil.copyfile(exp/name,body/name)
  donor='buffalo' if family=='buffalo' else 'skirmisher'+family[-1] if family.startswith('skirmisher') else 'projectile' if family.startswith('projectile') else 'javelin2'
  row=read(OUT/'donors.json')[donor];rgopath=official(row['logical_path'].removesuffix('.rgm')+'.rgo')
  shutil.copyfile(rgopath,body/'model.rgo');(body/'model.rgotemplate').write_text('<ObjectTemplate><LodDistances/></ObjectTemplate>\n')
  root=ET.Element('materialSet')
  for lod in (1,2,3):
   skinned=family=='buffalo' or family.startswith('skirmisher')
   mat=ET.SubElement(root,'material',{'name':'lod'+str(lod),'type':'shader','source':'unit' if skinned else 'object'})
   slots={'albedoTexture':'albedo','normalMap':'normal','metalTex':'metalness','roughnessTex':'roughness'}
   if skinned:slots['patternTex']='pattern'
   for slot,name in slots.items():ET.SubElement(mat,'param',{'name':slot,'type':'tex2D','value':rel+'/'+name+'.png'})
  ET.indent(root);(body/'model.material').write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
  text=text.replace('</Rules>','\n'.join(r.replace(old,rel.replace('/','\\')) for r in rules)+'\n</Rules>',1)
  records.append({'family':family,'revision':revision,'export_receipt_sha256':sha(OUT/'art'/family/revision/'export.json'),'member_root':rel,'source_files':{p.name:sha(p) for p in body.iterdir()}})
 burn.write_text(text,encoding='utf-8');ET.parse(burn)
 write(dest/'prepare.json',{'selection':selection,'records':records,'project':str(project),'native_runtime':False,'final_mod_assembly':False,'template_sha256':sha(template)})
 work=library/'burn';editor=Path(CFG['art_editor']);work.mkdir(parents=True)
 argv=[editor,'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report','--no_source_control','--log_path',work/'logs','--build_mod',project/'project'/f'{key}.aoe4mod','--no_burn_window','--burn_verbose_log_level','--burn_cache_type','Local','--burn_max_threads','1','--build_path',work/'output','--intermediate_path',work/'intermediate']
 lock=Path(CFG['external_root'])/'output/release_020/native-build.lock'
 with lock.open('r+b') as f:
  msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
  try:run('native-cook',argv,dest,1800,cwd=editor.parent)
  finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
 finish(label)
def finish(label):
 guard();dest=OUT/'cooks'/label;library=STAGE/label;work=library/'burn';prep=read(dest/'prepare.json');records=prep['records']
 log=(dest/'native-cook.log').read_text()
 if '\nEXIT 0\n' not in log or 'Package [Archive] created' not in log:raise ValueError('Completed native burn evidence required')
 for row in records:
  body=Path(prep['project'])/'project/source'/row['member_root']
  if row['source_files']!={p.name:sha(p) for p in body.iterdir() if p.is_file()}:raise ValueError('Cook source drift')
 archives=list((work/'output').rglob('*.sga'))
 if len(archives)!=1:raise ValueError('Expected one fresh art archive')
 archive=archives[0];listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',archive,'--verify'],dest))
 run('extract',[CFG['archive_tool'],'extract',archive,dest/'readback','--filter','.'],dest)
 members={r['path'] for r in listing['members']}
 for r in records:
  for ext in ('.rgm','.rrgeom','.rrmaterial'):
   if r['member_root']+'/model'+ext not in members:raise ValueError('Cook missing '+r['member_root']+ext)
 write(dest/'receipt.json',{'status':'fresh_art_cook_readback_complete_native_unverified','archive':str(archive),'archive_sha256':sha(archive),'records':records,'member_count':len(members),'final_mod_assembly':False,'release_package_created':False})
 print('ART_COOK_COMPLETE',str(dest/'receipt.json'))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--selection');p.add_argument('--label',required=True);p.add_argument('--readback-only',action='store_true');a=p.parse_args()
 if a.readback_only:finish(a.label)
 else:main(read(a.selection),a.label)

