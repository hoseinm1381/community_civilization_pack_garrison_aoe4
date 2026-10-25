"""Serial local GPU batches; every phrase/take has its own original and checks."""
import argparse
from collections import defaultdict, deque, Counter
import hashlib
from itertools import zip_longest
import json
import os
import random
import time

from local_audition import DEST, RUNTIME
from local_bank import local_guard, actor_qualified_roles, performance_text
from local_efforts import performance_matches, verified_performance
from local_check import LocalASR
from local_inputs import verify_inputs, validated_audition_results, verify_completed_recording
from local_work import attempt_plan, render_attempt, WorkBudget, performance_groups, validated_completed,retake_text
from pipeline import StateStore, save_json, digest, AudioError, wav_metrics
from quality import text_matches
from voice_scope import delivery_manifest


def main():
    local_guard()
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=120)
    parser.add_argument('--max-attempts', type=int)
    parser.add_argument('--batch-size', type=int, default=6, choices=range(1,7))
    parser.add_argument('--kind', choices=['dialogue','effort'], default='dialogue')
    parser.add_argument('--attempt-ceiling',type=int,choices=[3,5],default=3)
    args = parser.parse_args()
    manifest = json.loads((DEST/'recording-manifest.json').read_text())
    scoped=delivery_manifest(manifest)
    if args.kind=='effort' and len(scoped['jobs'])!=len(manifest['jobs']):
        raise RuntimeError('Custom efforts are outside the approved spoken-only delivery scope')
    inputs = verify_inputs(('vieneu','moss','whisper','phowhisper'))
    voices = {j['role']:j['casting']['voice'] for j in manifest['jobs']}
    legacy_path = DEST/'legacy-pilot-input-certification.json'
    legacy = json.loads(legacy_path.read_text()) if legacy_path.exists() else {}
    valid_auditions = validated_audition_results(json.loads((DEST/'auditions/local-asr.json').read_text()),
                         StateStore(DEST/'auditions'), voices, inputs['fingerprint'], legacy.get('auditions'))
    qualified = actor_qualified_roles(valid_auditions, voices)
    if not qualified: raise RuntimeError('No qualified actors')
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    import numpy as np
    import soundfile as sf
    import torch
    from vieneu import Vieneu
    if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable')
    print('LOADING_LOCAL_BATCH_MODELS',flush=True)
    tts = Vieneu(backbone_repo=str(RUNTIME/'models/vieneu'), moss_tokenizer=str(RUNTIME/'models/moss'),
                 device='cuda',backend='pytorch',max_batch_size=args.batch_size,max_streams=1,babble_retries=0)
    primary = LocalASR('phowhisper'); secondary = LocalASR('whisper')
    state = StateStore(DEST/'generation')
    attempts_file = DEST/'generation/attempts.json'
    attempts = json.loads(attempts_file.read_text()) if attempts_file.exists() else {}
    budget = WorkBudget(args.max_attempts if args.max_attempts is not None else args.limit*3)
    validated,known=validated_completed(state,{j['id']:j for j in manifest['jobs']},inputs['fingerprint'],legacy.get('generation_attempts'))
    counts=Counter(row['metadata']['job']['kind'] for row in state.data.values())
    roles = defaultdict(list)
    kind='dialogue' if args.kind=='dialogue' else 'nonverbal_effort'
    for group in performance_groups([j for j in manifest['jobs'] if j['kind']==kind and j['role'] in qualified]):
        roles[group[0]['role']].append(group)
    queue = deque(group for row in zip_longest(*roles.values()) for group in row if group is not None)
    accepted = 0
    run_started = time.monotonic()
    while queue and accepted < args.limit:
        if (DEST/'generation/STOP').exists(): print('COOPERATIVE_STOP',flush=True);break
        group = queue.popleft()
        pending = []
        for job in group:
            if job['id'] in validated:continue
            plan = next(iter(attempt_plan(DEST/'generation'/job['id'],attempts.get(job['id'],0),job,
                                         inputs['fingerprint'],legacy.get('generation_attempts'),ceiling=args.attempt_ceiling)),None)
            if plan is not None: pending.append((job,*plan))
            if len(pending) >= min(args.batch_size,args.limit-accepted): break
        if not pending: continue
        selected = []
        for item in pending:
            if item[3] or budget.reserve(): selected.append(item)
        if not selected: continue
        started = time.monotonic()
        fresh = [item for item in selected if not item[3]]
        if fresh:
            recipe = dict(jobs=[(j['id'],a) for j,a,_,_ in fresh],input_fingerprint=inputs['fingerprint'],mode='independent-rows-v1')
            if any(a>=3 for _,a,_,_ in fresh):
                recipe['synthesis_inputs']={j['id']:retake_text(j,a) for j,a,_,_ in fresh}
            batch_id = hashlib.sha256(json.dumps(recipe,sort_keys=True).encode()).hexdigest()
            seed = int(batch_id[:8],16)
            batch_folder = DEST/'batches'/batch_id
            batch_folder.mkdir(parents=True,exist_ok=True)
            save_json(batch_folder/'request-started.json',dict(**recipe,seed=seed))
            for position,(job,attempt,folder,_) in enumerate(fresh):
                folder.mkdir(parents=True,exist_ok=True)
                attempts[job['id']]=attempt+1
                save_json(attempts_file,attempts)
                save_json(folder/'request-started.json',dict(job=job,attempt=attempt+1,seed=seed,
                          input_fingerprint=inputs['fingerprint'],batch_id=batch_id,batch_position=position,
                          temperature={'T1':.75,'T2':.82,'T3':.9}[job['take']],batch_size=args.batch_size,
                          synthesis_text=retake_text(job,attempt),
                          synthesis_recipe='clear-first-word-pause-v1' if attempt>=3 else 'original-input-v1',
                          batch_jobs=[j['id'] for j,_,_,_ in fresh],backend='local VieNeu infer_batch; independent rows; same take only'))
            random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
            outputs = tts.infer_batch([retake_text(j,a) for j,a,_,_ in fresh],voice=fresh[0][0]['casting']['voice'],
                       temperature={'T1':.75,'T2':.82,'T3':.9}[fresh[0][0]['take']],batch_size=args.batch_size,max_new_frames=300)
            if len(outputs)!=len(fresh): raise RuntimeError('Wrong number of batch outputs')
            for (_,_,folder,_),wav in zip(fresh,outputs):
                original=folder/'original-float.wav'
                if original.exists(): raise RuntimeError('Refusing original overwrite')
                sf.write(original,np.asarray(wav,dtype=np.float32),tts.sample_rate,subtype='FLOAT')
                save_json(folder/'original.json',dict(sha256=digest(original),input_fingerprint=inputs['fingerprint']))
        checked=[]
        for job,attempt,folder,recovered in selected:
            request=json.loads((folder/'request-started.json').read_text())
            try:
                path,metrics=render_attempt(tts,performance_text(job),job['casting']['voice'],.8,folder,True,request['seed'])
                if job['kind']=='nonverbal_effort' and metrics['duration']>(5 if job['event']=='death' else 3):
                    raise AudioError('Nonverbal effort exceeds short-response duration')
                sha=digest(path)
                if sha in known and known[sha]!=job['id']: raise AudioError('Duplicate performance bytes')
                checked.append((job,attempt,folder,recovered,path,metrics,request,sha))
            except AudioError as error:
                save_json(folder/'final-quality.json',dict(status='rejected',reason=str(error),input_fingerprint=inputs['fingerprint']))
        if checked:
            texts=primary.transcribe_batch([item[4] for item in checked])
            if len(texts)!=len(checked): raise RuntimeError('Wrong primary transcription count')
            mismatch=[i for i,(item,text) in enumerate(zip(checked,texts))
                      if item[0]['kind']=='nonverbal_effort' or not performance_matches(item[0],text)]
            backup=secondary.transcribe_batch([checked[i][4] for i in mismatch])
            if len(backup)!=len(mismatch): raise RuntimeError('Wrong secondary transcription count')
            alternatives=dict(zip(mismatch,backup))
            for i,(job,attempt,folder,recovered,path,metrics,request,sha) in enumerate(checked):
                verification=dict(phowhisper=texts[i],whisper=alternatives.get(i),expected=job['text'],prompted=False,
                                  check='exact_words' if job['kind']=='dialogue' else 'nonlexical_screen_only')
                save_json(folder/'local-verification-v2.json',verification)
                if not verified_performance(job,verification):
                    save_json(folder/'final-quality.json',dict(status='rejected',reason='Both local ASR models failed the performance screen',input_fingerprint=inputs['fingerprint']))
                    continue
                if sha in known and known[sha]!=job['id']:
                    save_json(folder/'final-quality.json',dict(status='rejected',reason='Duplicate performance bytes'));continue
                state.complete(job['id'],path,dict(job=job,seed=request['seed'],metrics=metrics,
                               request_sha256=digest(folder/'request-started.json'),
                               original_sha256=digest(folder/'original-float.wav'),input_fingerprint=inputs['fingerprint'],
                               batch_id=request.get('batch_id'),recovered_saved_audio=recovered,transcription=verification,
                               seconds=time.monotonic()-started,qualification='automatic words/nonlexical and audio checks; acting pending'))
                known[sha]=job['id'];validated.add(job['id']);accepted+=1
                counts[job['kind']]+=1
                print('LOCAL_BATCH_ACCEPTED',len(state.data),job['role'],job['age'],job['event'],job['take'],flush=True)
        save_json(DEST/'generation/live.json',dict(recordings=len(state.data),dialogue_candidates=counts['dialogue'],
                  effort_candidates=counts['nonverbal_effort'],phase=args.kind,accepted_this_run=accepted,
                  synthesized_this_run=budget.used,synthesis_limit=budget.limit,elapsed_seconds=time.monotonic()-run_started,
                  attempt_ceiling=args.attempt_ceiling,
                  role=group[0]['role'],age=group[0]['age'],event=group[0]['event'],take=group[0]['take'],full_release=False))
        queue.append(group)
    save_json(DEST/'generation/checkpoint.json',dict(recordings=len(state.data),dialogue_candidates=counts['dialogue'],
              effort_candidates=counts['nonverbal_effort'],required=len(manifest['jobs']),
              synthesized_this_run=budget.used,synthesis_limit=budget.limit,accepted_this_run=accepted,
              attempt_ceiling=args.attempt_ceiling,
              qualified_text_roles=sorted(qualified),nonverbal_qualified=False,acting_qualified=False,
              complete_release=False,status='partial local listening pilot'))
    print('LOCAL_BATCH_FINISHED',len(state.data),'new accepted',accepted,'synthesized',budget.used,flush=True)


if __name__=='__main__':
    from exclusive_job import exclusive_job
    local_guard()
    with exclusive_job('local batch generation'):main()
