import unittest
from local_compress import validate_decode,LIMIT
from pipeline import AudioError


class CompressionTests(unittest.TestCase):
    def test_truncated_or_resampled_exports_fail(self):
        source=dict(duration=1.2,rms=100,sample_rate=48000)
        validate_decode(source,dict(source,duration=1.199,rms=99))
        for changes in [dict(duration=.8),dict(sample_rate=24000),dict(rms=20)]:
            with self.assertRaises(AudioError):validate_decode(source,dict(source,**changes))

    def test_user_limit_is_decimal_400_mb(self):
        self.assertEqual(LIMIT,400_000_000)


if __name__=='__main__':unittest.main()
