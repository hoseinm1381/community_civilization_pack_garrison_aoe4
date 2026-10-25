"""Freeze the accepted 0.4.0 delivery and immutable inputs for release 0.5.0.

The script is deliberately read-only outside tools/release_050 and the two
release_050-owned F: directories. It performs no native cooks or asset builds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import configuration, check_storage  # noqa: E402

CONFIG = configuration(ROOT)
EXTERNAL = Path(CONFIG['external_root'])
OUT = EXTERNAL / 'output/release_050'
BASELINE = OUT / 'baseline'
SOURCE_BASELINE = OUT / 'source-baseline'
ROLLBACK = EXTERNAL / 'archives/release_040_user_accepted'
RELEASE_040 = EXTERNAL / 'output/release_040'
ZIP_PATH = RELEASE_040 / 'community_civilization_pack-0.4.0.zip'
NORMAL = Path(CONFIG['source_root'])
OLD_FREEZE = RELEASE_040 / 'baseline/freeze-baseline.json'
REPORT = ROOT / 'docs/RELEASE_040_REPORT.md'
MANIFEST = BASELINE / 'freeze-baseline.json'
EXPECTED_ZIP = '23e3f815fcfe47a4c373ab8a4154b84e7adb457492aa7688bf1ab33b58f60f30'
EXPECTED_SGA = 'b33168a31409c57096678bcda7fdd929e08c2ecc8b31de4148bb20f7f44898b6'
EXPECTED_MEMBERS = ['garrison.json', 'community_civilization_pack.sga',
                    'START-HERE.txt', 'EVIDENCE.json']
PROJECT_GUID = 'b7fcea91-257b-408f-b9e8-ae4d8bc402e1'

# The user's separate "Check trap walkability" task has finished its normal-
# edition source revision. Its original and final observations are retained;
# no normal bytes are restored, built or imported here. Pin the complete final
# external delta rather than permitting mutable cache/archive prefixes.
EXTERNAL_NORMAL_SNAPSHOT = BASELINE/'external-normal-final-snapshot.json'
EXTERNAL_NORMAL_SHA256 = 'fa5895bf5a0ffe1dffcb23bf77d227d529fc181fbc26515909ff17c276b9878c'


def normal_preservation(frozen: dict, current: dict) -> dict:
    before={r['path']:r for r in frozen['files']}
    after={r['path']:r for r in current['files']}
    assert before.keys() <= after.keys(),'Normal edition files were removed'
    changed={p for p in before if before[p]!=after[p]}
    added=set(after)-set(before)
    external=None
    if changed or added:
        assert sha(EXTERNAL_NORMAL_SNAPSHOT)==EXTERNAL_NORMAL_SHA256
        external=json.loads(EXTERNAL_NORMAL_SNAPSHOT.read_text(encoding='utf-8'))
        expected_changed={r['path']:r for r in external['changed']}
        expected_added={r['path']:r for r in external['added']}
        assert not external['removed']
        assert changed==set(expected_changed),('Unexpected normal edits',sorted(changed^set(expected_changed)))
        assert added==set(expected_added),('Unexpected normal additions',sorted(added^set(expected_added)))
        assert all(after[p]==row for p,row in (expected_changed|expected_added).items()),'External normal snapshot drifted'
    result={'status':'unchanged' if not changed and not added else 'external_concurrent_trap_work_observed',
            'changed':[{'before':before[p],'after':after[p]} for p in sorted(changed)],
            'added':[after[p] for p in sorted(added)],'removed':[],
            'untouched_original_files':len(before)-len(changed),
            'our_normal_edition_writes':False,
            'external_task':external['external_task'] if external else None,
            'external_snapshot_sha256':EXTERNAL_NORMAL_SHA256 if external else None,
            'note':'No normal files are restored, integrated or built by the Castle/050 task; original freeze remains immutable.'}
    output=BASELINE/'normal-concurrent-observation.json'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def walk_files(root: Path):
    """Walk a specific owned tree without following or entering reparse points."""
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
    rows = [{'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size,
             'sha256': sha(p)} for p in walk_files(root)]
    rows.sort(key=lambda row: row['path'].casefold())
    return {'root': str(root.resolve()), 'file_count': len(rows), 'files': rows}


def record(path: Path) -> dict:
    return {'path': str(path.resolve()), 'size': path.stat().st_size, 'sha256': sha(path)}


def copy_tree_verified(source: Path, destination: Path, expected: dict) -> None:
    if destination.exists():
        actual = tree(destination)
        if actual['files'] != expected['files']:
            raise RuntimeError(f'Existing immutable source copy differs: {destination}')
        return
    destination.mkdir(parents=True, exist_ok=False)
    for source_file in walk_files(source):
        relative = source_file.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
    actual = tree(destination)
    if actual['files'] != expected['files']:
        raise RuntimeError(f'Source snapshot copy verification failed: {destination}')


def package_proof() -> tuple[dict, bytes]:
    if not ZIP_PATH.is_file():
        raise FileNotFoundError(ZIP_PATH)
    actual_zip_hash = sha(ZIP_PATH)
    if actual_zip_hash != EXPECTED_ZIP:
        raise RuntimeError(f'0.4.0 ZIP hash mismatch: {actual_zip_hash}')
    with zipfile.ZipFile(ZIP_PATH, 'r') as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if names != EXPECTED_MEMBERS or len(names) != len(set(names)):
            raise RuntimeError(f'Unexpected 0.4.0 ZIP member list: {names}')
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f'ZIP CRC failure at {bad}')
        manifest = json.loads(archive.read('garrison.json').decode('utf-8-sig'))
        sga_bytes = archive.read('community_civilization_pack.sga')
        sga_hash = hashlib.sha256(sga_bytes).hexdigest()
        details = manifest.get('details', {})
        if manifest.get('schema') != 'garrison.mod/v1':
            raise RuntimeError('Wrong Garrison manifest schema')
        if manifest.get('bundle_key') != 'community_civilization_pack':
            raise RuntimeError('Wrong Garrison bundle key')
        if details.get('id') != 'community_civilization_pack' or details.get('version') != '0.4.0':
            raise RuntimeError('Wrong packaged Garrison identity/version')
        if details.get('author') != 'hosein81 and chilly5':
            raise RuntimeError('Packaged author metadata mismatch')
        if sga_hash != EXPECTED_SGA:
            raise RuntimeError(f'Embedded SGA hash mismatch: {sga_hash}')
        tuning = [member for member in manifest.get('members', [])
                  if member.get('role') == 'tuning']
        if len(tuning) != 1 or tuning[0].get('path') != 'community_civilization_pack.sga' or tuning[0].get('sha256') != EXPECTED_SGA:
            raise RuntimeError('Packaged SGA member declaration mismatch')
        proof = {
            'path': str(ZIP_PATH.resolve()), 'size': ZIP_PATH.stat().st_size,
            'sha256': actual_zip_hash, 'crc_test': 'passed',
            'members': [{'name': i.filename, 'size': i.file_size, 'crc32': f'{i.CRC:08x}'}
                        for i in infos],
            'manifest': {'schema': manifest['schema'], 'bundle_key': manifest['bundle_key'],
                         'version': details['version'], 'author': details['author'],
                         'project_guid_from_workspace': PROJECT_GUID},
            'embedded_sga': {'name': 'community_civilization_pack.sga',
                             'size': len(sga_bytes), 'sha256': sga_hash},
        }
        return proof, sga_bytes


def art_groups() -> dict:
    groups = {}
    for category in ('authoring', 'exports', 'recipes'):
        base = ROOT / 'art' / category
        for path in sorted(base.iterdir(), key=lambda p: p.name.casefold()):
            if path.is_dir() and path.name.endswith(('010', '020', '021', '030', '040')):
                groups[f'{category}_{path.name}'] = tree(path)
    return groups


def capture() -> dict:
    check_storage(ROOT, CONFIG)
    if not OLD_FREEZE.is_file() or not REPORT.is_file():
        raise FileNotFoundError('Required historical 0.4.0 freeze/report is missing')
    if not NORMAL.is_dir():
        raise FileNotFoundError(f'Preserved normal source is missing: {NORMAL}')
    old = json.loads(OLD_FREEZE.read_text(encoding='utf-8'))
    if old.get('status') != 'immutable_pre_040_baseline':
        raise RuntimeError('Historical 0.4.0 freeze has unexpected status')
    package, _ = package_proof()
    prior_groups = art_groups()
    previous_groups = old['prior_editable_art_export_recipe']
    for key, value in previous_groups.items():
        if key not in prior_groups or prior_groups[key]['files'] != value['files']:
            raise RuntimeError(f'Prior editable art changed since the 0.4.0 freeze: {key}')
    normal_tree = tree(NORMAL)
    old_normal = {row['path']: row for row in old['normal_edition']['files']}
    new_normal = {row['path']: row for row in normal_tree['files']}
    normal_delta = {
        'added_since_040_freeze': sorted(set(new_normal) - set(old_normal)),
        'removed_since_040_freeze': sorted(set(old_normal) - set(new_normal)),
        'changed_since_040_freeze': sorted(path for path in set(old_normal) & set(new_normal)
                                           if old_normal[path] != new_normal[path]),
    }
    project = ROOT / CONFIG['project_file']
    if record(project)['sha256'] != old['active_project']['sha256']:
        raise RuntimeError('Active project file differs from the 0.4.0 immutable freeze')
    assets = tree(ROOT / 'assets')
    config_files = {
        'project': record(project),
        'workspace': record(ROOT / 'workspace.json'),
    }
    return {
        'schema': 'community-civilization-pack/release-050-freeze/v1',
        'milestone': '0.5.0',
        'captured_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'immutable_pre_050_baseline',
        'accepted_release_040': package,
        'rollback': {
            'root': str(ROLLBACK.resolve()),
            'zip': str((ROLLBACK / ZIP_PATH.name).resolve()),
            'sga': str((ROLLBACK / 'community_civilization_pack.sga').resolve()),
            'zip_sha256': package['sha256'], 'sga_sha256': package['embedded_sga']['sha256'],
        },
        'active_project_and_config': config_files,
        'active_source_assets': assets,
        'normal_edition': normal_tree,
        'normal_edition_delta_from_040_freeze': normal_delta,
        'prior_editable_art_export_recipe': prior_groups,
        'historical_040_freeze': record(OLD_FREEZE),
        'historical_040_report': record(REPORT),
        'source_baseline_copy': {
            'root': str(SOURCE_BASELINE.resolve()),
            'assets': assets,
            'config': {'project': config_files['project'], 'workspace': config_files['workspace']},
        },
        'totals': {
            'active_asset_files': assets['file_count'],
            'normal_edition_files': normal_tree['file_count'],
            'prior_art_files': sum(v['file_count'] for v in prior_groups.values()),
        },
    }


def verify_against_freeze(value: dict, mode: str) -> dict:
    if not MANIFEST.is_file():
        raise FileNotFoundError(f'Immutable freeze is missing: {MANIFEST}')
    frozen = json.loads(MANIFEST.read_text(encoding='utf-8'))
    required = ['accepted_release_040', 'prior_editable_art_export_recipe',
                'active_project_and_config', 'historical_040_freeze', 'historical_040_report']
    if mode == 'strict_pre_edit':
        required.append('active_source_assets')
    for key in required:
        if value[key] != frozen[key]:
            raise RuntimeError(f'Protected 0.4.0 baseline changed: {key}')
    normal=normal_preservation(frozen['normal_edition'],value['normal_edition'])
    # The copy remains immutable even when authorized 0.5.0 active-source deltas are made.
    copy_now = tree(SOURCE_BASELINE / 'assets')
    if copy_now['files'] != frozen['active_source_assets']['files']:
        raise RuntimeError('Frozen source-baseline asset copy changed')
    if record(SOURCE_BASELINE / 'config/community_civilization_pack.aoe4mod')['sha256'] != frozen['active_project_and_config']['project']['sha256']:
        raise RuntimeError('Frozen project copy changed')
    if record(SOURCE_BASELINE / 'config/workspace.json')['sha256'] != frozen['active_project_and_config']['workspace']['sha256']:
        raise RuntimeError('Frozen workspace config copy changed')
    for filename, expected in ((ZIP_PATH.name, EXPECTED_ZIP),
                               ('community_civilization_pack.sga', EXPECTED_SGA)):
        rollback_file = ROLLBACK / filename
        if not rollback_file.is_file() or sha(rollback_file) != expected:
            raise RuntimeError(f'Accepted rollback artifact missing or changed: {rollback_file}')
    return {
        'status': 'verified', 'mode': mode,
        'zip_sha256': frozen['accepted_release_040']['sha256'],
        'sga_sha256': frozen['accepted_release_040']['embedded_sga']['sha256'],
        'source_asset_files': frozen['totals']['active_asset_files'],
        'normal_files': frozen['totals']['normal_edition_files'],
        'prior_art_files': frozen['totals']['prior_art_files'],
        'active_source_assets_checked': mode == 'strict_pre_edit',
        'authorized_050_source_policy': 'separate verification required after edits',
        'normal_edition_preservation': normal,
    }


def freeze() -> dict:
    if MANIFEST.exists():
        raise FileExistsError(f'Refusing to replace immutable 0.5.0 freeze: {MANIFEST}')
    value = capture()
    # Existing rollback files are immutable and may only be reused on exact hash match.
    ROLLBACK.mkdir(parents=True, exist_ok=True)
    proof, sga_bytes = package_proof()
    targets = ((ZIP_PATH, ROLLBACK / ZIP_PATH.name, EXPECTED_ZIP),)
    for source, target, expected in targets:
        if target.exists():
            if sha(target) != expected:
                raise RuntimeError(f'Existing rollback ZIP has a different hash: {target}')
        else:
            shutil.copy2(source, target)
        if sha(target) != expected:
            raise RuntimeError(f'Rollback ZIP copy verification failed: {target}')
    sga_target = ROLLBACK / 'community_civilization_pack.sga'
    if sga_target.exists():
        if sha(sga_target) != EXPECTED_SGA:
            raise RuntimeError(f'Existing rollback SGA has a different hash: {sga_target}')
    else:
        with sga_target.open('xb') as stream:
            stream.write(sga_bytes)
    if sha(sga_target) != EXPECTED_SGA:
        raise RuntimeError('Extracted rollback SGA verification failed')

    SOURCE_BASELINE.mkdir(parents=True, exist_ok=True)
    assets_source = ROOT / 'assets'
    copy_tree_verified(assets_source, SOURCE_BASELINE / 'assets', value['active_source_assets'])
    config_copy = SOURCE_BASELINE / 'config'
    config_copy.mkdir(parents=True, exist_ok=True)
    for relative in (CONFIG['project_file'], 'workspace.json'):
        source = ROOT / relative
        target = config_copy / Path(relative).name
        expected = value['active_project_and_config']['project' if relative == CONFIG['project_file'] else 'workspace']
        if target.exists():
            if record(target)['sha256'] != expected['sha256']:
                raise RuntimeError(f'Existing config snapshot differs: {target}')
        else:
            shutil.copy2(source, target)
        if record(target)['sha256'] != expected['sha256']:
            raise RuntimeError(f'Config snapshot verification failed: {target}')

    BASELINE.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    with MANIFEST.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(encoded)
    return {
        'status': 'frozen', 'manifest': str(MANIFEST),
        'rollback_root': str(ROLLBACK), 'source_baseline': str(SOURCE_BASELINE),
        'zip_sha256': value['accepted_release_040']['sha256'],
        'sga_sha256': value['accepted_release_040']['embedded_sga']['sha256'],
        'source_asset_files': value['totals']['active_asset_files'],
        'normal_files': value['totals']['normal_edition_files'],
        'prior_art_files': value['totals']['prior_art_files'],
        'zip_crc': 'passed',
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--verify-only', action='store_true',
                      help='strictly verify the frozen baseline before 0.5.0 edits')
    mode.add_argument('--verify-post-edit', action='store_true',
                      help='verify immutable 0.4.0 inputs while allowing separate 0.5.0 source edits')
    args = parser.parse_args()
    check_storage(ROOT, CONFIG)
    if args.verify_only or args.verify_post_edit:
        current = capture()
        result = verify_against_freeze(current, 'strict_pre_edit' if args.verify_only else 'post_edit_preservation')
    else:
        result = freeze()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
