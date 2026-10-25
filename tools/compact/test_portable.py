import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collaboration'))
from store import Writer, Reader
from portable import AliasReader, rebase_text, check_member, overlay_map


class PortableTests(unittest.TestCase):
    def test_evidence_alias_reads_exact_retained_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Writer(Path(tmp)/'store')
            w.add('external/kept/audio.ogg', b'OggS-test')
            doc = w.finish()
            doc['aliases'] = {'external/old/audio.ogg':'external/kept/audio.ogg'}
            r = AliasReader(Path(tmp)/'store', doc)
            from unittest.mock import patch
            with patch('store.safe_path',side_effect=AssertionError('Virtual read must not probe physical paths')):
                self.assertEqual(r.read('external/old/audio.ogg'), b'OggS-test')
                with self.assertRaises(ValueError):
                    r.read('external/../bad')
            r.close()

    def test_relocation_is_case_insensitive_and_handles_json_escaped_paths(self):
        origins = [('E:/owner/source','G:/new/source'), ('F:/owner/external','H:/new/external')]
        self.assertEqual(rebase_text('E:\\OWNER\\source\\art\\a.blend', origins), 'G:/new/source/art/a.blend')
        self.assertEqual(rebase_text('"F:\\\\owner\\\\external\\\\models"', origins), '"H:/new/external/models"')

    def test_overlay_manifest_rejects_escape_and_ambiguous_alias(self):
        for name in ('../foo', '/absolute', 'attrib/../a', 'data\\a', 'C:/a'):
            with self.assertRaises(ValueError):
                check_member(name)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'a').write_bytes(b'replacement')
            self.assertEqual(overlay_map({'attrib/a.rgd':'a'}, root)['attrib'][0][0], 'attrib/a.rgd')


if __name__ == '__main__':
    unittest.main()
