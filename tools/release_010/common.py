"""Shared release paths and bounded file operations for the 0.1.0 art release."""
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
OUT = EXTERNAL / 'output/release_010'
STAGING = EXTERNAL / 'staging/release_010'
GUID = CONFIG['project_guid']
KEY = CONFIG['package_key']
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


def snapshot(root):
    return {p.relative_to(root).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(Path(root).rglob('*')) if p.is_file()}


def run_logged(label, command, *, cwd=None, timeout=1200):
    check_storage(ROOT, CONFIG)
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / (label + '.log')
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([str(a) for a in command], cwd=cwd, stdout=stream,
            stderr=subprocess.STDOUT, timeout=timeout,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    receipt = {'command': [str(a) for a in command], 'cwd': str(cwd) if cwd else None,
               'exit_code': result.returncode, 'log': str(log)}
    write(OUT / (label + '-command.json'), receipt)
    if result.returncode:
        raise RuntimeError(f'{label} failed ({result.returncode}); see {log}')
    return receipt
