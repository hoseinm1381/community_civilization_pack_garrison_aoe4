import array
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pipeline import StateStore,pcm_wav


class ResumeCacheTests(unittest.TestCase):
    def test_saved_wave_is_validated_once_before_skip_and_corruption_is_pending(self):
        from local_work import validated_completed
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'clip.wav'
            path.write_bytes(pcm_wav(array.array('h',(int(1000*math.sin(i*.1)) for i in range(9600))).tobytes(),48000))
            job=dict(id='a',role='CIV_M',age='A1',text='Có.',take='T1',direction='calm',casting={})
            store=StateStore(root);store.complete('a',path,dict(job=job))
            with patch('local_inputs.verify_completed_recording') as proof:
                valid,known=validated_completed(store,{'a':job},'fingerprint')
                self.assertEqual(valid,{'a'});self.assertEqual(known[store.data['a']['sha256']],'a')
                proof.assert_called_once()
                path.write_bytes(b'corrupt playback preserved for original recovery')
                valid,known=validated_completed(store,{'a':job},'fingerprint')
                self.assertEqual(valid,set());self.assertEqual(known,{})


if __name__=='__main__':unittest.main()
