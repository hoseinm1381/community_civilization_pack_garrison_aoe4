"""Immutable attempt planning and explicit per-run synthesis budgets."""
import json
import hashlib
import io
from pathlib import Path
import random
import re
from collections import defaultdict
from pipeline import digest, save_json, wav_metrics, AudioError


def validated_completed(store,jobs,fingerprint,legacy=None):
    """One complete resume audit per process; exclusive writer lock owns the run."""
    from local_inputs import verify_completed_recording
    valid=set();known={}
    for index,(key,row) in enumerate(store.data.items(),1):
        if key not in jobs:raise RuntimeError('Completed recording is outside the manifest')
        if not store.ready(key,jobs[key]):continue
        verify_completed_recording(row,jobs[key],fingerprint,legacy)
        wav_metrics(Path(row['path']).read_bytes())
        if row['sha256'] in known:raise RuntimeError('Duplicate completed performance')
        valid.add(key);known[row['sha256']]=key
        if index%500==0:print('RESUME_RECORDINGS_RECHECKED',index,'of',len(store.data),flush=True)
    return valid,known


class WorkBudget:
    def __init__(self, limit):
        if limit < 0: raise ValueError('Negative synthesis limit')
        self.limit = limit
        self.used = 0

    def reserve(self):
        if self.used >= self.limit: return False
        self.used += 1
        return True


def retake_text(job,attempt):
    from local_bank import performance_text
    from quality import text_matches
    text=performance_text(job)
    if not 0<=attempt<5:raise ValueError('Local attempts are bounded at five')
    if attempt>=3:
        if job['kind']!='dialogue':raise ValueError('Extra retakes are spoken-only')
        text=re.sub(r'^(\S+?)(?<![,;:!?])\s+',r'\1, ',text,count=1)
        if not text_matches(job['text'],text):raise RuntimeError('Clarity punctuation changed approved words')
    return text


def verify_request_text(request,job):
    attempt=request.get('attempt',1)-1
    if attempt>=3 or 'synthesis_text' in request:
        if (request.get('synthesis_text')!=retake_text(job,attempt) or
            request.get('synthesis_recipe')!=('clear-first-word-pause-v1' if attempt>=3 else 'original-input-v1')):
            raise RuntimeError('Saved synthesis input/recipe differs')


def attempt_plan(root, recorded_count, job, fingerprint, legacy=None,ceiling=3):
    if ceiling not in (3,5):raise ValueError('Local attempt ceiling must be three or five')
    root = Path(root)
    for attempt in range(ceiling):
        folder = root / f'attempt-{attempt+1}'
        request_path = folder / 'request-started.json'
        original = folder / 'original-float.wav'
        if (folder / 'final-quality.json').exists(): continue
        if request_path.exists():
            request = json.loads(request_path.read_text())
            if request.get('job') != job: raise RuntimeError('Saved request recipe changed: ' + str(folder))
            verify_request_text(request,job)
            attestation = (legacy or {}).get(str(folder.resolve()), {})
            known = request.get('input_fingerprint') == fingerprint
            certified = attestation.get('fingerprint') == fingerprint and attestation.get('request_sha256') == digest(request_path)
            if not known and not certified: raise RuntimeError('Saved request input identity is unverified: ' + str(folder))
            if original.is_file():
                receipt = folder / 'original.json'
                expected = json.loads(receipt.read_text())['sha256'] if receipt.exists() else attestation.get('original_sha256')
                if expected and digest(original) != expected: raise RuntimeError('Saved original audio changed: ' + str(folder))
                yield attempt, folder, True
            continue
        if original.exists(): raise RuntimeError('Unattributed saved original; refusing overwrite: ' + str(folder))
        if attempt >= recorded_count:
            yield attempt, folder, False


def validate_saved_wave(path):
    import struct
    data=Path(path).read_bytes()
    if len(data)<12 or data[:4]!=b'RIFF' or data[8:12]!=b'WAVE' or struct.unpack_from('<I',data,4)[0]+8!=len(data):
        raise AudioError('Corrupt or truncated original WAV container')
    offset=12
    while offset<len(data):
        if offset+8>len(data):raise AudioError('Truncated original WAV chunk')
        size=struct.unpack_from('<I',data,offset+4)[0]
        offset+=8+size+(size%2)
        if offset>len(data):raise AudioError('Truncated original WAV payload')


def render_attempt(tts, text, voice, temperature, folder, recovered, seed):
    import numpy as np
    import soundfile as sf
    import torch
    original = folder / 'original-float.wav'
    if recovered:
        validate_saved_wave(original)
        try: wav, rate = sf.read(original, dtype='float32')
        except sf.SoundFileError as error: raise AudioError('Corrupt saved original: '+str(error)) from error
    else:
        if original.exists(): raise RuntimeError('Refusing to overwrite an original recording')
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        wav = np.asarray(tts.infer(text, voice=voice, temperature=temperature, max_new_frames=300), dtype=np.float32)
        rate = tts.sample_rate
        sf.write(original, wav, rate, subtype='FLOAT')
        save_json(folder / 'original.json', dict(sha256=digest(original)))
    if rate != 48000 or wav.ndim != 1 or not np.isfinite(wav).all() or np.max(np.abs(wav), initial=0) >= 1:
        raise AudioError('Unsupported, nonfinite or clipped float output')
    buffer = io.BytesIO()
    sf.write(buffer, wav, rate, format='WAV', subtype='PCM_16')
    data = buffer.getvalue()
    metrics = wav_metrics(data)
    path = folder / 'candidate.wav'
    if path.exists() and path.read_bytes() != data:
        path = folder / ('candidate-recovered-' + hashlib.sha256(data).hexdigest() + '.wav')
    if not path.exists(): path.write_bytes(data)
    if path.read_bytes() != data: raise RuntimeError('Saved playback bytes changed')
    return path, metrics


def performance_groups(jobs):
    groups = defaultdict(list)
    for job in jobs:
        groups[(job['role'],job['age'],job['event'],job['take'],json.dumps(job['casting'],sort_keys=True))].append(job)
    return list(groups.values())
