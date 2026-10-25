import math
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from pipeline import pcm_wav
from providers import decode_flac


class TransportTests(unittest.TestCase):
    def test_flac_roundtrip_keeps_every_pcm_sample(self):
        pcm=b''.join(struct.pack('<h',int(5000*math.sin(i*.13))) for i in range(12000))
        wave=pcm_wav(pcm,48000)
        ffmpeg='C:/Users/RS/AppData/Local/Programs/Python/Python313/Scripts/ffmpeg.exe'
        compressed=subprocess.run([ffmpeg,'-v','error','-i','pipe:0','-f','flac','pipe:1'],input=wave,
                                  capture_output=True,check=True).stdout
        self.assertTrue(compressed.startswith(b'fLaC'))
        self.assertEqual(decode_flac(compressed),wave)


if __name__=='__main__':unittest.main()
