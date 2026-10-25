"""Freeze the accepted 0.3.0 release and all prior editable sources for 0.4.0."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys_path = ROOT / 'tools'
import sys
sys.path.insert(0, str(sys_path))
from workspace_support import configuration, check_storage

CONFIG = configuration(ROOT)
EXTERNAL = Path(CONFIG['external_root'])
OUT = EXTERNAL / 'output/release_040'
BASELINE = OUT / 'baseline'
ARCHIVE = EXTERNAL / 'archives/release_030_user_accepted'
RELEASE = EXTERNAL / 'output/release_030'
NORMAL = ROOT.parent / 'Community_civilization_pack_normal'
ZIP = RELEASE / 'community_civilization_pack-0.3.0.zip'
SGA = RELEASE / 'package/community_civilization_pack.sga'
MANIFEST = BASELINE / 'freeze-baseline.json'


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def walk_files(root: Path):
    if not root.is_dir():
        raise FileNotFoundError(root)
    stack = [root]
    while stack:
        folder = stack.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                path = Path(entry.path)
                if entry.is_symlink() or getattr(path, 'is_junction', lambda: False)():
                    raise RuntimeError(f'Unexpected link inside frozen tree: {path}')
                if entry.is_dir(follow_symlinks=False):
                    stack.append(path)
                elif entry.is_file(follow_symlinks=False):
                    yield path


def tree(root: Path) -> dict:
    rows = [{'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size, 'sha256': sha(p)}
            for p in walk_files(root)]
    rows.sort(key=lambda item: item['path'].casefold())
    return {'root': str(root.resolve()), 'file_count': len(rows), 'files': rows}


def record(path: Path) -> dict:
    return {'path': str(path.resolve()), 'size': path.stat().st_size, 'sha256': sha(path)}


def capture() -> dict:
    check_storage(ROOT, CONFIG)
    if not ZIP.is_file() or not SGA.is_file() or not NORMAL.is_dir():
        raise FileNotFoundError('Accepted 0.3.0 ZIP/SGA or preserved normal source is missing')
    old = json.loads((RELEASE / 'baseline/freeze-baseline.json').read_text(encoding='utf-8'))
    if old.get('status') != 'immutable_pre_030_baseline':
        raise RuntimeError('Historical 0.3.0 freeze has unexpected status')
    if not (RELEASE / 'package-verification.json').is_file():
        raise FileNotFoundError('0.3.0 package verification receipt is missing')
    # Capture the accepted current source tree and every prior authoring/export/recipe tree.
    groups = {}
    for category in ('authoring', 'exports', 'recipes'):
        base = ROOT / 'art' / category
        for path in sorted(base.iterdir()):
            if path.is_dir() and path.name.endswith(('010', '020', '021', '030')):
                groups[f'{category}_{path.name}'] = tree(path)
    return {
        'schema': 'community-civilization-pack/release-040-freeze/v1',
        'milestone': '0.4.0',
        'captured_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'immutable_pre_040_baseline',
        'release_030': {
            'zip': record(ZIP), 'sga': record(SGA),
            'package_verification': record(RELEASE / 'package-verification.json'),
            'historical_030_freeze': record(RELEASE / 'baseline/freeze-baseline.json'),
            'source_baseline': record(RELEASE / 'source-baseline.json'),
        },
        'active_project': record(ROOT / 'community_civilization_pack.aoe4mod'),
        'active_source_assets': tree(ROOT / 'assets'),
        'normal_edition': tree(NORMAL),
        'prior_editable_art_export_recipe': groups,
        'historical_030_source_baseline': json.loads((RELEASE / 'source-baseline.json').read_text(encoding='utf-8')),
        'totals': {
            'active_source_files': 0,
            'normal_edition_files': 0,
            'prior_art_files': sum(value['file_count'] for value in groups.values()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true',
                        help='strict pre-edit verification, including active source assets')
    parser.add_argument('--verify-post-edit', action='store_true',
                        help='verify immutable release/project/normal/prior-art state after authorized source edits')
    args = parser.parse_args()
    if args.verify_only and args.verify_post_edit:
        parser.error('choose only one verification mode')
    value = capture()
    value['totals']['active_source_files'] = value['active_source_assets']['file_count']
    value['totals']['normal_edition_files'] = value['normal_edition']['file_count']
    if args.verify_only or args.verify_post_edit:
        old = json.loads(MANIFEST.read_text(encoding='utf-8'))
        keys = ['release_030', 'active_project', 'normal_edition', 'prior_editable_art_export_recipe']
        if args.verify_only:
            keys.append('active_source_assets')
        for key in keys:
            if value[key] != old[key]:
                raise RuntimeError(f'Frozen baseline changed: {key}')
        for source, archived in ((ZIP, ARCHIVE / ZIP.name), (SGA, ARCHIVE / SGA.name)):
            if not archived.is_file() or sha(source) != sha(archived):
                raise RuntimeError(f'Accepted rollback copy mismatch: {archived}')
        print(json.dumps({'status': 'verified',
                          'mode': 'strict_pre_edit' if args.verify_only else 'post_edit_preservation',
                          'active_source_assets_deferred_to': None if args.verify_only else 'tools/release_040/source_policy.py',
                          'zip_sha256': value['release_030']['zip']['sha256'],
                          'sga_sha256': value['release_030']['sga']['sha256'],
                          'source_files': value['totals']['active_source_files'],
                          'normal_files': value['totals']['normal_edition_files'],
                          'prior_art_files': value['totals']['prior_art_files']}, indent=2))
        return 0
    if MANIFEST.exists():
        raise FileExistsError(f'Refusing to replace immutable 0.4.0 freeze: {MANIFEST}')
    check_storage(ROOT, CONFIG)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for source in (ZIP, SGA):
        target = ARCHIVE / source.name
        if target.exists():
            if sha(target) != sha(source):
                raise RuntimeError(f'Existing accepted archive copy differs: {target}')
        else:
            shutil.copy2(source, target)
            if sha(target) != sha(source):
                raise RuntimeError(f'Archive copy verification failed: {target}')
    BASELINE.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'frozen', 'manifest': str(MANIFEST),
                      'rollback_root': str(ARCHIVE), 'zip_sha256': value['release_030']['zip']['sha256'],
                      'sga_sha256': value['release_030']['sga']['sha256'],
                      'source_files': value['totals']['active_source_files'],
                      'normal_files': value['totals']['normal_edition_files'],
                      'prior_art_files': value['totals']['prior_art_files']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
