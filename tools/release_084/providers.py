"""Bounded provider requests. Secrets accepted through stdin/environment only."""
import base64
import json
import os
import hashlib
import subprocess
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pipeline import classify_error, pcm_wav, playback_wav, save_json, digest, wav_metrics, guard

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/release_084'
FFMPEG = Path('C:/Users/RS/AppData/Local/Programs/Python/Python313/Scripts/ffmpeg.exe')


def decode_flac(data):
    if not data.startswith(b'fLaC'):
        raise ValueError('Provider did not return FLAC')
    decoded=subprocess.run([str(FFMPEG),'-v','error','-i','pipe:0','-ac','1','-ar','48000',
                            '-f','s16le','-acodec','pcm_s16le','pipe:1'],input=data,capture_output=True,timeout=30)
    if decoded.returncode:
        raise ValueError('Lossless FLAC decode failed: '+decoded.stderr.decode(errors='replace')[:200])
    return pcm_wav(decoded.stdout,48000)


class ProviderError(RuntimeError):
    def __init__(self, status, body):
        self.status = status
        self.category = classify_error(status, body)
        self.body = body
        super().__init__(self.category)


def retry_delay(status, body, attempt, retry_after):
    if attempt>=2 or classify_error(status,body) not in ('rate_limit','transient'):
        return None
    delay=2**(attempt+1)
    if retry_after:
        try:delay=max(delay,float(retry_after))
        except ValueError:
            try:delay=max(delay,(parsedate_to_datetime(retry_after)-datetime.now(timezone.utc)).total_seconds())
            except (ValueError,TypeError):return None
    return delay if delay<=30 else None


