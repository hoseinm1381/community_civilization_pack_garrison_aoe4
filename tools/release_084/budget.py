"""Use only supplied existing ElevenLabs balances; never enable account overages."""
import json,math
from providers import request,ProviderError,OUT
from pipeline import save_json,wav_metrics

def account_for(secrets,required):
    keys=secrets.get('elevenlabs_accounts',[secrets['elevenlabs']])
    balances=[];selected=None
    for index,key in enumerate(keys):
        raw,_=request('https://api.elevenlabs.io/v1/user/subscription',{'xi-api-key':key})
        row=json.loads(raw);remaining=row['character_limit']-row['character_count']
        if row.get('can_extend_character_limit'):
            raise ValueError('Overage-enabled account is outside the authorized free-only route')
        balances.append(dict(account=index+1,remaining=remaining,limit=row['character_limit'],used=row['character_count']))
        if remaining>=required:
            selected=key
            break
    snapshot=OUT/'generation/account-balances.json'
    previous=json.loads(snapshot.read_text()).get('accounts',[]) if snapshot.exists() else []
    merged={r['account']:r for r in previous}
    merged.update({r['account']:r for r in balances})
    save_json(snapshot,dict(accounts=list(merged.values()),required=required))
    if selected is None:raise ProviderError(402,dict(message='Insufficient supplied existing credits',required=required))
    return selected

def transcription_key(secrets,audio):
    # Conservative preflight allocation; the service enforces the actual free balance.
    seconds=wav_metrics(audio,max_duration=120)['duration']
    return account_for(secrets,max(10,math.ceil(seconds*3)))
