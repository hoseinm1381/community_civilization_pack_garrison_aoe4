"""Independent source, recovery, rollback and physical allocation gates."""
import argparse
import collections
import concurrent.futures
import ctypes
import hashlib
import time
import zipfile
from common import *
from store import ResourceStore, key_path, owned_key, canonical


def is_generated(key, size=0):
    if key == 'F/output/consolidation_080/delivery/post1/community_civilization_pack-0.8.0.zip':
        return True
    if key.startswith(('F/staging/r80c/', 'F/staging/consolidation_080/')):
        return True
    for label in ('c8pre', 'c8post'):
        if key.startswith(('F/staging/r71/unit-' + label + '/',
                           'F/staging/r710/hideout-stone-' + label + '/',
                           'F/output/release_0710/hideout/readback-stone-' + label + '/')):
            return True
        if key.startswith(('F/output/release_071/unit-' + label + '/',
                           'F/output/consolidation_080/recent-units/' + label + '/')):
            p = Path(key)
            # Keep compact qualification receipts and logs accessible.
            if p.name in {'receipt.json', 'qualification.json', 'comparison.json', 'prepare.json'} or (p.suffix == '.log' and size < 2_000_000):
                return False
            return True
    return False


def projected_budget(allocated, stage):
    # Pre-retirement reserves room for the journal and post-build evidence.
    # Post already counts those files; retain another conservative 50 MB of
    # headroom, but do not apply the original planning target twice.
    assert stage in ('pre', 'post')
    projected = allocated + 50_000_000
    assert projected < 6_000_000_000, ('Preservation set exceeds budget; do not retire', projected)
    if stage == 'pre':
        assert projected < 5_700_000_000, ('Compact new evidence before retirement to meet the reviewed margin', projected)
    return projected


def post_duplicate_check():
    path = OUT / 'delivery/post1/community_civilization_pack-0.8.0.zip'
    if path.exists():
        from package import verify_package
        current_delivery_check()
        verify_package(path, EXPECTED_ZIP, EXPECTED)


def measure(excluded=None, exclude_generated=False):
    excluded = excluded or set()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    compressed = kernel.GetCompressedFileSizeW
    compressed.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    compressed.restype = ctypes.c_uint32
    result = {}
    seen = set()
    for drive, root in ROOTS.items():
        sectors, bps, free, clusters = [ctypes.c_uint32() for _ in range(4)]
        assert kernel.GetDiskFreeSpaceW(str(root.anchor), ctypes.byref(sectors), ctypes.byref(bps), ctypes.byref(free), ctypes.byref(clusters))
        cluster = sectors.value * bps.value
        total = allocated = count = 0
        for p in walk(root):
            key = drive + '/' + p.relative_to(root).as_posix()
            stat = p.stat()
            if key in excluded or (exclude_generated and is_generated(key, stat.st_size)):
                continue
            identity = stat.st_dev, stat.st_ino
            if stat.st_ino and identity in seen:
                continue
            if stat.st_ino:
                seen.add(identity)
            hi = ctypes.c_uint32()
            ctypes.set_last_error(0)
            lo = compressed('\\\\?\\' + str(p), ctypes.byref(hi))
            if lo == 0xffffffff and ctypes.get_last_error():
                raise ctypes.WinError(ctypes.get_last_error())
            physical = (hi.value << 32) | lo
            allocated += ((physical + cluster - 1) // cluster) * cluster
            total += stat.st_size
            count += 1
        result[drive] = {'files': count, 'logical': total, 'allocated': allocated, 'cluster': cluster}
    return {'by_volume': result, 'logical': sum(v['logical'] for v in result.values()),
            'allocated': sum(v['allocated'] for v in result.values()),
            'junctions_counted_once': True}


def protected():
    plain = read(TX / 'plain-retention.json')

    def check(item):
        key, row = item
        p = key_path(key, ROOTS)
        assert p.is_file() and p.stat().st_size == row['bytes'], key
        digest = hashlib.sha256(b'').hexdigest() if row['bytes'] == 0 else sha(p)
        assert digest == row['sha256'], key
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(check, plain.items()))
    normal = read(ROOT / 'output/release_0712/baseline/normal-hashes.json') if (ROOT / 'output/release_0712/baseline/normal-hashes.json').exists() else read(TX / 'normal-source-hashes.json')
    assert all(sha(path) == digest for path, digest in normal.items())
    write(TX / 'normal-source-hashes.json', normal)
    assert all(sha(ROOT / name) == digest for name, digest in read(TX / 'active-source-freeze.json').items())
    print('PLAIN_AND_SOURCE_PROTECTED', len(plain), 'normal', len(normal), flush=True)
    return len(plain)


