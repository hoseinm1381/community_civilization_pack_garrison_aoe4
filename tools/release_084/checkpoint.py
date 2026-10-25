"""Offline checkpoint, listening index and strict complete-bank release gate."""
import argparse,collections,html,json,os
from pathlib import Path
from urllib.parse import quote
from pipeline import StateStore,guard,save_json,wav_metrics,digest
from providers import OUT

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--require-complete',action='store_true');args=parser.parse_args()
    guard();manifest_path=OUT/'recording-manifest.json';manifest=json.loads(manifest_path.read_text())
    state=StateStore(OUT/'generation');roles={};clips=[];invalid=[]
    for job in manifest['jobs']:
        role=roles.setdefault(job['role'],dict(required=0,accepted=0,provider=job['casting']['provider'],voice=job['casting']['voice']))
        role['required']+=1
        if state.ready(job['id'],job):
            row=state.data[job['id']]
            try:
                metrics=wav_metrics(Path(row['path']).read_bytes())
                if metrics['sample_rate']!=48000:raise ValueError('Playback is not 48kHz')
            except ValueError as e:invalid.append(dict(id=job['id'],reason=str(e)));continue
            role['accepted']+=1;clips.append(dict(job=job,path=row['path'],sha256=row['sha256']))
    hashes=collections.defaultdict(list)
    for c in clips:hashes[c['sha256']].append(c['job']['id'])
    for sha,ids in hashes.items():
        if len(ids)>1:invalid.append(dict(reason='Duplicate audio for distinct jobs',sha256=sha,jobs=ids))
    accepted={c['job']['id'] for c in clips}
    complete=len(accepted)==len(manifest['jobs']) and not invalid
    report=dict(schema='ccp-084-checkpoint/v1',status='complete_audio_bank' if complete else 'partial_pilot',
        required=len(manifest['jobs']),accepted=len(accepted),missing=len(manifest['jobs'])-len(accepted),
        directed_slots=len(manifest['aliases']),covered_slots=sum(a['job'] in accepted for a in manifest['aliases']),
        manifest_sha256=digest(manifest_path),roles=roles,invalid=invalid,complete=complete,
        gates=dict(automatic_audio_text_checks='partial',audible_quality='pending',native_compile='not_run',
          integration='not_complete',archive_assembly='not_run',zip='not_built',native_import='not_run',age_routing='not_run',
          overlap='not_run',save_load='not_run',multiplayer='not_run'),
        policy='No full 0.8.4 delivery until every required job is covered; listening material is a partial pilot.')
    save_json(OUT/'checkpoint.json',report)
    rows=[]
    for c in sorted(clips,key=lambda c:(c['job']['role'],c['job']['age'],c['job']['event'],c['job']['take'],c['job']['phrase_number'])):
        j=c['job'];label=f"{j['role']} {j['age']} {j['event']} {j['take']} #{j['phrase_number']}"
        src=quote(os.path.relpath(c['path'],OUT.resolve()).replace('\\','/'),safe='/')
        rows.append(f'<article><p>{html.escape(label)} | {html.escape(j["text"])}</p><audio controls preload="none" src="{src}"></audio></article>')
    document='''<!doctype html><meta charset="utf-8"><title>Garrison 0.8.4 partial listening pilot</title>
<style>body{max-width:1000px;margin:2em auto;font:17px system-ui;background:#152027;color:#e6eee9}input{padding:.7em;width:90%;font:inherit}article{border-bottom:1px solid #58716a;padding:.5em}audio{width:100%}</style>
<h1>Garrison 0.8.4 — partial listening pilot</h1><p>Automatically checked recordings; native pronunciation and acting remain for listening review. This is not a release package.</p>'''
    document+=f'<p>{len(clips)} of {len(manifest["jobs"])} required recordings.</p><input placeholder="Filter role, age, event or words" oninput="for(const a of document.querySelectorAll(\'article\'))a.hidden=!a.textContent.toLowerCase().includes(this.value.toLowerCase())">'+''.join(rows)
    (OUT/'LISTEN_PARTIAL.html').write_text(document,encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','required','accepted','missing','covered_slots','complete']}))
    if args.require_complete and not complete:raise SystemExit(2)

if __name__=='__main__':main()
