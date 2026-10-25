import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('handoff_store', Path(__file__).with_name('store.py'))
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)


class StoreTests(unittest.TestCase):
    def test_roundtrip_deduplicates_and_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = b'abcdef' * 1000
            writer = store.Writer(root / 'data', chunk_size=1000, pack_size=2500)
            writer.add('source/a.bin', data)
            writer.add('external/b.bin', data)
            doc = writer.finish()
            reader = store.Reader(root / 'data', doc)
            self.assertLess(len(doc['chunks']), 12)
            self.assertEqual(reader.read('source/a.bin'), data)
            self.assertEqual(reader.verify()['files'], 2)
            self.assertTrue(all(p.stat().st_size < 5000 for p in (root/'data').glob('*.zip')))
            reader.close()

    def test_restore_refuses_edit_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); writer = store.Writer(root / 'data')
            writer.add('source/a.txt', b'original'); reader = store.Reader(root/'data', writer.finish())
            destination = root/'restore'; reader.restore('source/a.txt', destination)
            (destination/'source/a.txt').write_bytes(b'edited')
            with self.assertRaises(ValueError): reader.restore('source/a.txt', destination)
            for key in ['../escape', 'source/../escape', 'source/C:/escape', '/source/a', 'source/a:stream']:
                with self.assertRaises(ValueError): store.safe_path(destination, key)
            reader.close()

    def test_corrupt_bundle_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); writer=store.Writer(root/'data'); writer.add('source/a',b'abc')
            doc=writer.finish(); p=next((root/'data').glob('*.zip')); p.write_bytes(b'corrupt')
            with self.assertRaises(ValueError): store.Reader(root/'data',doc).verify()

    def test_secret_detection_and_safe_environment_reference(self):
        with self.assertRaises(ValueError): store.check_text('example.txt', b'sk_' + b'a'*40)
        store.check_text('example.py', b'os.environ["ELEVENLABS_API_KEY"]')

    def test_encoded_basic_credential_is_rejected(self):
        import base64
        with self.assertRaises(ValueError):
            store.check_text('receipt.json',base64.b64encode(b'username'*4+b':'+b'password'*4))

    def test_unsafe_manifest_key_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer=store.Writer(Path(tmp)/'data')
            with self.assertRaises(ValueError): writer.add('external/../../escape', b'x')

    def test_failed_export_pack_does_not_block_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=store.Writer(root);first.add('source/a',b'first');doc=first.finish()
            failed=store.Writer(root,previous=__import__('copy').deepcopy(doc));failed.add('source/b',b'failed');failed.finish()
            retry=store.Writer(root,previous=__import__('copy').deepcopy(doc));retry.add('source/b',b'retry');result=retry.finish()
            reader=store.Reader(root,result);self.assertEqual(reader.read('source/b'),b'retry');reader.close()


if __name__=='__main__': unittest.main()
