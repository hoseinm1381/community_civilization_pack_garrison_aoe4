"""0.6.1 storage ownership and exact baseline helpers."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CFG=configuration(ROOT)
EXT=Path(CFG['external_root'])
OUT=EXT/'output/release_061'
STAGE=EXT/'staging/release_061'
TOOLS=ROOT/'tools/release_061'
RECIPES=ROOT/'art/recipes/release_061'
ARCH=Path(CFG['archive_tool'])
OLD=EXT/'output/release_060'
ZIP060=OLD/'community_civilization_pack-0.6.0.zip'
SGA060=OLD/'assembly/candidate-r2/community_civilization_pack.sga'
ZIP060_SHA='913d5a8077aec36e8ce90ccfefcd06ccb39edb42f61bbbaf8667ac6168148ac9'
SGA060_SHA='204a889662e2b403b5c0caccb4b79f08bdf0654f90b5f9095ebebfd773b641c8'

def guard():return check_storage(ROOT,CFG)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def owned(path):
    guard();p=Path(path)
    if not any(p.resolve().is_relative_to(r.resolve()) for r in (OUT,STAGE,TOOLS,RECIPES)):
        raise ValueError('Outside061ownership: '+str(p))
    return p
def write(path,data):
    p=owned(path);p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f'.{os.getpid()}.tmp')
    t.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');t.replace(p)
def command(*args,timeout=180):
    r=subprocess.run([str(ARCH),*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    if r.returncode:raise RuntimeError(r.stderr+'\n'+r.stdout)
    return json.loads(r.stdout)
def files(root):
    root=Path(root);result={}
    if root.is_symlink() or root.is_junction():raise ValueError('Unexpected inventory root link')
    for current,dirs,names in os.walk(root,followlinks=False):
        for n in dirs:
            p=Path(current)/n
            if p.is_symlink() or p.is_junction():raise ValueError('Unexpected nested link')
        dirs[:]=sorted(d for d in dirs if d!='__pycache__')
        for n in sorted(names):
            p=Path(current)/n
            if p.is_symlink():raise ValueError('Unexpected file link')
            result[p.relative_to(root).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
    return result
def baseline():
    f=read(OUT/'baseline/freeze.json')
    if sha(ZIP060)!=ZIP060_SHA or sha(SGA060)!=SGA060_SHA:raise ValueError('Retained060delivery changed')
    return f
