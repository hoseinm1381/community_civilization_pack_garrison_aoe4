"""Offline recovery of exact phrases from already paid provider originals."""
import io
import json
import wave
from pathlib import Path
from batching import partial_ranges
from effort_probe import nonverbal_matches
from pipeline import AudioError, StateStore, digest, playback_wav, pcm_wav, save_json, wav_metrics, guard, same_recording
from providers import OUT


def main():
    guard()
    state=StateStore(OUT/'generation');recovered=0
    manifest=OUT/'recording-manifest.json'
    current={j['id']:j for j in json.loads(manifest.read_text())['jobs']}
    manifest_sha=digest(manifest)
    for folder in sorted((OUT/'generation/batch-masters').glob('*/attempt-*')):
        if not (folder/'original.wav').exists() or not (folder/'transcript.json').exists():continue
        jobs=json.loads((folder/'jobs.json').read_text());original=folder/'original.wav'
        eligible=[j for j in jobs if j['id'] in current and same_recording(j,current[j['id']])]
        if not any(not state.ready(j['id'],j) for j in eligible):continue
        cache_file=folder/'offline-salvage-v4.json'
        recipe=dict(manifest_sha256=manifest_sha,original_sha256=digest(original),transcript_sha256=digest(folder/'transcript.json'))
        if cache_file.exists():
            cache=json.loads(cache_file.read_text())
            if cache.get('recipe')==recipe and all(state.ready(k,current[k]) for k in cache.get('accepted_ids',[]) if k in current):continue
        try:audio=playback_wav(original.read_bytes(),max_duration=120)
        except AudioError as e:
            save_json(folder/'invalid-original.json',dict(reason=str(e)))
            continue
        metrics=wav_metrics(audio,max_duration=120)
        transcript=json.loads((folder/'transcript.json').read_text())
        if len(jobs)==1 and jobs[0].get('kind')=='nonverbal_effort':
            ranges={jobs[0]['id']:(0,metrics['duration'])} if nonverbal_matches(transcript.get('text','')) else {}
        else:ranges=partial_ranges(jobs,transcript,metrics['duration'])
        with wave.open(io.BytesIO(audio),'rb') as f:pcm=f.readframes(f.getnframes())
        proof={}
        for job in jobs:
            key=job['id']
            if key not in current or not same_recording(job,current[key]):continue
            if state.ready(key,current[key]) or key not in ranges:continue
            start,end=ranges[key]
            clip=pcm_wav(pcm[round(start*48000)*2:round(end*48000)*2],48000)
            try:clip_metrics=wav_metrics(clip)
            except AudioError as e:
                save_json(folder/(key+'-audio-rejected.json'),dict(reason=str(e)))
                continue
            path=folder/(key+'.wav')
            if path.exists():
                assert path.read_bytes()==clip,'Never overwrite a prior different segment'
            else:path.write_bytes(clip)
            clip_hash=digest(path)
            if any(k!=key and row['sha256']==clip_hash for k,row in state.data.items()):continue
            state.complete(key,path,dict(job=job,provider_original=str(original),original_sha256=digest(original),
                range_seconds=[start,end],metrics=clip_metrics,independent_transcript=str(folder/'transcript.json'),
                proof='independent exact phrase with safe timestamps or nonlexical effort screen',audible_review='pending'))
            proof[key]=dict(range_seconds=[start,end],sha256=digest(path));recovered+=1
        if proof:save_json(folder/'partial-salvage.json',proof)
        save_json(cache_file,dict(recipe=recipe,accepted_ids=[j['id'] for j in eligible if state.ready(j['id'],j)]))
    save_json(OUT/'generation/salvage.json',dict(recovered=recovered,charged_requests=0))
    print('084_RECOVERED_WITHOUT_NEW_REQUESTS',recovered)


if __name__=='__main__':main()
