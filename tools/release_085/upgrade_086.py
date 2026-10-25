"""Verified 086 one-member overlay; replace the current 085 delivery in place."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,data):path.write_bytes((json.dumps(data,indent=2)+'\n').encode('utf-8'))


def main():
    cfg=json.loads((ROOT/'workspace.json').read_text());check_storage(ROOT,cfg)
    dest=ROOT/'output/release_085/final-v2'
    prior=json.loads((dest/'verification.json').read_text())
    if prior['version']!='0.8.5':raise ValueError('This one-time upgrade requires the unchanged 0.8.5 delivery')
    archive=dest/'community_civilization_pack.sga';oldzip=dest/'community_civilization_pack-0.8.5.zip'
    if sha(archive)!=prior['sga_sha256'] or sha(oldzip)!=prior['zip_sha256']:raise ValueError('085 changed; preserve it for review')
    base=ROOT/'output/release_084/delivery/final-v1'
    original=base/'community_civilization_pack.sga';baseproof=json.loads((base/'verification.json').read_text())
    if sha(original)!=baseproof['sga_sha256']:raise ValueError('Independent 084 rollback changed')
    check(ROOT,original);check(ROOT,archive)
    member='scar/vietnam/voices_084.scar';source=ROOT/'tools/release_085/voices_086.scar'
    if any(prior['member_sha256'][k]!=v for k,v in baseproof['member_sha256'].items() if k!=member):raise ValueError('085 contains an unrelated change')
    for filename in ('verification.json','garrison.json','START-HERE.txt'):
        backup=dest/('085-'+filename+'.gz')
        if backup.exists():raise FileExistsError('Preserve prior upgrade attempts')
        backup.write_bytes(gzip.compress((dest/filename).read_bytes(),mtime=0))
    save(dest/'085-rollback-recipe.json',dict(baseline_sga_sha256=baseproof['sga_sha256'],
        dispatcher='tools/release_085/voices.scar',dispatcher_sha256=sha(ROOT/'tools/release_085/voices.scar'),
        replaced_member=member,old_sga_sha256=prior['sga_sha256'],old_zip_sha256=prior['zip_sha256'],
        restoration='084 owning archive plus original 085 dispatcher; compressed 085 metadata retained.'))
    def run(label,command):
        proc=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding='utf-8',errors='replace')
        (dest/('086-'+label+'.log')).write_text('EXIT '+str(proc.returncode)+'\n'+proc.stdout+'\n'+proc.stderr,encoding='utf-8')
        if proc.returncode:raise RuntimeError(label+' failed; original 085 remains until commit')
        return proc.stdout
    members=dest/'086-members.txt';members.write_bytes((member+'='+str(source)+'\n').encode('utf-8'))
    candidate=dest/'086-candidate.sga'
    if candidate.exists():raise FileExistsError('Preserve prior candidate')
    run('assemble',[cfg['archive_tool'],'set-members',original,members,candidate,'--alias','data'])
    check(ROOT,candidate)
    listing=json.loads(run('list',[cfg['archive_tool'],'list',candidate,'--verify']))
    mounts={m['path']:m['toc'] for m in listing['members']}
    if mounts!=prior['mounts']:raise ValueError('Mounts or member set changed')
    # Fresh readback uses ephemeral NTFS storage, avoiding exFAT small-file bloat.
    with tempfile.TemporaryDirectory(prefix='garrison086-') as temporary:
        folder=Path(temporary).resolve()
        if not folder.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not folder.name.startswith('garrison086-'):raise ValueError('Unexpected temporary target')
        run('extract',[cfg['archive_tool'],'extract',candidate,folder,'--filter','.'])
        actual={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
        expected=dict(prior['member_sha256']);expected[member]=sha(source)
        if actual!=expected:raise ValueError('Unexpected archive member change')
    manifest=json.loads((dest/'garrison.json').read_text())
    manifest['members'][0]['sha256']=sha(candidate)
    manifest['details'].update(version='0.8.6',updated='2026-10-25',
        summary='Vietnamese unit replies with independent per-unit cooldowns.',
        description='Each unit has its own 5-second selection/order cooldown, 8-second movement cooldown and 15-second under-attack cooldown. Existing playback arbitration, command/activity echo suppression, pain/death sounds, voices, artwork and gameplay are preserved.',
        changelog='Cooldowns now belong to each individual unit instead of the whole player. No voice regeneration or gameplay change.')
    staged_manifest=dest/'086-garrison.json';save(staged_manifest,manifest)
    note=dest/'086-START-HERE.txt';note.write_text('Garrison 0.8.6\n\nImport this ordinary Garrison ZIP and select its Tuning Pack and Vietnam Game Mode.\nEach unit independently observes the existing 5s reply, 8s movement and 15s under-attack limits. Another unit can reply once the current clip finishes. Group arbitration and duplicate suppression are unchanged. Pain/death sounds, all voices, gameplay and art are preserved.\nOffline tests and archive proof passed. Import, audible feel, save/load and multiplayer remain native acceptance gates; no new native compilation is claimed.\n',encoding='utf-8')
    package=dest/'community_civilization_pack-0.8.6.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path,name in ((staged_manifest,'garrison.json'),(candidate,'community_civilization_pack.sga'),(note,'START-HERE.txt')):z.write(path,name)
    size=package.stat().st_size
    if size>400_000_000:raise RuntimeError('NOTIFY USER: ZIP exceeds 400 MB; 085 not replaced')
    with zipfile.ZipFile(package) as z:
        if z.testzip() or set(z.namelist())!={'garrison.json','community_civilization_pack.sga','START-HERE.txt'}:raise ValueError('ZIP integrity failure')
        with z.open('community_civilization_pack.sga') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=sha(candidate):raise ValueError('Embedded SGA differs')
        if z.read('garrison.json')!=staged_manifest.read_bytes():raise ValueError('Embedded manifest differs')
    proof=dict(version='0.8.6',zip_bytes=size,zip_sha256=sha(package),sga_sha256=sha(candidate),
        baseline_sga_sha256=baseproof['sga_sha256'],superseded_085_sga_sha256=prior['sga_sha256'],
        archive_identity=listing['archive']['name'],member_sha256=actual,mounts=mounts,changed=[member],added=[],deleted=[],
        all_audio_art_gameplay_members_byte_identical=True,voice_regeneration=False,native_compilation=False,
        client_import=False,audible_behavior=False,save_load=False,multiplayer=False,output_folder_reused=True)
    staged_proof=dest/'086-verification.json';save(staged_proof,proof)
    # Commit only after all byte/hash/ZIP/identity checks passed. 084 stays intact.
    candidate.replace(archive);staged_manifest.replace(dest/'garrison.json');note.replace(dest/'START-HERE.txt');staged_proof.replace(dest/'verification.json')
    if sha(archive)!=proof['sga_sha256'] or sha(package)!=proof['zip_sha256']:raise ValueError('Post-replacement integrity failure; preserve old ZIP')
    oldzip.unlink()
    print('086_REPLACED_085_VERIFIED',size,proof['zip_sha256'],flush=True)


if __name__=='__main__':main()
