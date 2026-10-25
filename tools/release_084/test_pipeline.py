"""Production safety regressions; no network or charged requests."""
import io
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from pipeline import AudioError, StateStore, classify_error, job_key, pcm_wav, wav_metrics, choose_jobs, ensure_budget


class PipelineTests(unittest.TestCase):
    def test_keys_include_actor_age_delivery_and_take(self):
        job = dict(profile='ARCHER', age='A2', event='select', text='Có tôi đây.', take='T1', direction='calm')
        casting = dict(provider='google', model='model', voice='voice')
        first = job_key(job, casting)
        for field, value in [('take', 'T2'), ('age', 'A3'), ('direction', 'urgent'), ('profile', 'SCOUT')]:
            self.assertNotEqual(first, job_key(dict(job, **{field: value}), casting))
        self.assertNotEqual(first, job_key(job, dict(casting, voice='another')))

    def test_resume_rechecks_hash_instead_of_trusting_status(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / 'clip.wav'
            p.write_bytes(b'original')
            state = StateStore(root)
            state.complete('job', p, dict(provider='google'))
            self.assertTrue(state.ready('job'))
            self.assertFalse(StateStore(root).ready('unknown'))
            p.write_bytes(b'corrupt')
            self.assertFalse(StateStore(root).ready('job'))

    def test_resume_rejects_different_casting(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'clip.wav';p.write_bytes(b'audio')
            job=dict(role='MONK',age='A3',text='hello',take='T1',direction='calm',casting=dict(provider='inworld',voice='a'))
            state=StateStore(folder);state.complete('x',p,dict(job=job))
            self.assertTrue(state.ready('x',job))
            self.assertFalse(state.ready('x',dict(job,casting=dict(provider='elevenlabs',voice='b'))))

    def test_error_classification_never_retries_auth_or_quota_blindly(self):
        self.assertEqual(classify_error(401, {}), 'authentication')
        self.assertEqual(classify_error(401, {'detail':{'code':'quota_exceeded'}}), 'credits_exhausted')
        self.assertEqual(classify_error(403, {}), 'permission')
        self.assertEqual(classify_error(429, {'error': {'message': 'requests per day exhausted'}}), 'daily_quota')
        self.assertEqual(classify_error(429, {'detail': {'status': 'quota_exceeded'}}), 'credits_exhausted')
        self.assertEqual(classify_error(429, {}), 'rate_limit')
        self.assertEqual(classify_error(503, {}), 'transient')

    def test_budget_cannot_overrun_remaining_characters(self):
        ensure_budget('elevenlabs', 10, 10)
        with self.assertRaises(ValueError):
            ensure_budget('elevenlabs', 11, 10)
        with self.assertRaises(ValueError):
            ensure_budget('google', 1, None, free_only=False)

    def test_detects_silence_clipping_and_wrong_format(self):
        with self.assertRaises(AudioError):
            wav_metrics(pcm_wav(b'\0\0' * 24000, 24000))
        with self.assertRaises(AudioError):
            wav_metrics(pcm_wav(struct.pack('<h', 32767) * 24000, 24000))
        with self.assertRaises(AudioError):
            wav_metrics(b'not a wave')

    def test_valid_speech_like_signal(self):
        pcm = b''.join(struct.pack('<h', int(3000 * math.sin(i * .1))) for i in range(24000))
        data = pcm_wav(pcm, 24000)
        result = wav_metrics(data)
        self.assertAlmostEqual(result['duration'], 1)
        self.assertEqual(result['sample_rate'], 24000)
        self.assertEqual(result['clipped_samples'], 0)

    def test_bounded_retakes_and_deduplication(self):
        rows = [dict(id='a', attempt=0), dict(id='b', attempt=3), dict(id='a', attempt=0)]
        self.assertEqual([r['id'] for r in choose_jobs(rows, {'a': True}, 3)], [])
        self.assertEqual([r['id'] for r in choose_jobs(rows, {}, 3)], ['a'])


if __name__ == '__main__':
    unittest.main()
