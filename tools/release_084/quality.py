"""Conservative automatic text gate; never a substitute for listening approval."""
import base64
import json
from pathlib import Path
import re
import unicodedata
import urllib.request
import urllib.error
import uuid
import socket
import time
from pipeline import AudioError, save_json, playback_wav, wav_metrics, digest, guard
from providers import OUT, ProviderError, request, synthesize

VOICES = dict(CIV_M='Alex', CIV_F='Ashley', SCOUT='Mark', INFANTRY='Edward',
              ARCHER='Elliot', SKIRMISHER='Timothy', CROSSBOW='Oliver', GUNNER='Ronald',
              CAVALRY='James', MONK='Alaric', OFFICIAL='Craig', TRADER='Dennis',
              SIEGE='Hades', NAVAL_FISH='Clive', NAVAL_TRADE='Blake',
              NAVAL_MILITARY='Carter', NAVAL_TRANSPORT='Jarrah', NAVAL_FIRE='Sebastian')


def text_matches(expected, actual):
    def normalize(text):
        return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFC', text).casefold()))
    return normalize(expected) == normalize(actual)


def select_casting(voices):
    available = {x['voiceId'] for x in voices}
    if set(VOICES.values()) - available:
        raise ValueError('Missing audition voice: '+str(set(VOICES.values())-available))
    return {role:dict(provider='inworld', model='inworld-tts-2', voice=voice) for role,voice in VOICES.items()}


def transcribe(secret, audio):
    body = dict(transcribeConfig=dict(modelId='inworld/inworld-stt-1', audioEncoding='AUTO_DETECT',
                                      language='vi',numberOfChannels=1),
                audioData=dict(content=base64.b64encode(audio).decode()))
    raw, _ = request('https://api.inworld.ai/stt/v1/transcribe', {'Authorization':'Basic '+secret},body)
    return json.loads(raw)


def scribe(secret, audio):
    boundary = uuid.uuid4().hex
    body = bytearray()
    for key,value in [('model_id','scribe_v2'),('language_code','vie'),('tag_audio_events','false')]:
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="clip.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode())
    body.extend(audio)
    body.extend(f'\r\n--{boundary}--\r\n'.encode())
    req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text',data=bytes(body),headers={
        'xi-api-key':secret,'Content-Type':'multipart/form-data; boundary='+boundary})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise ProviderError(e.code,json.loads(e.read())) from None


def check_words(secrets, audio, text, previous=None):
    primary = previous or transcribe(secrets['inworld'],audio)
    actual = primary['transcription']['transcript']
    if text_matches(text,actual):
        return True, dict(primary=primary)
    independent = scribe(secrets['elevenlabs'],audio)
    return text_matches(text,independent.get('text','')), dict(primary=primary,independent=independent)


