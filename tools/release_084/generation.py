"""Serial synthesis and small contextual ASR reels, checkpointed per clip.

No credentials, authorization headers or command-line secrets are persisted.
"""
import io
import json
from pathlib import Path
import socket
import sys
import time
import urllib.error
import wave
from pipeline import AudioError, StateStore, digest, playback_wav, pcm_wav, save_json, wav_metrics
from providers import ROOT, OUT, ProviderError, synthesize
from quality import scribe, text_matches


def segment_transcripts(spans, transcript):
    if text_matches(' '.join(x['text'] for x in spans),transcript.get('text','')):
        return {x['id']:dict(match=True,mode='whole_reel_exact') for x in spans}
    result={}
    for span in spans:
        words=[w['text'] for w in transcript.get('words',[]) if w.get('type')=='word' and
               span['start'] <= (w['start']+w['end'])/2 <= span['end']]
        actual=' '.join(words)
        result[span['id']]=dict(match=text_matches(span['text'],actual),actual=actual,mode='timestamp_segment')
    return result


def status_counts(ids, ready, attempts):
    accepted=sum(bool(ready.get(k)) for k in ids)
    exhausted=sum(not ready.get(k) and attempts.get(k,0)>=3 for k in ids)
    return dict(accepted=accepted,exhausted_retakes=exhausted,pending=len(ids)-accepted-exhausted,total=len(ids))


def verify_batch(secrets, items, target):
    pcm=bytearray();spans=[]
    for job,path in items:
        with wave.open(str(path),'rb') as f:
            assert f.getframerate()==48000 and f.getnchannels()==1 and f.getsampwidth()==2
            start=len(pcm)/96000
            pcm.extend(f.readframes(f.getnframes()))
            end=len(pcm)/96000
        spans.append(dict(id=job['id'],start=start,end=end,text=job['text']))
        pcm.extend(b'\0\0'*24000)
    audio=pcm_wav(bytes(pcm),48000)
    target.mkdir(parents=True,exist_ok=False)
    (target/'reel.wav').write_bytes(audio)
    save_json(target/'segments.json',spans)
    transcript=scribe(secrets['elevenlabs'],audio)
    results=segment_transcripts(spans,transcript)
    save_json(target/'verification.json',dict(transcript=transcript,results=results,
        original_text_not_sent_to_recognizer=True,qualification='automatic_text_only'))
    return results


def main(secrets):
    manifest_path=OUT/'recording-manifest.json'
    manifest=json.loads(manifest_path.read_text())
    jobs=manifest['jobs'];counts={}
    for j in jobs:counts[j['role']]=counts.get(j['role'],0)+1
    # Finish smaller complete roles first, retaining stable per-role casting.
    jobs=sorted(jobs,key=lambda j:(counts[j['role']],j['role'],j['age'],j['event'],j['take'],j['phrase_number']))
    store=StateStore(OUT/'generation')
    attempts={};ready={j['id']:store.ready(j['id'],j) for j in jobs}
    attempts_file=OUT/'generation/attempts.json'
    if attempts_file.exists():attempts=json.loads(attempts_file.read_text())
    run_index=1
    while (OUT/f'generation/runs/{run_index:04d}').exists():run_index+=1
    run_dir=OUT/f'generation/runs/{run_index:04d}';run_dir.mkdir(parents=True)
    save_json(run_dir/'start.json',dict(manifest_sha256=digest(manifest_path),role_order=sorted(counts,key=lambda k:(counts[k],k)),
                                      concurrency_per_provider=1,existing_credits_only=True))
    batch_index=0
    def checkpoint(status, **extra):
        result=dict(status=status,**status_counts([j['id'] for j in jobs],ready,attempts),**extra)
        save_json(OUT/'generation/status.json',result)
        save_json(attempts_file,attempts)
        print(json.dumps(result),flush=True)
    checkpoint('running')
    try:
        for round_number in range(3):
            queue=[j for j in jobs if not ready[j['id']] and attempts.get(j['id'],0)<3]
            index=0
            while index<len(queue):
                selected=[]
                role=queue[index]['role']
                age=queue[index]['age']
                while index<len(queue) and len(selected)<6 and queue[index]['role']==role and queue[index]['age']==age:
                    selected.append(queue[index]);index+=1
                batch=[]
                for job in selected:
                    key=job['id'];attempt=attempts.get(key,0)+1
                    folder=OUT/'generation/masters'/key/f'attempt-{attempt}'
                    folder.mkdir(parents=True,exist_ok=True)
                    original=folder/'original.wav';receipt=folder/'receipt.json'
                    actor=job['casting']
                    if not original.exists():
                        prior=folder/'request-started.json'
                        if prior.exists() and not (folder/'provider-rejection.json').exists():
                            checkpoint('uncertain_request_requires_review',job=key,role=role,
                                reason='Prior request has no saved response; do not blindly charge again')
                            return
                        save_json(prior,dict(job=job,attempt=attempt,status='submitted',manifest_sha256=digest(manifest_path)))
                        try:
                            audio,usage=synthesize(actor['provider'],secrets[actor['provider']],actor['voice'],job['text'],job['direction'])
                        except ProviderError as e:
                            save_json(folder/'provider-rejection.json',dict(status=e.status,category=e.category))
                            raise
                        original.write_bytes(audio)
                        save_json(folder/'provider-receipt.json',usage)
                    else:
                        usage=json.loads((folder/'provider-receipt.json').read_text()) if (folder/'provider-receipt.json').exists() else dict(recovered_original=True)
                    try:
                        audio=playback_wav(original.read_bytes());metrics=wav_metrics(audio)
                        playback=folder/'playback.wav';playback.write_bytes(audio)
                    except AudioError as e:
                        attempts[key]=attempt
                        save_json(folder/'rejected.json',dict(reason=str(e),stage='audio_format'))
                        save_json(attempts_file,attempts)
                        continue
                    save_json(receipt,dict(job=job,attempt=attempt,original_sha256=digest(original),
                        playback_sha256=digest(playback),metrics=metrics,usage=usage,status='awaiting_text_check'))
                    batch.append((job,playback))
                if not batch:continue
                batch_index+=1
                target=run_dir/f'batch-{batch_index:05d}'
                result=verify_batch(secrets,batch,target)
                for job,path in batch:
                    key=job['id'];attempt=attempts.get(key,0)+1
                    attempts[key]=attempt
                    if result[key]['match']:
                        store.complete(key,path,dict(job=job,verification=str(target/'verification.json'),
                                                   metrics=wav_metrics(path.read_bytes()),audible_review='pending'))
                        ready[key]=True
                    else:
                        save_json(path.parent/'text-rejection.json',result[key])
                checkpoint('running',role=role,age=age,batch=batch_index)
        checkpoint('text_bank_complete' if all(ready.values()) else 'bounded_retakes_exhausted')
    except ProviderError as e:
        save_json(run_dir/'provider-stop.json',dict(status=e.status,category=e.category,body=e.body))
        checkpoint('provider_stopped',category=e.category,status_code=e.status)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        save_json(run_dir/'network-stop.json',dict(error=type(e).__name__))
        checkpoint('network_stopped',error=type(e).__name__)


if __name__=='__main__':main(json.load(sys.stdin))
