"""Guarded ownership and append-only evidence for the 0.4.0 release."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import configuration, check_storage

CONFIG = configuration(ROOT)
EXTERNAL = Path(CONFIG['external_root'])
OUT = EXTERNAL / 'output/release_040'
STAGING = EXTERNAL / 'staging/release_040'
GUID = CONFIG['project_guid']
KEY = CONFIG['package_key']
VERSION = '0.4.0'
CORE = Path(CONFIG['garrison_core'])
ARCH = Path(CONFIG['archive_tool'])
EDITOR = Path(CONFIG['content_editor'])
ART_EDITOR = Path(CONFIG['art_editor'])


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    if not any(path.resolve().is_relative_to(p.resolve()) for p in (ROOT, EXTERNAL)):
        raise ValueError(f'Write outside owned roots: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def guarded():
    check_storage(ROOT, CONFIG)


def run_logged(label, command, *, cwd=None, timeout=1200):
    guarded()
    log = OUT / 'logs' / (label + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([str(a) for a in command], cwd=cwd, stdout=stream,
            stderr=subprocess.STDOUT, timeout=timeout,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    receipt = {'command': [str(a) for a in command], 'cwd': str(cwd) if cwd else None,
               'exit_code': result.returncode, 'log': str(log)}
    write(log.with_suffix('.json'), receipt)
    if result.returncode:
        raise RuntimeError(f'{label} failed ({result.returncode}); see {log}')
    return receipt
