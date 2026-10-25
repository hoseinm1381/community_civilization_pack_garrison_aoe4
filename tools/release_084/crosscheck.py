"""Independent Vietnamese transcription of a bounded audition comparison reel."""
import io
import json
import sys
import urllib.request
import urllib.error
import uuid
import wave
from pipeline import pcm_wav, save_json
from providers import OUT


def main(secrets):
    selected = []
    pcm = bytearray()
    for role in ['CIV_M','CIV_F','INFANTRY']:
        for event in ['select','move','attack']:
            folder = OUT/'auditions-v2'/role/event/'attempt-1'
            path = folder/'playback.wav'
            if not path.exists():
                continue
            with wave.open(str(path),'rb') as f:
                assert f.getframerate()==48000 and f.getnchannels()==1 and f.getsampwidth()==2
                start = len(pcm)/96000
                pcm.extend(f.readframes(f.getnframes()))
                end = len(pcm)/96000
            selected.append(dict(role=role,event=event,path=str(path),start=start,end=end))
            pcm.extend(b'\0\0'*24000)
    folder = OUT/'independent-transcription'
    folder.mkdir(parents=True,exist_ok=True)
    audio = pcm_wav(bytes(pcm),48000)
    (folder/'comparison.wav').write_bytes(audio)
    save_json(folder/'segments.json',selected)
    boundary = uuid.uuid4().hex
    body = bytearray()
    for key,value in [('model_id','scribe_v2'),('language_code','vie'),('tag_audio_events','false')]:
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="comparison.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode())
    body.extend(audio)
    body.extend(f'\r\n--{boundary}--\r\n'.encode())
    req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text',data=bytes(body),headers={
        'xi-api-key':secrets['elevenlabs'],'Content-Type':'multipart/form-data; boundary='+boundary})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            result = json.load(r)
        save_json(folder/'scribe.json',result)
        print(json.dumps(dict(status='complete',text=result.get('text'),duration=len(pcm)/96000),ensure_ascii=True))
    except urllib.error.HTTPError as e:
        save_json(folder/'failure.json',dict(status=e.code,body=e.read().decode()[:1000]))
        print('SCRIBE_STOP',e.code)


if __name__ == '__main__':
    main(json.load(sys.stdin))
