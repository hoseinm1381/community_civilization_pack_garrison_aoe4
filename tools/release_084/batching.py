"""Six independent phrases per request; each requested take has a separate request.

Provider reels are retained. Only exact independently transcribed reels are split.
"""
import hashlib
import http.client
import io
import math
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
import urllib.error
import wave
from pipeline import AudioError, StateStore, digest, playback_wav, pcm_wav, save_json, wav_metrics, guard, same_recording
from providers import OUT, ProviderError, synthesize, decode_flac, eleven_payload
from quality import scribe, text_matches
from generation import status_counts, verify_batch
from effort_probe import nonverbal_matches
from budget import account_for, transcription_key


def tokens(text):
    return re.findall(r'\w+',unicodedata.normalize('NFC',text).casefold())


def group_jobs(jobs):
    counts={}
    for job in jobs:counts[job['role']]=counts.get(job['role'],0)+1
    ordered=sorted(jobs,key=lambda j:(counts[j['role']],j['role'],j['age'],j['event'],j['take'],j['phrase_number']))
    groups=[]
    for job in ordered:
        identity=tuple(job[k] for k in ['role','age','event','take','direction'])
        if not groups or len(groups[-1])>=6 or job.get('kind')=='nonverbal_effort' or tuple(groups[-1][0][k] for k in ['role','age','event','take','direction'])!=identity:
            groups.append([])
        groups[-1].append(job)
    return groups


def affordable_group(group,ceiling):
    """Reserve a short contextual transcription while trimming the last TTS batch."""
    result=list(group)
    while len(result)>1:
        text=' [long pause] '.join(j['text'] for j in result)
        if len(eleven_payload(text,result[0]['direction']))+12*len(result)<=ceiling:break
        result=result[:-1]
    return result


def valid_timestamps(transcript,duration):
    end=0
    try:
        for w in transcript.get('words',[]):
            if w.get('type')!='word':continue
            a,b=w['start'],w['end']
            if not (math.isfinite(a) and math.isfinite(b) and end<=a<b<=duration+.01):return False
            end=b
    except (KeyError,TypeError):return False
    return True


def aligned_ranges(jobs, transcript, duration):
    if not valid_timestamps(transcript,duration):raise ValueError('Invalid word timestamps')
    if not text_matches(' '.join(j['text'] for j in jobs),transcript.get('text','')):
        raise ValueError('Independent reel transcription differs')
    words=[w for w in transcript.get('words',[]) if w.get('type')=='word']
    expanded=[]
    for word in words:
        expanded.extend((token,word['start'],word['end']) for token in tokens(word['text']))
    expected=[token for job in jobs for token in tokens(job['text'])]
    if [x[0] for x in expanded]!=expected:
        raise ValueError('Word timing token stream differs')
    ranges=[];offset=0
    for job in jobs:
        count=len(tokens(job['text']))
        if not count:raise ValueError('Dialogue-only batch')
        first,last=expanded[offset],expanded[offset+count-1]
        if first[1]<0 or last[2]>duration+.1:raise ValueError('Timestamp outside provider audio')
        start=max(0,first[1]-.08);end=min(duration,last[2]+.10)
        if ranges and start<ranges[-1][1]:
            gap=first[1]-expanded[offset-1][2]
            if gap<.04:raise ValueError('No safe inter-phrase cut')
            boundary=(first[1]+expanded[offset-1][2])/2
            ranges[-1]=(ranges[-1][0],boundary);start=boundary
        if end-start<.12:raise ValueError('Implausible phrase range')
        ranges.append((start,end));offset+=count
    return ranges


def anchored_ranges(jobs,transcript,duration,isolation=.30):
    """Exact whole-word unique anchors; isolate them from any unverified speech."""
    words=[w for w in transcript.get('words',[]) if w.get('type')=='word']
    previous=0
    for w in words:
        a,b=w['start'],w['end']
        if not (math.isfinite(a) and math.isfinite(b) and previous<=a<b<=duration+.01):return {}
        previous=b
    stream=[]
    for index,w in enumerate(words):stream.extend((t,index) for t in tokens(w['text']))
    found=[]
    for job in jobs:
        expected=tokens(job['text']);n=len(expected)
        if not n:continue
        matches=[]
        for a in range(len(stream)-n+1):
            b=a+n
            if [t for t,_ in stream[a:b]]!=expected:continue
            if a and stream[a-1][1]==stream[a][1]:continue
            if b<len(stream) and stream[b-1][1]==stream[b][1]:continue
            matches.append((stream[a][1],stream[b-1][1]))
        if len(matches)==1:found.append((job['id'],*matches[0]))
    if any(a[2]>=b[1] for a,b in zip(found,found[1:])):return {}
    claimed={i for _,a,b in found for i in range(a,b+1)}
    result={}
    for key,a,b in found:
        before=words[a]['start']-words[a-1]['end'] if a else None
        after=words[b+1]['start']-words[b]['end'] if b+1<len(words) else None
        if before is not None and before < (.04 if a-1 in claimed else isolation):continue
        if after is not None and after < (.04 if b+1 in claimed else isolation):continue
        start=max(0,words[a]['start']-.08);end=min(duration,words[b]['end']+.10)
        if a:start=max(start,(words[a-1]['end']+words[a]['start'])/2)
        if b+1<len(words):end=min(end,(words[b]['end']+words[b+1]['start'])/2)
        if end-start>=.12:result[key]=(start,end)
    return result


