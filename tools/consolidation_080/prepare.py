"""Keep-first input consolidation. No original input is removed here."""
import collections
import hashlib
import shutil
import time
import zipfile
from common import *
from store import canonical, owned_key


def main():
    guard()
    inventory = read(TX / 'hashed-inventory.json')['files']
    rows = {r['root'] + '/' + r['path']: r for r in inventory}
    STORE.mkdir(exist_ok=True)
    bundle = STORE / 'payloads-v1.zip'
    if bundle.exists():
        raise FileExistsError('Preserve existing store attempt')
    linked = {owned_key(x['path'], ROOTS) for x in read(TX / 'canonical-image-dependencies.json')['images']}
    full = read(TX / 'blend-full-dependencies.json')
    assert len(full) == 339 and all('error' not in r for r in full)
    assert all(x['exists'] for r in full for x in r['paths'])
    shared_tools = {}
    brush = canonical(Path(CFG['blender']).parent / '5.2/datafiles/assets/brushes/essentials_brushes-gp_draw.blend')
    for r in full:
        for x in r['paths']:
            p = canonical(x['path'])
            if p == brush:
                shared_tools[str(p)] = {'sha256': sha(p), 'reason': 'Installed Blender essential brush, not model source'}
                continue
            if p.is_file():
                linked.add(owned_key(p, ROOTS))
            elif p.is_dir():
                linked.update(owned_key(n, ROOTS) for n in walk(p))
    write(TX / 'shared-tool-dependencies.json', shared_tools)
    keep, recovery, retired, native, zips = {}, {}, {}, {}, {}
    for key, row in rows.items():
        p = ROOTS[row['root']] / row['path']
        plain = (row['root'] == 'E' or key in linked or key.startswith((
            'F/resources_071/', 'F/consolidation_071/', 'F/archives/release_070_rollback/',
            'F/tool-cache/', 'F/garrison-library/')) or key == 'F/output/release_020/native-build.lock'
            or (key.startswith('F/output/release_0712/delivery/final-v1/') and p.name in {
                'community_civilization_pack.sga', 'community_civilization_pack-0.7.12.zip',
                'garrison.json', 'START-HERE.txt', 'delivery-proof.json', 'verification.json'})
            or p.suffix.lower() in {'.fbx', '.obj', '.rig', '.rgotemplate', '.material'})
        if plain:
            keep[key] = row | {'reason': 'Editable/plain dependency or designated protected baseline'}
        else:
            recovery[key] = row
    write(TX / 'plain-retention.json', keep)
    written = set()
    native_by_hash = collections.defaultdict(list)
    for k, r in recovery.items():
        if k.lower().endswith('.sga'):
            native_by_hash[r['sha256']].append(k)
    file_index, native_index, zip_index = {}, {}, {}
    start = last = time.monotonic()

    with zipfile.ZipFile(bundle, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as out:
        def add_data(key, data, expected=None):
            h = hashlib.sha256(data).hexdigest()
            if expected is not None:
                assert h == expected, key
            if h not in written:
                out.writestr(h, data)
                written.add(h)
            file_index[key] = {'member': h, 'sha256': h, 'bytes': len(data)}

        for i, (key, row) in enumerate(recovery.items()):
            p = ROOTS[row['root']] / row['path']
            assert p.stat().st_size == row['bytes'] and p.stat().st_mtime_ns == row['mtime_ns'], key
            if p.suffix.lower() == '.sga':
                continue
            if p.suffix.lower() == '.zip':
                with zipfile.ZipFile(p) as z:
                    names = z.namelist()
                    delivery = 'garrison.json' in names and any(n.lower().endswith('.sga') for n in names)
                    if delivery:
                        listing = []
                        for n in names:
                            if n.endswith('/'):
                                continue
                            data = z.read(n)
                            h = hashlib.sha256(data).hexdigest()
                            entry = {'path': n, 'bytes': len(data), 'sha256': h}
                            if n.lower().endswith('.sga'):
                                matches = [k for k, r in rows.items() if r['sha256'] == h and k.lower().endswith('.sga')]
                                if not matches:
                                    # Unique embedded native archives remain exact raw recovery inputs.
                                    target = 'F/resources_080/recovered_zip/' + row['sha256'] + '/' + n
                                    add_data(target, data, h)
                                    entry['recovery_key'] = target
                                else:
                                    entry['native_archive_keys'] = matches
                            else:
                                target = 'F/resources_080/recovered_zip/' + row['sha256'] + '/' + n
                                add_data(target, data, h)
                                entry['recovery_key'] = target
                            listing.append(entry)
                        zip_index[key] = {'sha256': row['sha256'], 'members': listing,
                                          'reason': 'Redundant delivery retired; unique contents preserved'}
                        continue
            add_data(key, p.read_bytes(), row['sha256'])
            if time.monotonic() - last > 20:
                print('PACKED_INPUTS', i + 1, '/', len(recovery), 'unique', len(written), flush=True)
                last = time.monotonic()

        for i, (digest, keys) in enumerate(native_by_hash.items()):
            source = ROOTS[keys[0][0]] / keys[0][2:]
            assert sha(source) == digest
            listing = json.loads(run('list-' + digest[:16], [CFG['archive_tool'], 'list', source, '--verify'], TX / 'native-logs'))
            target = STAGE / 'native-harvest' / digest
            if target.exists():
                raise FileExistsError('Preserve partial native harvest')
            run('extract-' + digest[:16], [CFG['archive_tool'], 'extract', source, target, '--filter', '.'], TX / 'native-logs')
            mounts = {m['path']: m['toc'] for m in listing['members']}
            members = {}
            harvested = list(walk(target))
            for p in harvested:
                rel = p.relative_to(target).as_posix()
                assert rel in mounts
                key = 'F/resources_080/recovered_native/' + digest + '/' + rel
                add_data(key, p.read_bytes())
                members[rel] = file_index[key] | {'recovery_key': key, 'toc': mounts[rel]}
            assert set(members) == set(mounts)
            native_index[digest] = {'original_keys': keys, 'archive': listing['archive'], 'members': members}
            if not members:
                assert listing['archive']['file_count'] == 0
                # Failed/empty cook containers have no member payload route.
                # Preserve their exact original bytes as compact diagnostics.
                for key in keys:
                    keep[key] = recovery.pop(key) | {'reason': 'Exact verified empty failed-cook diagnostic SGA preserved plain'}
            # These are newly generated readbacks; original archives remain intact.
            for p in harvested:
                assert canonical(p).is_relative_to(canonical(STAGE / 'native-harvest'))
                p.unlink()
            dirs = [p for p in target.rglob('*') if p.is_dir() and not p.is_junction()]
            for p in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
                p.rmdir()
            target.rmdir()
            print('NATIVE_ARCHIVES_PRESERVED', i + 1, '/', len(native_by_hash),
                  'unique_payloads', len(written), flush=True)
            write(TX / 'native-preservation-progress.json', {'completed': i + 1,
                  'total': len(native_by_hash), 'elapsed': time.monotonic() - start})

    write(STORE / 'index.json', {'schema': 'ccp.recovery-store/v2', 'bundle': bundle.name,
          'bundle_sha256': sha(bundle), 'roots': {k: str(v) for k, v in ROOTS.items()},
          'files': file_index})
    write(STORE / 'native-archives.json', native_index)
    write(STORE / 'retired-deliveries.json', zip_index)
    write(TX / 'recovery-retirement.json', recovery)
    write(TX / 'plain-retention.json', keep)
    write(TX / 'store-preparation.json', {'passed': True, 'bundle_bytes': bundle.stat().st_size,
          'bundle_sha256': sha(bundle), 'index_sha256': sha(STORE / 'index.json'),
          'plain_files': len(keep), 'recovery_paths': len(file_index),
          'unique_payloads': len(written), 'native_archives': len(native_index),
          'redundant_delivery_zips': len(zip_index), 'retirement_candidates': len(recovery)})
    print('STORE_PREPARED', bundle.stat().st_size, 'bytes', flush=True)


if __name__ == '__main__':
    main()
