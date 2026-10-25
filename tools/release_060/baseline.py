"""Inspect final merge candidates without accepting diagnostic or corrupt ZIPs."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath
from common import CFG, OUT, guard, write, sha

def inspect_zip(path):
    path = Path(path)
    if 'diagnostic' in path.name.lower():
        raise ValueError('Diagnostic ZIP is not a final integration baseline')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP members')
        if archive.testzip() is not None:
            raise ValueError('Unreadable ZIP member')
        manifest = json.loads(archive.read('garrison.json'))
        details = manifest.get('details', {})
        version = details.get('version')
        key = CFG['package_key']
        if manifest.get('schema') != 'garrison.mod/v1' or version not in ('0.5.2','0.5.3'):
            raise ValueError('Expected strict final 0.5.2 or 0.5.3 manifest')
        if manifest.get('bundle_key') != key or details.get('id') != key:
            raise ValueError('Wrong project identity')
        if path.name != f'{key}-{version}.zip':
            raise ValueError('Expected exact final delivery filename')
        members = manifest.get('members', [])
        if len(members) != 1 or members[0].get('role') != 'tuning' or members[0].get('mod_key') != key:
            raise ValueError('Expected one owning tuning archive')
        member = members[0]
        name = member.get('path', '')
        if name != f'{key}.sga' or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
            raise ValueError('Unexpected archive member path')
        with archive.open(name) as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != member.get('sha256'):
            raise ValueError('Embedded SGA does not match manifest SHA-256')
    return {'version': version, 'zip': str(path.resolve()), 'zip_sha256': sha(path),
            'sga_member': name, 'sga_sha256': digest,
            'status': 'zip-and-member-hash-verified-native-archive-source-and-completion-still-required'}

def readiness():
    guard()
    candidates, rejected = [], []
    for version, folder in (('0.5.3','release_053'),('0.5.2','release_052')):
        path = OUT.parent/folder/f"{CFG['package_key']}-{version}.zip"
        if not path.is_file():
            rejected.append({'version':version, 'reason':'Final delivery ZIP not present'})
            continue
        try:
            candidates.append(inspect_zip(path))
        except (ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as error:
            rejected.append({'version':version, 'reason':str(error)})
    report = {'schema':'ccp-060-integration-readiness/v1',
              'status':'awaiting-final-baseline' if not candidates else 'candidate-found-not-pinned',
              'preferred_candidate': candidates[0] if candidates else None,
              'candidates': candidates, 'rejected_or_missing':rejected,
              'remaining_gates':['Representative samples approved by user',
                 'All unit family export/cook qualification complete',
                 'Landmark release completion confirmed and matching source frozen',
                 'Expected-value visual delta applied to final baseline',
                 'Changed-resource allowlist and untouched-member verification']}
    pin = OUT/'baseline/final053/freeze.json'
    if pin.exists():
        # Verify the owned bytes, not merely the presence of a selection record.
        from pin_final053 import verify
        frozen = verify()
        report['status'] = 'final-baseline-pinned-unit-qualification-pending'
        report['pinned_baseline'] = {'version':frozen['version'], 'freeze':str(pin),
            'freeze_sha256':sha(pin), 'zip_sha256':frozen['zip_sha256'],
            'sga_sha256':frozen['sga_sha256'], 'archive_members':len(frozen['archive_members'])}
        report['remaining_gates'].remove('Landmark release completion confirmed and matching source frozen')
    write(OUT/'integration-readiness.json', report)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--inspect', type=Path)
    args = parser.parse_args()
    guard()
    print(json.dumps(inspect_zip(args.inspect) if args.inspect else readiness(), indent=2))
