import json,sys
from pipeline import guard,playback_wav,wav_metrics,save_json,digest
from providers import OUT,synthesize
from budget import account_for,transcription_key
from quality import scribe
from effort_probe import nonverbal_matches

def main(secrets):
    guard();results=[]
    casting=json.loads((OUT/'casting.json').read_text())['roles']['CROSSBOW']
    for event,text in [('pain_light','[grunt]'),('death','[groan]')]:
        folder=OUT/'effort-probe-elevenlabs-v2/CROSSBOW'/event;folder.mkdir(parents=True,exist_ok=True)
        path=folder/'original.wav'
        if not path.exists():
            jobs=json.loads((OUT/'recording-manifest.json').read_text())['jobs']
            direction=next(j['direction'] for j in jobs if j['role']=='CROSSBOW' and j['event']==event and j['phrase_number']==1 and j['take']=='T1')
            original,usage=synthesize('elevenlabs',account_for(secrets,150),casting['voice'],text,direction)
            path.write_bytes(original);save_json(folder/'provider-receipt.json',usage)
        audio=playback_wav(path.read_bytes());playback=folder/'playback.wav';playback.write_bytes(audio)
        target=folder/'transcript.json'
        if target.exists():transcript=json.loads(target.read_text())
        else:transcript=scribe(transcription_key(secrets,audio),audio);save_json(target,transcript)
        accepted=nonverbal_matches(transcript.get('text',''))
        row=dict(event=event,casting=casting,technical_nonverbal=accepted,actual=transcript.get('text'),metrics=wav_metrics(audio),sha256=digest(playback),audible_review='pending')
        save_json(folder/'qualification.json',row);results.append(row)
    save_json(OUT/'effort-probe-elevenlabs-v2/CROSSBOW/summary.json',dict(all_technical=all(r['technical_nonverbal'] for r in results),results=results))
    print(json.dumps(results,ensure_ascii=True),flush=True)
if __name__=='__main__':main(json.load(sys.stdin))
