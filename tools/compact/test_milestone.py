import tempfile
import unittest
import zipfile
from pathlib import Path
from current_package import write_package


class MilestoneTests(unittest.TestCase):
    def test_sparse_verification_retains_unchanged_members_and_original_index(self):
        from current_package import apply_verification_delta
        original={'version':'0.8.7','member_sha256':{'a':'1','b':'2'},'mounts':{'a':'data','b':'data'},'old_flag':True}
        current=apply_verification_delta(original,{'metadata':{'version':'0.8.8'},'member_sha256':{'b':'3'}})
        self.assertEqual(current['member_sha256'],{'a':'1','b':'3'})
        self.assertNotIn('old_flag',current)
        self.assertEqual(current['version'],'0.8.8')
        self.assertEqual(current['mounts'],original['mounts'])
        self.assertEqual(original['member_sha256']['b'],'2')

    def test_sparse_verification_rejects_unexpected_members_or_mounts(self):
        from current_package import apply_verification_delta
        for delta in ({'member_sha256':{'new':'3'}},{'mounts':{}}):
            with self.assertRaises(ValueError):
                apply_verification_delta({'member_sha256':{'a':'1'},'mounts':{'a':'data'}},delta)

    def test_package_preserves_original_zip_metadata_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = b'game archive' * 1000
            original = root/'original.zip'
            with zipfile.ZipFile(original, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
                info = zipfile.ZipInfo('community_civilization_pack.sga', (2026, 10, 25, 12, 30, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0x20
                z.writestr(info, data, compresslevel=6)
            with zipfile.ZipFile(original) as z:
                info = z.infolist()[0]
                fields = ['filename', 'date_time', 'compress_type', 'create_system',
                          'create_version', 'extract_version', 'external_attr', 'internal_attr']
                rows = [{k: getattr(info, k) for k in fields}]
            source = root/'archive.sga'
            source.write_bytes(data)
            target = root/'rebuilt.zip'
            write_package(target, rows, {'community_civilization_pack.sga': source})
            self.assertEqual(target.read_bytes(), original.read_bytes())

    def test_package_refuses_overwriting_and_unexpected_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'existing.zip'
            p.write_bytes(b'user file')
            with self.assertRaises(FileExistsError):
                write_package(p, [], {})
            with self.assertRaises(ValueError):
                write_package(Path(tmp)/'new.zip', [{'filename':'../escape'}], {})


if __name__ == '__main__':
    unittest.main()
