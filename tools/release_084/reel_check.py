"""Contextual ASR check: short isolated Vietnamese commands are ambiguous to ASR."""
import io
import json
import sys
import wave
from pipeline import pcm_wav, save_json
from providers import OUT
from quality import scribe, text_matches


def main(secrets):
    folder=OUT/'auditions-v2/NAVAL_MILITARY'
    clips=[folder/'select/attempt-1/receipt.json',folder/'move/attempt-1/receipt.json']
    clips += sorted((folder/'attack').glob('attempt-*/receipt.json'))
    pcm=bytearray();expected=[];segments=[]
    for p in clips:
        row=json.loads(p.read_text());audio=Path(row['path'])
        with wave.open(str(audio),'rb') as f:
            assert f.getframerate()==48000
            start=len(pcm)/96000
            pcm.extend(f.readframes(f.getnframes()))
            end=len(pcm)/96000
        segments.append(dict(receipt=str(p),start=start,end=end,text=row['text']))
        expected.append(row['text']);pcm.extend(b'\0\0'*24000)
    target=OUT/'audition-reels/NAVAL_MILITARY'
    target.mkdir(parents=True,exist_ok=True)
    audio=pcm_wav(bytes(pcm),48000);(target/'reel.wav').write_bytes(audio)
    result=scribe(secrets['elevenlabs'],audio)
    expected=' '.join(expected)
    matched=text_matches(expected,result.get('text',''))
    save_json(target/'verification.json',dict(expected=expected,transcription=result,match=matched,segments=segments,
        qualification='automatic_contextual_text_check_not_listening_approval'))
    print(json.dumps(dict(expected=expected,actual=result.get('text'),match=matched),ensure_ascii=True))
    if matched:
        casting=json.loads((OUT/'casting.json').read_text())
        casting['roles']['NAVAL_MILITARY']=dict(provider='inworld',model='inworld-tts-2',voice='Carter')
        casting['missing_roles']=[]
        save_json(OUT/'casting.json',casting)


if __name__=='__main__':
    from pathlib import Path
    main(json.load(sys.stdin))