def auditions(secrets):
    casting = select_casting(json.loads((OUT/'providers/inworld-voices.json').read_text()))
    # Representative emotional tests plus one exact-text identity test per remaining role.
    phrases = [('select','Có tôi đây.','calm, grounded readiness'),
               ('move','Tôi đi ngay.','prompt, purposeful acknowledgement'),
               ('attack','Tiến lên!','urgent battlefield command, projected but no distortion'),
               ('quiet','Có tôi đây.','quietly and cautiously, fully intelligible lexical tones')]
    representatives = {'CIV_M','CIV_F','SKIRMISHER','INFANTRY','MONK','NAVAL_MILITARY'}
    summary = {}
    for role,actor in casting.items():
        events = phrases if role in representatives else phrases[:1]
        outcomes = []
        for event,text,delivery in events:
            folder = OUT/'auditions-v2'/role/event
            existing = folder/'accepted.json'
            if existing.exists():
                row = json.loads(existing.read_text())
                if digest(row['path']) == row['sha256']:
                    outcomes.append(row)
                    continue
            for attempt in range(1,4):
                target = folder/f'attempt-{attempt}'
                receipt = target/'receipt.json'
                if receipt.exists():
                    row = json.loads(receipt.read_text())
                    if not row['text_match'] and 'independent' not in row.get('verification',{}):
                        matched,verification = check_words(secrets,Path(row['path']).read_bytes(),text,row['transcription'])
                        row.update(text_match=matched,verification=verification)
                        save_json(target/'recheck.json',row)
                else:
                    target.mkdir(parents=True,exist_ok=True)
                    direction = 'Northern Vietnamese accent; '+delivery+'; say every word exactly'
                    try:
                        original_path = target/'original.wav'
                        if original_path.exists():
                            original,usage = original_path.read_bytes(),dict(recovered_original=True)
                        else:
                            original,usage = synthesize(actor['provider'],secrets[actor['provider']],actor['voice'],text,direction)
                            original_path.write_bytes(original)
                        audio = playback_wav(original)
                        path = target/'playback.wav'
                        path.write_bytes(audio)
                        transcript = transcribe(secrets['inworld'],audio)
                        matched,verification = check_words(secrets,audio,text,transcript)
                        row = dict(role=role,event=event,text=text,direction=direction,**actor,
                                   attempt=attempt,path=str(path),sha256=digest(path),metrics=wav_metrics(audio),
                                   transcription=transcript,text_match=matched,verification=verification,usage=usage,
                                   audible_review='not_performed', historical_pronunciation='creative_approximation')
                        save_json(receipt,row)
                        print('AUDITION',role,event,attempt,'MATCH' if row['text_match'] else 'MISMATCH',flush=True)
                    except ProviderError as e:
                        save_json(target/'failure.json',dict(category=e.category,status=e.status,body=e.body))
                        save_json(OUT/'auditions-v2/status.json',dict(status='provider_stopped',role=role,event=event,category=e.category))
                        print('PROVIDER_STOP',e.category,e.status,flush=True)
                        return
                    except AudioError as e:
                        save_json(target/'audio-rejection.json',dict(reason=str(e)))
                        print('AUDIO_REJECTED',role,event,attempt,flush=True)
                        continue
                    except (urllib.error.URLError, TimeoutError, OSError) as e:
                        save_json(target/'network-stop.json',dict(error=type(e).__name__,original_preserved=(target/'original.wav').exists()))
                        print('NETWORK_STOP',role,event,type(e).__name__,flush=True)
                        return
                if row['text_match']:
                    save_json(existing,row)
                    outcomes.append(row)
                    break
            else:
                summary[role] = dict(technical_pass=False,failed_event=event)
                break
        else:
            summary[role] = dict(technical_pass=True,clips=len(outcomes),casting=actor)
        save_json(OUT/'auditions-v2/summary.json',summary)
    save_json(OUT/'auditions-v2/status.json',dict(status='technical_checks_complete',
              roles=len(summary),passed=sum(v['technical_pass'] for v in summary.values()),audible_review='pending'))


def alternate_auditions(secrets):
    summary=json.loads((OUT/'auditions-v2/summary.json').read_text())
    final={role:row['casting'] for role,row in summary.items() if row['technical_pass']}
    for role,voice in [('INFANTRY','Wei'),('NAVAL_MILITARY','Cedric')]:
        passed=True
        for event,text,delivery in [('select','Có tôi đây.','calm readiness'),('move','Tôi đi ngay.','prompt acknowledgement'),
                                    ('attack','Tiến lên!','urgent and clearly articulated'),('quiet','Có tôi đây.','quiet and cautious')]:
            success=False
            for attempt in range(1,4):
                folder=OUT/'auditions-v3'/role/event/f'attempt-{attempt}'
                receipt=folder/'receipt.json'
                if receipt.exists():
                    row=json.loads(receipt.read_text())
                else:
                    folder.mkdir(parents=True,exist_ok=True)
                    original,usage=synthesize('inworld',secrets['inworld'],voice,text,'Northern Vietnamese; '+delivery+'; exact words')
                    (folder/'original.wav').write_bytes(original)
                    audio=playback_wav(original);path=folder/'playback.wav';path.write_bytes(audio)
                    matched,verification=check_words(secrets,audio,text)
                    row=dict(role=role,event=event,voice=voice,provider='inworld',model='inworld-tts-2',text=text,
                             path=str(path),sha256=digest(path),metrics=wav_metrics(audio),text_match=matched,verification=verification,usage=usage)
                    save_json(receipt,row)
                    print('ALTERNATE',role,event,attempt,'MATCH' if matched else 'MISMATCH',flush=True)
                if row['text_match']:success=True;break
            if not success:passed=False;break
        if passed:final[role]=dict(provider='inworld',model='inworld-tts-2',voice=voice)
        else:print('ROLE_NEEDS_BACKUP',role,flush=True)
    save_json(OUT/'casting.json',dict(roles=final,technical_checks_only=True,audible_review='pending',
                                    missing_roles=sorted(set(VOICES)-set(final))))


