"""Owned Castle asset preparation paths; never activates or packages assets."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import configuration, check_storage
CFG = configuration(ROOT)
CONFIG = CFG
EXTERNAL = Path(CFG['external_root'])
OUT = EXTERNAL / 'output/castle_next'
WORK = OUT / 'integration'
CORE = Path(CFG['garrison_core'])
ARCH = Path(CFG['archive_tool'])
ART_EDITOR = Path(CFG['art_editor'])
STAGING = EXTERNAL / 'staging/castle_next'
ART = ROOT / 'art/authoring/castle_next'
EXPORT = ROOT / 'art/exports/castle_next'
RECIPES = ROOT / 'art/recipes/castle_next'
NATIVE_LOCK = EXTERNAL / 'output/release_020/native-build.lock'

def guarded():
    check_storage(ROOT, CFG)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, data):
    path = Path(path)
    allowed = (OUT, ART, EXPORT, RECIPES, ROOT / 'tools/castle_next', EXTERNAL / 'staging/castle_next')
    resolved = path.resolve()
    if not any(resolved.is_relative_to(p.resolve()) for p in allowed):
        raise ValueError(f'Outside Castle ownership: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(path)

def run_logged(name, command, cwd=ROOT, timeout=None):
    guarded()
    log = OUT / 'logs' / (name + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([str(p) for p in command], cwd=cwd, stdout=stream,
                                stderr=subprocess.STDOUT, encoding='utf-8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); see {log}')
    return str(log)
