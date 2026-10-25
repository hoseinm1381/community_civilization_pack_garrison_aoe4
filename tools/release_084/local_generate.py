"""Generate separately checked dialogue candidates after the local audition text gate."""
import argparse
from collections import defaultdict, deque
import json
import os
from pathlib import Path
import random
import time
from itertools import zip_longest
from local_audition import DEST, RUNTIME
from local_bank import take_seed, synthesis_text, actor_qualified_roles, local_guard as guard
from local_check import LocalASR
from pipeline import StateStore, digest, save_json, wav_metrics, AudioError
from quality import text_matches
from local_inputs import verify_inputs, validated_audition_results, verify_completed_recording
from local_work import attempt_plan, render_attempt, WorkBudget


def main():
    guard()
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--max-attempts', type=int)
    args = parser.parse_args()
    manifest = json.loads((DEST / 'recording-manifest.json').read_text())
    inputs = verify_inputs(('vieneu', 'moss', 'whisper', 'phowhisper'))
    audition_results = json.loads((DEST / 'auditions/local-asr.json').read_text())
    voices = {j['role']: j['casting']['voice'] for j in manifest['jobs']}
    legacy_path = DEST / 'legacy-pilot-input-certification.json'
    legacy = json.loads(legacy_path.read_text()) if legacy_path.exists() else {}
    audition_results = validated_audition_results(audition_results, StateStore(DEST / 'auditions'),
                                                voices, inputs['fingerprint'], legacy.get('auditions'))
    qualified = actor_qualified_roles(audition_results, voices)
    if not qualified: raise RuntimeError('No local role passed the audition text gate')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import numpy as np
    import soundfile as sf
    import torch
    from vieneu import Vieneu
    if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable')
    tts = Vieneu(backbone_repo=str(RUNTIME / 'models/vieneu'), moss_tokenizer=str(RUNTIME / 'models/moss'),
                 device='cuda', backend='pytorch', max_batch_size=1, max_streams=1, babble_retries=0)
    checker = LocalASR('phowhisper')
    backup_checker = LocalASR('whisper')
    budget = WorkBudget(args.max_attempts if args.max_attempts is not None else args.limit * 3)
    state = StateStore(DEST / 'generation')
    attempts_file = DEST / 'generation/attempts.json'
    attempts = json.loads(attempts_file.read_text()) if attempts_file.exists() else {}
    known_hashes = {r['sha256']: key for key, r in state.data.items() if state.ready(key)}
    pools = defaultdict(deque)
    for job in manifest['jobs']:
        if job['kind'] == 'dialogue' and job['role'] in qualified:
            pools[(job['role'], job['age'], job['event'])].append(job)
    by_role = defaultdict(list)
    for key, pool in pools.items(): by_role[key[0]].append(pool)
    queue = deque(pool for group in zip_longest(*by_role.values()) for pool in group if pool is not None)
    count = 0
    while queue and count < args.limit:
        if (DEST / 'generation/STOP').exists():
            print('Local cooperative stop acknowledged', flush=True); break
        pool = queue.popleft(); job = pool.popleft()
        if pool: queue.append(pool)
        key = job['id']
        if state.ready(key, job):
            verify_completed_recording(state.data[key], job, inputs['fingerprint'], legacy.get('generation_attempts'))
            wav_metrics(Path(state.data[key]['path']).read_bytes())
            continue
        for attempt, folder, recovered in attempt_plan(DEST / 'generation' / key, attempts.get(key, 0), job,
                                                       inputs['fingerprint'], legacy.get('generation_attempts')):
            if not recovered and not budget.reserve(): break
            folder.mkdir(parents=True, exist_ok=True)
            seed = json.loads((folder/'request-started.json').read_text())['seed'] if recovered else take_seed(key, attempt)
            started = time.monotonic()
            if not recovered:
                attempts[key] = attempt+1
                save_json(attempts_file, attempts)
                save_json(folder / 'request-started.json', dict(job=job, seed=seed, attempt=attempt+1,
                          input_fingerprint=inputs['fingerprint'], backend='local CUDA; no APIs'))
            try:
                path, metrics = render_attempt(tts, synthesis_text(job), job['casting']['voice'],
                                 {'T1':.75,'T2':.82,'T3':.9}[job['take']], folder, recovered, seed)
                sha = digest(path)
                if sha in known_hashes and known_hashes[sha] != key: raise AudioError('Duplicate performance bytes')
                actual = checker.transcribe(path)
                verification = dict(phowhisper=actual, expected=job['text'], prompted=False)
                if not text_matches(job['text'], actual):
                    verification['whisper'] = backup_checker.transcribe(path)
                save_json(folder / 'local-verification-v2.json', verification)
                if not any(text_matches(job['text'], v) for k,v in verification.items() if k in ['phowhisper','whisper']):
                    raise AudioError('Both local ASR models failed exact words')
            except AudioError as error:
                save_json(folder / 'final-quality.json', dict(status='rejected', reason=str(error), seed=seed,
                          input_fingerprint=inputs['fingerprint']))
                print('REJECTED', key, attempt+1, str(error), flush=True)
                continue
            state.complete(key, path, dict(job=job, seed=seed, metrics=metrics, seconds=time.monotonic()-started,
                           original_sha256=digest(folder / 'original-float.wav'),
                           input_fingerprint=inputs['fingerprint'], recovered_saved_audio=recovered,
                           transcription=verification, qualification='automatic words/audio pass; acting and native-speaker approval pending'))
            known_hashes[sha] = key
            print('LOCAL_DIALOGUE', len(state.data), job['role'], job['age'], job['event'], job['take'], flush=True)
            count += 1
            break
    save_json(DEST / 'generation/checkpoint.json', dict(dialogue_candidates=len(state.data), required=len(manifest['jobs']),
              synthesized_this_run=budget.used, synthesis_limit=budget.limit,
              qualified_text_roles=sorted(qualified), nonverbal_qualified=False, acting_qualified=False,
              complete_release=False, status='partial local listening pilot'))


if __name__ == '__main__':
    from exclusive_job import exclusive_job
    guard()
    with exclusive_job('local generation'):main()
