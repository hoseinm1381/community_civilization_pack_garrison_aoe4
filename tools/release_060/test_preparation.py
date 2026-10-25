import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import common
from verify_preparation import validate_freeze


class PreparationTests(unittest.TestCase):
    def freeze(self):
        return {'schema': 'ccp-060-preparation-freeze/v1',
                'status': 'preparation-only-not-final-release-baseline',
                'source_snapshot': str(common.STAGING/'preparation-source/assets'),
                'inputs': {name: {} for name in ('assets', 'normal', 'prior_art', 'identities')}}

    def test_freeze_rejects_wrong_identity_or_destination(self):
        self.assertEqual(validate_freeze(self.freeze()), (common.STAGING/'preparation-source/assets').resolve())
        for key, value in [('schema', 'unknown'), ('status', 'complete'),
                           ('source_snapshot', str(common.ROOT/'assets'))]:
            with self.subTest(key=key):
                data = self.freeze()
                data[key] = value
                with self.assertRaises(ValueError):
                    validate_freeze(data)

    def test_freeze_requires_all_preservation_sections(self):
        data = self.freeze()
        del data['inputs']['normal']
        with self.assertRaisesRegex(ValueError, 'normal'):
            validate_freeze(data)

    def test_copy_is_manifest_bounded_and_detects_source_drift(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(common, 'owned', side_effect=Path):
            root = Path(directory)
            source = root/'source'
            source.mkdir()
            (source/'kept').write_bytes(b'original')
            (source/'unlisted').write_bytes(b'excluded')
            manifest = {'kept': {'sha256': hashlib.sha256(b'original').hexdigest()}}
            common.copy_manifest(source, root/'copy', manifest)
            self.assertEqual([p.name for p in (root/'copy').iterdir()], ['kept'])
            (source/'kept').write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'Source changed'):
                common.copy_manifest(source, root/'drift-copy', manifest)

    def test_copy_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(common, 'owned', side_effect=Path):
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, 'Unsafe snapshot member'):
                common.copy_manifest(root, root/'copy', {'../outside': {'sha256': '0'*64}})

    def test_missing_source_rejected_and_empty_source_snapshot_exists(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(common, 'owned', side_effect=Path):
            root = Path(directory)
            with self.assertRaises(FileNotFoundError):
                common.copy_manifest(root/'missing', root/'copy', {})
            with self.assertRaises(FileNotFoundError):
                common.files(root/'missing')
            source = root/'empty'
            source.mkdir()
            common.copy_manifest(source, root/'copy', {})
            self.assertTrue((root/'copy').is_dir())

    def test_copy_rejects_directory_junction(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(common, 'owned', side_effect=Path):
            root = Path(directory)
            source = root/'source'
            source.mkdir()
            (source/'item').write_bytes(b'data')
            with patch.object(Path, 'is_junction', autospec=True, side_effect=lambda p: p == source):
                with self.assertRaisesRegex(ValueError, 'source link'):
                    common.copy_manifest(source, root/'copy', {'item': {'sha256': hashlib.sha256(b'data').hexdigest()}})


if __name__ == '__main__':
    unittest.main()
