"""Read-only archive preservation gate; does not qualify visual or native behavior.

Allowlist schema: {schema: ccp-060-resource-allowlist/v1, entries: [
 {member: art/..., before_sha256: <hash or null for addition>, after_sha256: <hash>}
]}. Every actual change/addition must match exactly; removals are refused.
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from common import ARCH, CFG, OUT, guard, owned, read, sha, files, write
from pin_final053 import PIN, RECEIPT, verify as verify_baseline


def safe_member(name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or name.startswith('/') or '..' in PurePosixPath(name).parts
            or str(PurePosixPath(name)) != name):
        raise ValueError(f'Unsafe resource path: {name!r}')
    return name


def require_evidence_area(path):
    path = Path(path)
    area = (OUT/'qualification').resolve()
    if path.resolve() == area or not path.resolve().is_relative_to(area):
        raise ValueError('Archive audit evidence must be a new OUT/qualification subdirectory')
    return path


def compare_maps(before, after, entries, protected):
    declared = {}
    for row in entries:
        name = safe_member(row['member'])
        if name.casefold() in {n.casefold() for n in declared}:
            raise ValueError('Duplicate allowlist resource: ' + name)
        for key in ('before_sha256', 'after_sha256'):
            digest = row.get(key)
            if digest is None and key == 'before_sha256':
                continue
            if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('Invalid ' + key + ' for ' + name)
        declared[name] = row
    for mapping in (before, after):
        if len({safe_member(n).casefold() for n in mapping}) != len(mapping):
            raise ValueError('Duplicate/case-colliding archive resources')
    removed = set(before) - set(after)
    if removed:
        raise ValueError('Baseline members removed: ' + repr(sorted(removed)))
    added = set(after) - set(before)
    changed = {n for n in set(before) & set(after) if before[n] != after[n]}
    actual = added | changed
    if actual & protected:
        raise ValueError('Final 053 protected payload changed: ' + repr(sorted(actual & protected)))
    if actual != set(declared):
        raise ValueError('Actual delta differs from allowlist: ' + repr(sorted(actual ^ set(declared))))
    for name, row in declared.items():
        expected_before = before.get(name, {}).get('sha256')
        if row['before_sha256'] != expected_before:
            raise ValueError('Wrong expected before hash: ' + name)
        if row['after_sha256'] != after[name]['sha256']:
            raise ValueError('Wrong expected after hash: ' + name)
    return {'changed':sorted(changed), 'added':sorted(added), 'removed':[],
            'unchanged_count':len(before)-len(changed),
            'status':'hash-preservation-passed-not-source-or-native-acceptance'}


def command(*args):
    proc = subprocess.run([str(ARCH), *map(str,args)], capture_output=True,
                          text=True, timeout=120)
    if proc.returncode:
        raise RuntimeError(proc.stderr + '\n' + proc.stdout)
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--allowlist', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True,
                        help='New owned 060 evidence directory; existing output is never replaced')
    args = parser.parse_args()
    guard()
    candidate, evidence = owned(args.candidate), require_evidence_area(owned(args.evidence))
    if evidence.resolve().is_relative_to(PIN.resolve()):
        raise ValueError('Evidence may not alter the immutable final baseline')
    baseline = verify_baseline()
    recipe = read(owned(args.allowlist))
    if recipe.get('schema') != 'ccp-060-resource-allowlist/v1':
        raise ValueError('Wrong resource allowlist schema')
    if evidence.exists():
        raise FileExistsError('Preserve earlier archive audit: ' + str(evidence))
    candidate_sha = sha(candidate)
    listing = command('list', candidate, '--verify')
    if not listing['archive']['verification']['verified']:
        raise ValueError('Archive verification failed')
    identity = listing['archive']['name'].replace('-','').lower()
    if identity != CFG['project_guid'].replace('-','').lower():
        raise ValueError('Candidate does not retain final project identity')
    names = [safe_member(row['path']) for row in listing['members']]
    if len({n.casefold() for n in names}) != len(names) or not all('.' in n for n in names):
        raise ValueError('Ambiguous member inventory or incomplete extraction filter')
    evidence.mkdir(parents=True)
    write(evidence/'listing.json', listing)
    extraction = command('extract', candidate, evidence/'members', '--filter', '.')
    write(evidence/'extraction.json', extraction)
    after = files(evidence/'members', reject_links=True, exclude_release_060=False)
    if set(after) != set(names) or sha(candidate) != candidate_sha:
        raise ValueError('Candidate inventory changed during readback')
    protected = {row['member'] for row in baseline['preserved053_resources']}
    result = compare_maps(baseline['archive_members'], after, recipe['entries'], protected)
    result.update(schema='ccp-060-archive-delta-verification/v1', candidate=str(candidate),
        candidate_sha256=candidate_sha, baseline_freeze=str(RECEIPT),
        baseline_freeze_sha256=sha(RECEIPT), allowlist_sha256=sha(args.allowlist),
        members=after, protected053_resources_unchanged=True,
        source_visual_scope='Requires separate source/binding qualification; this gate checks exact bytes only',
        native_match=False, multiplayer=False)
    write(evidence/'receipt.json', result)
    print(json.dumps({key:result[key] for key in ('status','changed','added','unchanged_count')}))


if __name__ == '__main__':
    main()