def rollback_check():
    expected = [
        (BASE, '0.7.12', EXPECTED, 'b942e131a05d7d35da0251f5c53c4b1e77f89af776a14cb126051b193530437e'),
        (EXT / 'archives/release_070_rollback', '0.7.0',
         '63e148ab21f0f2e157bee99a414b39c53284ceb9584812026cadfa47cc5accd2',
         'd44688715b6116e4cb0d4e1527dc01837d2e13f0dbd4655460d8e62c93a9faeb')]
    for directory, version, native_hash, zip_hash in expected:
        assert sha(directory / 'community_civilization_pack.sga') == native_hash
        package = directory / ('community_civilization_pack-' + version + '.zip')
        assert sha(package) == zip_hash
        with zipfile.ZipFile(package) as z:
            assert z.testzip() is None
            name = next(n for n in z.namelist() if n.endswith('.sga'))
            with z.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == native_hash


def current_delivery_check():
    from package import verify_package
    package = OUT / 'delivery/final-v1/community_civilization_pack-0.8.0.zip'
    proof = read(OUT / 'delivery/final-v1/delivery-proof.json')
    assert proof['zip_sha256'] == EXPECTED_ZIP and proof['sga_sha256'] == EXPECTED
    verify_package(package, EXPECTED_ZIP, EXPECTED)


def recovery_check():
    doc = read(STORE / 'index.json')
    assert sha(STORE / doc['bundle']) == doc['bundle_sha256']
    store = ResourceStore(STORE / doc['bundle'], doc['files'], ROOTS)
    seen, last = set(), time.monotonic()
    try:
        for key, row in store.index.items():
            key_path(key, ROOTS)
            if row['member'] in seen:
                continue
            store.read(key)
            seen.add(row['member'])
            if time.monotonic() - last > 20:
                print('RECOVERY_VERIFIED', len(seen), flush=True)
                last = time.monotonic()
        # A restore whose destination has never held the old inputs.
        selected = next(k for k in store.index if k.endswith('export.json'))
        target = STAGE / 'clean-recovery-check' / store.index[selected]['sha256']
        store.restore(selected, target)
        assert sha(target) == store.index[selected]['sha256']
    finally:
        store.close()
    candidates = read(TX / 'recovery-retirement.json')
    native = read(STORE / 'native-archives.json')
    deliveries = read(STORE / 'retired-deliveries.json')
    plain = read(TX / 'plain-retention.json')
    for key, row in candidates.items():
        if key in doc['files']:
            assert doc['files'][key]['sha256'] == row['sha256']
        elif key.lower().endswith('.sga'):
            archive = native[row['sha256']]
            assert key in archive['original_keys']
            assert archive['members']
            for member in archive['members'].values():
                assert doc['files'][member['recovery_key']]['sha256'] == member['sha256']
        else:
            assert key in deliveries, key
    for key, delivery in deliveries.items():
        for member in delivery['members']:
            if 'recovery_key' in member:
                assert doc['files'][member['recovery_key']]['sha256'] == member['sha256']
            else:
                assert any((k in plain and plain[k]['sha256'] == member['sha256'])
                           or (member['sha256'] in native and k in native[member['sha256']]['original_keys'])
                           for k in member['native_archive_keys']), (key, member['path'])
    # Original 071 store stays intact and independently readable.
    import importlib.util
    spec = importlib.util.spec_from_file_location('old071_resources', ROOT / 'tools/release_071/resources.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    old = module.ResourceStore(EXT / 'resources_071')
    old_seen = set()
    for key, row in old.index.items():
        if row['sha256'] not in old_seen:
            old.read(key)
            old_seen.add(row['sha256'])
    print('ALL_RECOVERY_VERIFIED', len(store.index), len(seen), 'old', len(old.index), flush=True)
    return len(seen)


def main(stage):
    guard()
    if stage == 'measure':
        current_delivery_check()
        doc = measure()
        write(TX / 'final-storage.json', doc)
        print(json.dumps(doc, indent=2), flush=True)
        assert doc['allocated'] < 6_000_000_000
        return
    count = protected()
    rollback_check()
    current_delivery_check()
    blobs = recovery_check()
    post_duplicate_check()  # Never exclude an unverified delivery from projection.
    projection = measure(set(read(TX / 'recovery-retirement.json')), exclude_generated=True)
    # Compact receipts and post-build metadata are included by a margin reserve.
    projected = projected_budget(projection['allocated'], stage)
    write(TX / ('pre-retirement-verification.json' if stage == 'pre' else 'post-retirement-verification.json'),
        {'passed': True, 'plain_files': count, 'recovery_payloads': blobs,
         'index_sha256': sha(STORE / 'index.json'), 'rollbacks': True, 'recovery': True,
         'editable': True, 'normal': True, 'projected_allocated': projected,
         'projection_before_reserve': projection, 'margin_reserve': 50_000_000,
         'under_5_7GB_target': projected < 5_700_000_000, 'under_6GB': projected < 6_000_000_000})
    print('PRESERVATION_GATE_PASSED', stage, projected, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['pre', 'post', 'measure'])
    main(p.parse_args().stage)
