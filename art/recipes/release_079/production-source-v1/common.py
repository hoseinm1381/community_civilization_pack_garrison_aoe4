"""Version-owned helpers. Never overwrite historical release inputs."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
OUT=Path(CFG['external_root'])/'output/release_079'
ART=ROOT/'art/authoring/release_079'
EXPORT=ROOT/'art/exports/release_079'
RECIPES=ROOT/'art/recipes/release_079'
STAGE=Path(CFG['external_root'])/'staging/r79'
BASE=ROOT/'output/release_078/delivery/final-v1'
EXPECTED='ca70903377c6a29b302e701a799c99f6f31e434428ed05021d717e27d1cf638e'
def guard():return check_storage(ROOT,CFG)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def run(label,args,folder=None,timeout=1800,cwd=None):
    folder=Path(folder or OUT/'logs');folder.mkdir(parents=True,exist_ok=True)
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,cwd=cwd)
    (folder/(label+'.log')).write_text(subprocess.list2cmdline(list(map(str,args)))+'\nEXIT '+str(r.returncode)+'\n'+r.stdout+'\n'+r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(label+' failed: '+str(folder/(label+'.log')))
    return r.stdout
