"""Recover rejected dialogue originals with pinned, unprompted Vietnamese ASR.

No synthesis, recasting, edits to earlier negative evidence, or effort relaxation.
"""
import json
import argparse
from local_audition import DEST
from local_bank import local_guard
from local_check import LocalASR
from local_inputs import verify_inputs
from local_efforts import verified_performance
from local_work import render_attempt,verify_request_text
from pipeline import StateStore, digest, save_json, AudioError


def main():
    local_guard()
    parser=argparse.ArgumentParser();parser.add_argument('--attempt-ceiling',type=int,choices=[3,5],default=3)
    args=parser.parse_args()
    inputs=verify_inputs(('vieneu','moss','phowhisper-medium'))
    fingerprint=inputs['fingerprint']
    state=StateStore(DEST/'generation')
    manifest=json.loads((DEST/'recording-manifest.json').read_text())
    ready={j['id'] for j in manifest['jobs'] if state.ready(j['id'],j)}
    jobs=[j for j in manifest['jobs'] if j['kind']=='dialogue' and j['id'] not in ready]
    if not jobs:print('NO_MISSING_DIALOGUE');return
    checker=LocalASR('phowhisper-medium')
    known={row['sha256']:key for key,row in state.data.items() if key in ready}
    checked=accepted=0
    for job in jobs:
        for attempt in range(1,args.attempt_ceiling+1):
            folder=DEST/'generation'/job['id']/f'attempt-{attempt}'
            old=folder/'local-verification-v2.json'
            receipt=folder/'original.json'
            if not old.exists() or not receipt.exists():continue
            request=json.loads((folder/'request-started.json').read_text())
            verify_request_text(request,job)
            if request.get('job')!=job or request.get('input_fingerprint')!=fingerprint:
                raise RuntimeError('Recheck request identity differs: '+str(folder))
            original=folder/'original-float.wav'
            if digest(original)!=json.loads(receipt.read_text())['sha256']:
                raise RuntimeError('Rejected original changed: '+str(folder))
            try:path,metrics=render_attempt(None,job['text'],job['casting']['voice'],.8,folder,True,request['seed'])
            except AudioError:continue
            sha=digest(path)
            if sha in known and known[sha]!=job['id']:continue
            previous=json.loads(old.read_text())
            if previous.get('prompted') is not False or previous.get('expected')!=job['text']:
                raise RuntimeError('Previous transcript identity differs')
            sidecar=folder/'local-recheck-medium.json'
            model_receipt=inputs['verifier_models']['phowhisper-medium']
            if sidecar.exists():
                proof=json.loads(sidecar.read_text())
                if proof['sha256']!=sha or proof['model_receipt']!=model_receipt or proof['previous_sha256']!=digest(old):
                    raise RuntimeError('Saved recheck evidence differs')
            else:
                text=checker.transcribe(path)
                proof=dict(sha256=sha,previous_sha256=digest(old),model_receipt=model_receipt,
                           transcription=dict(**previous,phowhisper_medium=text),
                           acting_approved=False,native_speaker_approved=False)
                save_json(sidecar,proof)
            checked+=1
            verification=proof['transcription']
            if verified_performance(job,verification):
                state.complete(job['id'],path,dict(job=job,seed=request['seed'],metrics=metrics,
                    request_sha256=digest(folder/'request-started.json'),
                    original_sha256=digest(original),input_fingerprint=fingerprint,
                    recovered_saved_audio=True,transcription=verification,recheck_sha256=digest(sidecar),
                    qualification='additional unprompted exact-word check; prior disagreements retained; acting pending'))
                known[sha]=job['id'];accepted+=1
                print('LOCAL_RECHECK_ACCEPTED',accepted,job['id'],flush=True)
                break
        save_json(DEST/'generation/recheck-medium-checkpoint.json',dict(checked=checked,accepted=accepted,
            recordings=len(state.data),synthesized=0,full_release=False))
    print('LOCAL_RECHECK_FINISHED',checked,accepted,flush=True)


if __name__=='__main__':
    from exclusive_job import exclusive_job
    local_guard()
    with exclusive_job('saved dialogue recheck'):main()
