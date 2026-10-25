"""Bind actual native reference compilation to current source and fresh readback.

Run the audit with Blender's Python (the RGD codec is a CPython 3.13 module).
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from pipeline import guard, digest, save_json
from providers import ROOT, OUT


def check_correspondence(native, identities, draft, identity_sha, draft_sha, actual):
    expected = {r['name']: {r['pbgid']} for r in identities['identities']}
    staged = {Path(r['path']).stem: {r['pbgid']} for r in draft['added']}
    if (not native.get('native_source_identity_compile') or
        native.get('new_identity_instances') != len(expected) or
        len(expected) != len(identities['identities']) or
        len(staged) != len(draft['added']) or expected != staged or expected != actual or
        draft.get('identity_receipt_sha256') != identity_sha or
        native.get('source_receipt_sha256') != draft_sha):
        raise RuntimeError('Native reference compilation does not correspond to current source identities')


def audit():
    guard()
    cfg = json.loads((ROOT/'workspace.json').read_text())
    folder = OUT/'integration/native-reference-v2'
    native_file = folder/'receipt.json'
    draft_file = OUT/'integration/source-draft-v2.json'
    identity_file = OUT/'integration/voice-identities-complete.json'
    native = json.loads(native_file.read_text())
    draft = json.loads(draft_file.read_text())
    identities = json.loads(identity_file.read_text())
    freeze = json.loads((folder/'input-freeze.json').read_text())
    draft_sha = digest(draft_file)
    if (freeze['source_receipt_sha256'] != draft_sha or
        digest(draft['project']) != draft['project_sha256'] or
        digest(native['archive']) != native['archive_sha256']):
        raise RuntimeError('Native compile archive or staged project provenance changed')
    for path, sha in freeze['staged_files'].items():
        if digest(path) != sha:
            raise RuntimeError('Native compile input changed: '+path)
    for row in draft['added']:
        if digest(row['path']) != row['sha256']:
            raise RuntimeError('Staged identity source changed')
    count = len(list((Path(draft['root'])/'assets/attrib/instances').rglob('*.xml')))
    if native['native_validated_instances'] != count:
        raise RuntimeError('Native validated instance count differs from current staged source')
    sys.path.insert(0, str(ROOT/'tools/release_073'))
    from check_identity import check
    namespace = check(ROOT, Path(native['archive']))
    if native['archive_identity'] != namespace:
        raise RuntimeError('Native namespace receipt differs')
    sys.path.insert(0, cfg['garrison_extension'])
    from garrison_shared import rgd
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest = folder/'rechecks'/stamp
    dest.mkdir(parents=True, exist_ok=False)
    actual = {}; members = {}
    expected_members = {}
    for row in draft['added']:
        relative = Path(row['path']).relative_to(Path(draft['root'])/'assets/attrib/instances').with_suffix('.rgd')
        expected_members['attrib/'+relative.as_posix()] = Path(row['path']).stem
    if set(native['readback']) != set(expected_members):
        raise RuntimeError('Native readback member scope differs')
    for member, name in sorted(expected_members.items()):
        target = dest/'readback'/member
        target.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run([cfg['archive_tool'], 'extract-member', native['archive'], member, str(target)],
                              capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError('Fresh native reference extraction failed: '+member)
        sha = digest(target)
        if sha != native['readback'][member]['sha256']:
            raise RuntimeError('Fresh native readback differs from compile receipt')
        actual[name] = {n.value for _, n in rgd.flatten(rgd.read(target.read_bytes()).nodes) if n.key == 'pbgid'}
        members[member] = sha
    check_correspondence(native, identities, draft, digest(identity_file), draft_sha, actual)
    proof = dict(native_receipt_sha256=digest(native_file), archive_sha256=native['archive_sha256'],
                 archive_identity=namespace, identity_receipt_sha256=digest(identity_file),
                 source_receipt_sha256=draft_sha, input_freeze_sha256=digest(folder/'input-freeze.json'),
                 native_validated_instances=count, identities={k: sorted(v) for k,v in sorted(actual.items())},
                 fresh_member_sha256=members)
    save_json(dest/'proof.json', proof)
    return proof


if __name__ == '__main__':
    print(json.dumps(audit(), sort_keys=True))
