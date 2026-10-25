"""Immutable isolated native building cook; never changes active release inputs."""
from pathlib import Path
import argparse,hashlib,json,msvcrt,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(family,label,revision=''):
 check_storage(ROOT,CFG)
 if family not in ('citadel','hq','ministry','pho_minh','one_pillar','garden','foundry') or not re.fullmatch('[a-z0-9-]{1,16}',label):raise ValueError('Invalid owned label')
 source=ROOT/'art/exports/release_0710'/family
 if revision:
  if not re.fullmatch('r[0-9]+',revision):raise ValueError('Invalid revision')
  source=source/revision
 out=ROOT/'output/release_0710/buffalo/cooks'/f'{family}-{label}'
 work=Path(CFG['external_root'])/'staging/r710b'/f'{family}-{label}'
 if out.exists() or work.exists():raise FileExistsError('Preserve every cook attempt')
 names=['model.fbx','building.json','albedo.png','normal.png','roughness.png','metalness.png']
 hashes={n:sha(source/n) for n in names}
 building=json.loads((source/'building.json').read_text())
 parts=building['parts'];expected=[f'garrison_part_{i:04}' for i in range(len(parts))]
 actual=sorted(s.split(b'\0')[0].decode() for s in re.findall(rb'garrison_part_\d{4}(?:\.\d{3})?\x00\x01Model',(source/'model.fbx').read_bytes()))
 assert [p['name'] for p in parts]==actual==expected
 stages={'ministry':[0,20],'pho_minh':[0,20,0],'one_pillar':[0,20,0]}.get(family,[0,20,0,80,20,20,20])
 assert [p['first_stage'] for p in parts]==stages
 preflight=ROOT/'output/release_0710/buffalo/art/ministry/r1/receipt.json'
 pf=json.loads(preflight.read_text())['preflight'];assert pf['ok'];exception=None
 out.mkdir(parents=True);work.mkdir(parents=True)
 staged=work/'inputs'/family;staged.mkdir(parents=True)
 for name in names:shutil.copyfile(source/name,staged/name)
 assert hashes=={n:sha(staged/n) for n in names}
 key='cc075'+family;library=work/'library';project=library/'Mods'/key
 frozen={'source':str(source),'hashes':hashes,'building':building,'preflight_sha256':sha(preflight),'baseline_sga_sha256':'f3e738f96e865f27b20d7d423bf3250b9a53dbea8b3414ecffe2d4ff040cc20d'}
 if exception:frozen['inherited_open_surface_exception']={'file':str(exception),'sha256':sha(exception)}
 (out/'input-freeze.json').write_text(json.dumps(frozen,indent=2)+'\n')
 def run(name,args,timeout=2100):
  try:p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
  except subprocess.TimeoutExpired as error:
   def decoded(value):return value.decode('utf-8','replace') if isinstance(value,bytes) else (value or '')
   (out/(name+'.log')).write_text('COMMAND '+subprocess.list2cmdline(args)+f'\nTIMEOUT {timeout} seconds\n'+decoded(error.stdout)+'\n'+decoded(error.stderr),encoding='utf-8')
   raise
  (out/(name+'.log')).write_text('COMMAND '+subprocess.list2cmdline(args)+f'\nEXIT {p.returncode}\n'+p.stdout+'\n'+p.stderr,encoding='utf-8')
  if p.returncode:raise RuntimeError(name+' failed; retained log')
  return p.stdout
 core=CFG['garrison_core'];lock=Path(CFG['external_root'])/'output/release_020/native-build.lock'
 with lock.open('r+b') as stream:
  msvcrt.locking(stream.fileno(),msvcrt.LK_LOCK,1)
  try:
   run('create',[core,'mod-project','create','--library',str(library),'--name',key],120)
   run('settings',[core,'mod-project','settings','--project',str(project),'--live-reload','off'],120)
   run('register',[core,'mod-project','building','--project',str(project),'--source',str(staged),'--name',family,'--profile','english-house','--integration','script'],300)
   config=json.loads((project/'mod-project.json').read_text())
   assert not config['game_mode']['enabled'] and not config['game_mode']['live_reload']
   run('native-cook',[core,'mod-project','cook','--project',str(project),'--editor',CFG['art_editor'],'--timeout','1800'])
  finally:
   stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
 archive=project/'dist'/(key+'.sga');assert archive.is_file()
 back=out/'readback';run('readback',[CFG['archive_tool'],'extract',str(archive),str(back),'--filter','.'],600)
 model=back/'art/scenario/garrison'/key/'buildings'/family
 media={p.name:sha(p) for p in model.iterdir() if p.is_file()}
 assert {'model.rgm','model.rrgeom','model.rrmaterial'}<=set(media)
 assert hashes=={n:sha(source/n) for n in names}
 receipt={'status':'fresh_native_cook_and_readback_complete_runtime_unverified','family':family,'archive':str(archive),'archive_sha256':sha(archive),'model_readback':str(model),'media':media,'input_freeze_sha256':sha(out/'input-freeze.json'),'temporary_key':key}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('family');p.add_argument('--label',default='v1');p.add_argument('--revision',default='');a=p.parse_args();main(a.family,a.label,a.revision)

