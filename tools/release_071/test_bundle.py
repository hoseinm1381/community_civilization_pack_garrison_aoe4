import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import bundle_exfat


class BundleRerunTests(unittest.TestCase):
    def test_registered_bundle_rerun_preserves_exact_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tx=root/'tx';store=root/'store';tx.mkdir();store.mkdir()
            (tx/'retained.json').write_text('{}')
            name='native-and-diagnostics-v1.zip';payload=b'only retained donor copy'
            archive=store/name
            with zipfile.ZipFile(archive,'w') as z:z.writestr('payload',payload)
            row=dict(blob=name,codec='zip',member='payload',bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
            (store/'index.json').write_text(json.dumps({'files':{'F/donor.rrtex':row}}))
            before=archive.read_bytes()
            with patch.multiple(bundle_exfat,TX=tx,STORE=store):bundle_exfat.main()
            self.assertEqual(archive.read_bytes(),before)

    def test_unregistered_existing_archive_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tx=root/'tx';store=root/'store';tx.mkdir();store.mkdir()
            (tx/'retained.json').write_text('{}');(store/'index.json').write_text('{"files":{}}')
            archive=store/'native-and-diagnostics-v1.zip';archive.write_bytes(b'preserve interrupted candidate')
            with patch.multiple(bundle_exfat,TX=tx,STORE=store):
                with self.assertRaises(FileExistsError):bundle_exfat.main()
            self.assertEqual(archive.read_bytes(),b'preserve interrupted candidate')


if __name__=='__main__':unittest.main()
