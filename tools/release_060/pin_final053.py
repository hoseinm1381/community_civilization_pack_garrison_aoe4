"""Freeze the user-selected final release; never refresh historical freezes.

This is a read-only consumer of 053 and the active project. All writes belong
to 060. Re-running verifies the existing snapshot instead of replacing it.
"""
import datetime
import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from common import *
from baseline import inspect_zip

PIN = OUT/'baseline/final053'
RECEIPT = PIN/'freeze.json'
ZIP_SHA = '8f5bca3e884e26012518dbdfcada4fc3e31d8a9025b44e3e88c0a08d9f6e1bb1'
SGA_SHA = 'af202bcb644b4a8c74ff4a598a5374fff7c7a3df47457f3eee5c2195509b6456'
ABILITY = 'attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'
ABILITY_SHA = '7f0d8c6380b73474a8e4794ce14d336be76900371e369c01978cf1c4b3dba382'


def checked(command):
    run = subprocess.run([str(p) for p in command], capture_output=True,
                         text=True, timeout=120)
    if run.returncode:
        raise RuntimeError(f'{command[0]} failed: {run.stderr}\n{run.stdout}')
    return run.stdout


def copy_exact(source, target, expected):
    source, target = Path(source), owned(target)
    if sha(source) != expected:
        raise ValueError(f'Input hash mismatch: {source}')
    if target.exists():
        if not target.is_file() or sha(target) != expected:
            raise ValueError(f'Existing copy differs; preserve for inspection: {target}')
        return {'path': str(target), 'sha256': expected, 'bytes': target.stat().st_size,
                'original': str(source)}
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst)
    if sha(target) != expected or sha(source) != expected:
        raise RuntimeError(f'Copy/input drift: {source}')
    return {'path': str(target), 'sha256': expected, 'bytes': target.stat().st_size,
            'original': str(source)}


def verify_protection(frozen, embedded_payloads):
    """Bind the protected list to evidence inside the hash-pinned delivery ZIP."""
    rows = frozen.get('preserved053_resources', [])
    expected = {row['member']:row['sha256'] for row in embedded_payloads}
    actual = {row['member']:row['sha256'] for row in rows}
    if (len(rows) != 4 or len(embedded_payloads) != 4 or len(expected) != 4
            or actual != expected or any(frozen['archive_members'].get(name, {}).get('sha256')
                                        != digest for name, digest in expected.items())):
        raise ValueError('Final 053 protected resource list differs from delivered ZIP evidence')


