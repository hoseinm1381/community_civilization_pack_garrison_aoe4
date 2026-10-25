"""Independent original-path recovery; edited destinations are never overwritten."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import zipfile


def canonical(path):
    return Path(str(path).removeprefix('\\\\?\\')).resolve()


def owned_key(path, roots):
    target = canonical(path)
    for label, root in roots.items():
        root = canonical(root)
        if target.is_relative_to(root):
            return label + '/' + target.relative_to(root).as_posix()
    raise ValueError('Outside owned roots: ' + str(path))


def key_path(key, roots):
    key = key.replace('\\', '/')
    parts = PurePosixPath(key).parts
    if len(parts) < 2 or parts[0] not in roots or any(
            p in ('.', '..') or ':' in p for p in parts):
        raise ValueError('Invalid original-path key: ' + key)
    root = canonical(roots[parts[0]])
    if not root.is_dir():
        raise ValueError('Owned storage is unavailable: ' + str(root))
    target = canonical(root.joinpath(*parts[1:]))
    if not target.is_relative_to(root):
        raise ValueError('Recovery path escapes root: ' + key)
    return target


class ResourceStore:
    def __init__(self, bundle, index, roots):
        self.bundle, self.index, self.roots = Path(bundle), index, roots
        self._zip = None

    def close(self):
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    def read(self, key):
        row = self.index[key]
        if self._zip is None:
            self._zip = zipfile.ZipFile(self.bundle)
        data = self._zip.read(row['member'])
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Recovery integrity failure: ' + key)
        return data

    def restore(self, key, destination=None):
        original = key_path(key, self.roots)
        target = original if destination is None else canonical(destination)
        owned_key(target, self.roots)
        data = self.read(key)
        if target.exists():
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError('Edited destination preserved: ' + str(target))
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents replacing a concurrent edit.
        with target.open('xb') as stream:
            stream.write(data)
        return target

    def restore_required(self, keys):
        restored = []
        for key in keys:
            existed = key_path(key, self.roots).exists()
            target = self.restore(key)  # Also verify an existing fixture; refuse edits.
            if not existed:
                restored.append(str(target))
        return restored


def retirement_gate(proof):
    for name in ('approved', 'package', 'rollbacks', 'native_source', 'asset_cooks',
                 'recovery', 'editable', 'normal', 'review'):
        if proof.get(name) is not True:
            raise ValueError('Retirement blocked: ' + name)
    if not 0 < proof.get('projected_allocated', 0) < 6_000_000_000:
        raise ValueError('Retirement blocked: allocated budget')


def main():
    from common import ROOTS, STORE, guard, read
    guard()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['list', 'verify', 'restore'])
    p.add_argument('key', nargs='?')
    args = p.parse_args()
    doc = read(STORE / 'index.json')
    store = ResourceStore(STORE / doc['bundle'], doc['files'], ROOTS)
    try:
        if args.command == 'list':
            print('\n'.join(store.index))
        elif args.command == 'restore':
            print(store.restore(args.key))
        else:
            seen = set()
            for key, row in store.index.items():
                if row['member'] in seen:
                    continue
                store.read(key)
                seen.add(row['member'])
            print('Verified', len(store.index), 'original keys /', len(seen), 'payloads')
    finally:
        store.close()


if __name__ == '__main__':
    main()
