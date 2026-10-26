"""Supported compact-checkout workflows; immutable evidence stays in the store."""
import argparse
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/collaboration'))
from store import Reader, load, write_json, file_sha, safe_path, sha, check_text, walk
import dev as legacy

FOLDER = ROOT/'development-data/current-084-v1'
FINAL = 'external/output/release_084/delivery/final-v1/'


class AliasReader(Reader):
    def git_pack(self,name):
        if Path(name).name!=name or name not in self.doc['packs']:
            raise ValueError('Unsafe or undeclared pack name')
        config=ROOT/'workspace.json'
        cfg=load(config) if config.exists() else {}
        executable=os.environ.get('GIT_EXECUTABLE') or cfg.get('git_path') or shutil.which('git')
        if not executable:raise ValueError('Git is required to read an omitted immutable pack')
        relative=(self.folder/name).resolve().relative_to(ROOT.resolve()).as_posix()
        result=subprocess.run([str(executable),'-C',str(ROOT),'show','HEAD:'+relative],capture_output=True)
        expected=self.doc['packs'][name]
        if result.returncode or len(result.stdout)!=expected['bytes'] or sha(result.stdout)!=expected['sha256']:
            raise ValueError('Missing or corrupt Git-backed immutable pack: '+name)
        return result.stdout

    def chunk(self,h):
        row=self.doc['chunks'][h];name=row['pack']
        if Path(name).name!=name or name not in self.doc['packs']:
            raise ValueError('Unsafe or undeclared pack name')
        if name not in self.opened and not (self.folder/name).is_file():
            data=self.git_pack(name)
            if len(self.opened)>=8:self.opened.pop(next(iter(self.opened))).close()
            self.opened[name]=zipfile.ZipFile(io.BytesIO(data))
        return super().chunk(h)

    def verify(self,progress=None):
        for name,row in self.doc['packs'].items():
            if Path(name).name!=name:raise ValueError('Unsafe pack name')
            path=self.folder/name
            if path.is_file():
                if path.stat().st_size!=row['bytes'] or file_sha(path)!=row['sha256']:
                    raise ValueError('Corrupt pack: '+name)
            else:
                self.git_pack(name)
        for i,key in enumerate(self.doc['files'],1):
            check_text(key,self.read(key))
            if progress and i%2000==0:progress(i)
        return dict(files=len(self.doc['files']),chunks=len(self.doc['chunks']),packs=len(self.doc['packs']))

    def read(self, key):
        key = self.doc.get('aliases', {}).get(key, key)
        # Keys address virtual archive records, not physical workspace files.
        if '\\' in key or key.startswith('/') or any(p in ('','.','..') or ':' in p for p in key.split('/')) or key.split('/')[0] not in ('source','external'):
            raise ValueError('Unsafe virtual development-data key')
        row = self.doc['files'][key]
        data = b''.join(self.chunk(h) for h in row['chunks'])
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            raise ValueError('Corrupt development-data file: '+key)
        return data


def load_index(index):
    doc = load(index)
    if 'base_index' in doc:
        name = doc['base_index']
        if Path(name).name != name or name in ('', '.', '..') or ':' in name or '\\' in name:
            raise ValueError('Unsafe base index')
        base = load(index.parent/name)
        if 'base_index' in base:
            raise ValueError('Only one immutable baseline layer is supported')
        for field in ('files', 'chunks', 'packs'):
            base[field].update(doc[field])
        base['milestone'] = doc['milestone']
        doc = base
    return doc


def reader():
    config = load(ROOT/'development.json')
    index = (ROOT/config['data_index']).resolve()
    if index.parent != FOLDER.resolve():
        raise ValueError('Unexpected compact input index location')
    return AliasReader(FOLDER, load_index(index))


