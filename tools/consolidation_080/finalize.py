"""Retire only release-owned regenerated attempts, retaining compact evidence."""
import argparse
import gzip
import hashlib
import os
import zipfile
from common import *
from store import owned_key, key_path, canonical
from retire import candidate_path, retire_with_journal
from verify import is_generated, post_duplicate_check


def compact():
    records = read(TX / 'evidence-compaction.json') if (TX / 'evidence-compaction.json').exists() else {}
    names = ['initial-inventory.json', 'hashed-inventory.json', 'hash-journal.jsonl',
             'compression-probe.json', 'asset-readiness.json', 'recipe-paths.json',
             'outside-image-dependencies.json', 'blend-dependencies.json',
             'blend-full-dependencies.json', 'canonical-image-dependencies.json']
    for name in names:
        p = TX / name
        if not p.exists():
            continue
        raw = p.read_bytes()
        target = Path(str(p) + '.gz')
        data = gzip.compress(raw, compresslevel=6, mtime=0)
        if target.exists():
            assert gzip.decompress(target.read_bytes()) == raw
        else:
            target.write_bytes(data)
        assert gzip.decompress(target.read_bytes()) == raw
        records[name] = {'original_sha256': hashlib.sha256(raw).hexdigest(),
                         'original_bytes': len(raw), 'gzip_sha256': sha(target),
                         'gzip_bytes': target.stat().st_size}
        p.unlink()  # Only this release's new, fully verified alternate representation.
    # Native listing/extraction logs are large and mostly repeated JSON.
    folder = TX / 'native-logs'
    archive = TX / 'native-logs.zip'
    if folder.exists() and not archive.exists() and (STORE / 'index.json').exists():
        files = list(walk(folder))
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for p in files:
                z.write(p, p.relative_to(folder).as_posix())
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for p in files:
                assert hashlib.sha256(z.read(p.relative_to(folder).as_posix())).hexdigest() == sha(p)
        for p in files:
            p.unlink()
        folder.rmdir()
        records['native-logs/'] = {'zip': archive.name, 'sha256': sha(archive), 'files': len(files)}
    write(TX / 'evidence-compaction.json', records)
    print('NEW_EVIDENCE_COMPACTED', len(records), flush=True)


def plan_generated(label):
    safe_label(label)
    assert read(TX / 'retirement-complete.json')['passed']
    assert read(OUT / 'native/post1/receipt.json')['passed']
    assert read(OUT / 'asset-qualification/c8post/receipt.json')['passed']
    assert read(TX / 'post-retirement-verification.json')['passed']
    post_duplicate_check()  # Exact reproduced ZIP only; keep proof and metadata.
    restored = set(read(OUT / 'asset-qualification/c8post/restored-inputs.json'))
    for receipt in (OUT / 'validation').glob('*/restored-inputs.json'):
        restored.update(read(receipt))
    original = read(TX / 'recovery-retirement.json')
    rows = {}
    for drive, root in ROOTS.items():
        if drive == 'E':
            continue
        for p in walk(root):
            key = owned_key(p, ROOTS)
            stat = p.stat()
            restored_original = str(p) in restored
            if not is_generated(key, stat.st_size) and not restored_original:
                continue
            digest = sha(p)
            if restored_original:
                assert key in original and digest == original[key]['sha256'], key
            rows[key] = {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
                         'sha256': digest, 'allocated': 0,
                         'reason': 'Verified restored input duplicate' if restored_original else 'Release-owned reproducible qualification output'}
    bundle = STORE / ('qualification-evidence-' + label + '.zip')
    if bundle.exists():
        raise FileExistsError('Immutable evidence label exists')
    saved = {}
    with zipfile.ZipFile(bundle, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for key, row in rows.items():
            p = key_path(key, ROOTS)
            if p.suffix.lower() in {'.json', '.log', '.txt', '.xml', '.burnproj', '.aoe4mod', '.csv', '.scar'}:
                z.write(p, key)
                saved[key] = row['sha256']
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        for key, expected in saved.items():
            assert hashlib.sha256(z.read(key)).hexdigest() == expected
    doc = {'files': rows, 'evidence_bundle': str(bundle), 'evidence_sha256': sha(bundle),
           'saved_metadata': saved, 'originals_preserved': True,
           'postqualification_passed': True}
    write(TX / ('generated-retirement-' + label + '.json'), doc)
    print('GENERATED_RETIREMENT_PLAN', label, len(rows), flush=True)


def clean_generated(label):
    safe_label(label)
    path = TX / ('generated-retirement-' + label + '.json')
    doc = read(path)
    review = read(TX / ('generated-retirement-review-' + label + '.json'))
    assert review['passed'] and review['manifest_sha256'] == sha(path)
    assert doc['postqualification_passed'] and sha(doc['evidence_bundle']) == doc['evidence_sha256']
    rows = doc['files']
    protected = set(read(TX / 'plain-retention.json'))
    ledger = ROOT / '.consolidation_080' / ('generated-retirement-' + label + '.jsonl')
    retire_with_journal(rows, ROOTS, protected, ledger)
    write(TX / ('generated-retirement-complete-' + label + '.json'), {'passed': True,
        'files': len(rows), 'logical_bytes': sum(r['bytes'] for r in rows.values()),
        'manifest_sha256': sha(path)})
    print('GENERATED_CLEANUP_COMPLETE', len(rows), flush=True)


def empty_dirs():
    original = read(TX / 'recovery-retirement.json')
    targets = set()
    for key in original:
        p = key_path(key, ROOTS).parent
        while p != EXT and p.is_relative_to(EXT):
            targets.add(p)
            p = p.parent
    # Include only the new generated attempt roots, never source/master trees.
    for base in (EXT / 'staging/r80c', EXT / 'staging/consolidation_080'):
        if base.exists():
            targets.add(base)
            targets.update(p for p in base.rglob('*') if p.is_dir() and not p.is_junction())
    protected_roots = {EXT / value for value in CFG['links'].values()} | {EXT, TX, STORE}
    removed = 0
    for p in sorted(targets, key=lambda p: len(p.parts), reverse=True):
        if not p.exists() or p in protected_roots or p.is_junction() or p.is_symlink():
            continue
        assert canonical(p).is_relative_to(canonical(EXT))
        try:
            p.rmdir()
            removed += 1
        except OSError:
            pass  # A nonempty/new directory is preserved.
    guard()
    write(TX / 'empty-directories.json', {'removed': removed, 'all_links_preserved': True})
    print('EMPTY_OWNED_DIRECTORIES_REMOVED', removed, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['compact', 'plan-generated', 'clean-generated', 'empty-dirs'])
    p.add_argument('label', nargs='?', default='v1')
    args = p.parse_args()
    safe_label(args.label)
    guard()
    {'compact': compact, 'plan-generated': lambda: plan_generated(args.label),
     'clean-generated': lambda: clean_generated(args.label), 'empty-dirs': empty_dirs}[args.stage]()
