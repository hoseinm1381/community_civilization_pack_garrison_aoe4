import json
from pathlib import Path
import tempfile
import unittest


class ClearRetakeTests(unittest.TestCase):
    def test_two_extra_attempts_preserve_original_attempts_and_remain_bounded(self):
        from local_work import attempt_plan
        job=dict(kind='dialogue',text='Tôi vào trú.')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for n in range(1,4):
                folder=root/f'attempt-{n}';folder.mkdir();(folder/'final-quality.json').write_text('{}')
            self.assertEqual(list(attempt_plan(root,3,job,'pinned')),[])
            self.assertEqual([a for a,_,_ in attempt_plan(root,3,job,'pinned',ceiling=5)],[3,4])
            self.assertEqual(list(attempt_plan(root,5,job,'pinned',ceiling=5)),[])
            with self.assertRaises(ValueError):list(attempt_plan(root,5,job,'pinned',ceiling=6))
            self.assertEqual((root/'attempt-1/final-quality.json').read_text(),'{}')

    def test_clear_pause_preserves_all_words_and_never_relaxes_the_word_gate(self):
        from local_work import retake_text,verify_request_text
        from quality import text_matches
        job=dict(kind='dialogue',text='Tôi vào trú.')
        self.assertEqual(retake_text(job,0),job['text'])
        self.assertEqual(retake_text(job,3),'Tôi, vào trú.')
        self.assertTrue(text_matches(job['text'],retake_text(job,4)))
        request=dict(attempt=4,synthesis_text=retake_text(job,3),synthesis_recipe='clear-first-word-pause-v1')
        verify_request_text(request,job)
        request['synthesis_text']='Tôi và chú.'
        with self.assertRaises(RuntimeError):verify_request_text(request,job)

    def test_completed_new_request_payload_is_hash_bound(self):
        from local_inputs import verify_completed_recording
        from local_work import retake_text
        from pipeline import digest
        job=dict(kind='dialogue',text='Có tôi đây.')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);original=root/'original-float.wav';original.write_bytes(b'original')
            request=root/'request-started.json'
            request.write_text(json.dumps(dict(attempt=4,job=job,synthesis_text=retake_text(job,3),synthesis_recipe='clear-first-word-pause-v1')))
            row=dict(path=str(root/'candidate.wav'),metadata=dict(job=job,input_fingerprint='pin',
                 original_sha256=digest(original),request_sha256=digest(request)))
            verify_completed_recording(row,job,'pin')
            request.write_text('{}')
            with self.assertRaises(RuntimeError):verify_completed_recording(row,job,'pin')


if __name__=='__main__':unittest.main()
