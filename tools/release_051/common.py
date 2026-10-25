"""Release 0.5.1 ownership, immutable inputs, and native tool coordination."""
from __future__ import annotations
import contextlib, hashlib, json, msvcrt, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CONFIG=CFG=configuration(ROOT)
EXTERNAL=Path(CONFIG['external_root'])
OUT=EXTERNAL/'output/release_051'
WORK=OUT/'integration'
STAGING=EXTERNAL/'staging/release_051'
ART=ROOT/'art/authoring/release_051'
EXPORT=ROOT/'art/exports/release_051'
RECIPES=ROOT/'art/recipes/release_051'
CORE=Path(CONFIG['garrison_core']); ARCH=Path(CONFIG['archive_tool'])
ART_EDITOR=Path(CONFIG['art_editor']); EDITOR=Path(CONFIG['content_editor'])
NATIVE_LOCK=EXTERNAL/'output/release_020/native-build.lock'
KEY=CONFIG['package_key']; GUID=CONFIG['project_guid']; VERSION='0.5.1'
PRIOR=EXTERNAL/'output/release_050'
BASELINE=OUT/'baseline/community_civilization_pack.sga'
ZIP050=PRIOR/'community_civilization_pack-0.5.0.zip'
ZIP050_SHA='be5e3ac2e6b859ce2d4efdf591c3fa94b11af0e6a4e8e870ce723bcd53dfdb01'
SGA050_SHA='78b90561306f6874872b5f88a5f82c3354e14fceebdf52cf0f0ffba28cbf1e80'
def guarded():return check_storage(ROOT,CONFIG)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    path=Path(path); resolved=path.resolve()
    assert any(resolved.is_relative_to(p.resolve()) for p in (OUT,STAGING,ART,EXPORT,RECIPES,ROOT/'tools/release_051')),path
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temp.replace(path)
def run_logged(label,command,cwd=ROOT,timeout=None):
    guarded(); log=OUT/'logs'/(label+'.log');log.parent.mkdir(parents=True,exist_ok=True)
    assert not log.exists(),f'Use a fresh log label: {label}'
    with log.open('w',encoding='utf-8') as f:
        result=subprocess.run([str(x) for x in command],cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    if result.returncode:raise RuntimeError(f'Command failed {result.returncode}: {log}')
    return str(log)
@contextlib.contextmanager
def exclusive_native():
    guarded()
    with NATIVE_LOCK.open('r+b') as f:
        try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as e:raise RuntimeError('Native build lock is busy') from e
        try:yield
        finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