def rebase_text(text, origins):
    """Relocate only working copies; escaped JSON and ordinary Windows paths."""
    for old, new in origins:
        parts = old.replace('\\', '/').strip('/').split('/')
        pattern = r'[/\\]+'.join(re.escape(p) for p in parts)
        text = re.sub(pattern + r'(?=[/\\"\'\s]|$)', lambda _:new.replace('\\','/'), text, flags=re.I)
    # Convert suffix separators only in a relocated path token, not unrelated code.
    for _, new in origins:
        pattern = re.escape(new.replace('\\','/')) + r'[^"\'\r\n]*'
        text = re.sub(pattern, lambda m:re.sub(r'\\+', '/', m.group()), text)
    return text


def check_member(member):
    if not member or member.startswith('/') or '\\' in member or ':' in member or any(p in ('','.','..') for p in member.split('/')):
        raise ValueError('Unsafe archive member: '+member)
    return member


def overlay_map(mapping, parent):
    groups = {'attrib': [], 'data': []}
    for member, value in mapping.items():
        check_member(member)
        path = (parent/value).resolve()
        if not path.is_file():
            raise ValueError('Missing replacement: '+str(path))
        groups['attrib' if member.startswith('attrib/') else 'data'].append((member,path))
    return groups


def restore(args, r):
    dest = args.destination.resolve()
    source_parent = (args.source_parent or dest).resolve()
    if dest == ROOT or dest.is_relative_to(ROOT/'development-data') or source_parent == ROOT:
        raise ValueError('Restore into a separate workspace')
    count = 0
    for key in r.doc['files']:
        if args.profile == 'art':
            wanted = key.startswith(('source/art/','external/garrison-library/','external/stock-cache/','external/resources_'))
        elif args.profile == 'voices':
            wanted = key.endswith('.ogg') or key.startswith('external/output/release_084/local/') and key.count('/') == 4
        elif args.profile == 'all':
            wanted = True
        else:
            wanted = key.startswith(('source/','external/resources_','external/garrison-library/','external/stock-cache/',
                                     'external/output/release_085/'))
        if args.prefix:
            wanted = key.startswith(args.prefix)
        if wanted:
            count += r.restore(key, source_parent if key.startswith('source/') else dest)
            if count and count%1000 == 0:
                print('RESTORED', count, flush=True)
    # Maintain contributor fixes rather than resurrecting frozen owner scripts.
    src = source_parent/'source'
    if src.exists() and args.profile in ('development','all') and not args.prefix:
        for file in walk(ROOT):
            rel = file.relative_to(ROOT)
            if rel.parts[0] in ('development-data','.local') or file.name == 'workspace.json':
                continue
            target = src/rel
            old = r.doc['files'].get('source/'+rel.as_posix())
            if target.exists() and file_sha(target) != file_sha(file) and (not old or file_sha(target) != old['sha256']):
                raise ValueError('Edited working file preserved: '+str(target))
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists() or file_sha(target) != file_sha(file):
                shutil.copy2(file,target)
    print(json.dumps(dict(restored=count,source=str(src),external=str(dest/'external'))))


