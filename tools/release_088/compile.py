"""Real Content Editor source reference compilation for minimal 088 fixes."""
import json,msvcrt,re,shutil,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];cfg=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
check_storage(ROOT,cfg);check(ROOT,ROOT/'output/release_085/final-v2/community_civilization_pack.sga')
work=Path(cfg['external_root'])/'staging/r88';work.mkdir(exist_ok=False)
source=work/'src';shutil.copytree(ROOT/'assets',source/'assets');shutil.copy2(ROOT/cfg['project_file'],source/cfg['project_file'])
freeze={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
(ROOT/'output/release_085/088-native-input-freeze.json').write_text(json.dumps({'staged_root':str(source),'files':freeze,'all_match_current_source':all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in freeze.items())},indent=2),encoding='utf-8')
cmd=[cfg['garrison_core'],'essence','build-mod','--editor',cfg['content_editor'],'--mod',str(source/cfg['project_file']),'--run-root',str(work/'run'),'--timeout','900']
with (ROOT/'output/release_020/native-build.lock').open('r+b') as lock:
 msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 try:p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1000)
 finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
(ROOT/'output/release_085/088-native-build-final.log').write_text('EXIT '+str(p.returncode)+'\n'+p.stdout+'\n'+p.stderr,encoding='utf-8')
state=json.loads((work/'run/run.json').read_text());logs='\n'.join(p.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace') for p in (work/'run/logs').glob('*') if p.suffix in ('.log','.txt'))
count=len(list((source/'assets/attrib/instances').rglob('*.xml')));counts=re.findall(r'(\d+) instances validated',logs)
assert p.returncode==0 and state['status']=='succeeded' and state['exit_code']==0 and counts and int(counts[-1])==count,(state,counts,count)
assert 'EssenceEditor.exe Error:' not in logs
archives=list((work/'run/output').rglob('*.sga'));assert len(archives)==1
check(ROOT,archives[0]);receipt={'native_compile':True,'validated_instances':count,'archive':str(archives[0]),'state':state,'final_release_archive':False}
(ROOT/'output/release_085/088-native-reference.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print('NATIVE_088_REFERENCE_COMPILED',count,str(archives[0]),flush=True)
