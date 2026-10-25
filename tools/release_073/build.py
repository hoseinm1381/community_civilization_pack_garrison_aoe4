"""Native identity repair; retain every 0.7.2 member byte and mount."""
import argparse
import hashlib
import json
import msvcrt
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from check_identity import ROOT, check

CFG = json.loads((ROOT/'workspace.json').read_text())
OUT = ROOT/'output/release_073'
BASE = ROOT/'output/release_072/delivery/community_civilization_pack.sga'
PIN = '31c0b316e4aed71cfc31c592a1fbd982ff7262a7b446b2542a9806aa714783e5'

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2)+'\n', encoding='utf-8')

def run(label, args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1000)
    (OUT/(label+'.log')).write_text(repr([str(x) for x in args])+'\n'+result.stdout+'\n'+result.stderr, encoding='utf-8')
    assert result.returncode == 0, (label, result.returncode)
    return result.stdout

def source_policy():
    before = json.loads((OUT/'before.json').read_text())
    active = {p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
    assert set(active) == {k for k in before if k.startswith('assets/')}
    assert [k for k in active if active[k] != before[k]] == ['assets/_default.burnproj']
    with zipfile.ZipFile(OUT/'before-source.zip') as z:
        old = z.read('assets/_default.burnproj')
    fixed = (ROOT/'assets/_default.burnproj').read_bytes()
    # The patch tool may normalize line endings; compare exact logical content.
    assert fixed.replace(b'\r\n',b'\n') == old.replace(b'a743d7d1d7534cf78817e29d8ded7366', b'b7fcea91257b408fb9e8ae4d8bc402e1').replace(b'\r\n',b'\n')
    assert sha(ROOT/CFG['project_file']) == before[CFG['project_file']]
    sys.path.insert(0,str(ROOT/'tools/release_072'))
    from freeze import freeze
    freeze()  # Rechecks normal source, protected art, 0.7.1 and 0.7.0 rollback.
    return active

def build(label):
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace_support import check_storage
    check_storage(ROOT, CFG)
    expected = source_policy()
    check(ROOT)
    assert sha(BASE) == PIN
    work = Path(CFG['external_root'])/'staging/r73'/label
    work.mkdir(parents=True, exist_ok=False)
    src = work/'src'
    shutil.copytree(ROOT/'assets', src/'assets')
    shutil.copy2(ROOT/CFG['project_file'], src/CFG['project_file'])
    lockpath = ROOT/'output/release_020/native-build.lock'
    with lockpath.open('r+b') as lock:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            run('native-'+label, [CFG['garrison_core'],'essence','build-mod','--editor',CFG['content_editor'],'--mod',src/CFG['project_file'],'--run-root',work/'run','--timeout','900'])
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    state = json.loads((work/'run/run.json').read_text())
    logs = '\n'.join(p.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace') for p in (work/'run/logs').glob('*') if p.suffix in ('.log','.txt'))
    validated = re.findall(r'(\d+) instances validated',logs)
    count = len(list((src/'assets/attrib/instances').rglob('*.xml')))
    assert state['status']=='succeeded' and state['exit_code']==0 and validated and int(validated[-1])==count
    assert 'EssenceEditor.exe Error:' not in logs and 'System does not support' not in logs
    native = list((work/'run/output').rglob('*.sga'))
    assert len(native)==1
    native = native[0]
    check(ROOT,native)
    listing = json.loads(run('baseline-list-'+label,[CFG['archive_tool'],'list',BASE,'--verify']))
    assert listing['archive']['verification']['verified']
    assert listing['archive']['name']=='a743d7d1d7534cf78817e29d8ded7366'
    back = work/'baseline'
    run('extract-baseline-'+label,[CFG['archive_tool'],'extract',BASE,back,'--filter',''])
    mounts = {x['path']:x['toc'] for x in listing['members']}
    hashes = {k:sha(back/k) for k in mounts}
    current = native
    for alias in sorted(set(mounts.values())):
        mapping=work/(alias+'.txt')
        mapping.write_text('\n'.join(k+'='+str(back/k) for k,v in mounts.items() if v==alias)+'\n',encoding='utf-8')
        target=work/(alias+'.sga')
        run('preserve-'+alias+'-'+label,[CFG['archive_tool'],'set-members',current,mapping,target,'--alias',alias])
        current=target
    final_list=json.loads(run('final-list-'+label,[CFG['archive_tool'],'list',current,'--verify']))
    assert {x['path']:x['toc'] for x in final_list['members']}==mounts
    check(ROOT,current)
    readback=work/'readback'
    run('readback-'+label,[CFG['archive_tool'],'extract',current,readback,'--filter',''])
    assert {p.relative_to(readback).as_posix():sha(p) for p in readback.rglob('*') if p.is_file()}==hashes
    assert expected==source_policy()
    delivery=OUT/'delivery';delivery.mkdir(exist_ok=True)
    sga=delivery/'community_civilization_pack.sga';shutil.copy2(current,sga)
    manifest=json.loads((BASE.parent/'garrison.json').read_text())
    manifest['members'][0]['sha256']=sha(sga)
    manifest['details'].update(version='0.7.3',updated='2026-10-23',summary='Fix Vietnam selection by correcting the Garrison archive GUID.',description='Identity-only fix for the Vietnam selection fatal error. All 0.7.2 gameplay, scripts and custom art resources are preserved byte-for-byte.',changelog='Correct copied burn-project archive NiceName to the Garrison GUID. All 1,267 resource bytes and mounts match 0.7.2. Native retest pending.')
    dump(delivery/'garrison.json',manifest)
    evidence=dict(version='0.7.3',passed=True,baseline_sha256=PIN,sga_sha256=sha(sga),archive_guid=check(ROOT,sga),native_build_completed=True,validated_instances=count,unchanged_members=len(hashes),unchanged_mounts=True,gameplay_and_art_byte_identical=True,native_import_tested=False,native_match_tested=False,save_load_tested=False,multiplayer_tested=False,member_sha256=hashes,mounts=mounts)
    dump(OUT/('verification-'+label+'.json'),evidence)
    start='Community Civilization Pack 0.7.3\nCredits: hosein81 and chilly5\n\nClose AoE4. Import this ZIP in Garrison and enable it.\nSelect Community Civilization Pack as BOTH Game Mode and Tuning Pack.\nChoose China in the lobby, then Vietnam at match start in a fresh match.\n\nThis fixes the archive GUID mismatch behind the Vietnam-selection fatal error.\nEvery gameplay, SCAR, localization and art member is identical to 0.7.2.\nThe SCAR revision banner intentionally still identifies runtime-v12-garrison-072.\nConfirm Vietnam selection completes, the private Town Center, six villagers,\nscout and Water Buffalo initialize, and no missing-blueprint errors appear.\nImport, native match, save/load and multiplayer remain separate unverified gates.\nKeep the 0.7.2 ZIP for exact rollback; it retains the reported selection defect.\n'
    package=delivery/'community_civilization_pack-0.7.3.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(delivery/'garrison.json','garrison.json');z.write(sga,sga.name)
        z.writestr('START-HERE.txt',start)
        z.writestr('EVIDENCE.json',json.dumps({k:v for k,v in evidence.items() if k not in ('member_sha256','mounts')},indent=2)+'\n')
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'garrison.json',sga.name,'START-HERE.txt','EVIDENCE.json'}
        assert sum(Path(k).name.lower()=='garrison.json' for k in z.namelist())==1
        assert hashlib.sha256(z.read(sga.name)).hexdigest()==manifest['members'][0]['sha256']
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.3'
    assert sha(BASE)==PIN
    dump(OUT/'delivery-proof.json',dict(passed=True,zip_sha256=sha(package),sga_sha256=sha(sga),zip_bytes=package.stat().st_size,label=label))
    print(json.dumps({'passed':True,'package':str(package),'unchanged_members':len(hashes),'validated_instances':count}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);args=p.parse_args()
    assert re.fullmatch('[a-z0-9-]{1,16}',args.label)
    build(args.label)
