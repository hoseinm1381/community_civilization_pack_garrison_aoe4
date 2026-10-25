import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from pipeline import pcm_wav
import math, struct
from batching import aligned_ranges, group_jobs, partial_ranges, account_request, recover_lossless, anchored_ranges, affordable_group


class BatchingTests(unittest.TestCase):
    def test_attempt_ledger_survives_interruption_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);ledger=root/'ledger.json';attempts={}
            account_request(root/'batch1',[dict(id='a'),dict(id='b')],attempts,ledger)
            stale={}
            account_request(root/'batch1',[dict(id='a'),dict(id='b')],stale,ledger)
            self.assertEqual(stale,dict(a=1,b=1))
            account_request(root/'batch2',[dict(id='b')],stale,ledger)
            self.assertEqual(stale['b'],2)

    def test_retained_flac_decodes_without_synthesis(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'provider.flac').write_bytes(b'fLaCfixture')
            audio=pcm_wav(b''.join(struct.pack('<h',int(2000*math.sin(i*.1))) for i in range(48000)),48000)
            with patch('batching.decode_flac',return_value=audio) as decode:
                self.assertTrue(recover_lossless(root))
                self.assertFalse(recover_lossless(root))
                decode.assert_called_once()
            self.assertEqual((root/'original.wav').read_bytes(),audio)

    def test_anchors_reject_embedded_ambiguous_and_reordered_speech(self):
        def transcript(items):return dict(words=[dict(type='word',text=t,start=a,end=b) for t,a,b in items])
        job=[dict(id='a',text='go now')]
        embedded=transcript([('not',0,.2),('go',.25,.4),('now',.45,.6),('please',.65,.8)])
        self.assertFalse(anchored_ranges(job,embedded,1))
        duplicate=transcript([('go',0,.1),('now',.2,.3),('go',1,1.1),('now',1.2,1.3)])
        self.assertFalse(anchored_ranges(job,duplicate,2))
        multi=transcript([('not go',0,.2),('now',.3,.5)])
        self.assertFalse(anchored_ranges(job,multi,1))
        reverse=transcript([('two',0,.2),('one',1,1.2)])
        self.assertFalse(anchored_ranges([dict(id='a',text='one'),dict(id='b',text='two')],reverse,2))
        isolated=transcript([('wrong',0,.2),('go',.7,.9),('now',1,1.2)])
        self.assertEqual(set(anchored_ranges(job,isolated,2)),{'a'})
        invalid=transcript([('go',.5,.6),('now',.4,.8)])
        self.assertFalse(anchored_ranges(job,invalid,1))

    def test_last_budget_batch_is_reduced_and_reserves_qa(self):
        jobs=[dict(text='A short phrase.',direction='calm') for _ in range(6)]
        group=affordable_group(jobs,100)
        self.assertGreater(len(group),0);self.assertLess(len(group),6)
        from providers import eleven_payload
        self.assertLessEqual(len(eleven_payload(' [long pause] '.join(j['text'] for j in group),'calm'))+12*len(group),100)

    def test_three_takes_are_separate_requests(self):
        jobs=[dict(id=str(i)+t,role='GUNNER',age='A4',event='select',take=t,phrase_number=i,direction='calm')
              for t in ['T1','T2','T3'] for i in range(1,7)]
        batches=group_jobs(jobs)
        self.assertEqual(len(batches),3)
        self.assertTrue(all(len({j['take'] for j in batch})==1 for batch in batches))

    def test_alignment_requires_exact_text_and_nonoverlapping_boundaries(self):
        jobs=[dict(text='Có tôi.'),dict(text='Đi ngay.')]
        transcript=dict(text='Có tôi. Đi ngay.',words=[dict(type='word',text=w,start=a,end=b) for w,a,b in
            [('Có',.1,.2),('tôi.',.3,.5),('Đi',1,1.1),('ngay.',1.2,1.4)]])
        ranges=aligned_ranges(jobs,transcript,1.6)
        self.assertEqual(len(ranges),2)
        self.assertLessEqual(ranges[0][1],ranges[1][0])
        transcript['text']='Có tôi. Đi.'
        with self.assertRaises(ValueError):aligned_ranges(jobs,transcript,1.6)

    def test_safe_pause_salvage_does_not_accept_incorrect_phrase(self):
        jobs=[dict(text='Có tôi.',id='a'),dict(text='Đi ngay.',id='b')]
        transcript=dict(text='Có tôi. Đi.',words=[dict(type='word',text=w,start=a,end=b) for w,a,b in
            [('Có',.1,.2),('tôi.',.3,.5),('Đi',1.5,1.7)]])
        ranges=partial_ranges(jobs,transcript,2)
        self.assertEqual(set(ranges),{'a'})


if __name__=='__main__':unittest.main()
