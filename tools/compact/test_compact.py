import copy
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collaboration'))
from store import Writer, Reader, load, write_json, file_sha
from compact_export import retain, repack, required_payloads


class CompactTests(unittest.TestCase):
    def test_policy_keeps_editable_sources_and_required_baseline(self):
        self.assertTrue(retain('source/art/authoring/release_010/house.blend'))
        self.assertTrue(retain('external/output/release_083/delivery/final-v2/community_civilization_pack.sga'))
        self.assertTrue(retain('external/output/release_084/local/compressed-v1/abc/attempt-1/audio.ogg'))
        self.assertFalse(retain('external/output/release_084/local/generation/abc/attempt-1/float.wav'))
        self.assertFalse(retain('external/output/release_084/local/generation/abc/attempt-1/request.json'))
        self.assertFalse(retain('external/output/release_083/delivery/final-v1/old.zip'))
        self.assertFalse(retain('external/output/release_084/delivery/final-v1/fresh-readback/a.rgd'))

    def test_raw_repack_preserves_files_deduplicates_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            w = Writer(root/'old', chunk_size=9, pack_size=30)
            for key, data in [('source/a.txt', b'abc'*20), ('source/b.txt', b'abc'*20),
                              ('external/old.wav', b'discard'*20)]:
                w.add(key, data)
            doc = w.finish()
            before = {p.name: file_sha(p) for p in (root/'old').glob('*.zip')}
            compact = repack(root/'old', doc, root/'new', {'source/a.txt','source/b.txt'}, pack_bytes=45)
            r = Reader(root/'new', compact)
            self.assertEqual(r.read('source/a.txt'), b'abc'*20)
            self.assertEqual(r.read('source/b.txt'), b'abc'*20)
            self.assertLess(len(compact['chunks']), len(doc['chunks']))
            r.verify()
            r.close()
            self.assertEqual(before, {p.name: file_sha(p) for p in (root/'old').glob('*.zip')})
            with self.assertRaises(FileExistsError):
                repack(root/'old', doc, root/'new', {'source/a.txt'})

    def test_missing_current_overlay_is_a_hard_error(self):
        doc = {'files': {'source/a.txt': {'sha256':'a'}}}
        with self.assertRaisesRegex(ValueError, 'Missing'):
            required_payloads(doc, {'payload': {'data/a': {'file':'F:/old/output/a','sha256':'b'}}})


if __name__ == '__main__':
    unittest.main()
