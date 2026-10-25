"""0.7.1 preservation rebuild: native source qualification plus exact native overlay.

The baseline archive contains compiled-only lifecycle/selector fixes. A source-only
Content Editor build must never silently replace those owning native resources.
"""
import argparse
import json
import msvcrt
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from consolidate import ROOT, EXT, CFG, TX, dump, walk
from resources import sha

sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import check_storage

OUT = EXT / 'output/release_071'
ROLLBACK = EXT / 'archives/release_070_rollback'
KEY = CFG['package_key']
SGA_SHA = '63e148ab21f0f2e157bee99a414b39c53284ceb9584812026cadfa47cc5accd2'
ZIP_SHA = 'd44688715b6116e4cb0d4e1527dc01837d2e13f0dbd4655460d8e62c93a9faeb'


def run(label, args, timeout=1000):
    OUT.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([str(x) for x in args], capture_output=True, encoding='utf-8', errors='replace', timeout=timeout)
    (OUT / (label + '.log')).write_text('COMMAND ' + repr([str(x) for x in args]) + '\n' + p.stdout + '\n' + p.stderr, encoding='utf-8')
    if p.returncode:
        raise RuntimeError(label + ' failed: ' + p.stderr[-2000:])
    return p.stdout


def freeze():
    check_storage(ROOT, CFG)
    ROLLBACK.mkdir(parents=True, exist_ok=True)
    pairs = [(EXT/'output/release_070/release/assembly-v1'/f'{KEY}.sga', SGA_SHA),
             (EXT/'output/release_070/release'/f'{KEY}-0.7.0.zip', ZIP_SHA)]
    for source, expected in pairs:
        target = ROLLBACK / source.name
        if not target.exists():
            assert sha(source) == expected
            shutil.copy2(source, target)
        assert sha(target) == expected
    receipt = EXT / 'output/release_070/release/verification-v4/receipt.json'
    if not (ROLLBACK/'member-receipt.json').exists():
        shutil.copy2(receipt, ROLLBACK/'member-receipt.json')
    dump(ROLLBACK/'rollback.json', dict(version='0.7.0', sga_sha256=SGA_SHA, zip_sha256=ZIP_SHA, user_requested_rollback=True))
    hashes = {p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size, sha256=sha(p)) for p in walk(ROOT/'assets')}
    hashes[CFG['project_file']] = dict(bytes=(ROOT/CFG['project_file']).stat().st_size, sha256=sha(ROOT/CFG['project_file']))
    if (TX/'active-source-before.json').exists():
        assert hashes == json.loads((TX/'active-source-before.json').read_text()), 'Active source changed'
    else:
        dump(TX/'active-source-before.json', hashes)
    return hashes


def source_build(label):
    expected = freeze()
    work = EXT / 'staging/r71' / label
    assert not work.exists(), 'Preserve existing native attempt; use a new label'
    source = work / 'src'
    shutil.copytree(ROOT/'assets', source/'assets')
    shutil.copy2(ROOT/CFG['project_file'], source/CFG['project_file'])
    command = [CFG['garrison_core'], 'essence', 'build-mod', '--editor', CFG['content_editor'],
               '--mod', source/CFG['project_file'], '--run-root', work/'run', '--timeout', '900']
    lock_path = EXT/'output/release_020/native-build.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if not lock_path.exists():
        lock_path.write_bytes(b'0')
    with lock_path.open('r+b') as lock:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            log = run('native-source-'+label, command)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    state = json.loads((work/'run/run.json').read_text())
    for p in (work/'run/logs').glob('*'):
        if p.is_file() and p.suffix.lower() in ('.log','.txt'):
            log += '\n' + p.read_bytes().rstrip(b'\0').decode('utf-8', errors='replace')
    count = sum(p.startswith('assets/attrib/instances/') and p.endswith('.xml') for p in expected)
    validated = re.findall(r'(\d+) instances validated', log)
    errors = [l for l in log.splitlines() if 'EssenceEditor.exe Error:' in l or 'System does not support' in l]
    passed = state.get('status') == 'succeeded' and state.get('exit_code') == 0 and bool(validated) and int(validated[-1]) == count and not errors
    archives = list((work/'run/output').rglob('*.sga'))
    assert len(archives) == 1
    listing = json.loads(run('native-source-list-'+label, [CFG['archive_tool'], 'list', archives[0], '--verify']))
    passed = passed and listing['archive']['verification']['verified']
    staged = {p.relative_to(source).as_posix():dict(bytes=p.stat().st_size, sha256=sha(p)) for p in walk(source/'assets')}
    staged[CFG['project_file']] = dict(bytes=(source/CFG['project_file']).stat().st_size, sha256=sha(source/CFG['project_file']))
    assert expected == staged
    assert freeze() == expected
    receipt = dict(passed=bool(passed), expected_instances=count, validated=validated, errors=errors,
                   archive_sha256=sha(archives[0]), state=state, active_source_unchanged=True,
                   scope='Native source qualification; exact compiled-only native resources retained by overlay.', native_match_tested=False)
    dump(OUT/('native-source-'+label+'.json'), receipt)
    assert passed, receipt
    print(json.dumps(receipt), flush=True)


