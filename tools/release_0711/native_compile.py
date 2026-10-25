"""Isolated source compile under the shared native lock; never install."""
import msvcrt,re,shutil
from common import *

def main(label):
    guard();out=OUT/'native'/label;assert not out.exists();out.mkdir(parents=True)
    with (OUT.parent/'release_020/native-build.lock').open('r+b') as f:
        msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        try:
            run('identity-before',[CFG['python'],ROOT/'tools/release_073/check_identity.py','--archive',BASE/'community_civilization_pack.sga'],out)
            work=STAGE/('source-'+label);assert not work.exists();src=work/'src'
            shutil.copytree(ROOT/'assets',src/'assets');shutil.copy2(ROOT/CFG['project_file'],src/CFG['project_file'])
            frozen={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()};write(out/'inputs.json',frozen)
            run('compile',[CFG['garrison_core'],'essence','build-mod','--editor',CFG['content_editor'],'--mod',src/CFG['project_file'],'--run-root',work/'run','--timeout','900'],out,timeout=1200)
            state=read(work/'run/run.json');assert state['status']=='succeeded' and state['exit_code']==0
            log='\n'.join(p.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace') for p in (work/'run/logs').glob('*') if p.suffix in ('.log','.txt'))
            validated=re.findall(r'(\d+) instances validated',log);assert validated and int(validated[-1])==377
            archives=list((work/'run/output').rglob('*.sga'));assert len(archives)==1
            run('identity-after',[CFG['python'],ROOT/'tools/release_073/check_identity.py','--archive',archives[0]],out)
            back=out/'readback';run('readback',[CFG['archive_tool'],'extract',archives[0],back,'--filter','.'],out)
            assert frozen=={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()}
            write(out/'receipt.json',{'archive':str(archives[0]),'sha256':sha(archives[0]),'readback':str(back),
                'status':'native_compile_passed','validated_instances':377,'inputs_sha256':sha(out/'inputs.json'),
                'run':str(work/'run/run.json'),'source_policy_sha256':sha(OUT/'source-policy.json')})
            print('NATIVE_COMPILE_PASSED',label)
        finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)

if __name__=='__main__':main(sys.argv[1])
