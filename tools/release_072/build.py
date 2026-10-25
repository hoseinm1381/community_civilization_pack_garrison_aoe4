"""0.7.2 source build and narrowly admitted native visual assembly."""
from freeze import *
import subprocess,re,shutil,argparse
EXT=Path(CFG['external_root']);STAGING=EXT/'staging/r72'
def run(label,args,timeout=1200):
    p=subprocess.run([str(x)for x in args],capture_output=True,encoding='utf-8',errors='replace',timeout=timeout)
    (OUT/(label+'.log')).write_text(repr([str(x)for x in args])+'\nEXIT '+str(p.returncode)+'\n'+p.stdout+'\n'+p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(label+' failed; see retained log')
    return p.stdout
def source(label):
    freeze();s=STAGING/'ported-source';work=STAGING/('build-'+label)
    assert not work.exists(),'Use a new label; retain failed diagnostics'
    log=run('native-source-'+label,[CFG['garrison_core'],'essence','build-mod','--editor',CFG['content_editor'],'--mod',s/CFG['project_file'],'--run-root',work,'--timeout','900'])
    state=json.loads((work/'run.json').read_text())
    for p in (work/'logs').glob('*'):
        if p.suffix.lower() in ('.txt','.log'):log+='\n'+p.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace')
    count=len(list((s/'assets/attrib/instances').rglob('*.xml')))
    validated=re.findall(r'(\d+) instances validated',log)
    errors=[l for l in log.splitlines()if 'EssenceEditor.exe Error:' in l or 'System does not support' in l]
    archives=list((work/'output').rglob('*.sga'))
    proof={'state':state,'expected_instances':count,'validated':validated,'errors':errors,'archives':[str(p)for p in archives]}
    proof['passed']=state.get('status')=='succeeded' and state.get('exit_code')==0 and validated and int(validated[-1])==count and not errors and len(archives)==1
    dump(OUT/('native-source-'+label+'.json'),proof)
    assert proof['passed'],proof
    assert json.loads((OUT/'source-port.json').read_text())['staged_hashes']=={p.relative_to(s).as_posix():sha(p)for p in files(s) if not p.relative_to(s).parts[0] in ('cache','output')}
    listing=json.loads(run('source-list-'+label,[CFG['archive_tool'],'list',archives[0],'--verify']))
    assert listing['archive']['verification']['verified']
    proof.update(archive_sha256=sha(archives[0]),listing=listing)
    dump(OUT/('native-source-'+label+'.json'),proof)
    print(json.dumps({k:v for k,v in proof.items()if k!='listing'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['source']);p.add_argument('--label',default='v1');a=p.parse_args();assert re.fullmatch('[a-z0-9-]{1,16}',a.label);source(a.label)
