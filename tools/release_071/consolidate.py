"""Keep-first transaction. Preparation never deletes or modifies original inputs."""
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from resources import sha, ResourceStore

ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / 'workspace.json').read_text())
EXT = Path(CFG['external_root'])
AUDIT = Path(r'C:\Users\RS\.codex\visualizations\2026\10\19\01a153b8-8737-7cf0-b664-cff859208c1f\garrison-071-retention-audit')
TX = EXT / 'consolidation_071'
STORE = EXT / 'resources_071'
ROOTS = {'E': ROOT, 'F': EXT}


def dump(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding='utf-8')


def key(path):
    text = str(path).removeprefix('\\\\?\\')
    p = Path(text)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    for drive, root in ROOTS.items():
        if p.is_relative_to(root):
            return drive + '/' + p.relative_to(root).as_posix()
    raise ValueError('Outside owned roots: ' + text)


def physical(logical):
    drive, rel = logical.split('/', 1)
    p = (ROOTS[drive] / rel).resolve()
    if not p.is_relative_to(ROOTS[drive]):
        raise ValueError(logical)
    return p


def walk(root):
    with os.scandir(root) as entries:
        for entry in entries:
            if entry.is_symlink() or entry.is_junction():
                continue
            if entry.is_dir(follow_symlinks=False):
                yield from walk(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                yield Path(entry.path)


def prepare():
    inventory = json.loads((AUDIT / 'inventory.json').read_text())
    proposal = json.loads((AUDIT / 'retention-proposal-raw.json').read_text())
    kept = {}
    # Audit input is a list in the reviewed manifest.
    retained = json.loads((AUDIT / 'retained-inputs.json').read_text())
    if isinstance(retained, dict):
        retained = retained.get('files', retained.get('keep_files'))
    for row in retained:
        kept[row['drive'] + '/' + row['path']] = set(row.get('reasons', ['Reviewed rebuild input']))
    for row in inventory['files']:
        if Path(row['path']).suffix.lower() == '.log':
            kept.setdefault(row['drive']+'/'+row['path'], set()).add('Historical diagnostic evidence, including failed cooks')
    kept.setdefault('F/output/castle_next/donors/donor-manifest.json', set()).add('Lossless historical aggregate donor input')
    kept.setdefault('F/output/release_020/native-build.lock', set()).add('Shared native editor serialization lock, never retire')
    for name in ('community_civilization_pack.sga','community_civilization_pack-0.7.0.zip'):
        old = ('F/output/release_070/release/assembly-v1/' if name.endswith('.sga') else 'F/output/release_070/release/') + name
        kept.pop(old, None)
        kept['F/archives/release_070_rollback/'+name] = {'Exact independently stored 0.7.0 rollback'}
    def keep(p, reason):
        k = key(p)
        assert physical(k).is_file(), p
        kept.setdefault(k, set()).add(reason)
    # Preserve every editable master, even historical alternatives, and every
    # external image that Blender actually resolved. No master needs rewriting.
    deps = json.loads((AUDIT / 'blend-dependencies.json').read_text())
    if isinstance(deps, dict):
        deps = deps.get('files', deps.get('blends'))
    for row in deps:
        keep(row['blend'], 'All editable Blender masters, byte unchanged')
        for image in row['images']:
            if not image['packed'] and image.get('resolved') and image.get('exists'):
                keep(image['resolved'], 'External image required by retained Blender master')
    for p in walk(ROOT / 'art'):
        if p.suffix.lower() in {'.fbx', '.obj'}:
            keep(p, 'All editable mesh exchange sources')
    for item in proposal['qualified_authored_geometry_specs']:
        spec = item['inputs']
        body = Path(spec['template_body'])
        project = Path(spec['template_project'])
        for name in ('model.fbx', 'model.rig', 'model.rgo', 'model.rgotemplate', 'model.material', 'albedo.png', 'normal.png', 'metalness.png', 'roughness.png'):
            keep(body / name, 'Native unit rebuild template: ' + item['model'])
        keep(project / 'project/source/_default.burnproj', 'Native unit burner rules: ' + item['model'])
    # Include new/concurrently added files, never delete unknown material.
    audited = {r['drive'] + '/' + r['path'] for r in inventory['files']}
    print('Keeping new E source files; F retirement limited to audited paths', flush=True)
    for drive, root in [('E', ROOT)]:
        for p in walk(root):
            k = drive + '/' + p.relative_to(root).as_posix()
            if k not in audited and not any(k.startswith('F/' + x) for x in ('consolidation_071/', 'resources_071/', 'staging/r71/', 'output/release_071/', 'archives/release_070_rollback/')):
                keep(p, 'New file since read-only audit')
    # Pin all files and current editable source before any mutation.
    rows = {}
    reused = {}
    duplicate_doc = json.loads((AUDIT / 'duplicates.json').read_text())
    for group in duplicate_doc['duplicate_groups']:
        for r in group['files']:
            reused[r['drive'] + '/' + r['path']] = (r['bytes'], r['mtime_ns'], group['sha256'])
    if (TX/'retained.json').exists():
        for k,r in json.loads((TX/'retained.json').read_text()).items():
            reused[k] = (r['bytes'],r['mtime_ns'],r['sha256'])
    print('Hashing retained inputs', len(kept), flush=True)
    for i, (k, reasons) in enumerate(sorted(kept.items())):
        p = physical(k)
        st = p.stat()
        old = reused.get(k)
        digest = old[2] if old and old[:2] == (st.st_size, st.st_mtime_ns) else sha(p)
        rows[k] = dict(bytes=st.st_size, mtime_ns=st.st_mtime_ns, sha256=digest, reasons=sorted(reasons))
        if i % 1000 == 0:
            print(i, k, flush=True)
    normal = Path(CFG['source_root'])
    normal_hashes = {p.relative_to(normal).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in walk(normal)}
    dump(TX / 'normal-before.json', normal_hashes)
    dump(TX / 'retained.json', rows)
    dump(TX / 'geometry-specs.json', proposal['qualified_authored_geometry_specs'])
    # Keep JSON compressed outside its original location, exposing original
    # logical paths via the indexed loader. Other inputs stay at original paths.
    index = {}
    total = 0
    same_volume = {}
    for i, (k, row) in enumerate(rows.items()):
        p = physical(k)
        if p.suffix.lower() == '.json' and row['bytes'] >= 1048576:
            blob = 'blobs/' + row['sha256'] + '.json.gz'
            dest = STORE / blob
            good = False
            if dest.exists():
                try:
                    with gzip.open(dest, 'rb') as existing:
                        good = hashlib.file_digest(existing, 'sha256').hexdigest() == row['sha256']
                except (EOFError, OSError):
                    good = False
            if not good:
                dest.parent.mkdir(parents=True, exist_ok=True)
                temporary = dest.with_suffix('.tmp')
                with p.open('rb') as inp, temporary.open('wb') as out:
                    with gzip.GzipFile(filename='', mode='wb', compresslevel=6, fileobj=out, mtime=0) as packed:
                        shutil.copyfileobj(inp, packed)
                temporary.replace(dest)
            index[k] = dict(blob=blob, codec='gzip', bytes=row['bytes'], sha256=row['sha256'])
            row['packed'] = True
        else:
            immutable_native = {'.dds','.rrtex','.rhka','.rgm','.rgo','.rrgeom','.rrmaterial'}
            share = False  # Owned F: is exFAT; use bundle_exfat, never hardlinks.
            identity = row['sha256'] if share else k
            canonical = same_volume.setdefault((k[0], identity), k)
            row['canonical'] = canonical
            if canonical == k:
                total += row['bytes']
        if i % 1000 == 0:
            print('Packing', i, flush=True)
    dump(STORE / 'index.json', dict(schema='ccp.resource-store/v1', roots={k:str(v) for k,v in ROOTS.items()}, files=index))
    for k in index:
        ResourceStore(STORE, index).read(k)
    store_bytes = sum(p.stat().st_size for p in walk(STORE))
    total += store_bytes
    dump(TX / 'retained.json', rows)
    dump(TX / 'preparation.json', dict(files=len(rows), packed_files=len(index), retained_physical_bytes=total, store_bytes=store_bytes, all_blends=len([k for k in rows if k.endswith('.blend')]), note='Excludes additional 071 delivery and compact transaction evidence.'))
    print(json.dumps(json.loads((TX / 'preparation.json').read_text()), indent=2), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        prepare()
