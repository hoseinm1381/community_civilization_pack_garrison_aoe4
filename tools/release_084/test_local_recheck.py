import unittest
import json
import tempfile
from pathlib import Path
from local_efforts import verified_performance
from pipeline import digest


class RecheckTests(unittest.TestCase):
    def test_additional_unprompted_checker_can_recover_exact_dialogue(self):
        job=dict(kind='dialogue',text='Có tôi đây.')
        proof=dict(expected=job['text'],prompted=False,phowhisper='Sai.',whisper='Khác.',phowhisper_medium='Có tôi đây.')
        self.assertTrue(verified_performance(job,proof))
        proof['prompted']=True
        self.assertFalse(verified_performance(job,proof))

    def test_additional_checker_does_not_relax_efforts(self):
        job=dict(kind='nonverbal_effort',text='Hự!')
        proof=dict(expected=job['text'],prompted=False,phowhisper='',whisper='',phowhisper_medium='Hự!')
        self.assertFalse(verified_performance(job,proof))

    def test_saved_medium_evidence_is_required_and_bound_to_state(self):
        from local_inputs import verify_recheck_evidence
        from download_local_models import MODELS
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);audio=folder/'candidate.wav';audio.write_bytes(b'audio')
            prior=folder/'local-verification-v2.json';prior.write_text('{}')
            transcript=dict(phowhisper_medium='Có tôi đây.')
            repo,revision=MODELS['phowhisper-medium']
            proof=dict(sha256=digest(audio),previous_sha256=digest(prior),transcription=transcript,
                       model_receipt=dict(repo=repo,revision=revision))
            sidecar=folder/'local-recheck-medium.json';sidecar.write_text(json.dumps(proof))
            row=dict(path=str(audio),sha256=digest(audio),metadata=dict(transcription=transcript,recheck_sha256=digest(sidecar)))
            verify_recheck_evidence(row)
            prior.write_text('{"changed":true}')
            with self.assertRaises(RuntimeError):verify_recheck_evidence(row)


if __name__=='__main__':unittest.main()
