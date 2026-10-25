"""Small backup voice qualification; credentials arrive only on stdin."""
import json,sys
from providers import OUT,synthesize
from pipeline import guard,playback_wav,save_json,wav_metrics,digest
from quality import scribe,text_matches

def main(secrets):
    guard();voice=secrets.get('voice','JBFqnCBsd6RMkjVDRZzb');role=secrets.get('role','CROSSBOW');folder=OUT/'auditions-elevenlabs'/(role+'-'+voice);folder.mkdir(parents=True,exist_ok=True)
    lines=[('calm','Có tôi đây.'),('purposeful','Tôi đi ngay.'),('urgent','Tiến lên!'),('whispering','Tôi đang nghe.')]
    import io,wave
    pcm=bytearray();expected=[]
    for index,(direction,text) in enumerate(lines):
        path=folder/f'{index}.wav'
        if not path.exists():
            audio,usage=synthesize('elevenlabs',secrets['elevenlabs'],voice,text,'Northern Vietnamese; '+direction)
            (folder/f'{index}-original.wav').write_bytes(audio);path.write_bytes(playback_wav(audio))
            save_json(folder/f'{index}.json',dict(text=text,direction=direction,usage=usage,sha256=digest(path),metrics=wav_metrics(path.read_bytes())))
        with wave.open(str(path),'rb') as f:pcm.extend(f.readframes(f.getnframes()))
        pcm.extend(b'\0\0'*24000);expected.append(text)
    from pipeline import pcm_wav
    reel=pcm_wav(bytes(pcm),48000);(folder/'reel.wav').write_bytes(reel)
    transcript_path=folder/'transcript.json'
    if transcript_path.exists():transcript=json.loads(transcript_path.read_text())
    else:transcript=scribe(secrets.get('qa_key',secrets['elevenlabs']),reel);save_json(transcript_path,transcript)
    matched=text_matches(' '.join(expected),transcript.get('text',''))
    save_json(folder/'qualification.json',dict(match=matched,expected=' '.join(expected),actual=transcript.get('text'),voice=voice,model='eleven_v3',audible_review='pending'))
    print('BACKUP_CONTEXT_EXACT',matched,flush=True)

if __name__=='__main__':main(json.load(sys.stdin))