def configure(args, r):
    dest = args.destination.resolve()
    src = (args.source_parent or dest).resolve()/'source'
    external = dest/'external'
    if src == ROOT or not (src/'workspace.json').exists():
        raise ValueError('Restore development into a separate workspace first')
    if legacy.filesystem(src) != 'NTFS':
        raise ValueError('Source workspace must be on NTFS; use --source-parent')
    local = load(args.tools) if args.tools else {}
    cfg = load(src/'workspace.json')
    write_json(src/'workspace.original.json', cfg) if not (src/'workspace.original.json').exists() else None
    # Never fall back to original owner roots for optional preservation comparisons.
    cfg['source_root'] = str(src/'.optional-normal-reference')
    cfg['donor_root'] = str(src/'.optional-donor-reference')
    write_json(src/'workspace.json', cfg)
    legacy.configure(args)
    origins = [(r.doc['provenance']['source_root'],str(src)),
               (r.doc['provenance']['external_root'],str(external))]
    changes = []
    # Frozen reports remain original. These are new, logged working recipe copies.
    roots = [src/'tools',src/'art/recipes',external/'garrison-library']
    for base in roots:
        if not base.exists():
            continue
        for file in walk(base):
            if file.suffix not in ('.py','.ps1','.json','.toml','.ini','.cfg'):
                continue
            before = file.read_bytes()
            try:
                text = before.decode('utf-8-sig')
            except UnicodeDecodeError:
                continue
            updated = rebase_text(text, origins).encode('utf-8')
            if updated != before:
                file.write_bytes(updated)
                changes.append(dict(path=str(file),before=sha(before),after=sha(updated)))
    for name in ('resources_071','resources_080'):
        index = external/name/'index.json'
        if index.exists():
            doc = load(index)
            doc['roots'] = dict(E=str(src),F=str(external))
            write_json(index.with_name('index.original.json'),load(index)) if not index.with_name('index.original.json').exists() else None
            write_json(index,doc)
    # Used by isolated Blender path repair and new voice jobs; no secrets.
    write_json(src/'workspace.compact.json', dict(origins=origins,tools=local,source=str(src),external=str(external)))
    receipt = src/'relocation-proof.json'
    previous = load(receipt) if receipt.exists() else dict(runs=[])
    previous.setdefault('runs',[]).append(dict(changed_working_recipes=changes,immutable_store_changed=False))
    write_json(receipt,previous)
    manifest = ROOT/'docs/compact/art-inputs.json'
    if manifest.exists():
        from recover_inputs import Recovery
        recovery = Recovery(r,src/'workspace.compact.json')
        try:
            for key in load(manifest)['keys']:
                recovery.recover(key)
            write_json(src/'art-input-recovery-proof.json',dict(passed=True,files=recovery.rows))
        finally:
            recovery.close()
    print('PORTABLE_WORKSPACE_CONFIGURED', src, len(changes),flush=True)


def verify_bank(r):
    members = {m:row for m,row in r.doc['current_payloads'].items() if m.endswith('.ogg')}
    total = 0
    for i,(member,row) in enumerate(members.items(),1):
        data = r.read(row['key'])
        if sha(data) != row['sha256'] or not data.startswith(b'OggS'):
            raise ValueError('Changed/invalid shipped audio: '+member)
        total += len(data)
    if len(members) != 10529 or total != 118761135:
        raise ValueError('Current shipped audio coverage differs')
    print(json.dumps(dict(ogg_files=len(members),bytes=total,wav_required=False,unchanged=True)))


def rebuild(args, r):
    legacy.ROOT = ROOT
    policy = json.loads(r.read(FINAL+'changed-member-policy.json'))
    paths = {row['file']:r.doc['current_payloads'][m]['key'] for m,row in policy['payload'].items()}
    legacy.path_key = lambda value, doc:paths[value]
    legacy.rebuild(args,r)


