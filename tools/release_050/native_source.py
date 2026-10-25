"""Isolated Content Editor compile and exact nonvisual actor proof for 0.5.0."""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from common import ARCH, BASELINE, CONFIG, GUID, OUT, ROOT, guarded, read, run_logged, sha, write
from source_policy import verify as verify_source
from reference_contracts import ACTORS
from bindings import exclusive_native

sys.path.insert(0, CONFIG['garrison_extension'])
from garrison_shared import rgd

WORK = OUT / 'native-source'
GUID32 = GUID.replace('-', '')
EDITOR = Path(CONFIG['content_editor'])


def extract(archive, member, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists(), destination
    run_logged('native050-extract-' + sha(archive)[:9] + '-' + member.replace('/', '-'),
               [ARCH, 'extract-member', archive, member, destination])


def compiled_visual_proof(before, after, identities):
    """Revert only explicit visual List references, then demand byte identity."""
    old, new = rgd.read(before.read_bytes()), rgd.read(after.read_bytes())
    left, right = dict(rgd.flatten(old.nodes)), dict(rgd.flatten(new.nodes))
    assert left.keys() == right.keys(), ('Compiled actor structure changed', after)
    actor = after.stem
    expected = {r['source'].rsplit('/', 1)[-1]: r for r in identities.values()
                if actor in r['actors']}
    assert expected, actor
    expected_paths = {}
    for path, previous in left.items():
        if (previous.key == '$PBGNAME' and '/attachments/' in path and
                previous.value in expected):
            row = expected[previous.value]
            expected_paths[path] = GUID32 + ':' + row['name']
    assert expected_paths, actor
    restored, edits = copy.deepcopy(new), []
    for path, previous in left.items():
        current = right[path]
        assert (previous.kind, previous.key) == (current.kind, current.key), path
        if path in expected_paths:
            assert current.value == expected_paths[path], \
                ('Expected private visual reference absent', actor, path, current.value)
        if previous.kind in ('List', 'List2') or previous.value == current.value: continue
        assert previous.key in ('$PBGNAME', '$PBGMAP') and '/attachments/' in path, (path, previous.value, current.value)
        assert previous.key == '$PBGNAME', (path, previous.value, current.value)
        row = expected.get(previous.value)
        assert row, ('Unexpected attachment donor', path, previous.value)
        assert current.value == GUID32 + ':' + row['name'], (path, current.value, row['name'])
        rgd.find(restored.nodes, path).value = previous.value
        edits.append({'path': path, 'before': previous.value, 'after': current.value,
                      'private_identity': row['member']})
    assert {r['path'] for r in edits} == set(expected_paths), \
        ('Incomplete actor visual rewire', actor, expected_paths, edits)
    assert rgd.write(restored) == rgd.write(old), 'Nonvisual compiled bytes changed'
    return {'edits': edits, 'all_nonvisual_compiled_fields_byte_identical': True,
            'accepted_actor_sha256': sha(before), 'new_actor_sha256': sha(after)}


def identity_proof(archive, extraction_root, entries):
    proofs = {}
    for row in entries.values():
        member = row['member']
        compiled = extraction_root / member
        extract(archive, member, compiled)
        doc = rgd.read(compiled.read_bytes())
        leaves = {p: n.value for p, n in rgd.flatten(doc.nodes) if not isinstance(n.value, list)}
        assert leaves['default/pbgid'] == row['pbgid'], member
        assert leaves['default/parent_pbg/$PBGNAME'] == row['source'].rsplit('/', 1)[-1]
        assert leaves['default/parent_pbg/$PBGMAP'] == r'attachments\attachment_lists'
        final = OUT / 'integration/payload' / member
        assert final.is_file(), ('Private attachment absent', member)
        private = rgd.read(final.read_bytes())
        assert rgd.find(private.nodes, 'default/pbgid').value == row['pbgid']
        proofs[member] = {'compiled_identity_sha256': sha(compiled),
                          'final_private_sha256': sha(final),
                          'pbgid': row['pbgid'], 'parent': row['source'],
                          'compiled_parent_verified': True}
    return proofs


MONASTERY = 'vn_building_unit_religious_control_chi'


def overlay_monastery_visuals(accepted, compiled, target, entries):
    """Reproduce four private attachment substitutions on the compiled actor.

    The installed Content Editor does not apply this actor's inherited sparse
    tier XML. Its accepted source is retained verbatim, and this private RGD
    overlay is gated by an exact pre-edit byte comparison and full post-edit
    compiled_visual_proof. No other compiled leaf may change.
    """
    assert sha(compiled) == sha(accepted), 'Raw monastery compile drifted from accepted 0.4 actor'
    doc = rgd.read(compiled.read_bytes())
    old = dict(rgd.flatten(doc.nodes))
    allowed = {entries[key]['source'].rsplit('/', 1)[-1]: entries[key]
               for key in ('monastery03', 'monastery04')}
    actions = []
    for path, node in old.items():
        if node.key != '$PBGNAME' or '/attachments/' not in path or node.value not in allowed:
            continue
        assert path.startswith(('default/tier_ext/', 'campaign/tier_ext/')), path
        row = allowed[node.value]
        previous_value = node.value
        new_value = GUID32 + ':' + row['name']
        rgd.find(doc.nodes, path).value = new_value
        actions.append({'path': path, 'before': previous_value, 'after': new_value,
                        'private_identity': row['member']})
    assert len(actions) == 4
    assert {(a['path'].split('/', 1)[0], a['before']) for a in actions} == {
        (branch, donor) for branch in ('default', 'campaign') for donor in allowed
    }, 'Monastery branch-by-donor visual coverage incomplete'
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), target
    target.write_bytes(rgd.write(doc))
    proof = compiled_visual_proof(accepted, target, entries)
    assert sorted(actions, key=lambda r: r['path']) == sorted(proof['edits'], key=lambda r: r['path'])
    return {'method': 'exact-compiled-visual-reference-overlay',
            'source_actor_byte_identical_to_accepted_040': True,
            'raw_compiled_actor': str(compiled), 'raw_sha256': sha(compiled),
            'final_actor': str(target), 'final_sha256': sha(target),
            'actions': actions, 'full_nonvisual_byte_restoration_passed': True}


