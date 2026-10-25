"""Offline GPU audition spike. Outputs candidates, never a release-ready bank."""
import argparse
import io
import json
import logging
import os
from pathlib import Path
import random
import time

from local_bank import VOICES, MODEL_REVISION, SDK_REVISION, local_manifest, take_seed, local_guard as guard
from pipeline import save_json, wav_metrics, digest, StateStore, AudioError
from providers import OUT
from local_inputs import verify_inputs
from local_work import attempt_plan, render_attempt, WorkBudget

RUNTIME = Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/tool-cache/local-voices-084')
DEST = OUT / 'local'


def main():
    guard()
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--max-attempts', type=int)
    args = parser.parse_args()
    source = json.loads((OUT / 'recording-manifest.json').read_text())
    manifest_path = DEST / 'recording-manifest.json'
    existing = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    selected = {j['role']: j['casting']['voice'] for j in existing['jobs']} if existing else None
    manifest = local_manifest(source, selected)
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise RuntimeError('Local recipe changed; preserve existing bank and use a new revision path')
    save_json(manifest_path, manifest)
    presets = json.loads((RUNTIME / 'VieNeu-TTS/src/vieneu/assets/voices_v3_turbo.json').read_text(encoding='utf-8'))['presets']
    for role, name in VOICES.items():
        if presets[name]['region'] != 'Bắc': raise RuntimeError('Non-Northern preset in local cast: ' + role)
    save_json(DEST / 'casting-candidates.json', dict(roles=VOICES, sdk=SDK_REVISION, model=MODEL_REVISION,
              status='audition candidates; expressive delivery not qualified',
              voices={name: {k: presets[name].get(k) for k in ['description', 'gender', 'region', 'style']} for name in set(VOICES.values())}))
    if args.prepare_only:
        print('Prepared isolated local manifest:', len(manifest['jobs']), flush=True)
        return
    inputs = verify_inputs()
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import numpy as np
    import soundfile as sf
    import torch
    from vieneu import Vieneu
    if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable; refusing an unnoticed CPU fallback')
    save_json(DEST / 'hardware.json', dict(torch=torch.__version__, cuda=torch.version.cuda,
              gpu=torch.cuda.get_device_name(0), sdk=SDK_REVISION, model=MODEL_REVISION))
    print('Loading local TTS on', torch.cuda.get_device_name(0), flush=True)
    logging.basicConfig(level=logging.INFO)
    started = time.monotonic()
    tts = Vieneu(backbone_repo=str(RUNTIME / 'models/vieneu'), moss_tokenizer=str(RUNTIME / 'models/moss'),
                 device='cuda', backend='pytorch', max_batch_size=1, max_streams=1, babble_retries=0)
    save_json(DEST / 'model-loaded.json', dict(seconds=time.monotonic()-started, backend=tts.backend, sample_rate=tts.sample_rate))
    state = StateStore(DEST / 'auditions')
    attempts_path = DEST / 'auditions/attempts.json'
    attempts = json.loads(attempts_path.read_text()) if attempts_path.exists() else {}
    budget = WorkBudget(args.max_attempts if args.max_attempts is not None else args.limit*3)
    legacy_path = DEST / 'legacy-pilot-input-certification.json'
    legacy = json.loads(legacy_path.read_text()).get('auditions', {}) if legacy_path.exists() else {}
    contexts = [('calm', 'Có tôi đây.'), ('urgent', 'Quân địch tới! Giữ vững hàng ngũ!'),
                ('quiet', 'Khẽ thôi, có quân địch gần đây.'), ('effort-probe', 'Hự!')]
    count = 0
    for role, voice in VOICES.items():
        for context, text in contexts:
            for take in range(3):
                key = f'{role}-{context}-T{take+1}'
                if state.ready(key):
                    row = state.data[key]; meta = row['metadata']
                    known = meta.get('input_fingerprint') == inputs['fingerprint']
                    certified = legacy.get(key, {}).get('fingerprint') == inputs['fingerprint'] and legacy.get(key, {}).get('sha256') == row['sha256']
                    if not (known or certified) or meta.get('voice') != voice or meta.get('text') != text:
                        raise RuntimeError('Saved audition recipe or inputs changed: ' + key)
                    continue
                if count >= args.limit: return
                recipe = dict(role=role, voice=voice, context=context, take=take+1, text=text)
                root = DEST / 'auditions' / role / context / f'T{take+1}'
                for attempt, folder, recovered in attempt_plan(root, attempts.get(key, 0), recipe, inputs['fingerprint']):
                    if not recovered and not budget.reserve(): break
                    folder.mkdir(parents=True, exist_ok=True)
                    seed = take_seed(key, attempt)
                    started = time.monotonic()
                    if not recovered:
                        attempts[key] = attempt+1; save_json(attempts_path, attempts)
                        save_json(folder/'request-started.json', dict(job=recipe, seed=seed, input_fingerprint=inputs['fingerprint']))
                    try:
                        path, metrics = render_attempt(tts, text, voice, [.75,.82,.9][take], folder, recovered, seed)
                    except AudioError as error:
                        save_json(folder/'final-quality.json', dict(status='rejected',reason=str(error)))
                        continue
                    metadata = dict(**recipe, seed=seed, input_fingerprint=inputs['fingerprint'],
                                    original_sha256=digest(folder/'original-float.wav'),
                                    temperature=[.75,.82,.9][take], metrics=metrics, seconds=time.monotonic()-started,
                                    qualification='candidate; local ASR and listening pending',
                                    delivery_control='Text and preset reference only; deprecated style ignored')
                    save_json(folder/'receipt.json', metadata)
                    state.complete(key, path, metadata)
                    print('CANDIDATE', key, round(metrics['duration'],2), round(metadata['seconds'],2), flush=True)
                    count += 1
                    break
    save_json(DEST / 'auditions/finished.json', dict(candidates=len(state.data), status='unqualified listening pilot'))


if __name__ == '__main__':
    from exclusive_job import exclusive_job
    guard()
    with exclusive_job('local auditions'):main()
