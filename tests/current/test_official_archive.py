from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from official_archive import members
import official_archive


class ArchiveReaderTests(unittest.TestCase):
    def test_explicit_build_editor_override_wins_over_local_configuration(self):
        with patch.object(official_archive,'configuration',return_value={'editor_root':'C:/old'}):
            with patch.dict('os.environ',{'AOE4_EDITOR_ROOT':'D:/selected'},clear=True):
                self.assertEqual(official_archive.archive_path(),Path('D:/selected/cardinal/archives/ReferenceAttributes.sga'))

    def test_reads_uncompressed_v10_member_and_rejects_wrong_version(self):
        payload=b'<instance version="6" />'
        directory=b'instances\\ebps\\example'
        names=directory+b'\0unit.xml\0'
        header=struct.pack('<8I',0,0,44,1,64,1,94,len(names))+b'\0'*12
        header+=struct.pack('<5I',0,0,0,0,1)
        header+=struct.pack('<2IQ2I2BI',len(directory)+1,0,0,len(payload),len(payload),0,0,0)+names
        meta=struct.pack('<128sQI QI 2I256s',b'test',428+len(payload),len(header),428,len(payload),0,1,b'\0'*256)
        with tempfile.TemporaryDirectory() as temporary:
            file=Path(temporary)/'reference.sga'
            file.write_bytes(b'_ARCHIVE\x0a\x00\x00\x00'+meta+payload+header)
            self.assertEqual(list(members(file)),[('instances\\ebps\\example\\unit.xml',payload)])
            file.write_bytes(b'wrong archive')
            with self.assertRaises(ValueError):list(members(file))


if __name__=='__main__':unittest.main()
