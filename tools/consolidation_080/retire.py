"""Exact allowlisted physical-copy retirement. Never recursive-delete a root."""
import argparse
import hashlib
import os
import time
from pathlib import Path
from store import canonical, key_path, owned_key, retirement_gate


def candidate_path(key, row, roots, protected, allowed):
    if key not in allowed or key in protected:
        raise ValueError('Unknown or protected retirement path: ' + key)
    p = key_path(key, roots)
    if owned_key(p, roots).casefold() != key.casefold() or not p.is_file() or p.is_symlink():
        raise ValueError('Retirement identity changed: ' + key)
    before = p.stat()
    if before.st_size != row['bytes'] or before.st_mtime_ns != row['mtime_ns']:
        raise ValueError('Retirement file changed: ' + key)
    with p.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = p.stat()
    if digest != row['sha256'] or after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
        raise ValueError('Retirement hash changed: ' + key)
    return p


def retire_sequence(rows, roots, protected, record):
    allowed = set(rows)
    for key, row in rows.items():
        p = candidate_path(key, row, roots, protected, allowed)
        event = {'key': key, 'bytes': row['bytes'], 'allocated': row['allocated'],
                 'sha256': row['sha256']}
        record(event | {'operation': 'intent_remove_verified_copy'})
        p.unlink()
        record(event | {'operation': 'removed_verified_copy'})


def retire_with_journal(rows, roots, protected, ledger_path):
    import json
    ledger_path = Path(ledger_path)
    ledger_path.parent.mkdir(exist_ok=True)
    completed, pending = set(), set()
    if ledger_path.exists():
        for line in ledger_path.read_text().splitlines():
            event = json.loads(line)
            key = event['key']
            if key not in rows or event['sha256'] != rows[key]['sha256']:
                raise ValueError('Journal does not match retirement manifest')
            if event['operation'] == 'removed_verified_copy':
                completed.add(key)
            elif event['operation'] == 'intent_remove_verified_copy':
                pending.add(key)
    count, last = len(completed), time.monotonic()
    if any(key_path(key, roots).exists() for key in completed):
        raise ValueError('A completed retirement path reappeared; preserving all remaining copies')
    with ledger_path.open('a', encoding='utf-8', buffering=1) as ledger:
        def record(event):
            nonlocal count, last
            ledger.write(json.dumps(event) + '\n')
            ledger.flush()
            os.fsync(ledger.fileno())
            if event['operation'] == 'removed_verified_copy':
                count += 1
            if time.monotonic() - last > 20:
                print('RETIRED_VERIFIED_COPIES', count, '/', len(rows), flush=True)
                last = time.monotonic()
        for key in sorted(pending - completed):
            if key in protected:
                raise ValueError('Protected path in journal')
            if not key_path(key, roots).exists():
                row = rows[key]
                record({'key': key, 'operation': 'removed_verified_copy', 'bytes': row['bytes'],
                        'allocated': row['allocated'], 'sha256': row['sha256'],
                        'recovered_after_interruption': True})
                completed.add(key)
        retire_sequence({k: r for k, r in rows.items() if k not in completed}, roots, protected, record)
    return count


def main():
    from common import ROOTS, TX, STORE, OUT, guard, read, write, sha
    guard()
    rows = read(TX / 'recovery-retirement.json')
    protected = set(read(TX / 'plain-retention.json'))
    review = read(TX / 'retirement-review.json')
    verification = read(TX / 'pre-retirement-verification.json')
    assert review['passed'] and review['retirement_sha256'] == sha(TX / 'recovery-retirement.json')
    assert review['index_sha256'] == sha(STORE / 'index.json')
    assert verification['passed'] and verification['index_sha256'] == sha(STORE / 'index.json')
    for path, digest in review['tools'].items():
        assert sha(path) == digest, 'Tool changed after review: ' + path
    from verify import protected as refresh_protected
    refresh_protected()
    source = read(OUT / 'native/pre3/receipt.json')
    asset = read(OUT / 'asset-qualification/c8pre/receipt.json')
    proof = {'approved': True, 'package': read(OUT / 'delivery/final-v1/delivery-proof.json')['verified'],
        'rollbacks': verification['rollbacks'], 'native_source': source['passed'],
        'asset_cooks': asset['passed'], 'recovery': verification['recovery'],
        'editable': verification['editable'], 'normal': verification['normal'],
        'review': review['passed'], 'projected_allocated': verification['projected_allocated']}
    retirement_gate(proof)
    write(TX / 'retirement-gates.json', proof)
    # NTFS journal avoids repeated exFAT cluster flushes while remaining inside
    # owned project storage. The final compact copy also lives with F: evidence.
    ledger_path = ROOTS['E'] / '.consolidation_080/retirement-operations.jsonl'
    count = retire_with_journal(rows, ROOTS, protected, ledger_path)
    write(TX / 'retirement-complete.json', {'passed': True, 'files': count,
          'retired_logical': sum(r['bytes'] for r in rows.values()),
          'retired_allocated': sum(r['allocated'] for r in rows.values()),
          'manifest_sha256': sha(TX / 'recovery-retirement.json'),
          'operation_ledger': str(ledger_path), 'operation_ledger_sha256': sha(ledger_path)})
    print('RETIREMENT_COMPLETE', count, flush=True)


if __name__ == '__main__':
    main()
