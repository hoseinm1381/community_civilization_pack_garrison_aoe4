"""Compile Hideout build-time change and preserve all other 0.7.3 resources."""
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
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'release_073'))
from check_identity import ROOT, check

CFG = json.loads((ROOT/'workspace.json').read_text())
OUT = ROOT/'output/release_074'
BASE = ROOT/'output/release_073/delivery/community_civilization_pack.sga'
PIN = '907b596c01e147342e76e0700170cb72c76b525bd766a1a1dfb71a45b4107f8d'

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
    changed = sorted(k for k in active if active[k] != before[k])
    allowed = sorted('assets/attrib/instances/ebps/vietnam/buildings/hideouts/'+n+'.xml' for n in ('vn_building_defense_outpost_chi','vn_building_defense_outpost_2_chi'))
    assert changed == allowed, changed
    with zipfile.ZipFile(OUT/'before-source.zip') as z:
        for k in allowed:
            old = z.read(k)
            needle = b'<float name="time_seconds" value="60" overrideParent="True" />'
            assert old.count(needle) == 2
            assert (ROOT/k).read_bytes() == old.replace(needle, needle.replace(b'60', b'30'))
    assert sha(ROOT/CFG['project_file']) == before[CFG['project_file']]
    normal = Path(CFG['source_root'])
    normal_rows = {p.relative_to(normal).as_posix():sha(p) for p in (normal/'assets').rglob('*') if p.is_file()}
    for name in ('Vietnam_v2.aoe4mod','workspace.json'):
        if (normal/name).exists(): normal_rows[name]=sha(normal/name)
    assert normal_rows == json.loads((OUT/'normal-baseline.json').read_text()), 'Normal source changed during 074'
    protected = json.loads((ROOT/'output/release_072/freeze/protected.json').read_text())
    assert all(sha(ROOT/k)==v for k,v in protected.items()), 'Protected art/delivery drift'
    return active

def build(label):
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace_support import check_storage
    check_storage(ROOT, CFG)
    expected = source_policy()
    check(ROOT)
    assert sha(BASE) == PIN
    work = Path(CFG['external_root'])/'staging/r74'/label
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
    assert listing['archive']['name']=='b7fcea91257b408fb9e8ae4d8bc402e1'
    back = work/'baseline'
    run('extract-baseline-'+label,[CFG['archive_tool'],'extract',BASE,back,'--filter',''])
    mounts = {x['path']:x['toc'] for x in listing['members']}
    hashes = {k:sha(back/k) for k in mounts}
    # Native output owns the changed Hideout records; baseline owns every other byte.
    native_back = work/'native-readback'
    run('extract-native-'+label,[CFG['archive_tool'],'extract',native,native_back,'--filter',''])
    allowed = {k for k in mounts if '/hideouts/vn_building_defense_outpost' in k and k.endswith('.rgd')}
    assert len(allowed) == 4, allowed
    for k in allowed:
        assert (native_back/k).is_file(), k
        shutil.copy2(native_back/k, back/k)
    final_hashes = {k:sha(back/k) for k in mounts}
    changed_members = sorted(k for k in mounts if hashes[k] != final_hashes[k])
    assert changed_members and set(changed_members) <= allowed
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
    assert {p.relative_to(readback).as_posix():sha(p) for p in readback.rglob('*') if p.is_file()}==final_hashes
    assert expected==source_policy()
    delivery=OUT/'delivery';delivery.mkdir(exist_ok=True)
    sga=delivery/'community_civilization_pack.sga';shutil.copy2(current,sga)
    manifest=json.loads((BASE.parent/'garrison.json').read_text())
    manifest['members'][0]['sha256']=sha(sga)
    manifest['details'].update(version='0.7.4',updated='2026-10-23',summary='Reduce Hideout construction time to 30 seconds.',description='Hideout base construction time reduced from 60 to 30 seconds in both branches and campaign variants. Garrison archive identity and all other resources preserved.',changelog='Hideout construction: 60 to 30 seconds. Native import and gameplay timing test pending.')
    dump(delivery/'garrison.json',manifest)
    evidence=dict(version='0.7.4',passed=True,baseline_sha256=PIN,sga_sha256=sha(sga),archive_guid=check(ROOT,sga),native_build_completed=True,validated_instances=count,unchanged_members=len(hashes)-len(changed_members),changed_members=changed_members,unchanged_mounts=True,all_other_resources_byte_identical=True,hideout_base_build_seconds=30,native_import_tested=False,native_match_tested=False,save_load_tested=False,multiplayer_tested=False,member_sha256=final_hashes,mounts=mounts)
    dump(OUT/('verification-'+label+'.json'),evidence)
    start='Community Civilization Pack 0.7.4\nCredits: hosein81 and chilly5\n\nClose AoE4. Import this ZIP into Garrison and enable it.\nSelect the pack as BOTH Game Mode and Tuning Pack, then choose China and Vietnam.\nHideout base construction time is now 30 seconds (previously 60).\nBoth branches and campaign variants are covered; fortified variants inherit it.\nAll other packaged resources and Garrison identity are preserved from 0.7.3.\nNative import, match timing, save/load and multiplayer remain unverified.\nKeep 0.7.3 for rollback.\n'
    package=delivery/'community_civilization_pack-0.7.4.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(delivery/'garrison.json','garrison.json');z.write(sga,sga.name)
        z.writestr('START-HERE.txt',start)
        z.writestr('EVIDENCE.json',json.dumps({k:v for k,v in evidence.items() if k not in ('member_sha256','mounts')},indent=2)+'\n')
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'garrison.json',sga.name,'START-HERE.txt','EVIDENCE.json'}
        assert sum(Path(k).name.lower()=='garrison.json' for k in z.namelist())==1
        assert hashlib.sha256(z.read(sga.name)).hexdigest()==manifest['members'][0]['sha256']
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.4'
    assert sha(BASE)==PIN
    dump(OUT/'delivery-proof.json',dict(passed=True,zip_sha256=sha(package),sga_sha256=sha(sga),zip_bytes=package.stat().st_size,label=label))
    print(json.dumps({'passed':True,'package':str(package),'unchanged_members':len(hashes)-len(changed_members),'changed_members':changed_members,'validated_instances':count}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);args=p.parse_args()
    assert re.fullmatch('[a-z0-9-]{1,16}',args.label)
    build(args.label)
