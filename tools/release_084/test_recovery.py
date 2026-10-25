import json,tempfile,unittest
import array,math
from pipeline import pcm_wav,StateStore
from pathlib import Path
from unittest.mock import patch
import salvage
class RecoveryTests(unittest.TestCase):
    def test_invalid_original_is_preserved_without_blocking_other_jobs(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);batch=root/'generation/batch-masters/a/attempt-1';batch.mkdir(parents=True)
            job=dict(id='x',role='CROSSBOW',age='A3',text='hello',take='T1',direction='calm',casting=dict(provider='elevenlabs',model='m',voice='v'))
            (root/'recording-manifest.json').write_text(json.dumps(dict(jobs=[job])))
            (batch/'original.wav').write_bytes(b'broken original')
            (batch/'transcript.json').write_text('{}');(batch/'jobs.json').write_text(json.dumps([job]))
            with patch('salvage.OUT',root),patch('salvage.guard'):
                salvage.main()
            self.assertEqual((batch/'original.wav').read_bytes(),b'broken original')
            self.assertTrue((batch/'invalid-original.json').exists())
    def test_bad_segment_does_not_block_valid_paid_phrase(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);batch=root/'generation/batch-masters/a/attempt-1';batch.mkdir(parents=True)
            base=dict(role='CROSSBOW',age='A3',take='T1',direction='calm',casting=dict(provider='elevenlabs',model='m',voice='v'))
            jobs=[dict(base,id='a',text='one'),dict(base,id='b',text='two')]
            (root/'recording-manifest.json').write_text(json.dumps(dict(jobs=jobs)))
            (batch/'jobs.json').write_text(json.dumps(jobs))
            samples=array.array('h',(int(2000*math.sin(i*.1)) for i in range(96000)))
            for i in range(12000,12003):samples[i]=32767
            (batch/'original.wav').write_bytes(pcm_wav(samples.tobytes(),48000))
            transcript=dict(text='one two',words=[dict(type='word',text='one',start=.2,end=.35),dict(type='word',text='two',start=1,end=1.2)])
            (batch/'transcript.json').write_text(json.dumps(transcript))
            with patch('salvage.OUT',root),patch('salvage.guard'):salvage.main()
            state=StateStore(root/'generation')
            self.assertFalse(state.ready('a',jobs[0]))
            self.assertTrue(state.ready('b',jobs[1]))

if __name__=='__main__':unittest.main()
