"""Verify 0.4.0 delivery and reclaim only regenerable release-owned readbacks."""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from zipfile import ZipFile

from common import ROOT, OUT, KEY, guarded, read, sha, write


def safe_files(folder):
    result, pending = {}, [folder]
    while pending:
        current = pending.pop()
        stat = current.lstat()
        assert not current.is_symlink() and not (getattr(stat, 'st_file_attributes', 0) & 0x400)
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                stat = path.lstat()
                assert not entry.is_symlink() and not (getattr(stat, 'st_file_attributes', 0) & 0x400), path
                if entry.is_dir(follow_symlinks=False): pending.append(path)
                else:
                    assert entry.is_file(follow_symlinks=False)
                    result[path.relative_to(folder).as_posix()] = {'sha256': sha(path), 'bytes': stat.st_size}
    return result


def finalize():
    guarded()
    delivery = read(OUT / 'package-verification.json')
    audit = read(OUT / 'archive-verification.json')
    checks = read(OUT / 'release-checks.json')
    assert delivery['status'] == audit['status'] == 'passed'
    assert checks['status'] == 'baseline-equivalent-with-two-inherited-failures'
    assert sha(delivery['zip']) == delivery['zip_sha256']
    assert sha(delivery['sga']) == delivery['sga_sha256'] == audit['sga_sha256']
    with ZipFile(delivery['zip']) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == {'garrison.json', KEY + '.sga', 'START-HERE.txt', 'EVIDENCE.json'}
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == delivery['sga_sha256']
    cooked = read(read(OUT / 'art-cook-pointer.json')['receipt'])
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    candidate = read(OUT / 'candidate.json')
    assert sha(candidate['archive']) == candidate['sha256']
    readbacks = []
    for folder in (OUT / 'readback').glob('*'):
        marker = folder / '.complete.json'
        if not folder.is_dir() or not marker.is_file(): continue
        digest = read(marker).get('archive_sha256')
        if digest in (candidate['baseline_sha256'], candidate['sha256']): readbacks.append(folder)
    art_readback = Path(cooked['readback'])
    if art_readback.exists(): readbacks.append(art_readback)
    removed = []
    for folder in readbacks:
        absolute = folder.resolve()
        assert absolute.is_relative_to(OUT.resolve()) and absolute != OUT.resolve()
        assert folder.parent == OUT / 'readback' or folder.name.startswith('readback-cc040art-')
        files = safe_files(folder)
        removed.append({'path': str(folder), 'files': files,
                        'bytes': sum(item['bytes'] for item in files.values())})
        shutil.rmtree(absolute)
    assert sha(delivery['zip']) == delivery['zip_sha256']
    assert sha(delivery['sga']) == delivery['sga_sha256']
    result = {'status': 'passed', 'zip_sha256': delivery['zip_sha256'],
              'sga_sha256': delivery['sga_sha256'],
              'reclaimed_bytes': sum(row['bytes'] for row in removed),
              'targets': removed,
              'restoration': 'sga-archiver unpack the retained accepted, candidate or cooked SGA',
              'retained': ['all editable blends, exports, recipes and source',
                           'Garrison projects and cooked archives', 'native logs and build receipts',
                           '0.4.0 ZIP and SGA', '0.3.0 rollback',
                           'donor cache pending verified regeneration audit']}
    write(OUT / 'cleanup-verification.json', result)
    report = (f'# Community Civilization Pack 0.4.0\n\n'
              f'Delivery: `{delivery["zip"]}`. ZIP SHA-256 `{delivery["zip_sha256"]}`; '
              f'SGA SHA-256 `{delivery["sga_sha256"]}`.\n\n'
              f'Exactly {len(audit["changed"])} accepted 0.3.0 members changed and '
              f'{len(audit["added"])} private members were added; '
              f'{audit["untouched_members"]} prior members remain byte-identical. '
              f'Fresh Garrison landmark cook, model-reference cook, Content Editor source build, '
              f'archive readback, {checks["tests"]["tests"]} tests with only the two inherited '
              f'weapon-parity failures, and strict Garrison ZIP verification passed. '
              f'Cleanup reclaimed {result["reclaimed_bytes"]} bytes.\n\n'
              f'Client import, lobby selection, selectability and repair in a fresh match, '
              f'visual appearance, and multiplayer remain user gates. Rollback is the accepted '
              f'0.3.0 ZIP under `archives/release_030_user_accepted`.\n')
    (OUT / 'release-report.md').write_text(report, encoding='utf-8')
    return result


if __name__ == '__main__':
    finalize()
