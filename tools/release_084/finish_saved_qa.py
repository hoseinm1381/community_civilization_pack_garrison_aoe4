"""One final QA request against an existing free-plan hard cap, no synthesis."""
import json,sys
from providers import OUT,request,ProviderError
from pipeline import save_json,playback_wav,wav_metrics
from quality import scribe

def main(secret):
    raw,_=request('https://api.elevenlabs.io/v1/user/subscription',{'xi-api-key':secret})
    subscription=json.loads(raw)
    if subscription['tier']!='free' or subscription.get('can_extend_character_limit'):
        raise ValueError('Final QA requires the existing enforced free-plan cap')
    remaining=subscription['character_limit']-subscription['character_count']
    folder=OUT/'generation/batch-masters/a30f5beb00cd400b410ca5e451dca1f4df4b3a1fd21bb65c1362eb704f30af84/attempt-1'
    if remaining<=0:
        save_json(folder/'final-qa-not-run.json',dict(status='credits_exhausted',remaining=remaining,charged_requests=0))
        print('FINAL_QA_NO_EXISTING_CREDITS');return
    target=folder/'transcript.json'
    if target.exists():print('FINAL_QA_ALREADY_PRESENT');return
    audio=playback_wav((folder/'original.wav').read_bytes(),max_duration=120)
    receipt=dict(remaining_before=remaining,audio_seconds=wav_metrics(audio,max_duration=120)['duration'],synthesis_requests=0,
        billing_guard='Existing free account, overages unavailable; server enforces the remaining-credit cap. Single request only.')
    try:
        transcript=scribe(secret,audio);save_json(target,transcript);receipt['status']='transcribed'
    except ProviderError as e:receipt.update(status='rejected',status_code=e.status,category=e.category,body=e.body)
    save_json(folder/'final-qa-budget.json',receipt)
    print('084_FINAL_QA',receipt['status'],flush=True)

if __name__=='__main__':main(json.load(sys.stdin)['elevenlabs'])
