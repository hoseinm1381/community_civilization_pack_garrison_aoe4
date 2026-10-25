"""Publish a clearly labelled local listening pilot without touching cloud reports."""
import html
import json
import os
from pathlib import Path
from urllib.parse import quote
from local_audition import DEST, RUNTIME
from local_bank import local_guard as guard
from pipeline import StateStore, wav_metrics, save_json, digest


def main():
    guard()
    DEST.mkdir(parents=True, exist_ok=True)
    clips = []
    for category in ['auditions', 'generation']:
        state = StateStore(DEST / category)
        for key, row in state.data.items():
            if not state.ready(key): continue
            metrics = wav_metrics(Path(row['path']).read_bytes())
            meta = row['metadata']; job = meta.get('job', meta)
            label = ' '.join(str(job.get(k, '')) for k in ['role', 'age', 'event', 'context', 'take'])
            voice=job.get('voice') or job.get('casting',{}).get('voice','')
            if voice:label+=' | '+voice
            clips.append(dict(category=category, kind=job.get('kind','audition'), key=key, label=label, text=job.get('text', ''), path=row['path'],
                              sha256=row['sha256'], metrics=metrics,
                              original_sha256=digest(Path(row['path']).parent / 'original-float.wav')))
    summary = dict(status='partial local listening pilot', clips=len(clips),
                   auditions=sum(c['category'] == 'auditions' for c in clips),
                   dialogue_candidates=sum(c['category'] == 'generation' and c['kind']=='dialogue' for c in clips),
                   effort_candidates=sum(c['category'] == 'generation' and c['kind']=='nonverbal_effort' for c in clips),
                   runtime=str(RUNTIME), full_release=False, acting_approved=False,
                   nonverbal_approved=False, native_compilation='not run', package='not assembled')
    save_json(DEST / 'checkpoint.json', summary)
    save_json(DEST / 'audio-inventory.json', clips)
    rows = []
    for clip in clips:
        src = quote(os.path.relpath(clip['path'], DEST.resolve()).replace('\\', '/'), safe='/')
        rows.append(f'<article><p>{html.escape(clip["category"]+" | "+clip["label"]+" | "+clip["text"])}</p><audio controls preload="none" src="{src}"></audio></article>')
    page = '''<!doctype html><meta charset="utf-8"><title>Garrison 0.8.4 local listening pilot</title>
<style>body{max-width:1000px;margin:2em auto;background:#16232a;color:#edf3eb;font:17px system-ui}input{padding:.7em;width:90%;font:inherit}article{border-bottom:1px solid #52756c;padding:.6em}audio{width:100%}</style>
<h1>Garrison 0.8.4 — local listening pilot</h1><p>Candidate recordings. Intent labels do not establish acting quality. Native pronunciation, expressive delivery and efforts remain for listening review. This is not a full release.</p>
<input placeholder="Filter role, context or words" oninput="for(const a of document.querySelectorAll('article'))a.hidden=!a.textContent.toLowerCase().includes(this.value.toLowerCase())">'''
    (DEST / 'LISTEN_LOCAL_PARTIAL.html').write_text(page + ''.join(rows), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__': main()
