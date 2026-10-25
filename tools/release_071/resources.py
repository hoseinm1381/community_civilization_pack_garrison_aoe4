"""Lossless retained rebuild inputs. Index keys preserve original owning paths."""
import gzip
import hashlib
import json
import zipfile
from pathlib import Path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class ResourceStore:
    def __init__(self, root, index=None):
        self.root = Path(root).resolve()
        self.index = index if index is not None else json.loads((self.root / 'index.json').read_text())['files']
        self._archives={}

    def read(self, key):
        visited = set()
        while True:
            if key in visited:
                raise ValueError('Resource alias cycle: ' + key)
            visited.add(key)
            row = self.index[key]
            if 'alias' not in row:
                break
            key = row['alias']
        relative = Path(row['blob'])
        path = (self.root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(self.root):
            raise ValueError('Resource escapes store')
        if row['codec']=='zip':
            archive=self._archives.setdefault(str(path),None)
            if archive is None:
                archive=zipfile.ZipFile(path);self._archives[str(path)]=archive
            data=archive.read(row['member'])
        elif row['codec']=='gzip':
            data=gzip.decompress(path.read_bytes())
        elif row['codec']=='raw':
            data=path.read_bytes()
        else:
            raise ValueError('Unknown resource codec')
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Resource integrity failure: ' + key)
        return data

    def read_json(self, key):
        return json.loads(self.read(key).decode('utf-8-sig'))

    def materialize(self, key, destination):
        data = self.read(key)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return destination

    def materialize_tree(self, keys, destination):
        root=Path(destination).resolve()
        result={}
        for key in keys:
            relative=Path(key)
            target=(root/relative).resolve()
            if relative.is_absolute() or '..' in relative.parts or not target.is_relative_to(root):
                raise ValueError('Materialized input escapes destination')
            result[key]=self.materialize(key,target)
        return result


def deletion_gate(proof):
    for key in ('package', 'rollback', 'native_source', 'asset_cooks', 'resources', 'editable', 'normal_unchanged', 'review'):
        if proof.get(key) is not True:
            raise ValueError('Cleanup blocked: ' + key)
    if not 0 < proof.get('retained_bytes', 0) < 3000000000:
        raise ValueError('Cleanup blocked: retained storage budget')
