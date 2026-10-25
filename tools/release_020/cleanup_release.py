"""Remove only verified regenerable 0.2.0 readback/compile caches after ZIP proof."""
import shutil
import sys
from pathlib import Path
from common import EXTERNAL, OUT, ROOT, guarded, read, sha, write
from package_release import verify_existing


def inventory(path):
    result = []
    for entry in [path, *path.rglob('*')]:
        if entry.is_symlink() or entry.is_junction():
            raise ValueError(f'Unexpected link in cleanup candidate: {entry}')
        if not entry.resolve().is_relative_to(path.resolve()):
            raise ValueError(f'Cleanup candidate escaped resolved root: {entry}')
        if entry.is_file():
            result.append({'path': entry.relative_to(path).as_posix(), 'bytes': entry.stat().st_size})
    return result


def cleanup(apply=False):
    frozen = guarded()
    pointer = read(OUT / 'integration/candidate-pointer.json')
    candidate_path = Path(pointer['receipt'])
    assert sha(candidate_path) == pointer['sha256']
    candidate = read(candidate_path)
    delivery = verify_existing(candidate_path)
    before = {key: sha(delivery[key]) for key in ('zip', 'sga')}
    assert before == {'zip': delivery['zip_sha256'], 'sga': delivery['sga_sha256']}
    # No authoring, recipes, media, frozen inputs, cook archives or diagnostic
    # source/log directories are candidates. The two roots below are exact.
    compile_label = candidate['candidate_source_build']['label']
    assert compile_label and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in compile_label)
    work = OUT / 'integration'
    candidates = [(OUT / 'verification-readback',
                   'Independent unpack cache; rebuild with tools/build_release_020.ps1 -VerifyOnly.'),
                  (work / ('candidate-intermediate-' + compile_label),
                   'Successful Content Editor intermediate only; regenerate with a fresh labeled full build.')]
    protected = [Path(frozen['source_stage']), ROOT / 'archives/release_010_user_accepted',
                 ROOT / 'art/authoring/buildings_020', ROOT / 'art/exports/buildings_020',
                 ROOT / 'art/recipes/release_020', candidate_path, Path(candidate['archive']),
                 Path(delivery['zip']), Path(delivery['sga'])]
    assert all(p.exists() for p in protected), 'A required rebuild/delivery dependency is missing'
    rows = []
    for path, restore in candidates:
        if not path.exists():
            continue
        resolved = path.resolve(strict=True)
        assert resolved.is_relative_to(EXTERNAL.resolve()) and resolved.is_relative_to(OUT.resolve())
        assert resolved not in (EXTERNAL.resolve(), OUT.resolve(), work.resolve())
        assert not any(p.resolve().is_relative_to(resolved) for p in protected)
        files = inventory(path)
        rows.append({'path': str(resolved), 'files': len(files),
                     'bytes': sum(row['bytes'] for row in files), 'restore': restore})
    record = {'status': 'planned', 'apply': apply, 'candidate': str(candidate_path),
              'candidate_sha256': sha(candidate_path),
              'delivery_before': before, 'targets': rows,
              'protected_dependencies': [str(p) for p in protected]}
    write(OUT / 'cleanup-inventory.json', record)
    if apply:
        previous = OUT / 'cleanup-verification.json'
        if previous.exists():
            history = OUT / 'cleanup-history' / (sha(previous) + '.json')
            if not history.exists():
                history.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(previous, history)
        for row in rows:
            path = Path(row['path'])
            # Repeat safety checks immediately before the destructive operation.
            assert path.resolve(strict=True).is_relative_to(OUT.resolve())
            assert not path.is_junction() and not path.is_symlink()
            inventory(path)
            shutil.rmtree(path)
        after = {key: sha(delivery[key]) for key in ('zip', 'sga')}
        assert after == before, 'Delivery changed during cleanup'
        record.update(status='passed', bytes_reclaimed=sum(row['bytes'] for row in rows),
                      delivery_after=after,
                      accounting='This pass only; repeated cache regeneration/removal is not cumulative net space gain.')
        write(OUT / 'cleanup-verification.json', record)
    return record


if __name__ == '__main__':
    import json
    print(json.dumps(cleanup('--apply' in sys.argv), indent=2))