def request(url, headers, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={**headers, 'Content-Type': 'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read(), dict(response.headers)
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:error = json.loads(raw)
            except ValueError:error = {'message': raw.decode(errors='replace')[:500]}
            delay=retry_delay(e.code,error,attempt,e.headers.get('Retry-After'))
            if delay is None:raise ProviderError(e.code,error) from None
            time.sleep(delay)


def eleven_text(text):
    # Eleven rejects a tags-only request. These are human efforts, not dialogue words.
    return {'[grunt]':'[grunts] Hự.', '[groan]':'[groans] Ah...'}.get(text,text)


def eleven_payload(text,direction):
    if text not in ('[grunt]','[groan]'):return f'[{direction}] {text}'
    take='[softly]' if 'Small, contained realization' in direction else ('[intensely]' if 'Medium, immediate realization' in direction else '[strongly]')
    lead=direction.split('.')[0].lower()
    if text=='[groan]':
        sound=('[exhales sharply]' if 'sudden lost' in lead else '[gasping]' if 'soft involuntary' in lead else
               '[groans]' if 'collapse' in lead else '[gasping]' if 'abrupt' in lead else
               '[inhales deeply]' if 'shocked' in lead else '[sighs]')
        return take+' '+sound+' [groans] Ah...'
    sound=('[grunts]' if 'closed-mouth' in lead else '[gasping]' if 'caught breath' in lead else
           '[exhales sharply]' if 'wince' in lead else '[grunts]' if 'compressed' in lead else
           '[inhales deeply]' if 'sharp intake' in lead else '[grunts]')
    return take+' '+sound+' Hự.'


def synthesize(provider, secret, voice, text, direction, flac_path=None):
    if provider == 'inworld':
        payload = dict(text=f'[{direction}] {text}', voiceId=voice, modelId='inworld-tts-2',
                       audioConfig=dict(audioEncoding='FLAC' if flac_path else 'LINEAR16', sampleRateHertz=48000),
                       language='vi', deliveryMode='BALANCED')
        raw, headers = request('https://api.inworld.ai/tts/v1/voice', {'Authorization': 'Basic ' + secret}, payload)
        response = json.loads(raw)
        audio = base64.b64decode(response['audioContent'], validate=True)
        metadata=dict(usage=response.get('usage'),request_id=headers.get('x-request-id'))
        if flac_path:
            Path(flac_path).write_bytes(audio)
            metadata.update(provider_original=str(flac_path),provider_original_sha256=hashlib.sha256(audio).hexdigest(),
                            lossless_transport='FLAC',decoder=str(FFMPEG),decoder_sha256=digest(FFMPEG))
            audio=decode_flac(audio)
        return audio,metadata
    payload = dict(text=eleven_payload(text,direction), model_id='eleven_v3', language_code='vi')
    raw, headers = request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=pcm_24000',
                           {'xi-api-key': secret}, payload)
    return pcm_wav(raw, 24000), dict(request_id=headers.get('request-id'), character_cost=len(payload['text']),input_text=payload['text'])


def check(secrets):
    result = {}
    for provider in ['inworld', 'elevenlabs']:
        try:
            if provider == 'inworld':
                raw, _ = request('https://api.inworld.ai/tts/v1/voices', {'Authorization': 'Basic '+secrets[provider]})
                voices = json.loads(raw)['voices']
                save_json(OUT/'providers/inworld-voices.json', voices)
                result[provider] = dict(status=200, voices=len(voices), vietnamese_primary=[v['voiceId'] for v in voices if 'vi' in v.get('languages',[])])
            else:
                raw, _ = request('https://api.elevenlabs.io/v1/user/subscription', {'xi-api-key': secrets[provider]})
                subscription = json.loads(raw)
                result[provider] = {k:subscription.get(k) for k in ['tier','character_count','character_limit','can_extend_character_limit']}
                result[provider]['remaining'] = subscription['character_limit']-subscription['character_count']
                raw, _ = request('https://api.elevenlabs.io/v1/voices', {'xi-api-key': secrets[provider]})
                save_json(OUT/'providers/elevenlabs-voices.json', json.loads(raw)['voices'])
        except ProviderError as e:
            result[provider] = dict(status=e.status, category=e.category)
    save_json(OUT/'providers/access.json', result)
    print(json.dumps(result), flush=True)


def audition(secrets):
    # Two smallest probes first; a rejected request must not trigger bulk generation.
    tests = [('inworld','CIV_M','Minh','Có tôi đây.','Speak Vietnamese with a natural Northern Vietnamese accent, grounded calm readiness'),
             ('inworld','CIV_F','Linh','Tôi đi ngay.','Speak Vietnamese with a natural Northern Vietnamese accent, brisk warm acknowledgement')]
    voices = json.loads((OUT/'providers/inworld-voices.json').read_text())
    available = {v['voiceId'] for v in voices}
    # Primary-language Vietnamese voices if available; otherwise cross-lingual system voices.
    vietnamese = [v for v in voices if 'vi' in v.get('languages', [])]
    for index,(provider, role, preferred, text, direction) in enumerate(tests):
        voice = preferred if preferred in available else (['Alex','Ashley'][index])
        if vietnamese:
            voice = vietnamese[min(index,len(vietnamese)-1)]['voiceId']
        dest = OUT/'auditions'/f'{provider}-{role}'
        receipt = dest/'receipt.json'
        if receipt.exists():
            print('EXISTING_AUDITION', role, flush=True)
            continue
        dest.mkdir(parents=True, exist_ok=True)
        try:
            audio, metadata = synthesize(provider,secrets[provider],voice,text,direction)
            (dest/'original.wav').write_bytes(audio)
            playback = playback_wav(audio)
            (dest/'playback.wav').write_bytes(playback)
            record = dict(provider=provider,model='inworld-tts-2',voice=voice,role=role,text=text,direction=direction,
                          metrics=wav_metrics(playback),sha256=digest(dest/'playback.wav'),**metadata,
                          listening_status='pending', historical_pronunciation='creative_approximation')
            save_json(receipt, record)
            print('AUDITION_GENERATED',role,record['metrics'],flush=True)
        except ProviderError as e:
            save_json(dest/'failure.json',dict(status=e.status,category=e.category,body=e.body))
            print('PROVIDER_STOP',provider,e.status,e.category,json.dumps(e.body),flush=True)
            # Auth/credit/unsupported model blocks this provider, never blindly retries.
            break


if __name__ == '__main__':
    guard()
    secrets = json.load(sys.stdin)
    {'check':check,'audition':audition}[sys.argv[1]](secrets)
