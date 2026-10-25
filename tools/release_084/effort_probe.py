"""Small same-actor nonverbal qualification; never replaces animal/mechanism audio."""
import json
import sys
import re
from pathlib import Path
from pipeline import AudioError, guard, playback_wav, save_json, wav_metrics, digest
from providers import OUT, ProviderError, synthesize
from quality import scribe


def nonverbal_matches(text):
    text=text.strip().casefold()
    if text in ['(groans)','(grunts)','(sighs)','[groans]','[grunts]','[sighs]']:return True
    words=re.findall(r'\w+',text)
    return all(w in {'a','à','á','ah','ha','hự','hừ','ư','ừ','ơ','ờ','ugh','huh','oh','o','ô','ồ'} for w in words)


def main(secrets):
    guard()
    casting=json.loads((OUT/'casting.json').read_text())['roles']['GUNNER']
    results=[]
    for event,text,direction in [
        ('pain_light','[grunt]','A short involuntary human impact grunt; closed mouth, no spoken words'),
        ('death','[groan]','A brief human dying effort with an exhausted breath; no words, no animal sounds')]:
        folder=OUT/'effort-probe'/event;folder.mkdir(parents=True,exist_ok=True)
        receipt=folder/'receipt.json'
        if receipt.exists():
            row=json.loads(receipt.read_text())
            if 'transcription' in row:
                row['technical_nonverbal']=nonverbal_matches(row['transcription'].get('text',''))
                save_json(folder/'nonlexical-screen-v2.json',row)
            results.append(row);continue
        try:
            original,usage=synthesize('inworld',secrets['inworld'],casting['voice'],text,direction)
            (folder/'original.wav').write_bytes(original)
            audio=playback_wav(original);path=folder/'playback.wav';path.write_bytes(audio)
            transcript=scribe(secrets['elevenlabs'],audio)
            row=dict(event=event,text=text,direction=direction,casting=casting,usage=usage,
                     metrics=wav_metrics(audio),path=str(path),sha256=digest(path),transcription=transcript,
                     technical_nonverbal=nonverbal_matches(transcript.get('text','')),
                     qualification='nonverbal waveform/text screen only; human acting requires listening')
        except (AudioError,ProviderError) as e:
            row=dict(event=event,technical_nonverbal=False,error=type(e).__name__,reason=str(e))
        save_json(receipt,row);results.append(row)
        print('EFFORT_PROBE',event,json.dumps(row,ensure_ascii=True),flush=True)
    save_json(OUT/'effort-probe/summary.json',dict(results=results,all_technical=all(r['technical_nonverbal'] for r in results)))


if __name__=='__main__':main(json.load(sys.stdin))
