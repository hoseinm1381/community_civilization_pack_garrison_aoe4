"""Isolated 0.5.2 repair ownership; accepted 051 gameplay remains immutable."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CONFIG=configuration(ROOT)
OUT=Path(CONFIG['external_root'])/'output/release_052'
KEY=CONFIG['package_key'];GUID=CONFIG['project_guid']
ARCH=Path(CONFIG['archive_tool'])
BASELINE=OUT.parent/'release_051/package'/(KEY+'.sga')
ZIP051=OUT.parent/'release_051'/(KEY+'-0.5.1.zip')
SGA051_SHA='c7da8e37d4ec3750ff9c9668a86a72384e2769a05eb69a699b55caf2c36e9444'
ZIP051_SHA='40a0dc66621dea0c66823a56d4c0a2479431db456cfcea3554e65e6853a11265'
sys.path.insert(0,CONFIG['garrison_extension'])
sys.path.insert(0,str(ROOT/'tools/release_010'))
from garrison_shared import relic_chunky as rc
from integration_native import NativeTree

def guard():return check_storage(ROOT,CONFIG)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,value):
    p=Path(p);assert p.resolve().is_relative_to(OUT.resolve())
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def command(label,args,cwd=ROOT):
    guard();p=OUT/'logs'/(label+'.log');p.parent.mkdir(parents=True,exist_ok=True)
    assert not p.exists(),'Use a fresh run label'
    with p.open('w',encoding='utf-8') as f:
        result=subprocess.run([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT,cwd=cwd)
    assert result.returncode==0,(result.returncode,str(p));return str(p)
def files(root):
    result={};root=Path(root)
    for current,dirs,names in os.walk(root,followlinks=False):
        for name in list(dirs):
            p=Path(current)/name
            assert not p.is_symlink() and not p.is_junction(),p
            if name in ('__pycache__','release_052'):dirs.remove(name)
        for name in names:
            p=Path(current)/name;assert not p.is_symlink(),p
            result[p.relative_to(root).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
    return result
def snapshot():
    return {'assets':files(ROOT/'assets'),'normal':files(CONFIG['source_root']),
        'art':{k:files(ROOT/'art'/k) for k in ('authoring','exports','recipes')},
        'tools':{p.name:files(p) for p in (ROOT/'tools').iterdir() if p.is_dir() and p.name not in ('release_052','__pycache__')},
        'tests':files(ROOT/'tests'),
        'identities':{p:sha(ROOT/p) for p in ('workspace.json',CONFIG['project_file'])}}
def verify_frozen():
    guard();f=read(OUT/'baseline/freeze.json')
    assert sha(BASELINE)==SGA051_SHA and sha(ZIP051)==ZIP051_SHA
    current=snapshot();before=f['inputs'];additions={}
    for key in ('assets','normal','tests','identities'):
        assert current[key]==before[key],f'Protected {key} changed'
    for category in ('art','tools'):
        for name,old in before[category].items():
            assert name in current[category],('Protected input root missing',category,name)
            now=current[category][name]
            assert all(now.get(p)==meta for p,meta in old.items()),('Protected input changed',category,name)
            added=set(now)-set(old)
            # Another user-owned chat started 060 authoring after this freeze.
            # Admit only new files in that separate namespace; every previously
            # frozen byte and every active source/test/identity remains guarded.
            assert category=='art' and all(p.startswith('release_060/') for p in added) or not added,('Unexpected added inputs',category,name,added)
            if added:additions[category+'/'+name]=sorted(added)
        roots=set(current[category])-set(before[category])
        assert not roots or category=='tools' and roots=={'release_060'},('Unexpected input root',category,roots)
        if roots:additions[category+'/new_roots']=sorted(roots)
    write(OUT/'preservation.json',{'status':'passed','all_frozen_entries_byte_identical':True,
        'active_source_normal_tests_and_identity_exact':True,'concurrent_060_additions':additions,
        'concurrent_scope':'New 060 authoring inputs are owned by another chat, may keep changing, and are not included or modified by052.'})
    return True

