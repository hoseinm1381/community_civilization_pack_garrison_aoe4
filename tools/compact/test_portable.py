import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collaboration'))
from store import Writer, Reader
from portable import AliasReader, rebase_text, check_member, overlay_map, load_index


class PortableTests(unittest.TestCase):
    def test_small_update_layer_keeps_base_and_overrides_current_source(self):
        from store import write_json, load
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = dict(files={'source/a':{'old':True}},chunks={'old':{}},packs={'base.zip':{}})
            write_json(root/'base.json', base)
            update = dict(base_index='base.json',files={'source/a':{'new':True}},
                          chunks={'new':{}},packs={'delta.zip':{}},milestone={'version':'0.8.7'})
            write_json(root/'update.json', update)
            merged = load_index(root/'update.json')
            self.assertEqual(merged['files']['source/a'], {'new':True})
            self.assertEqual(set(merged['packs']), {'base.zip','delta.zip'})
            self.assertEqual(load(root/'base.json'), base)
            update['base_index'] = '../escape.json'
            write_json(root/'update.json', update)
            with self.assertRaises(ValueError): load_index(root/'update.json')

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
