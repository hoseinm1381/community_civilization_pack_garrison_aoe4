"""Compose the 0.2.0 visual allowlist over the accepted 0.1.0 archive."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from common import ARCH, GUID, OUT, ROOT, guarded, read, run_logged, sha, write
from source_policy import CONSUMERS, verify as verify_sources

sys.dont_write_bytecode = True
WORK = OUT / 'integration'
BASELINE = ROOT / 'archives/release_010_user_accepted/community_civilization_pack.sga'


def archive_index(path):
    result = subprocess.run([str(ARCH), 'list', str(path), '--verify'], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', check=True)
    data = json.loads(result.stdout)
    assert data['archive']['verification']['verified']
    assert data['archive']['name'].replace('-', '').lower() == GUID.replace('-', '').lower()
    return {row['path']: row for row in data['members']}


def payloads(compiled, media, run):
    candidates = read(WORK / 'private-bindings.json')['payloads'] + media['payloads']
    actor_root = run / 'compiled-actor-payload'
    for name in CONSUMERS:
        member = f'attrib/ebps/vietnam/{name}.rgd'
        target = actor_root / member
        target.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([str(ARCH), 'extract-member', compiled['archive'], member,
                                 str(target)], capture_output=True, text=True,
                                encoding='utf-8', errors='replace')
        if result.returncode: raise RuntimeError(result.stdout + result.stderr)
        candidates.append({'member': member, 'file': str(target), 'sha256': sha(target),
                           'bytes': target.stat().st_size})
    indexed = {}
    for row in candidates:
        assert row['member'] not in indexed and sha(row['file']) == row['sha256'], row['member']
        indexed[row['member']] = row
    return [indexed[key] for key in sorted(indexed)]


def compose(label):
    frozen = guarded()
    assert re.fullmatch(r'c020[a-z0-9-]{2,24}', label)
    run = WORK / 'runs' / label
    if run.exists(): raise ValueError(f'Append-only candidate run already exists: {run}')
    run.mkdir(parents=True)
    assert sha(BASELINE) == frozen['accepted_release_010']['sga_sha256']
    source = verify_sources(read(WORK / 'source-bindings.json')['source_new_files'])
    pointer = read(WORK / 'candidate-build-pointer.json')
    compiled = read(pointer['receipt'])
    assert compiled['status'] == 'passed' and sha(compiled['archive']) == compiled['sha256']
    assert compiled['native_validated_instances'] == 255
    assert compiled['source_preservation']['source_assets_sha256'] == source['source_assets_sha256']
    media = read(WORK / 'media-020.json')
    assert media['status'] == 'passed'
    reference = read(WORK / 'reference-cook.json')
    assert reference['status'] == 'passed' and sha(reference['archive']) == reference['sha256']
    rows = payloads(compiled, media, run)
    referenced = reference['exact_inputs_sha256']
    private_members = {row['member'] for row in rows if row['member'].startswith('art/scenario/cc020/')}
    assert set(referenced) == private_members
    assert reference['models'] == media['models']
    for row in rows:
        if row['member'].startswith('art/scenario/cc020/'):
            assert referenced[row['member']] == row['sha256'], row['member']
    old = archive_index(BASELINE)
    expected_changed = {f'attrib/ebps/vietnam/{name}.rgd' for name in CONSUMERS}
    assert expected_changed <= set(old)
    new = {r['member'] for r in rows if r['member'] not in old}
    assert all(m.startswith(('art/scenario/cc020/', 'art/stamps/cc020/',
                             'attrib/attachments/attachment_lists/vietnam/release_020/vn_020_')) for m in new)
    frozen_inputs = {'status': 'frozen before composition', 'baseline': str(BASELINE),
                     'baseline_sha256': sha(BASELINE), 'candidate_source_build': compiled,
                     'media_receipt_sha256': sha(WORK / 'media-020.json'),
                     'native_reference_cook': reference, 'payloads': rows,
                     'changed_existing_allowlist': sorted(expected_changed), 'new_allowlist': sorted(new)}
    write(run / 'changed-resource-allowlist.json', frozen_inputs)
    current = BASELINE
    for alias, prefix in (('data', 'art/'), ('attrib', 'attrib/')):
        subset = [r for r in rows if r['member'].startswith(prefix)]
        mapping = run / f'{alias}-020-members.txt'
        mapping.write_text('\n'.join(r['member'] + '=' + r['file'] for r in subset) + '\n', encoding='utf-8')
        target = run / f'{alias}-020-candidate.sga'
        run_logged(f'compose-020-{label}-{alias}', [ARCH, 'set-members', current, mapping, target, '--alias', alias])
        current = target
    final = run / 'candidate/community_civilization_pack.sga'
    final.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(current, final)
    final_index = archive_index(final)
    assert set(final_index) == set(old) | new
    readback = run / 'candidate-archive-readback'
    run_logged(f'compose-020-{label}-readback', [ARCH, 'unpack', final, '--output', readback])
    for row in rows:
        assert sha(readback / row['member']) == row['sha256'], row['member']
    receipt = {'status': 'passed', 'archive': str(final), 'sha256': sha(final),
               'project_guid': GUID, 'baseline_archive': str(BASELINE),
               'baseline_sha256': sha(BASELINE), 'changed_existing_allowlist': sorted(expected_changed),
               'new_members': sorted(new), 'payloads': rows,
               'stamp_model_targets': media['stamp_model_targets'],
               'source_new_files': read(WORK / 'source-bindings.json')['source_new_files'],
               'candidate_source_build': compiled, 'native_reference_cook': reference,
               'native_runtime': 'unverified'}
    write(run / 'candidate.json', receipt)
    write(WORK / 'candidate-pointer.json', {'label': label, 'receipt': str(run / 'candidate.json'),
                                            'sha256': sha(run / 'candidate.json')})
    print('CANDIDATE_020_COMPOSED', len(old), len(final_index), sha(final))
    return receipt


if __name__ == '__main__':
    compose(sys.argv[1])
