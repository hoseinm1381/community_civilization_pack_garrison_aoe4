"""Self-contained, explicitly partial listening media; never a Garrison mod ZIP."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from local_bank import local_guard,local_manifest
from local_bank_validation import validate_structure,verify_bank
from local_efforts import verified_performance
from local_inputs import verify_completed_recording
from local_work import validate_saved_wave
from pipeline import StateStore,digest,wav_metrics,save_json
from providers import OUT
from quality import text_matches


PAGE='''<!doctype html><meta charset="utf-8"><title>Garrison 0.8.4 — partial local listening pilot</title>
<style>body{max-width:960px;margin:2rem auto;padding:0 1rem;background:#15262c;color:#e7eee9;font:17px system-ui}input,select,button{padding:.6rem;margin:.3rem;font:inherit}article{border-bottom:1px solid #54736c;padding:1rem 0}audio{width:100%}small{color:#b9ccc5}</style>
<h1>Garrison 0.8.4 · partial local listening pilot</h1>
<p>Candidate Vietnamese voices. This is listening media, not an installable mod or a complete release. Word/audio checks do not establish expressive acting, historical accuracy or native-speaker approval.</p>
<select id="role"><option value="">All roles</option></select><input id="query" placeholder="Filter age, action, voice or words"><p id="count"></p><div id="clips"></div>
<button id="back">Previous</button><button id="next">Next</button>
<script>const rows=__DATA__;let page=0;const size=50;
for(const x of [...new Set(rows.map(x=>x.role))].sort())role.add(new Option(x,x));
function draw(){const term=query.value.toLowerCase(),chosen=rows.filter(x=>(!role.value||x.role===role.value)&&JSON.stringify(x).toLowerCase().includes(term));
const max=Math.max(0,Math.ceil(chosen.length/size)-1);page=Math.min(page,max);clips.replaceChildren();count.textContent=chosen.length+' clips · page '+(page+1)+' of '+(max+1);
for(const x of chosen.slice(page*size,(page+1)*size)){const a=document.createElement('article'),p=document.createElement('p'),s=document.createElement('small'),audio=document.createElement('audio');
p.textContent=x.role+' · '+x.age+' · '+x.event+' · '+x.take+' · '+x.voice;s.textContent=x.text+' — '+x.kind;audio.controls=true;audio.preload='none';audio.src=x.member;a.append(p,s,audio);clips.append(a)}
back.disabled=page===0;next.disabled=page===max}
role.onchange=query.oninput=()=>{page=0;draw()};back.onclick=()=>{page--;draw()};next.onclick=()=>{page++;draw()};draw();</script>'''


def main():
    local_guard()
    parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true')
    parser.add_argument('--label',default='representative-v1');parser.add_argument('--compressed',action='store_true');args=parser.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,40}',args.label):raise ValueError('Invalid immutable listening-package label')
    bank=OUT/'local';manifest_file=bank/'recording-manifest.json';manifest=json.loads(manifest_file.read_text())
    voices={j['role']:j['casting']['voice'] for j in manifest['jobs']}
    if manifest!=local_manifest(json.loads((OUT/'recording-manifest.json').read_text()),voices):raise RuntimeError('Recipe drift')
    validate_structure(manifest);jobs={j['id']:j for j in manifest['jobs']}
    state=StateStore(bank/'generation')
    if args.all:
        verification=verify_bank()
        if verification['errors']:raise RuntimeError('Invalid recordings cannot enter a listening package')
        selected=set(verification['recordings'])
    else:
        triples=defaultdict(dict)
        for key in state.data:
            job=jobs[key]
            if job['kind']=='dialogue' and job['event']=='select':
                triples[(job['role'],job['age'],job['phrase_number'])][job['take']]=key
        selected=set()
        for role in sorted(voices):
            candidates=[(k,v) for k,v in triples.items() if k[0]==role and set(v)=={'T1','T2','T3'}]
            if not candidates:raise RuntimeError('No complete representative triple for '+role)
            _,takes=min(candidates,key=lambda item:(item[0][1],item[0][2]))
            selected.update(takes.values())
    exports=None
    if args.compressed:
        from local_compress import compressed_recordings
        if not args.all:raise ValueError('Compressed listening exports require --all verified coverage')
        exports=compressed_recordings(verification)
    fingerprint=json.loads((bank/'input-verification.json').read_text())['fingerprint']
    legacy=json.loads((bank/'legacy-pilot-input-certification.json').read_text())
    dest=bank/'delivery'/args.label
    if dest.exists():raise FileExistsError('Preserve listening packages; use a new explicit label')
    dest.mkdir(parents=True);audio=dest/'audio';audio.mkdir()
    if args.all:save_json(dest/'bank-verification.json',verification)
    rows=[];known=set()
    for key in sorted(selected,key=lambda k:(jobs[k]['role'],jobs[k]['age'],jobs[k]['event'],jobs[k]['phrase_number'],jobs[k]['take'])):
        row=state.data[key];job=jobs[key]
        if not state.ready(key,job):raise RuntimeError('Changed playback')
        verify_completed_recording(row,job,fingerprint,legacy.get('generation_attempts'))
        validate_saved_wave(Path(row['path']).parent/'original-float.wav')
        metrics=wav_metrics(Path(row['path']).read_bytes())
        if metrics['sample_rate']!=48000:raise RuntimeError('Unexpected playback rate')
        proof=row['metadata']['transcription']
        if isinstance(proof,str):passed=job['kind']=='dialogue' and text_matches(job['text'],proof)
        else:passed=verified_performance(job,proof)
        if not passed or row['sha256'] in known:raise RuntimeError('Unverified or duplicate performance')
        known.add(row['sha256']);export=exports[key] if exports is not None else row
        member='audio/'+export['sha256']+('.ogg' if args.compressed else '.wav');target=dest/member
        shutil.copyfile(export['path'],target)
        if digest(target)!=export['sha256']:raise RuntimeError('Playback copy changed')
        rows.append(dict(job=key,role=job['role'],age=job['age'],event=job['event'],take=job['take'],
                         text=job['text'],kind=job['kind'],voice=job['casting']['voice'],member=member,
                         sha256=export['sha256'],pcm_sha256=row['sha256'],duration=metrics['duration']))
    data=json.dumps(rows,ensure_ascii=True).replace('<','\\u003c')
    (dest/'LISTEN.html').write_text(PAGE.replace('__DATA__',data),encoding='utf-8')
    summary=dict(status='partial listening pilot',installable_garrison_mod=False,full_release=False,
                 clips=len(rows),roles=len({r['role'] for r in rows}),required_unique_recordings=len(jobs),
                 scope='all currently verified recordings' if args.all else 'one complete select phrase × three independent takes per role',
                 manifest_sha256=digest(manifest_file),input_fingerprint=fingerprint,
                 codec='vorbis-64k-mono-48k' if args.compressed else 'pcm16-mono-48k',final_zip_limit_bytes=400000000,
                 acting_approved=False,native_speaker_approved=False,native_game_test=False,recordings=rows)
    save_json(dest/'coverage.json',summary)
    (dest/'README.txt').write_text('Garrison 0.8.4 — PARTIAL LOCAL LISTENING PILOT\n\nOpen LISTEN.html to listen. This ZIP contains audio for review, not a Garrison mod. Do not import it as a release.\nMono 48 kHz PCM16 files passed waveform, hash, recipe and unprompted word/nonlexical checks. Voices use local VieNeu v3 Turbo Northern presets. All provider originals and request records remain in the authoring workspace on F:. No paid API call was made for these recordings.\nNative pronunciation, expressive acting and historical approximation require listening. The complete voice bank, native integration, original-voice overlap, save/load and multiplayer are not approved by this pilot. Normal and the 0.8.3 release remain unchanged.\n',encoding='utf-8')
    archive=dest/('Garrison-0.8.4-local-voices-PARTIAL-'+args.label+'.zip')
    if args.compressed:
        note=dest/'README.txt'
        note.write_text(note.read_text(encoding='utf-8')+'\nThis listening export uses mono 48 kHz, nominal 64 kbps Ogg Vorbis. Canonical PCM16 masters remain in the authoring workspace. Every compressed file was fully decoded and hash checked. In-game compressed playback is an independent gate.\n',encoding='utf-8')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in [dest/'LISTEN.html',dest/'README.txt',dest/'coverage.json',*sorted(audio.iterdir())]:z.write(p,p.relative_to(dest).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise RuntimeError('Listening ZIP integrity failed')
        expected={'LISTEN.html','README.txt','coverage.json'}|{r['member'] for r in rows}
        if set(z.namelist())!=expected:raise RuntimeError('Unexpected listening ZIP members')
        for row in rows:
            with z.open(row['member']) as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=row['sha256']:raise RuntimeError('Embedded WAV hash mismatch')
    from local_compress import enforce_zip_budget
    archive_bytes=enforce_zip_budget(archive)
    save_json(dest/'package-proof.json',dict(zip=str(archive),sha256=digest(archive),bytes=archive_bytes,final_zip_limit_bytes=400000000,clips=len(rows),zip_integrity=True,
              all_embedded_audio_sha256_verified=True,full_release=False,installable_garrison_mod=False))
    print('PARTIAL_LISTENING_PACKAGE_VERIFIED',len(rows),str(archive),flush=True)


if __name__=='__main__':main()