def compile(label):
    """Caller holds the controller grant; this function owns the native lock."""
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label), label
    source_policy = verify_source()
    bindings = read(OUT / 'integration/private-bindings.json')
    assert bindings['status'] == 'passed'
    run = WORK / 'runs' / label
    assert not run.exists(), 'Use a fresh append-only native source run label'
    source = run / 'source'
    source.mkdir(parents=True)
    shutil.copytree(ROOT / 'assets', source / 'assets')
    shutil.copy2(ROOT / CONFIG['project_file'], source / CONFIG['project_file'])
    with exclusive_native():
        log = run_logged('native-source050-' + label,
            [EDITOR, '-rtm', '--safe_settings', '--do_not_restore',
             '--quiet_crash_report', '--no_source_control',
             '--log_path', run / 'native-logs', '--build_mod', source / CONFIG['project_file'],
             '--build_path', run / 'build', '--no_burn_window', '--burn_cache_type', 'Local',
             '--burn_max_threads', '1', '--burn_platform', 'PC', '--burn_log_path', run / 'burn.log',
             '--intermediate_path', run / 'intermediate'], cwd=EDITOR.parent, timeout=1800)
    return finish(label, source_policy, log)


def finish(label, source_policy=None, log=None):
    """Resume a finished editor run without rerunning the native compilation."""
    guarded()
    run = WORK / 'runs' / label
    source = run / 'source'
    assert source.is_dir(), run
    source_policy = source_policy or verify_source()
    log = Path(log or OUT / 'logs' / ('native-source050-' + label + '.log'))
    text = log.read_text(encoding='utf-8', errors='replace')
    errors = [line for line in text.splitlines() if 'EssenceEditor.exe Error:' in line or
              'System does not support' in line]
    missing = [line for line in text.splitlines() if str(source).lower() in line.lower() and
               ("doesn't exist" in line or 'does not exist' in line)]
    counts = re.findall(r'(\d+) instances validated', text)
    expected_count = len(list((source / 'assets/attrib/instances').rglob('*.xml')))
    assert (not errors and not missing and counts and int(counts[-1]) == expected_count), \
        (errors, missing, counts, expected_count)
    archives = list((run / 'build').rglob('*.sga'))
    assert len(archives) == 1, archives
    archive = archives[0]
    listing = json.loads(subprocess.run([str(ARCH), 'list', str(archive), '--verify'],
                                 capture_output=True, text=True, check=True).stdout)
    assert listing['archive']['verification']['verified']
    assert listing['archive']['name'].replace('-', '').lower() == GUID32.lower()
    entries = read(OUT / 'integration/registered-identities.json')['entries']
    assert len(entries) == 9
    binding = read(OUT / 'integration/private-bindings.json')
    assert binding['status'] == 'passed'
    proofs = identity_proof(archive, run / 'compiled-identity', entries)
    rows, actors = [], {}
    monastery_overlay = None
    for actor in ACTORS:
        member = f'attrib/ebps/vietnam/{actor}.rgd'
        target, prior = run / 'payload' / member, run / 'accepted-040' / member
        extract(BASELINE, member, prior)
        if actor == MONASTERY:
            raw = run / 'compiled-raw' / member
            extract(archive, member, raw)
            monastery_overlay = overlay_monastery_visuals(prior, raw, target, entries)
            write(run / 'monastery-compiled-overlay.json', monastery_overlay)
        else:
            extract(archive, member, target)
        actors[member] = compiled_visual_proof(prior, target, entries)
        rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                     'bytes': target.stat().st_size})
    # The compiled identities prove Content Editor registration. The final
    # archive receives the private visual-list RGDs at these same members.
    assert len(rows) == 6 and len({r['member'] for r in rows}) == 6
    assert source_policy == verify_source()
    assert {p.relative_to(source / 'assets').as_posix(): sha(p)
            for p in (source / 'assets').rglob('*') if p.is_file()} == {
            p.relative_to(ROOT / 'assets').as_posix(): sha(p)
            for p in (ROOT / 'assets').rglob('*') if p.is_file()}
    receipt = {'schema': 'ccp.release050.native-source/v1', 'status': 'passed',
               'source_policy': source_policy, 'native_validated_instances': expected_count,
               'log': str(log), 'archive': str(archive), 'archive_sha256': sha(archive),
               'payloads': rows, 'compiled_proofs_nonvisual': actors,
               'monastery_compiled_visual_overlay': monastery_overlay,
               'compiled_attachment_identities': proofs, 'native_runtime': 'unverified'}
    write(run / 'receipt.json', receipt)
    write(WORK / 'current.json', {'receipt': str(run / 'receipt.json'),
                                 'sha256': sha(run / 'receipt.json')})
    return receipt


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'compile': compile(sys.argv[2])
    elif action == 'finish': finish(sys.argv[2])
    else: raise SystemExit('compile LABEL|finish LABEL')