def partial_ranges(jobs, transcript, duration):
    """Exact reel, isolated unique anchors, or dominant authored pauses."""
    if not valid_timestamps(transcript,duration):return {}
    try:
        return {job['id']:span for job,span in zip(jobs,aligned_ranges(jobs,transcript,duration))}
    except ValueError:
        pass
    words=[w for w in transcript.get('words',[]) if w.get('type')=='word']
    if not words:return {}
    anchored=anchored_ranges(jobs,transcript,duration)
    gaps=sorted([(b['start']-a['end'],i+1) for i,(a,b) in enumerate(zip(words,words[1:]))],reverse=True)
    needed=len(jobs)-1
    if needed:
        if len(gaps)<needed or gaps[needed-1][0]<.65:return anchored
        if len(gaps)>needed and gaps[needed-1][0]-gaps[needed][0]<.15:return anchored
    cuts=[0]+sorted(index for _,index in gaps[:needed])+[len(words)]
    result={}
    for job,a,b in zip(jobs,cuts,cuts[1:]):
        subset=words[a:b]
        if text_matches(job['text'],' '.join(w['text'] for w in subset)):
            start=max(0,subset[0]['start']-.08);end=min(duration,subset[-1]['end']+.10)
            if 0<=start<end<=duration and end-start>=.12:result[job['id']]=(start,end)
    return {**anchored,**result}


def account_request(folder, jobs, attempts, ledger_file):
    """One atomic authoritative ledger; repeated recovery never adds another attempt."""
    ledger=json.loads(ledger_file.read_text()) if ledger_file.exists() else dict(attempts=dict(attempts),requests=[])
    identity=str(folder.resolve())
    if identity not in ledger['requests']:
        for job in jobs:
            key=job['id'];ledger['attempts'][key]=ledger['attempts'].get(key,0)+1
        ledger['requests'].append(identity)
        save_json(ledger_file,ledger)
    attempts.clear();attempts.update(ledger['attempts'])


def recover_lossless(folder):
    original=folder/'original.wav';source=folder/'provider.flac'
    if original.exists() or not source.exists():return False
    audio=decode_flac(source.read_bytes())
    wav_metrics(audio,max_duration=120)
    original.write_bytes(audio)
    save_json(folder/'lossless-recovery.json',dict(source_sha256=digest(source),wav_sha256=digest(original),charged_requests=0))
    return True


