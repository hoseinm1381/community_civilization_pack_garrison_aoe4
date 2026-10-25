import array
import math
import unittest
from unittest.mock import patch


class PCMStatisticsTests(unittest.TestCase):
    def test_vectorized_and_portable_statistics_match_exactly_including_negative_peak(self):
        from pipeline import _pcm_statistics
        values=array.array('h',(int(2500*math.sin(i*.173)) for i in range(48000)))
        values[1]=-32768;values[2]=32767;values[3]=32759
        pcm=values.tobytes()
        expected=_pcm_statistics(pcm,vectorized=False)
        self.assertEqual(expected[1:],(2,32768))
        self.assertEqual(_pcm_statistics(pcm),expected)
        with patch.dict('sys.modules',{'numpy':None}):self.assertEqual(_pcm_statistics(pcm),expected)

    def test_optimized_path_keeps_silence_clipping_and_truncation_rejection(self):
        from pipeline import pcm_wav,wav_metrics,AudioError
        silent=pcm_wav(b'\0\0'*9600,48000)
        clipped=pcm_wav(array.array('h',[32767]*9600).tobytes(),48000)
        valid=pcm_wav(array.array('h',(int(1000*math.sin(i*.1)) for i in range(9600))).tobytes(),48000)
        for raw in [silent,clipped,valid[:-2]]:
            with self.assertRaises(AudioError):wav_metrics(raw)
        self.assertEqual(wav_metrics(valid)['duration'],.2)


if __name__=='__main__':unittest.main()