def assemble(label):
    freeze()
    work = EXT/'staging/r71'/('assemble-'+label)
    assert not work.exists()
    work.mkdir(parents=True)
    baseline = ROLLBACK/f'{KEY}.sga'
    listing = json.loads(run('baseline-list-'+label, [CFG['archive_tool'], 'list', baseline, '--verify']))
    assert listing['archive']['verification']['verified']
    receipt = json.loads((ROLLBACK/'member-receipt.json').read_text())
    native = work/'native'
    run('extract-baseline-'+label, [CFG['archive_tool'], 'extract', baseline, native, '--filter', ''], 600)
    actual = {p.relative_to(native).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in walk(native)}
    assert actual == receipt['member_hashes'], '070 native payloads changed'
    # Repack, then explicitly rewrite every native member from independently
    # extracted/hashed retained payloads. This retains native TOC ownership.
    current = work/'base.sga'
    run('repack-'+label, [CFG['archive_tool'], 'repack', baseline, current], 600)
    for toc in ('attrib','data','locale','info'):
        members = [r for r in listing['members'] if r['toc'] == toc]
        if not members:
            continue
        mapping = work/(toc+'.txt')
        mapping.write_text('\n'.join(r['path']+'='+str(native/r['path']) for r in members)+'\n', encoding='utf-8')
        target = work/(toc+'.sga')
        run('assemble-'+toc+'-'+label, [CFG['archive_tool'], 'set-members', current, mapping, target, '--alias', toc], 600)
        current = target
    final = OUT/'delivery'/f'{KEY}.sga'
    final.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(current, final)
    rebuilt_listing = json.loads(run('final-list-'+label, [CFG['archive_tool'],'list', final,'--verify']))
    assert rebuilt_listing['archive']['verification']['verified']
    old_mounts = {r['path']:r['toc'] for r in listing['members']}
    assert {r['path']:r['toc'] for r in rebuilt_listing['members']} == old_mounts
    readback = work/'readback'
    run('final-readback-'+label, [CFG['archive_tool'],'extract',final,readback,'--filter',''], 600)
    final_hashes = {p.relative_to(readback).as_posix():dict(bytes=p.stat().st_size, sha256=sha(p)) for p in walk(readback)}
    assert final_hashes == actual
    package_delivery(final,actual,old_mounts,label)


def package_delivery(final,actual,old_mounts,label):
    with zipfile.ZipFile(ROLLBACK/f'{KEY}-0.7.0.zip') as old:
        assert old.testzip() is None
        manifest = json.loads(old.read('garrison.json'))
        manifest['details']['version'] = '0.7.1'
        manifest['members'][0]['sha256'] = sha(final)
    start = f'''Community Civilization Pack 0.7.1
Credits: hosein81 and chilly5

Close Age of Empires IV, import this ZIP through Garrison, and select Community
Civilization Pack as both Game Mode and Tuning Pack. Start China and select
Vietnam using the existing civilization flow. This is the complete pack.

All 0.7.0 native resources and features are preserved. This release consolidates
the development workspace; no in-match acceptance is claimed. Client import,
lobby selection, building/unit appearance and native gameplay remain separate tests.

Rollback: reimport the exact original 0.7.0 ZIP retained at
{ROLLBACK / (KEY+'-0.7.0.zip')}
Keep the editable workspace and its lossless resource store for future development.
See docs/DEVELOPMENT_071.md for rebuild instructions and retained-input restoration.
'''
    manifest['details'].update(summary='0.7.0 feature parity and consolidated development workspace',
                               changelog='0.7.1 preserves every 0.7.0 native resource and mount; consolidates rebuild inputs and keeps exact 0.7.0 rollback.')
    evidence = dict(schema='ccp.release071.evidence/v1',version='0.7.1',credits='hosein81 and chilly5', native_member_count=len(actual), all_070_native_members_and_mounts_identical=True,
                    sga_sha256=sha(final), rollback_sga_sha256=SGA_SHA, native_import_tested=False, native_match_tested=False,
                    rebuild_method='Validated editable source plus exact native owning-resource preservation overlay')
    assert manifest['details']['author'] == 'hosein81 and chilly5'
    dump(OUT/'delivery/garrison.json', manifest)
    package = OUT/'delivery'/f'{KEY}-0.7.1.zip'
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name,data in [('garrison.json',json.dumps(manifest,indent=2).encode()),
                          (f'{KEY}.sga',None),('START-HERE.txt',start.encode()),
                          ('EVIDENCE.json',json.dumps(evidence,indent=2).encode())]:
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info._compresslevel=6
            if data is None:
                with z.open(info,'w') as target, final.open('rb') as source:
                    shutil.copyfileobj(source,target)
            else:z.writestr(info,data)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {'garrison.json',f'{KEY}.sga','START-HERE.txt','EVIDENCE.json'}
        import hashlib
        assert hashlib.sha256(z.read(f'{KEY}.sga')).hexdigest() == sha(final)
        assert json.loads(z.read('garrison.json'))['details']['version'] == '0.7.1'
    evidence.update(package_verified=True, zip_sha256=sha(package), zip_bytes=package.stat().st_size, all_members_sha256=actual, mounts=old_mounts)
    dump(OUT/('package-'+label+'.json'),evidence)
    print(json.dumps({k:v for k,v in evidence.items() if k not in ('all_members_sha256','mounts')}),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['freeze','source','assemble','package'])
    p.add_argument('--label',default='v1')
    args = p.parse_args()
    assert re.fullmatch('[a-z0-9-]{1,16}',args.label)
    if args.stage == 'freeze': freeze()
    elif args.stage == 'source': source_build(args.label)
    elif args.stage=='assemble': assemble(args.label)
    else:
        proof=json.loads((OUT/('package-'+args.label+'.json')).read_text())
        final=OUT/'delivery'/f'{KEY}.sga'
        assert proof['package_verified'] and sha(final)==proof['sga_sha256']
        package_delivery(final,proof['all_members_sha256'],proof['mounts'],args.label)
