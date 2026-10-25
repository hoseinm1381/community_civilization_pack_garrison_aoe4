"""Owned 0.6.0 workspace helpers; never mutate the active gameplay project."""
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import configuration, check_storage
CFG = configuration(ROOT)
EXTERNAL = Path(CFG['external_root'])
OUT = EXTERNAL / 'output/release_060'
STAGING = EXTERNAL / 'staging/release_060'
ART = ROOT / 'art/authoring/release_060'
EXPORT = ROOT / 'art/exports/release_060'
RECIPES = ROOT / 'art/recipes/release_060'
TOOLS = ROOT / 'tools/release_060'
CORE = Path(CFG['garrison_core'])
ARCH = Path(CFG['archive_tool'])
NATIVE_LOCK = EXTERNAL / 'output/release_020/native-build.lock'
OWNED = (OUT, STAGING, ART, EXPORT, RECIPES, TOOLS)

def guard():
    return check_storage(ROOT, CFG)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def owned(path):
    guard()
    path = Path(path)
    if not any(path.resolve().is_relative_to(root.resolve()) for root in OWNED):
        raise ValueError(f'Outside 0.6.0 ownership: {path}')
    return path

def write(path, data):
    path = owned(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(path)

def files(root, reject_links=False, exclude_release_060=True):
    """Historical scans exclude new art; archive/source gates opt into all files."""
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f'Inventory root is not a directory: {root}')
    if reject_links and (root.is_symlink() or root.is_junction()):
        raise ValueError(f'Unexpected root link: {root}')
    result = {}
    for current, dirs, names in os.walk(root, followlinks=False):
        if reject_links:
            for name in dirs:
                p = Path(current)/name
                if p.is_junction() or p.is_symlink():
                    raise ValueError(f'Unexpected directory link: {p}')
        dirs[:] = sorted(d for d in dirs if d != '__pycache__'
                         and (not exclude_release_060 or d != 'release_060')
                         and not (Path(current)/d).is_junction()
                         and not (Path(current)/d).is_symlink())
        for name in sorted(names):
            p = Path(current)/name
            if p.is_symlink():
                raise ValueError(f'Unexpected file link: {p}')
            before = p.stat()
            digest = sha(p)
            after = p.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError(f'Input changed while hashing: {p}')
            result[p.relative_to(root).as_posix()] = {'sha256': digest, 'bytes': after.st_size}
    return result

def copy_manifest(source, target, manifest):
    """Copy enumerated plain files only; never recurse through a source link."""
    source, target = Path(source), owned(target)
    if not source.is_dir():
        raise FileNotFoundError(f'Snapshot source is not a directory: {source}')
    if target.exists():
        raise FileExistsError(target)
    target.mkdir(parents=True)
    for relative, record in manifest.items():
        part = Path(relative)
        if part.is_absolute() or '..' in part.parts:
            raise ValueError(f'Unsafe snapshot member: {relative}')
        src = source/part
        for ancestor in (src, *src.parents):
            if ancestor.is_symlink() or ancestor.is_junction():
                # Source itself is an E: authoring folder, not an output junction.
                raise ValueError(f'Unexpected snapshot source link: {ancestor}')
            if ancestor == source:
                break
        payload = src.read_bytes()
        if hashlib.sha256(payload).hexdigest() != record['sha256']:
            raise RuntimeError(f'Source changed before copy: {src}')
        dest = owned(target/part)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as stream:
            stream.write(payload)
