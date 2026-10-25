"""Capture and verify immutable pre-0.3.0 source, delivery, and prior-art hashes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from common import ROOT, OUT, guarded, write

NORMAL = ROOT.parent / 'Community_civilization_pack_normal'
ACTIVE_PROJECT = ROOT / 'community_civilization_pack.aoe4mod'
ZIP = OUT.parent / 'release_021' / 'community_civilization_pack-0.2.1.zip'
SGA = OUT.parent / 'release_021' / 'package' / 'community_civilization_pack.sga'
EXPECTED_ZIP = '01e034c8ce692ff34b050bc443c71f2cdcad751cb9a1fb3fa4c87e996449216b'
EXPECTED_SGA = 'e9ae2e1f61a05c37fac96b932578e1f6121ee8bf131e2123495a96fd5e764821'
MANIFEST = OUT / 'baseline' / 'freeze-baseline.json'


def hash_file(path: Path) -> str:
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def files_without_links(root: Path):
    """Walk explicitly without traversing symlinks or Windows junctions."""
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(root)
    stack = [root]
    while stack:
        folder = stack.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                p = Path(entry.path)
                if entry.is_symlink() or getattr(p, 'is_junction', lambda: False)():
                    raise RuntimeError(f'Unexpected link inside frozen tree: {p}')
                if entry.is_dir(follow_symlinks=False):
                    stack.append(p)
                elif entry.is_file(follow_symlinks=False):
                    yield p


def file_record(path: Path, relative_to: Path) -> dict:
    return {'path': path.relative_to(relative_to).as_posix(), 'size': path.stat().st_size,
            'sha256': hash_file(path)}


def collect_tree(label: str, root: Path) -> dict:
    rows = [file_record(p, root) for p in files_without_links(root)]
    rows.sort(key=lambda x: x['path'].casefold())
    return {'root': str(root.resolve()), 'file_count': len(rows), 'files': rows}


def capture() -> dict:
    guarded()
    if not ACTIVE_PROJECT.is_file() or not NORMAL.is_dir():
        raise FileNotFoundError('Active project or preserved normal edition is missing')
    zip_hash, sga_hash = hash_file(ZIP), hash_file(SGA)
    if zip_hash != EXPECTED_ZIP:
        raise RuntimeError(f'0.2.1 ZIP hash mismatch: {zip_hash}')
    if sga_hash != EXPECTED_SGA:
        raise RuntimeError(f'0.2.1 SGA hash mismatch: {sga_hash}')

    groups = {}
    paths = [
        ('authoring_houses_010', ROOT / 'art/authoring/houses_010'),
        ('authoring_traps_010', ROOT / 'art/authoring/traps_010'),
        ('authoring_buildings_020', ROOT / 'art/authoring/buildings_020'),
        ('authoring_buildings_021', ROOT / 'art/authoring/buildings_021'),
        ('authoring_traps_021', ROOT / 'art/authoring/traps_021'),
        ('exports_houses_010', ROOT / 'art/exports/houses_010'),
        ('exports_traps_010', ROOT / 'art/exports/traps_010'),
        ('exports_buildings_020', ROOT / 'art/exports/buildings_020'),
        ('exports_buildings_021', ROOT / 'art/exports/buildings_021'),
        ('exports_traps_021', ROOT / 'art/exports/traps_021'),
        ('recipes_release_010', ROOT / 'art/recipes/release_010'),
        ('recipes_release_020', ROOT / 'art/recipes/release_020'),
        ('recipes_release_021', ROOT / 'art/recipes/release_021'),
    ]
    for label, path in paths:
        groups[label] = collect_tree(label, path)
    return {
        'schema': 'community-civilization-pack/release-030-freeze/v1',
        'milestone': '0.3.0',
        'captured_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'status': 'immutable_pre_030_baseline',
        'deliverables': {
            'release_021_zip': {'path': str(ZIP.resolve()), 'size': ZIP.stat().st_size,
                                'sha256': zip_hash, 'expected_sha256': EXPECTED_ZIP},
            'release_021_sga': {'path': str(SGA.resolve()), 'size': SGA.stat().st_size,
                                'sha256': sga_hash, 'expected_sha256': EXPECTED_SGA},
        },
        'active_project': file_record(ACTIVE_PROJECT, ROOT),
        'normal_edition': collect_tree('normal_edition', NORMAL),
        'prior_editable_art_export_recipe': groups,
        'totals': {
            'normal_edition_files': 0,
            'prior_art_export_recipe_files': sum(v['file_count'] for v in groups.values()),
        },
    }



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    value = capture()
    value['totals']['normal_edition_files'] = value['normal_edition']['file_count']
    if args.verify_only:
        if not MANIFEST.is_file():
            raise FileNotFoundError(MANIFEST)
        old = json.loads(MANIFEST.read_text(encoding='utf-8'))
        if value['deliverables'] != old['deliverables']:
            raise RuntimeError('Frozen 0.2.1 package or SGA changed')
        if value['active_project'] != old['active_project']:
            raise RuntimeError('Active project changed since baseline freeze')
        if value['normal_edition'] != old['normal_edition']:
            raise RuntimeError('Normal-edition file tree changed since baseline freeze')
        if value['prior_editable_art_export_recipe'] != old['prior_editable_art_export_recipe']:
            raise RuntimeError('Prior editable art/export/recipe inputs changed since baseline freeze')
        print(json.dumps({'status': 'verified', 'zip_sha256': value['deliverables']['release_021_zip']['sha256'],
                          'sga_sha256': value['deliverables']['release_021_sga']['sha256'],
                          'normal_edition_files': value['totals']['normal_edition_files'],
                          'prior_art_files': value['totals']['prior_art_export_recipe_files']}, indent=2))
        return 0
    if MANIFEST.exists():
        raise FileExistsError(f'Refusing to refresh immutable freeze: {MANIFEST}')
    write(MANIFEST, value)
    print(json.dumps({'status': 'frozen', 'manifest': str(MANIFEST),
                      'zip_sha256': value['deliverables']['release_021_zip']['sha256'],
                      'sga_sha256': value['deliverables']['release_021_sga']['sha256'],
                      'normal_edition_files': value['totals']['normal_edition_files'],
                      'prior_art_files': value['totals']['prior_art_export_recipe_files']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
