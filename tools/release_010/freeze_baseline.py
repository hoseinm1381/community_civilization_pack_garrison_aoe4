"""Freeze source and compile an isolated unchanged baseline for visual comparison."""
import argparse
import shutil
import sys
from datetime import datetime, timezone
from common import CONFIG, EDITOR, KEY, OUT, ROOT, STAGING, check_storage, read, run_logged, sha, snapshot, write
from workspace_support import check_preservation


def freeze():
    check_storage(ROOT, CONFIG)
    receipt_path = OUT / 'baseline-freeze.json'
    source = STAGING / 'baseline_source'
    if receipt_path.is_file():
        record = read(receipt_path)
        if snapshot(source / 'assets') != record['assets'] or sha(source / CONFIG['project_file']) != record['project_sha256']:
            raise ValueError('Frozen baseline source changed')
        return record
    check_preservation(ROOT, CONFIG)
    if source.exists():
        raise ValueError('Unowned/incomplete baseline source exists; inspect before continuing')
    source.mkdir(parents=True)
    shutil.copytree(ROOT / 'assets', source / 'assets')
    shutil.copy2(ROOT / CONFIG['project_file'], source / CONFIG['project_file'])
    record = {'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
              'project_guid': CONFIG['project_guid'], 'source': str(source),
              'assets': snapshot(source / 'assets'),
              'project_sha256': sha(source / CONFIG['project_file']),
              'normal_proof': check_preservation(ROOT, CONFIG)}
    write(receipt_path, record)
    write(ROOT / 'art/recipes/release_010/baseline-freeze.json', record)
    return record


def build():
    record = freeze()
    source = STAGING / 'baseline_source'
    destination = OUT / 'baseline'
    destination.mkdir(exist_ok=True)
    log = OUT / 'baseline-burn.log'
    receipt = run_logged('baseline-build', [EDITOR, '-rtm', '--safe_settings', '--do_not_restore',
        '--quiet_crash_report', '--no_source_control', '--log_path', OUT / 'baseline-logs',
        '--build_mod', source / CONFIG['project_file'], '--build_path', destination,
        '--no_burn_window', '--burn_cache_type', 'Local', '--burn_max_threads', '1',
        '--burn_platform', 'PC', '--burn_log_path', log,
        '--intermediate_path', STAGING / 'baseline_intermediate'],
        cwd=EDITOR.parent, timeout=1800)
    archives = list(destination.rglob('*.sga'))
    if len(archives) != 1:
        raise RuntimeError(f'Expected one baseline archive; found {archives}')
    receipt.update({'archive': str(archives[0]), 'sha256': sha(archives[0]),
        'source_frozen': snapshot(source / 'assets') == record['assets'],
        'scope': 'unchanged new-GUID Content Editor baseline, not native match evidence'})
    if not receipt['source_frozen']:
        raise ValueError('Baseline assets changed during compile')
    write(OUT / 'baseline-build-result.json', receipt)
    print(receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    build() if args.build else print(freeze()['source'])
