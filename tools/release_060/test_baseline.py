import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from baseline import inspect_zip
from common import CFG

class BaselineTests(unittest.TestCase):
    def fixture(self, root, version='0.5.3', suffix='', bad_hash=False, wrong_id=False):
        key = CFG['package_key']
        path = Path(root)/f'{key}-{version}{suffix}.zip'
        sga = b'fixture SGA bytes; ZIP integrity tests only'
        manifest = {'schema':'garrison.mod/v1','bundle_key':key,
                    'details':{'id':'wrong' if wrong_id else key,'version':version},
                    'members':[{'role':'tuning','mod_key':key,'path':key+'.sga',
                       'sha256':'0'*64 if bad_hash else hashlib.sha256(sga).hexdigest()}]}
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('garrison.json',json.dumps(manifest))
            z.writestr(key+'.sga',sga)
        return path

    def test_hash_checked_but_source_and_completion_not_assumed(self):
        with tempfile.TemporaryDirectory() as root:
            result=inspect_zip(self.fixture(root))
            self.assertIn('still-required',result['status'])
            self.assertEqual(result['version'],'0.5.3')

    def test_diagnostic_rejected_even_with_valid_hash(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'Diagnostic'):
                inspect_zip(self.fixture(root,'0.5.2','-diagnostic-a'))

    def test_corrupt_hash_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                inspect_zip(self.fixture(root,bad_hash=True))

    def test_wrong_identity_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'identity'):
                inspect_zip(self.fixture(root,wrong_id=True))

    def test_old_release_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'0.5.2 or 0.5.3'):
                inspect_zip(self.fixture(root,'0.5.1'))

if __name__ == '__main__':
    unittest.main()
