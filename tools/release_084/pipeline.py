"""Resumable speech-production primitives. Credentials never enter persisted jobs."""
import array
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import time
import wave


class AudioError(ValueError):
    pass


def guard():
    root=Path(__file__).resolve().parents[2]
    cfg=json.loads((root/'workspace.json').read_text())
    sys.path.insert(0,str(root/'tools'))
    from workspace_support import check_storage
    return check_storage(root,cfg)


def job_key(job, casting):
    data = {"job": job, "casting": casting}
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.new')
    temp.write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    # Windows readers may briefly omit FILE_SHARE_DELETE while polling status.
    # Keep the complete temporary file and retry the atomic rename, never rewrite
    # the destination in place or discard an accepted-audio checkpoint.
    for attempt in range(10):
        try:
            temp.replace(path)
            break
        except PermissionError:
            if attempt == 9: raise
            time.sleep(.05 * (attempt + 1))


def same_recording(a,b):
    fields=['role','age','text','take','direction','casting']
    return all(a.get(k)==b.get(k) for k in fields)


class StateStore:
    def __init__(self, root):
        self.root = Path(root)
        self.file = self.root / 'state.json'
        self.data = json.loads(self.file.read_text()) if self.file.exists() else {}

    def complete(self, key, path, metadata):
        self.data[key] = dict(path=str(Path(path).resolve()), sha256=digest(path), metadata=metadata)
        save_json(self.file, self.data)

    def ready(self, key, job=None):
        row = self.data.get(key)
        if job is not None and (not row or not same_recording(row.get('metadata',{}).get('job',{}),job)):
            return False
        return bool(row and Path(row['path']).is_file() and digest(row['path']) == row['sha256'])


def classify_error(status, body):
    text = json.dumps(body).lower()
    if status == 402 or 'quota_exceeded' in text or 'credit' in text and ('exhaust' in text or 'insufficient' in text):
        return 'credits_exhausted'
    if status == 401:
        return 'authentication'
    if status == 403:
        return 'permission'
    if status == 429:
        return 'daily_quota' if 'per day' in text or 'daily' in text else 'rate_limit'
    return 'transient' if status >= 500 else 'invalid_request'


def ensure_budget(provider, requested, remaining, free_only=True):
    if not free_only:
        raise ValueError('Only existing credits are authorized')
    if requested < 0 or remaining is not None and requested > remaining:
        raise ValueError('Insufficient existing credits')


def choose_jobs(rows, completed, max_attempts):
    seen = set()
    result = []
    for row in rows:
        key = row['id']
        if key not in seen and not completed.get(key) and row.get('attempt', 0) < max_attempts:
            result.append(row)
        seen.add(key)
    return result


def pcm_wav(pcm, rate):
    output = io.BytesIO()
    with wave.open(output, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(pcm)
    return output.getvalue()


def _pcm_statistics(pcm,vectorized=True):
    if not pcm or len(pcm)%2:raise AudioError('Empty or truncated PCM')
    if vectorized:
        try:
            import numpy as np
        except ImportError:
            pass
        else:
            values=np.frombuffer(pcm,dtype='<i2').astype(np.int64)
            # Int64 accumulation is exact for bounded unit-response clips;
            # Python division/sqrt preserves the portable implementation's RMS.
            squares=int(np.dot(values,values));absolute=np.abs(values)
            return math.sqrt(squares/len(values)),int(np.count_nonzero(absolute>=32760)),int(absolute.max())
    values=array.array('h',pcm)
    return math.sqrt(sum(x*x for x in values)/len(values)),sum(abs(x)>=32760 for x in values),max(abs(x) for x in values)


def wav_metrics(data, max_duration=25):
    try:
        with wave.open(io.BytesIO(data), 'rb') as f:
            channels, width, rate, frames = f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()
            pcm = f.readframes(frames)
        if channels != 1 or width != 2 or len(pcm) != frames * 2 or not 8000 <= rate <= 96000:
            raise AudioError('Unsupported or truncated PCM')
        if not pcm:
            raise AudioError('Empty audio')
        rms,clipped,peak = _pcm_statistics(pcm)
        if rms < 12 or clipped > max(2, frames * .0001):
            raise AudioError('Silent or clipped audio')
        duration = frames / rate
        if not .12 <= duration <= max_duration:
            raise AudioError('Implausible unit-response duration')
        return dict(duration=duration, sample_rate=rate, rms=rms, peak=peak, clipped_samples=clipped)
    except (wave.Error, EOFError, ValueError) as e:
        raise AudioError(str(e)) from e


def playback_wav(data, max_duration=25):
    wav_metrics(data,max_duration)
    with wave.open(io.BytesIO(data), 'rb') as f:
        rate = f.getframerate()
        samples = array.array('h', f.readframes(f.getnframes()))
    if rate == 48000:
        return data
    # Linear resampling for exact playback format; provider originals remain intact.
    count = round(len(samples) * 48000 / rate)
    out = array.array('h')
    for i in range(count):
        pos = i * rate / 48000
        low = min(int(pos), len(samples)-1)
        high = min(low+1, len(samples)-1)
        out.append(round(samples[low] + (samples[high]-samples[low])*(pos-low)))
    result = pcm_wav(out.tobytes(), 48000)
    wav_metrics(result,max_duration)
    return result
