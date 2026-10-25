"""Guarded 0.5.0 integration after the user-authorized 0.4.0 freeze."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CONFIG=configuration(ROOT)
CFG=CONFIG
EXTERNAL=Path(CONFIG['external_root'])
OUT=EXTERNAL/'output/release_050'
STAGING=EXTERNAL/'staging/release_050'
WORK=OUT/'integration'
CORE=Path(CONFIG['garrison_core'])
ARCH=Path(CONFIG['archive_tool'])
ART_EDITOR=Path(CONFIG['art_editor'])
GUID=CONFIG['project_guid']
KEY=CONFIG['package_key']
VERSION='0.5.0'
CASTLE=EXTERNAL/'output/castle_next'
BASELINE=ROOT/'archives/release_040_user_accepted/community_civilization_pack.sga'
NATIVE_LOCK=EXTERNAL/'output/release_020/native-build.lock'

def guarded():check_storage(ROOT,CONFIG)

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def write(path,data):
    path=Path(path);resolved=path.resolve()
    allowed=(OUT,STAGING,ROOT/'tools/release_050',ROOT/'art/recipes/release_050')
    if not any(resolved.is_relative_to(p.resolve()) for p in allowed):
        raise ValueError(f'Outside050 report/config ownership: {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    temp.replace(path)

def run_logged(label,command,cwd=ROOT,timeout=None):
    guarded();log=OUT/'logs'/(label+'.log');log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run([str(c) for c in command],cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,
                              encoding='utf-8',errors='replace',timeout=timeout)
    if result.returncode:raise RuntimeError(f'050 command failed ({result.returncode}); see {log}')
    return str(log)