def backup_auditions(secrets):
    casting=json.loads((OUT/'casting.json').read_text())
    voice='JBFqnCBsd6RMkjVDRZzb'
    for event,text,direction in [('select','Có tôi đây.','calm'),('move','Tôi đi ngay.','confident'),
                                 ('attack','Tiến lên!','shouting'),('quiet','Có tôi đây.','whispering')]:
        success=False
        for attempt in range(1,4):
            target=OUT/'auditions-elevenlabs'/'NAVAL_MILITARY'/event/f'attempt-{attempt}'
            receipt=target/'receipt.json'
            if receipt.exists():row=json.loads(receipt.read_text())
            else:
                target.mkdir(parents=True,exist_ok=True)
                original,usage=synthesize('elevenlabs',secrets['elevenlabs'],voice,text,direction)
                (target/'original.wav').write_bytes(original)
                audio=playback_wav(original);path=target/'playback.wav';path.write_bytes(audio)
                verification=scribe(secrets['elevenlabs'],audio)
                row=dict(provider='elevenlabs',model='eleven_v3',voice=voice,text=text,direction=direction,
                         text_match=text_matches(text,verification.get('text','')),verification=verification,
                         metrics=wav_metrics(audio),path=str(path),sha256=digest(path),usage=usage)
                save_json(receipt,row)
                print('BACKUP_AUDITION',event,attempt,'MATCH' if row['text_match'] else 'MISMATCH',flush=True)
            if row['text_match']:success=True;break
        if not success:
            print('BACKUP_ROLE_FAILED',event,flush=True)
            return
    casting['roles']['NAVAL_MILITARY']=dict(provider='elevenlabs',model='eleven_v3',voice=voice)
    casting['missing_roles']=[]
    save_json(OUT/'casting.json',casting)


def gender_auditions(secrets):
    casting=json.loads((OUT/'casting.json').read_text())
    expected='Có tôi đây. Tôi đi ngay. Tiến lên! Có tôi đây.'
    script='Có tôi đây. <break time="600ms"/> Tôi đi ngay. <break time="600ms"/> [urgent and clearly articulated] Tiến lên! <break time="600ms"/> [whispering clearly] Có tôi đây.'
    for role,candidates in [('SCOUT_F',['Hana','Ashley']),('INFANTRY_F',['Sarah','Ashley'])]:
        for voice in candidates:
            folder=OUT/'auditions-gender'/role/voice;folder.mkdir(parents=True,exist_ok=True)
            receipt=folder/'receipt.json'
            if receipt.exists():row=json.loads(receipt.read_text())
            else:
                original,usage=synthesize('inworld',secrets['inworld'],voice,script,'Natural Northern Vietnamese; an alert adult woman; say all words exactly')
                (folder/'original.wav').write_bytes(original)
                audio=playback_wav(original);path=folder/'playback.wav';path.write_bytes(audio)
                transcript=scribe(secrets['elevenlabs'],audio)
                row=dict(role=role,voice=voice,provider='inworld',model='inworld-tts-2',expected=expected,
                         transcription=transcript,text_match=text_matches(expected,transcript.get('text','')),
                         metrics=wav_metrics(audio),path=str(path),sha256=digest(path),usage=usage,audible_review='pending')
                save_json(receipt,row)
            print('GENDER_AUDITION',role,voice,row['text_match'],flush=True)
            if row['text_match']:
                casting['roles'][role]=dict(provider='inworld',model='inworld-tts-2',voice=voice)
                break
        else:
            print('GENDER_CASTING_UNRESOLVED',role,flush=True)
    save_json(OUT/'casting.json',casting)


if __name__ == '__main__':
    guard()
    import sys
    action=sys.argv[1] if len(sys.argv)>1 else 'auditions'
    {'alternates':alternate_auditions,'backup':backup_auditions,'auditions':auditions,'genders':gender_auditions}[action](json.load(sys.stdin))
