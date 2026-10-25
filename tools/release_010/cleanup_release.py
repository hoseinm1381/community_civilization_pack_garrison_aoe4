"""Remove only explicitly regenerable readbacks/intermediates after ZIP proof."""
import argparse
import hashlib
import shutil
from pathlib import Path
from zipfile import ZipFile
from common import ARCH, CONFIG, EXTERNAL, OUT, ROOT, STAGING, check_storage, read, sha, snapshot, write


def cleanup(apply=False):
    check_storage(ROOT, CONFIG)
    delivery = read(OUT / 'package-verification.json')
    archive, zipped = Path(delivery['sga']), Path(delivery['zip'])
    expected = {str(archive): delivery['sga_sha256'], str(zipped): delivery['zip_sha256']}
    if any(sha(path) != digest for path, digest in expected.items()):
        raise ValueError('Delivery hash changed before cleanup')
    with ZipFile(zipped) as bundle:
        assert bundle.testzip() is None
        assert bundle.namelist().count('garrison.json') == 1
        assert hashlib.sha256(bundle.read(archive.name)).hexdigest() == delivery['sga_sha256']
    # These have verified source archives or frozen source, and supported rebuild
    # commands. Family projects, donors, media, recipes and diagnostic logs stay.
    targets = [STAGING / 'baseline_intermediate', OUT / 'verification-readback']
    restoration = {}
    for receipt in (OUT / 'integration').rglob('*-cook.json'):
        record = read(receipt)
        if record.get('status') != 'passed' or 'cook' not in record or 'readback' not in record:
            continue
        target = Path(record['readback'])
        if not target.resolve().is_relative_to((OUT / 'integration').resolve()) or not target.name.startswith('readback-'):
            raise ValueError(f'Unexpected native readback cleanup path: {target}')
        if not target.exists():
            continue
        cooked = record['cook']
        if sha(cooked['archive']) != cooked['sha256']:
            raise ValueError(f'Cannot regenerate readback from changed cook archive: {receipt}')
        targets.append(target)
        restoration[str(target.resolve())] = [str(ARCH), 'unpack', cooked['archive'], '--output', str(target)]
    candidate = read(delivery['candidate'])
    command = candidate['candidate_source_build']['command']['command']
    intermediate = Path(command[command.index('--intermediate_path') + 1])
    if not intermediate.resolve().is_relative_to((OUT / 'integration').resolve()) or not intermediate.name.startswith('candidate-intermediate'):
        raise ValueError(f'Unexpected candidate intermediate path: {intermediate}')
    targets.append(intermediate)
    targets = list(dict.fromkeys(targets))
    entries = []
    for target in targets:
        resolved = target.resolve()
        if not resolved.is_relative_to(EXTERNAL.resolve()) or resolved == EXTERNAL.resolve():
            raise ValueError(f'Cleanup target outside owned external root: {resolved}')
        if target.exists():
            for item in [target, *target.rglob('*')]:
                if item.is_symlink() or item.is_junction():
                    raise ValueError(f'Cleanup refuses junction/symlink: {item}')
            files = snapshot(target)
            entries.append({'path': str(resolved), 'bytes': sum(r['bytes'] for r in files.values()),
                            'files': files, 'restore_command': restoration.get(str(resolved),
                                'Regenerate from retained frozen source/archive with a fresh isolated build/readback; preserve current baseline/delivery.')})
    record = {'status': 'planned', 'targets': entries,
        'bytes_reclaimed': 0, 'delivery_hashes_before': expected,
        'restoration': [
            'Baseline intermediates: recompile retained frozen source with the command in baseline-build-result.json, substituting a new isolated output/intermediate directory. Preserve the designated baseline archive and receipt; never overwrite them just to restore a cache.',
            'Archive readbacks: verify_archive.py extracts the retained baseline/final archives using the installed archive tool.'],
        'retained': ['editable source blends and all textures/exports', 'family Garrison projects and recipes',
            'required donor/decoded/native geometry/material inputs', 'baseline source/archive rollback',
            'all fresh native cook archives, staged media, diagnostic logs and compact receipts',
            'final ZIP and packaged SGA', 'comparison previews']}
    write(OUT / 'cleanup-plan.json', record)
    if apply:
        previous_path = OUT / 'cleanup-verification.json'
        previous = read(previous_path) if previous_path.exists() else None
        for entry in entries:
            shutil.rmtree(Path(entry['path']))
            record['bytes_reclaimed'] += entry['bytes']
        if any(sha(path) != digest for path, digest in expected.items()):
            raise ValueError('Delivery hash changed during cleanup')
        record['status'] = 'passed'
        record['delivery_hashes_after'] = {p: sha(p) for p in expected}
        if previous:
            write(OUT / 'cleanup-history' / (sha(previous_path) + '.json'), previous)
        prior_bytes = previous.get('total_bytes_reclaimed', previous['bytes_reclaimed']) if previous else 0
        record['total_bytes_reclaimed'] = prior_bytes + record['bytes_reclaimed']
        record['initial_bytes_reclaimed'] = previous.get('initial_bytes_reclaimed', previous['bytes_reclaimed']) if previous else record['bytes_reclaimed']
        record['accounting'] = 'Each pass measures removed file bytes. Recreated verification readbacks can be removed again; aggregate removal activity is not cumulative net free-space gain.'
        write(OUT / 'cleanup-verification.json', record)
    print(f"{record['status']}: {record['bytes_reclaimed']} bytes reclaimed; {len(entries)} regenerable directories")
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    cleanup(parser.parse_args().apply)
