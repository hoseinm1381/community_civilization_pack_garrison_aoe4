"""Freeze/verify accepted 0.1.0 editable art without traversing storage links."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import configuration, check_storage

TREES = ('art/authoring/houses_010', 'art/authoring/traps_010',
         'art/exports/houses_010', 'art/exports/traps_010')


def verify():
    cfg = configuration(ROOT)
    check_storage(ROOT, cfg)
    output = Path(cfg['external_root']) / 'output/release_020/accepted-art-baseline.json'
    files = {}
    for relative in TREES:
        tree = ROOT / relative
        if not tree.is_dir() or tree.is_junction() or tree.is_symlink():
            raise ValueError(f'Expected owned editable art directory: {tree}')
        for path in sorted(tree.rglob('*')):
            if path.is_symlink() or path.is_junction():
                raise ValueError(f'Unexpected link in editable art: {path}')
            if path.is_file():
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                files[path.relative_to(ROOT).as_posix()] = {
                    'sha256': digest, 'bytes': path.stat().st_size}
    if not files:
        raise ValueError('Empty accepted editable art inventory')
    record = {'schema': 'community.release020.accepted-art/v1', 'files': files,
              'directories': list(TREES), 'status': 'passed'}
    if output.exists():
        if json.loads(output.read_text(encoding='utf-8')) != record:
            raise ValueError('Accepted 0.1.0 editable sources/exports changed')
    elif '--verify-only' in sys.argv:
        raise ValueError('Accepted art baseline missing')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return {'status': 'passed', 'files_unchanged': len(files), 'receipt': str(output)}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
