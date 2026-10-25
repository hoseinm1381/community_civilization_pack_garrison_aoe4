"""Lossless content-addressed developer inputs. Standard-library Python 3.12+."""
from pathlib import Path, PurePosixPath
import base64
import gzip
import hashlib
import json
import os
import re
import zipfile

TEXT = {'.py','.ps1','.md','.txt','.json','.jsonl','.xml','.scar','.lua','.csv','.log',
        '.rdo','.burnproj','.aoe4mod','.locdb','.ini','.cfg','.toml','.yaml','.yml','.html','.js'}
SECRET = re.compile(rb'\b(?:sk_[A-Za-z0-9]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')


def sha(data): return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def safe_path(root, key):
    if '\\' in key or key.startswith('/') or any(p in ('','..','.') or ':' in p for p in key.split('/')):
        raise ValueError('Unsafe development-data key')
    p=PurePosixPath(key)
    if p.parts[0] not in ('source','external'): raise ValueError('Unknown development-data root')
    root=Path(root).resolve(); target=root.joinpath(*p.parts)
    if not target.resolve().is_relative_to(root): raise ValueError('Development-data path escapes root')
    return target


def check_text(name, data):
    if Path(name).suffix.lower() not in TEXT and not Path(name).name.startswith('.env'):return
    if SECRET.search(data):raise ValueError('Credential-like content refused in '+name)
    for match in re.finditer(rb'(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{60,180}={0,2}(?![A-Za-z0-9+/=])',data):
        try:decoded=base64.b64decode(match.group(),validate=True)
        except ValueError:continue
        if decoded.count(b':')==1 and all(33<=c<=126 for c in decoded):
            left,right=decoded.split(b':')
            if len(left)>=16 and len(right)>=16:raise ValueError('Encoded credential-like content refused in '+name)


def walk(root):
    stack=[Path(root)]
    while stack:
        with os.scandir(stack.pop()) as entries:
            for e in entries:
                if e.is_symlink() or e.is_junction(): continue
                if e.is_dir(follow_symlinks=False):
                    if e.name not in ('.git','__pycache__','.pytest_cache','.codegraph'): stack.append(Path(e.path))
                elif e.is_file(follow_symlinks=False): yield Path(e.path)


def write_json(path, doc):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(doc,ensure_ascii=True,separators=(',',':')).encode()
    p.write_bytes(gzip.compress(data,mtime=0) if p.suffix=='.gz' else data+b'\n')


def load(path):
    p=Path(path); data=p.read_bytes()
    return json.loads(gzip.decompress(data) if p.suffix=='.gz' else data)


class Writer:
    def __init__(self, folder, chunk_size=16*1024*1024, pack_size=40*1024*1024, previous=None):
        self.folder=Path(folder); self.folder.mkdir(parents=True,exist_ok=True)
        self.chunk_size=chunk_size; self.pack_size=pack_size; self.archive=None; self.used=0
        self.doc=previous or dict(schema='garrison.development-data/v1',files={},chunks={},packs={})
        existing=[p.name for p in self.folder.glob('pack-*.zip') if re.fullmatch(r'pack-\d+\.zip',p.name)]
        self.number=max([int(n[5:-4]) for n in set(self.doc['packs'])|set(existing)] or [0])

    def close_pack(self):
        if self.archive:
            self.archive.close(); p=self.folder/self.name
            self.doc['packs'][self.name]=dict(bytes=p.stat().st_size,sha256=file_sha(p))
            self.archive=None

    def add(self, key, data):
        safe_path(self.folder, key); check_text(key,data)
        pieces=[]
        for offset in range(0,len(data),self.chunk_size):
            chunk=data[offset:offset+self.chunk_size]; h=sha(chunk); pieces.append(h)
            if h in self.doc['chunks']: continue
            if self.archive and (self.used+len(chunk)>self.pack_size or len(self.archive.filelist)>=4096): self.close_pack()
            if self.archive is None:
                self.number+=1; self.name=f'pack-{self.number:05d}.zip'; self.used=0
                self.archive=zipfile.ZipFile(self.folder/self.name,'x',zipfile.ZIP_DEFLATED,compresslevel=6)
            self.archive.writestr(h,chunk); self.used+=len(chunk)
            self.doc['chunks'][h]=dict(pack=self.name,bytes=len(chunk))
        self.doc['files'][key]=dict(bytes=len(data),sha256=sha(data),chunks=pieces)

    def finish(self):
        self.close_pack(); return self.doc


class Reader:
    def __init__(self, folder, doc): self.folder=Path(folder); self.doc=doc; self.opened={}

    def chunk(self,h):
        row=self.doc['chunks'][h]; name=row['pack']
        if Path(name).name!=name or name not in self.doc['packs']:
            raise ValueError('Unsafe or undeclared pack name')
        if name not in self.opened:
            if len(self.opened)>=8:
                oldest=next(iter(self.opened)); self.opened.pop(oldest).close()
            self.opened[name]=zipfile.ZipFile(self.folder/name)
        data=self.opened[name].read(h)
        if len(data)!=row['bytes'] or sha(data)!=h: raise ValueError('Corrupt development-data chunk')
        return data

    def read(self,key):
        safe_path(self.folder,key); row=self.doc['files'][key]
        data=b''.join(self.chunk(h) for h in row['chunks'])
        if len(data)!=row['bytes'] or sha(data)!=row['sha256']: raise ValueError('Corrupt development-data file: '+key)
        return data

    def restore(self,key,destination):
        path=safe_path(destination,key); row=self.doc['files'][key]
        if path.exists():
            if path.is_file() and file_sha(path)==row['sha256']: return False
            raise ValueError('Edited destination preserved: '+str(path))
        data=self.read(key); path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f: f.write(data)
        return True

    def verify(self,progress=None):
        for name,row in self.doc['packs'].items():
            if Path(name).name!=name: raise ValueError('Unsafe pack name')
            p=self.folder/name
            if p.stat().st_size!=row['bytes'] or file_sha(p)!=row['sha256']: raise ValueError('Corrupt pack: '+name)
        for i,key in enumerate(self.doc['files'],1):
            data=self.read(key);check_text(key,data)
            if progress and i%2000==0: progress(i)
        return dict(files=len(self.doc['files']),chunks=len(self.doc['chunks']),packs=len(self.doc['packs']))

    def close(self):
        for z in self.opened.values(): z.close()
        self.opened.clear()