def verify(check_selection=True):
    guard()
    frozen = read(RECEIPT)
    if frozen['schema'] != 'ccp-060-final-baseline-freeze/v1' or frozen['version'] != '0.5.3':
        raise ValueError('Wrong baseline receipt')
    if check_selection:
        selection = read(RECIPES/'integration-baseline-selection.json')
        if (selection.get('freeze_sha256') != sha(RECEIPT)
                or selection.get('selected_version') != '0.5.3'
                or not selection.get('identity_pinned')
                or selection.get('zip_sha256') != ZIP_SHA
                or selection.get('sga_sha256') != SGA_SHA):
            raise ValueError('Pinned freeze differs from final baseline selection')
    for item in frozen['retained_files']:
        if sha(item['path']) != item['sha256']:
            raise ValueError(f'Pinned input changed: {item["path"]}')
    for category, path in (('assets', PIN/'source/assets'), ('identities', PIN/'source/identity')):
        if files(path, reject_links=True) != frozen['inputs'][category]:
            raise ValueError(f'Pinned source changed: {category}')
    if files(PIN/'archive-members', reject_links=True) != frozen['archive_members']:
        raise ValueError('Pinned archive-member bytes changed')
    inspection = inspect_zip(PIN/'community_civilization_pack-0.5.3.zip')
    if inspection['zip_sha256'] != ZIP_SHA or inspection['sga_sha256'] != SGA_SHA:
        raise ValueError('Pinned ZIP/SGA identity changed')
    with zipfile.ZipFile(PIN/'community_civilization_pack-0.5.3.zip') as archive:
        embedded = json.loads(archive.read('EVIDENCE.json'))
    verify_protection(frozen, embedded['payloads'])
    return frozen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-incomplete', action='store_true')
    args = parser.parse_args()
    guard()
    if RECEIPT.exists():
        result = verify()
        print(json.dumps({'status':'existing-final053-freeze-verified',
                          'receipt':str(RECEIPT), 'archive_members':len(result['archive_members'])}))
        return
    if PIN.exists() and not args.resume_incomplete:
        raise FileExistsError('Incomplete pin preserved for inspection: ' + str(PIN))
    previous = OUT.parent/'release_053'
    delivery = previous/'community_civilization_pack-0.5.3.zip'
    inspection = inspect_zip(delivery)
    if inspection['zip_sha256'] != ZIP_SHA or inspection['sga_sha256'] != SGA_SHA:
        raise ValueError('Unexpected final 053 delivery')
    verification = checked([sys.executable, ROOT/'tools/release_053/verify.py'])
    reconciliation = read(OUT/'inventory/final053-source-reconciliation.json')
    if reconciliation['comparison']['changed_count'] != 1:
        raise ValueError('Unexpected final-source reconciliation')
    prep = read(OUT/'baseline/preparation-freeze.json')
    assets = files(ROOT/'assets', reject_links=True)
    expected = dict(prep['inputs']['assets'])
    expected[ABILITY] = {'sha256':ABILITY_SHA, 'bytes':13866}
    if assets != expected or files(CFG['source_root']) != prep['inputs']['normal']:
        raise ValueError('Active final source/normal edition does not match expected baseline')
    recipe_path = ROOT/'art/recipes/release_053/integration.json'
    recipe = read(recipe_path)
    if sha(recipe['source_overlay']) != ABILITY_SHA:
        raise ValueError('Source overlay mismatch')
    PIN.mkdir(parents=True, exist_ok=args.resume_incomplete)
    retained = [copy_exact(delivery, PIN/delivery.name, ZIP_SHA),
                copy_exact(previous/'package/community_civilization_pack.sga',
                           PIN/'community_civilization_pack.sga', SGA_SHA)]
    if (PIN/'source/assets').exists():
        if files(PIN/'source/assets', reject_links=True) != assets:
            raise ValueError('Incomplete source snapshot differs; preserve for inspection')
    else:
        copy_manifest(ROOT/'assets', PIN/'source/assets', assets)
    identities = {n:{'sha256':sha(ROOT/n), 'bytes':(ROOT/n).stat().st_size}
                  for n in ('workspace.json', CFG['project_file'])}
    if (PIN/'source/identity').exists():
        if files(PIN/'source/identity', reject_links=True) != identities:
            raise ValueError('Incomplete identity snapshot differs; preserve for inspection')
    else:
        copy_manifest(ROOT, PIN/'source/identity', identities)
    archive = PIN/'community_civilization_pack.sga'
    listing = json.loads(checked([ARCH, 'list', archive, '--verify']))
    members = listing['members']
    if not listing['archive']['verification']['verified'] or len(members) != 811:
        raise ValueError('Final archive verification/member count failed')
    names = [m['path'] for m in members]
    if len({n.casefold() for n in names}) != len(names):
        raise ValueError('Duplicate/case-colliding archive members')
    for name in names:
        if Path(name).is_absolute() or '..' in Path(name).parts or ':' in name:
            raise ValueError('Unsafe archive member: ' + name)
    write(PIN/'archive-listing.json', listing)
    if not all('.' in name for name in names):
        raise ValueError('Full-member filter would omit a member')
    if (PIN/'archive-members').exists():
        raise FileExistsError('Partial extraction requires inspection; will not overwrite it')
    extracted = json.loads(checked([ARCH, 'extract', archive, PIN/'archive-members', '--filter', '.']))
    write(PIN/'archive-extraction.json', extracted)
    inventory = files(PIN/'archive-members', reject_links=True)
    if set(inventory) != set(names):
        raise ValueError('Readback member set mismatch')
    for payload in recipe['payloads']:
        if inventory[payload['member']]['sha256'] != payload['sha256']:
            raise ValueError('Final 053 preserved payload mismatch: ' + payload['member'])
    dependency_paths = [recipe_path, previous/'package-verification.json',
        previous/'package/EVIDENCE.json', ROOT/'docs/RELEASE_053_REPORT.md',
        Path(recipe['source_native_receipt']), Path(recipe['material_recipe']),
        OUT/'inventory/final053-source-reconciliation.json',
        OUT/'baseline/preparation-freeze.json']
    for i, path in enumerate(dependency_paths):
        retained.append(copy_exact(path, PIN/'provenance'/f'{i:02d}-{path.name}', sha(path)))
    for payload in recipe['payloads']:
        retained.append(copy_exact(payload['file'], PIN/'preserved053'/payload['member'], payload['sha256']))
    (PIN/'verification053.txt').write_text(verification, encoding='utf-8')
    retained.append({'path':str(PIN/'verification053.txt'), 'sha256':sha(PIN/'verification053.txt')})
    if files(ROOT/'assets', reject_links=True) != assets:
        raise RuntimeError('Active source changed during freeze')
    freeze = {'schema':'ccp-060-final-baseline-freeze/v1', 'version':'0.5.3',
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'final-baseline-pinned-artwork-integration-pending',
        'selection':'User: version 0.5.3 is finalized, so we can use that',
        'zip_sha256':ZIP_SHA, 'sga_sha256':SGA_SHA,
        'inputs':{'assets':assets, 'identities':identities, 'normal':prep['inputs']['normal']},
        'retained_files':retained, 'archive_members':inventory,
        'preserved053_resources':recipe['payloads'],
        'source_archive_relation':'314 active source files match 053 preservation policy; the stealth overlay matches native cook. The three material payloads are compiled archive changes and must be retained independently of source.',
        'native_acceptance':'053 finalized by explicit user request without another native test. This does not qualify 060 import, appearance, gameplay or multiplayer.',
        'integration_policy':'Start from this exact SGA; use expected values and explicit visual allowlist. Preserve all unrelated archive-member SHA256 values, including the four 053 payloads.',
        'historical_freeze':'Preparation freeze remains unchanged; final053 is a separate snapshot.'}
    write(RECEIPT, freeze)
    verify(check_selection=False)
    write(RECIPES/'integration-baseline-selection.json', {
        'schema':'ccp-060-baseline-selection/v1', 'selected_version':'0.5.3',
        'selection_source':freeze['selection'], 'recorded_utc':freeze['created_utc'],
        'completion_reported_by_user':True, 'artifact_path':str(PIN/delivery.name),
        'identity_pinned':True, 'status':freeze['status'],
        'zip_sha256':ZIP_SHA, 'sga_sha256':SGA_SHA,
        'freeze':str(RECEIPT), 'freeze_sha256':sha(RECEIPT),
        'previous_selection':'Earlier 052 completion report was corrected by user; no diagnostic/test candidate was pinned.'})
    verify()
    print(json.dumps({'status':freeze['status'], 'receipt':str(RECEIPT),
                      'asset_files':len(assets), 'archive_members':len(inventory)}))


if __name__ == '__main__':
    main()
