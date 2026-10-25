"""Owned paths and evidence helpers; historical release tools stay unchanged."""
from pathlib import Path
import hashlib
import gzip
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / 'workspace.json').read_text())
EXT = Path(CFG['external_root'])
ROOTS = {'E': ROOT, 'F': EXT}
TX = EXT / 'consolidation_080'
STORE = EXT / 'resources_080'
OUT = EXT / 'output/consolidation_080'
STAGE = EXT / 'staging/r80c'
BASE = ROOT / 'output/release_0712/delivery/final-v1'
EXPECTED = 'e54fad91112350c70dab1c8cc826da26aa5c6ae9a6754244ed9141fe75d75eb1'
EXPECTED_ZIP = '58f57c1a09b2d7e5d2a3c986ac2a1ec3c390e07edaa212b4faf83a34b3702505'
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import check_storage


def guard():
    return check_storage(ROOT, CFG)


def safe_label(value):
    if not re.fullmatch('[a-z0-9-]{1,24}', value):
        raise ValueError('Unsafe owned attempt label')
    return value


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    path = Path(path)
    if not path.exists() and Path(str(path) + '.gz').exists():
        return json.loads(gzip.decompress(Path(str(path) + '.gz').read_bytes()).decode('utf-8-sig'))
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def walk(root):
    stack = [Path(root)]
    while stack:
        with os.scandir(stack.pop()) as entries:
            for entry in entries:
                if entry.is_symlink() or entry.is_junction():
                    continue
                p = Path(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    stack.append(p)
                elif entry.is_file(follow_symlinks=False):
                    yield p


def run(label, args, folder=TX / 'logs', timeout=1800):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(list(map(str, args)), capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=timeout)
    (folder / (label + '.log')).write_text(subprocess.list2cmdline(list(map(str, args)))
        + '\nEXIT ' + str(proc.returncode) + '\n' + proc.stdout + '\n' + proc.stderr,
        encoding='utf-8')
    if proc.returncode:
        raise RuntimeError(label + ' failed; see ' + str(folder))
    return proc.stdout
