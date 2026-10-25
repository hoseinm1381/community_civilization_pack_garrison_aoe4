"""Independently read back every member and compare final SGA with frozen baseline."""
import argparse
import json
import subprocess
from pathlib import Path
from common import ARCH, CONFIG, GUID, OUT, check_storage, ROOT, read, sha, snapshot, write


def listing(path):
    result = subprocess.run([str(ARCH), 'list', str(path), '--verify'], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', check=True)
    data = json.loads(result.stdout)
    if not data['archive']['verification']['verified']:
        raise ValueError('Archive member verification failed')
    if data['archive']['name'].replace('-', '').lower() != GUID.replace('-', '').lower():
        raise ValueError('Archive identity differs from final project')
    return data


def extracted(path, label):
    parent = OUT / 'verification-readback'
    folder = parent / (label + '-' + sha(path)[:16])
    marker = folder / '.readback-complete.json'
    if not marker.exists():
        if folder.exists():
            raise ValueError(f'Incomplete readback exists; preserve for diagnosis: {folder}')
        result = subprocess.run([str(ARCH), 'unpack', str(path), '--output', str(folder)], capture_output=True,
                                text=True, encoding='utf-8', errors='replace')
        if result.returncode:
            raise RuntimeError(f'Whole-archive readback failed: {result.stdout}\n{result.stderr}')
        write(marker, {'archive': str(path), 'sha256': sha(path)})
    if read(marker)['sha256'] != sha(path):
        raise ValueError('Readback identity changed')
    return folder


def verify(candidate_path):
    check_storage(ROOT, CONFIG)
    candidate = read(candidate_path)
    baseline = Path(read(OUT / 'baseline-build-result.json')['archive'])
    final = Path(candidate['archive'])
    if sha(final) != candidate['sha256']:
        raise ValueError('Candidate archive hash changed')
    a, b = listing(baseline), listing(final)
    original = {r['path'].lower(): r for r in a['members']}
    updated = {r['path'].lower(): r for r in b['members']}
    if set(original) - set(updated):
        raise ValueError('Final archive dropped baseline members')
    before, after = extracted(baseline, 'baseline'), extracted(final, 'final')
    changed = []
    unchanged = []
    for key, row in original.items():
        left, right = before / row['path'], after / updated[key]['path']
        if sha(left) == sha(right):
            unchanged.append(key)
        else:
            changed.append(key)
    declared = candidate['changed_existing_members']
    declared = {r.lower() if isinstance(r, str) else r.get('path', r.get('member')).lower() for r in declared}
    if set(changed) != declared:
        raise ValueError(f'Changed-member declaration mismatch: actual={changed}, declared={declared}')
    expected_actors = {f'attrib/ebps/vietnam/{name}.rgd' for name in (
        'vn_building_house_control_chi', 'vn_building_house_control_faster_chi',
        'vn_building_bambo_outpost_chi', 'vn_building_defense_outpost_bambo_chi')}
    if set(changed) != expected_actors:
        raise ValueError(f'Unapproved existing member changes: {changed}')
    new = sorted(set(updated) - set(original))
    declared_new = {r.lower() if isinstance(r, str) else r.get('path', r.get('member')).lower() for r in candidate['new_members']}
    if set(new) != declared_new:
        raise ValueError('New-member declaration mismatch')
    if any(not p.startswith(('art/', 'attrib/attachments/')) for p in new):
        raise ValueError('New resource outside visual namespace')
    # Re-run the typed compiled graph reader against this independently extracted
    # final archive, then bind every visited private resource to these exact bytes.
    subprocess.run([CONFIG['blender_python'], '-B', str(ROOT / 'tools/release_010/integration_closure.py'),
                    str(final), str(after), str(candidate_path.parent)], check=True)
    closure = read(candidate_path.parent / 'closure.json')
    if closure['status'] != 'passed' or closure['archive_sha256'] != sha(final):
        raise ValueError('Compiled dependency closure is stale or failed')
    visited = {r['member'].lower(): r for r in closure['visited_private_entries']}
    if not set(new).issubset(visited) or len(closure['actors']) != 4 or len(closure['private_stamps']) != 6:
        raise ValueError('Closure does not cover all new resources/four actors/six stamps')
    for member, record in visited.items():
        if member not in updated or sha(after / updated[member]['path']) != record['sha256']:
            raise ValueError(f'Compiled closure resource mismatch: {member}')
    result = {'status': 'passed', 'baseline_sha256': sha(baseline), 'sga_sha256': sha(final),
        'candidate_sha256': sha(candidate_path),
        'baseline_members': len(original), 'final_members': len(updated),
        'unchanged_member_count': len(unchanged), 'changed_existing_members': changed,
        'new_members': new, 'project_guid': GUID,
        'compiled_closure': {'status':'passed','visited_private_members':len(visited),
                            'native_terminal_members':len(closure['resolved_native_entries'])},
        'proof': 'Every baseline/final decoded member SHA-256 compared; both archives passed CRC/SHA1-block verification',
        'native_runtime': 'not tested'}
    write(OUT / 'archive-verification.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'new_members'}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, default=OUT / 'integration/candidate.json')
    verify(parser.parse_args().candidate)