def patch_archive(args):
    """Explicit selective integration on an existing owning archive, never a broad replacement."""
    mapping = load(args.manifest)
    groups = overlay_map(mapping,args.manifest.resolve().parent)
    dest = args.destination.resolve()
    if dest.exists():
        raise FileExistsError('Use a new immutable destination')
    if not mapping:
        raise ValueError('Empty change policy')
    dest.mkdir(parents=True)
    listing = json.loads(legacy.run([args.archive_tool,'list',args.base,'--verify'],dest,'baseline-list'))
    if listing['archive']['name'] != legacy.NAMESPACE or not listing['archive']['verification']['verified']:
        raise ValueError('Base namespace/verification differs')
    readback = dest/'baseline-readback'
    legacy.run([args.archive_tool,'extract',args.base,readback,'--filter','.'],dest,'baseline-extract')
    expected = {p.relative_to(readback).as_posix():file_sha(p) for p in readback.rglob('*') if p.is_file()}
    mounts = {m['path']:m['toc'] for m in listing['members']}
    current = args.base.resolve()
    replacements = {}
    for alias, rows in groups.items():
        if not rows:
            continue
        manifest = dest/(alias+'-members.txt')
        manifest.write_bytes(('\n'.join(m+'='+str(p) for m,p in rows)+'\n').encode('utf-8'))
        target = dest/(alias+'.sga')
        legacy.run([args.archive_tool,'set-members',current,manifest,target,'--alias',alias],dest,'overlay-'+alias)
        current = target
        for member,path in rows:
            expected[member] = file_sha(path)
            replacements[member] = file_sha(path)
            mounts.setdefault(member,alias)
    final = dest/'community_civilization_pack.sga'
    shutil.copy2(current,final)
    final_listing = json.loads(legacy.run([args.archive_tool,'list',final,'--verify'],dest,'final-list'))
    fresh = dest/'fresh-readback'
    legacy.run([args.archive_tool,'extract',final,fresh,'--filter','.'],dest,'final-extract')
    actual = {p.relative_to(fresh).as_posix():file_sha(p) for p in fresh.rglob('*') if p.is_file()}
    if actual != expected or {m['path']:m['toc'] for m in final_listing['members']} != mounts:
        raise ValueError('Member bytes or mounts escaped explicit policy')
    if final_listing['archive']['name'] != legacy.NAMESPACE or not final_listing['archive']['verification']['verified']:
        raise ValueError('Final namespace differs')
    write_json(dest/'integration-proof.json',dict(base_sha256=file_sha(args.base),sga_sha256=file_sha(final),
        replacements=replacements,members=len(actual),namespace=legacy.NAMESPACE,
        native_compile=False,native_game_test=False))
    print('SELECTIVE_INTEGRATION_VERIFIED',final)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command',required=True)
    sub.add_parser('verify')
    sub.add_parser('verify-audio')
    for name in ('restore','configure'):
        a = sub.add_parser(name)
        a.add_argument('--destination',type=Path,required=True)
        a.add_argument('--source-parent',type=Path)
        if name == 'restore':
            a.add_argument('--profile',choices=['development','art','voices','all'],default='development')
            a.add_argument('--prefix')
        else:
            a.add_argument('--tools',type=Path)
    a = sub.add_parser('release')
    a.add_argument('--destination',type=Path,required=True)
    a.add_argument('--archive-tool',type=Path)
    a = sub.add_parser('rebuild-088', aliases=['rebuild-087'])
    a.add_argument('--destination',type=Path,required=True)
    a.add_argument('--archive-tool',type=Path,required=True)
    a = sub.add_parser('rebuild-084')
    a.add_argument('--destination',type=Path,required=True)
    a.add_argument('--archive-tool',type=Path,required=True)
    a = sub.add_parser('integrate')
    a.add_argument('--base',type=Path,required=True)
    a.add_argument('--manifest',type=Path,required=True)
    a.add_argument('--archive-tool',type=Path,required=True)
    a.add_argument('--destination',type=Path,required=True)
    args = p.parse_args()
    if args.command == 'integrate':
        patch_archive(args)
        return
    r = reader()
    try:
        if args.command == 'verify':
            legacy.check_source_identity(ROOT)
            print(json.dumps(r.verify(lambda n:print('VERIFIED_FILES',n,flush=True))))
        elif args.command == 'verify-audio':
            verify_bank(r)
        elif args.command == 'restore':
            restore(args,r)
        elif args.command == 'configure':
            configure(args,r)
        elif args.command == 'release':
            if 'milestone' in r.doc:
                from current_package import rebuild as rebuild_current
                rebuild_current(args,r)
            else:
                legacy.release(args,r)
        elif args.command in ('rebuild-087','rebuild-088'):
            from current_package import rebuild as rebuild_current
            rebuild_current(args,r)
        elif args.command == 'rebuild-084':
            rebuild(args,r)
    finally:
        r.close()


if __name__ == '__main__':
    main()
