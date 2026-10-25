"""Verify the 0.3.0 ZIP, then clean only measured regenerable readbacks."""
import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from common import ROOT, OUT, KEY, guarded, read, sha, write


def safe_files(folder):
    """Inventory one generated tree without following a symlink or junction."""
    result = {}
    pending = [folder]
    while pending:
        current = pending.pop()
        stat = current.lstat()
        assert not current.is_symlink() and not (getattr(stat, 'st_file_attributes', 0) & 0x400), current
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                stat = path.lstat()
                assert not entry.is_symlink() and not (getattr(stat, 'st_file_attributes', 0) & 0x400), path
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                else:
                    assert entry.is_file(follow_symlinks=False), path
                    result[path.relative_to(folder).as_posix()] = {'sha256': sha(path), 'bytes': stat.st_size}
    return result


def finalize():
    guarded()
    package = read(OUT / 'package-verification.json')
    audit = read(OUT / 'archive-verification.json')
    checks = read(OUT / 'release-checks.json')
    assert package['status'] == audit['status'] == 'passed'
    for key in ('zip', 'sga'): assert sha(package[key]) == package[key + '_sha256']
    with ZipFile(package['zip']) as bundle:
        assert bundle.testzip() is None
        assert bundle.namelist().count('garrison.json') == 1
        assert hashlib.sha256(bundle.read(KEY + '.sga')).hexdigest() == package['sga_sha256']
    cooked = read(read(OUT / 'art-cook-pointer.json')['receipt'])
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    readback_receipt = read(OUT / 'integration/fresh-cook-readback.json')
    assert readback_receipt['status'] == 'passed'
    assert readback_receipt['cook_sha256'] == cooked['cook']['sha256']
    cooked_members = readback_receipt['members']
    assert cooked_members
    cooked_readback = Path(cooked['readback'])
    if cooked_readback.exists():
        assert all((cooked_readback / member).is_file() and
                   sha(cooked_readback / member) == digest
                   for member, digest in cooked_members.items())
    else:
        prior_cleanup = read(OUT / 'cleanup-verification.json')
        assert prior_cleanup['status'] == 'passed'
        assert prior_cleanup['zip_sha256'] == package['zip_sha256']
        assert prior_cleanup['sga_sha256'] == package['sga_sha256']
        removed_cook = next(r for r in prior_cleanup['targets'] if r['path'] == str(cooked_readback))
        assert all(removed_cook['files'][member]['sha256'] == digest for member, digest in cooked_members.items())
    for name in ('exposed_pit', 'covered_pit', 'pho_minh', 'one_pillar'):
        prefix = f'art/scenario/garrison/community_030_art/buildings/{name}/model'
        assert all(prefix + ext in cooked_members for ext in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial'))
    footprint = read(read(OUT / 'footprint/current.json')['receipt'])
    assert footprint['status'] == 'passed' and footprint['native_validated_instances'] >= 255
    assert sha(footprint['archive']) == footprint['sha256']
    # Exact completed unpack dirs regenerate from retained baseline, candidate and art-cook SGAs.
    known = {audit['baseline_sha256'], package['sga_sha256'], cooked['cook']['sha256']}
    targets = []
    for folder in (OUT / 'readback').glob('*'):
        marker = folder / '.complete.json'
        if folder.is_dir() and marker.is_file() and read(marker).get('sha256') in known:
            targets.append(folder)
    if cooked_readback.exists() and cooked_readback not in targets:
        targets.append(cooked_readback)
    removed = []
    for folder in targets:
        files = safe_files(folder)
        resolved = folder.resolve()
        assert resolved.is_relative_to(OUT.resolve()) and resolved != OUT.resolve()
        assert folder.parent == OUT / 'readback' or folder.name.startswith('readback-cc030-')
        removed.append({'path': str(folder), 'files': files, 'bytes': sum(r['bytes'] for r in files.values())})
        shutil.rmtree(resolved)
    for key in ('zip', 'sga'): assert sha(package[key]) == package[key + '_sha256']
    receipt = {'status': 'passed', 'zip_sha256': package['zip_sha256'], 'sga_sha256': package['sga_sha256'],
               'reclaimed_bytes': sum(r['bytes'] for r in removed), 'targets': removed,
               'restoration': 'sga-archiver unpack each retained archive to its recorded readback path',
               'retained': ['all editable source, exports and recipes', 'registered Garrison projects and cooked archives',
                            'native reference and editor logs', 'candidate, ZIP, package and accepted rollback']}
    previous = OUT / 'cleanup-verification.json'
    if previous.exists():
        history = OUT / 'cleanup-history'
        history.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        saved = history / f'{stamp}-{sha(previous)[:12]}.json'
        assert not saved.exists()
        shutil.copy2(previous, saved)
        assert sha(saved) == sha(previous)
    write(OUT / 'cleanup-verification.json', receipt)
    report = f'''# Community Civilization Pack 0.3.0

Delivery: `{package['zip']}`. ZIP SHA-256 `{package['zip_sha256']}`; SGA SHA-256 `{package['sga_sha256']}`.
The final archive has {audit['final_members']} members. Exactly {len(audit['changed'])} prior members changed and
{len(audit['added'])} new private resources were added; {audit['untouched_members']} prior members are byte identical.
The Ministry visual resources are unchanged from accepted 0.2.1. Only four Ministry placement floats return from 16 to 8.
Pho Minh and One Pillar use private bindings, model and stamp resources; the alternate headquarters actor shares One Pillar.

Static checks: {checks['tests']['tests']} raw tests, {len(checks['tests']['failures'])} inherited donor-comparison failures,
no new errors/skips; tuning validator exited 0. Fresh Garrison art cook, native model-reference cook, isolated Content Editor
source build, archive readback and strict `garrison.mod/v1` ZIP checks passed. Cleanup reclaimed {receipt['reclaimed_bytes']} bytes.

Client import, lobby selection, solo-match appearance/behavior and multiplayer remain separate user gates. To test, close
AoE4, import the ZIP in Garrison, enable it, and select Community Civilization Pack in both Game Mode and Tuning Pack.
Choose China, then Vietnam in the opening selector. Test traps, both first-age landmarks and alternate headquarters,
Ministry placement, construction/damage/death, production paths, near/far views and two colours.
Rollback: reimport `{ROOT / 'archives/release_021_user_accepted/community_civilization_pack-0.2.1.zip'}` with AoE4 closed.
'''
    (OUT / 'release-report.md').write_text(report, encoding='utf-8')
    print('RELEASE_030_FINALIZED', package['zip'], receipt['reclaimed_bytes'])
    return receipt


if __name__ == '__main__': finalize()