def main(secrets,max_batches=8,max_seconds=90):
    guard()
    started_at=time.monotonic();completed_batches=0
    manifest_path=OUT/'recording-manifest.json';manifest=json.loads(manifest_path.read_text())
    jobs=manifest['jobs'];by_id={j['id']:j for j in jobs}
    state=StateStore(OUT/'generation');ready={j['id']:state.ready(j['id'],j) for j in jobs}
    attempts_file=OUT/'generation/attempts.json'
    attempts=json.loads(attempts_file.read_text()) if attempts_file.exists() else {}
    run=1
    while (OUT/f'generation/batched-runs/{run:04d}').exists():run+=1
    run_dir=OUT/f'generation/batched-runs/{run:04d}';run_dir.mkdir(parents=True)
    def checkpoint(status,**extra):
        value=dict(status=status,**status_counts(list(by_id),ready,attempts),**extra)
        save_json(OUT/'generation/status.json',value);save_json(attempts_file,attempts)
        print(json.dumps(value),flush=True)
    checkpoint('running_batched',manifest_sha256=digest(manifest_path))
    try:
        ledger_file=OUT/'generation/request-ledger.json'
        prior_requests=list((OUT/'generation/batch-masters').glob('*/attempt-*/request-started.json'))
        if not ledger_file.exists():
            # Historical checkpoints already counted many requests. Reconcile by maximum,
            # conservatively counting every submitted marker including rejected requests.
            counts={}
            for prior in prior_requests:
                for key in json.loads(prior.read_text())['job_ids']:counts[key]=counts.get(key,0)+1
            for key,count in counts.items():attempts[key]=max(attempts.get(key,0),count)
            save_json(ledger_file,dict(attempts=attempts,requests=[str(p.parent.resolve()) for p in prior_requests]))
        for prior in prior_requests:
            ids=json.loads(prior.read_text())['job_ids']
            account_request(prior.parent,[dict(id=k) for k in ids],attempts,ledger_file)
            try:recover_lossless(prior.parent)
            except (AudioError,ValueError) as e:
                save_json(prior.parent/'invalid-lossless.json',dict(reason=str(e),provider_original_preserved=True))
        save_json(attempts_file,attempts)
        # Finish QA on paid originals before scheduling any more synthesis.
        for prior in prior_requests:
            folder=prior.parent
            if (folder/'original.wav').exists() and not (folder/'transcript.json').exists():
                saved=json.loads((folder/'jobs.json').read_text())
                if any(j['id'] in by_id and same_recording(j,by_id[j['id']]) and not ready[j['id']] for j in saved):
                    try:
                        audio=playback_wav((folder/'original.wav').read_bytes(),max_duration=120)
                    except AudioError as e:
                        save_json(folder/'invalid-original.json',dict(reason=str(e),regenerate_only_within_attempt_budget=True))
                        continue
                    transcript=scribe(transcription_key(secrets,audio),audio)
                    save_json(folder/'transcript.json',transcript)
        from salvage import main as salvage_saved
        salvage_saved()
        state=StateStore(OUT/'generation')
        ready={j['id']:state.ready(j['id'],j) for j in jobs}
        # Recover previously generated individual originals before asking for any new speech.
        recovery=[]
        for job in jobs:
            key=job['id']
            if ready[key]:continue
            folder=OUT/'generation/masters'/key/f'attempt-{attempts.get(key,0)+1}'
            original=folder/'original.wav'
            if original.exists():
                try:
                    playback=folder/'playback.wav';playback.write_bytes(playback_wav(original.read_bytes()))
                    recovery.append((job,playback))
                except AudioError:
                    attempts[key]=attempts.get(key,0)+1
            elif (folder/'request-started.json').exists() and not (folder/'provider-rejection.json').exists():
                # A deliberately interrupted request counts against the bounded retake budget.
                save_json(folder/'interrupted-recovery.json',dict(status='no_response_saved',
                    possible_charge=True,counts_as_attempt=True))
                attempts[key]=attempts.get(key,0)+1
        if recovery:
            result=verify_batch(secrets,recovery,run_dir/'recovered-individuals')
            for job,path in recovery:
                key=job['id'];attempts[key]=attempts.get(key,0)+1
                if result[key]['match']:
                    state.complete(key,path,dict(job=job,verification=str(run_dir/'recovered-individuals/verification.json'),
                        metrics=wav_metrics(path.read_bytes()),audible_review='pending'))
                    ready[key]=True
            checkpoint('running_batched',recovered=len(recovery))
        for round_number in range(3):
            queue=[j for j in jobs if not ready[j['id']] and attempts.get(j['id'],0)<3 and
                (not secrets.get('production_provider') or j['casting']['provider']==secrets['production_provider']) and
                (not secrets.get('production_role') or j['role']==secrets['production_role'])]
            # Spend the first-pass budget on unrecorded phrases before repeating failed phrases.
            floor=min((attempts.get(j['id'],0) for j in queue),default=0)
            groups=group_jobs([j for j in queue if attempts.get(j['id'],0)==floor])
            for index,group in enumerate(groups):
                if group[0]['casting']['provider']=='elevenlabs':
                    snapshot=OUT/'generation/account-balances.json'
                    if snapshot.exists():
                        ceiling=max((r['remaining'] for r in json.loads(snapshot.read_text())['accounts']),default=0)
                        if ceiling<500:group=affordable_group(group,ceiling)
                key=hashlib.sha256('|'.join(j['id'] for j in group).encode()).hexdigest()
                attempt=max(attempts.get(j['id'],0) for j in group)+1
                folder=OUT/'generation/batch-masters'/key/f'attempt-{attempt}'
                folder.mkdir(parents=True,exist_ok=True)
                original=folder/'original.wav';actor=group[0]['casting']
                assert all(j['casting']==actor and j['take']==group[0]['take'] for j in group)
                separator=' <break time="600ms"/> ' if actor['provider']=='inworld' else ' [long pause] '
                payload_text=separator.join(j['text'] for j in group)
                save_json(folder/'jobs.json',group)
                if not original.exists():
                    started=folder/'request-started.json'
                    if started.exists() and not (folder/'provider-rejection.json').exists():
                        checkpoint('uncertain_batch_requires_review',batch=key,role=group[0]['role'])
                        return
                    active_secret=account_for(secrets,len(eleven_payload(payload_text,group[0]['direction']))+12*len(group)) if actor['provider']=='elevenlabs' else secrets[actor['provider']]
                    save_json(started,dict(status='submitted',job_ids=[j['id'] for j in group],
                        provider=actor['provider'],model=actor['model'],voice=actor['voice'],
                        text=payload_text,direction=group[0]['direction']))
                    account_request(folder,group,attempts,ledger_file)
                    save_json(attempts_file,attempts)
                    try:
                        audio,usage=synthesize(actor['provider'],active_secret,actor['voice'],payload_text,
                                               group[0]['direction'],flac_path=folder/'provider.flac' if actor['provider']=='inworld' else None)
                    except ProviderError as e:
                        save_json(folder/'provider-rejection.json',dict(status=e.status,category=e.category));raise
                    original.write_bytes(audio);save_json(folder/'provider-receipt.json',usage)
                try:
                    audio=playback_wav(original.read_bytes(),max_duration=120)
                    metrics=wav_metrics(audio,max_duration=120)
                    transcript_file=folder/'transcript.json'
                    if transcript_file.exists():transcript=json.loads(transcript_file.read_text())
                    else:
                        transcript=scribe(transcription_key(secrets,audio),audio);save_json(transcript_file,transcript)
                    nonverbal=group[0].get('kind')=='nonverbal_effort'
                    if nonverbal:
                        assert len(group)==1
                        ranges={group[0]['id']:(0,metrics['duration'])} if nonverbal_matches(transcript.get('text','')) else {}
                    else:ranges=partial_ranges(group,transcript,metrics['duration'])
                    with wave.open(io.BytesIO(audio),'rb') as f:pcm=f.readframes(f.getnframes())
                    prepared=[]
                    for job in group:
                        if job['id'] not in ranges:continue
                        start,end=ranges[job['id']]
                        clip=pcm_wav(pcm[round(start*48000)*2:round(end*48000)*2],48000)
                        try:clip_metrics=wav_metrics(clip)
                        except AudioError as e:
                            save_json(folder/(job['id']+'-audio-rejected.json'),dict(reason=str(e)))
                            continue
                        path=folder/(job['id']+'.wav');path.write_bytes(clip)
                        prepared.append((job,path,dict(job=job,provider_original=str(original),
                            original_sha256=digest(original),range_seconds=[start,end],metrics=clip_metrics,
                            independent_transcript=str(transcript_file),audible_review='pending')))
                    unique=[]
                    known_hashes={r['sha256']:k for k,r in state.data.items()}
                    for job,path,metadata in prepared:
                        clip_hash=digest(path)
                        if clip_hash in known_hashes and known_hashes[clip_hash]!=job['id']:
                            save_json(folder/(job['id']+'-duplicate.json'),dict(sha256=clip_hash,other_job=known_hashes[clip_hash]))
                            continue
                        state.complete(job['id'],path,metadata);ready[job['id']]=True
                        known_hashes[clip_hash]=job['id'];unique.append((job,path,metadata))
                    prepared=unique
                    save_json(folder/'verification.json',dict(accepted=len(prepared)==len(group),independent_text_exact=not nonverbal and len(prepared)==len(group),
                        independent_nonverbal_screen=nonverbal and len(prepared)==len(group),
                        original_sha256=digest(original),ranges=ranges,clips={j['id']:digest(p) for j,p,_ in prepared}))
                except (AudioError,ValueError) as e:
                    save_json(folder/'rejected.json',dict(reason=str(e),independent_text_exact=False))
                checkpoint('running_batched',role=group[0]['role'],age=group[0]['age'],
                    event=group[0]['event'],take=group[0]['take'],round=round_number+1,batch=index+1)
                completed_batches+=1
                if (OUT/'generation/STOP_AFTER_BATCH').exists():
                    checkpoint('checkpoint_requested')
                    return
                if completed_batches>=max_batches or time.monotonic()-started_at>=max_seconds:
                    checkpoint('chunk_complete',completed_batches=completed_batches)
                    return
        checkpoint('text_bank_complete' if all(ready.values()) else 'bounded_retakes_exhausted')
    except ProviderError as e:
        save_json(run_dir/'provider-stop.json',dict(status=e.status,category=e.category,body=e.body))
        checkpoint('provider_stopped',category=e.category,status_code=e.status)
    except (urllib.error.URLError,TimeoutError,OSError,http.client.HTTPException) as e:
        if isinstance(e,http.client.IncompleteRead):
            (run_dir/'partial-response.bin').write_bytes(e.partial)
        save_json(run_dir/'network-stop.json',dict(error=type(e).__name__))
        checkpoint('network_stopped',error=type(e).__name__)


if __name__=='__main__':main(json.load(sys.stdin))
