"""Recheck safely cut candidate clips using fresh independent ASR, never new TTS."""
import io,json,wave
from pathlib import Path
from batching import anchored_ranges
from budget import transcription_key
from generation import verify_batch
from pipeline import AudioError, StateStore,guard,same_recording,playback_wav,pcm_wav,wav_metrics,digest,save_json
from providers import OUT

def main(secrets,max_reels=4):
    guard();current={j['id']:j for j in json.loads((OUT/'recording-manifest.json').read_text())['jobs']}
    state=StateStore(OUT/'generation');checked=0;accepted=0
    for folder in sorted((OUT/'generation/batch-masters').glob('*/attempt-*')):
        if checked>=max_reels:break
        if not (folder/'original.wav').exists() or not (folder/'transcript.json').exists():continue
        target=folder/'candidate-recheck'
        if (target/'finished.json').exists():continue
        jobs=json.loads((folder/'jobs.json').read_text())
        if jobs[0].get('kind')=='nonverbal_effort':continue
        try:audio=playback_wav((folder/'original.wav').read_bytes(),max_duration=120)
        except AudioError:continue
        metrics=wav_metrics(audio,max_duration=120)
        spans=anchored_ranges(jobs,json.loads((folder/'transcript.json').read_text()),metrics['duration'],isolation=.04)
        candidates=[j for j in jobs if j['id'] in current and same_recording(j,current[j['id']]) and not state.ready(j['id'],j) and j['id'] in spans]
        if not candidates:continue
        target.mkdir(parents=True,exist_ok=True)
        with wave.open(io.BytesIO(audio),'rb') as f:pcm=f.readframes(f.getnframes())
        items=[]
        for j in candidates:
            a,b=spans[j['id']];clip=pcm_wav(pcm[round(a*48000)*2:round(b*48000)*2],48000)
            try:wav_metrics(clip)
            except AudioError:continue
            path=target/(j['id']+'.wav');path.write_bytes(clip);items.append((j,path))
        if not items:continue
        # A fresh transcript of the extracted audio must match; source substring alone is insufficient.
        seconds=sum(wav_metrics(p.read_bytes())['duration']+.5 for _,p in items)
        from budget import account_for
        key=account_for(secrets,max(10,int(seconds*3)+1))
        qa=target/'qa'
        if (qa/'verification.json').exists():result=json.loads((qa/'verification.json').read_text())['results']
        elif qa.exists():
            # Preserve interrupted diagnostics, choose a fresh bounded QA directory.
            n=2
            while (target/f'qa-{n}').exists():n+=1
            if n>3:continue
            qa=target/f'qa-{n}';result=verify_batch(dict(elevenlabs=key),items,qa)
        else:result=verify_batch(dict(elevenlabs=key),items,qa)
        checked+=1
        for j,path in items:
            if not result[j['id']]['match']:continue
            sha=digest(path)
            if any(k!=j['id'] and row['sha256']==sha for k,row in state.data.items()):continue
            state.complete(j['id'],path,dict(job=j,provider_original=str(folder/'original.wav'),range_seconds=spans[j['id']],
                original_sha256=digest(folder/'original.wav'),metrics=wav_metrics(path.read_bytes()),
                verification=str(qa/'verification.json'),proof='fresh independent ASR on extracted clip reel',audible_review='pending'))
            accepted+=1
        save_json(target/'finished.json',dict(checked=len(items),accepted=sum(result[j['id']]['match'] for j,_ in items),synthesis_requests=0))
    print('084_PAID_AUDIO_RECHECK',checked,'REELS',accepted,'ADDITIONAL_CLIPS',flush=True)

if __name__=='__main__':
    import sys
    main(json.load(sys.stdin))
