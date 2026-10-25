"""One-SCAR-member presentation overlay on immutable final 0.8.4; no synthesis."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='final-v2')
    args=parser.parse_args()
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label):raise ValueError('Invalid label')
    cfg=json.loads((ROOT/'workspace.json').read_text());check_storage(ROOT,cfg)
    base=ROOT/'output/release_084/delivery/final-v1'
    proof=json.loads((base/'verification.json').read_text())
    original=base/'community_civilization_pack.sga'
    if sha(original)!=proof['sga_sha256'] or sha(base/'community_civilization_pack-0.8.4.zip')!=proof['zip_sha256']:raise ValueError('Rollback changed')
    check(ROOT,original)
    dest=ROOT/'output/release_085'/args.label
    dest.mkdir(parents=True,exist_ok=False)
    def run(label,command):
        process=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding='utf-8',errors='replace')
        (dest/(label+'.log')).write_text('EXIT '+str(process.returncode)+'\n'+process.stdout+'\n'+process.stderr,encoding='utf-8')
        if process.returncode:raise RuntimeError('Archive operation failed: '+label)
        return process.stdout
    # The mounted path is intentionally stable; existing lifecycle imports it.
    member='scar/vietnam/voices_084.scar'
    dispatcher=ROOT/'tools/release_085/voices.scar'
    raw=dispatcher.read_bytes()
    if b'\r' in raw:raise ValueError('Dispatcher must use canonical LF UTF-8 bytes')
    emitted=dest/'voices_085.scar';emitted.write_bytes(raw)
    members=dest/'members.txt';members.write_text(member+'='+str(emitted)+'\n',encoding='utf-8')
    final=dest/'community_civilization_pack.sga'
    run('assemble',[cfg['archive_tool'],'set-members',original,members,final,'--alias','data'])
    check(ROOT,final)
    listing=json.loads(run('list-verify',[cfg['archive_tool'],'list',final,'--verify']))
    mounts={m['path']:m['toc'] for m in listing['members']}
    if mounts!=proof['mounts']:raise ValueError('Archive members/mounts changed')
    readback=dest/'fresh-readback'
    run('fresh-extract',[cfg['archive_tool'],'extract',final,readback,'--filter','.'])
    actual={p.relative_to(readback).as_posix():sha(p) for p in readback.rglob('*') if p.is_file()}
    expected=dict(proof['member_sha256']);expected[member]=sha(emitted)
    if actual!=expected:raise ValueError('Unexpected archive delta')
    changed=sorted(k for k in actual if actual[k]!=proof['member_sha256'][k])
    if changed!=[member]:raise ValueError('Expected exactly one dispatcher change')
    manifest=json.loads((base/'garrison.json').read_text())
    manifest['members'][0]['sha256']=sha(final)
    manifest['details'].update(version='0.8.5',updated='2026-10-25',
        summary='Vietnamese voices with fewer repeated unit replies.',
        description='Selection/order replies wait 5 seconds; movement replies wait 8 seconds; under-attack dialogue waits 15 seconds. Command/activity echoes are suppressed. Existing voices, stock pain/death sounds, artwork and gameplay are preserved.',
        changelog='Reduced cosmetic chatter only; no voice regeneration. In-game playback, routing, save/load and multiplayer acceptance remain separate.')
    save(dest/'garrison.json',manifest)
    (dest/'START-HERE.txt').write_text('Garrison 0.8.5\n\nImport the ordinary ZIP and select its Tuning Pack and Vietnam Game Mode.\n5 seconds between selection/order/activity replies; 8 seconds between movement replies; 15 seconds between under-attack dialogue. Command/activity echo suppression.\nAll 0.8.4 audio, stock pain/death media and existing effort timing, gameplay and art are unchanged. No synthesis or new installation.\nOffline Lua and exact archive checks are separate from native import, audible behavior, save/load and multiplayer acceptance. 0.8.4 pronunciation/acting caveats remain.\n',encoding='utf-8')
    package=dest/'community_civilization_pack-0.8.5.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in (dest/'garrison.json',final,dest/'START-HERE.txt'):z.write(path,path.name)
    size=package.stat().st_size
    if size>400_000_000:
        save(dest/'budget-exceeded.json',dict(bytes=size,limit_bytes=400_000_000,notify_user=True))
        raise RuntimeError('NOTIFY USER: final ZIP exceeds 400 MB')
    with zipfile.ZipFile(package) as z:
        if z.testzip() or set(z.namelist())!={'garrison.json',final.name,'START-HERE.txt'}:raise ValueError('ZIP integrity/member failure')
        if z.read('garrison.json')!=(dest/'garrison.json').read_bytes():raise ValueError('Embedded manifest differs')
        with z.open(final.name) as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=sha(final):raise ValueError('Embedded SGA differs')
    save(dest/'verification.json',dict(version='0.8.5',zip_bytes=size,zip_sha256=sha(package),sga_sha256=sha(final),
        baseline_sga_sha256=proof['sga_sha256'],baseline_zip_sha256=proof['zip_sha256'],
        archive_identity=listing['archive']['name'],member_sha256=actual,mounts=mounts,changed=changed,added=[],deleted=[],
        all_audio_art_gameplay_members_byte_identical=True,voice_regeneration=False,
        native_compilation=False,build_route='one-member SCAR overlay on verified 084 owning archive',
        client_import=False,audible_behavior=False,save_load=False,multiplayer=False))
    print('085_PACKAGE_VERIFIED',size,sha(package),flush=True)


if __name__=='__main__':main()
