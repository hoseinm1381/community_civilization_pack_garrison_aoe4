import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/compact'))
from github_build import completed_native, verify_source_snapshot

class IndependentBuildTests(unittest.TestCase):
    def test_zero_exit_without_completed_instance_log_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'logs').mkdir()
            (root/'run.json').write_text(json.dumps({'status':'succeeded','exit_code':0,'timed_out':False}))
            with self.assertRaises(ValueError):completed_native(root,658)

    def test_failed_native_run_cannot_be_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'logs').mkdir();(root/'logs/burn.log').write_text('658 instances validated')
            (root/'run.json').write_text(json.dumps({'status':'failed','exit_code':0,'timed_out':False}))
            with self.assertRaises(ValueError):completed_native(root,658)

    def test_validation_only_log_is_not_a_completed_burn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'logs').mkdir();(root/'output').mkdir()
            (root/'logs/burn.log').write_text('658 instances validated')
            (root/'output/reference.sga').write_bytes(b'_ARCHIVE'+b'\0'*512)
            (root/'run.json').write_text(json.dumps({'status':'succeeded','exit_code':0,'timed_out':False}))
            with self.assertRaises(ValueError):completed_native(root,658)

    def test_deleted_and_untracked_source_inputs_are_rejected(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'assets').mkdir();(root/'assets/keep.xml').write_bytes(b'kept')
            indexed={'source/assets/keep.xml':{'sha256':hashlib.sha256(b'kept').hexdigest()},
                     'source/assets/deleted.scar':{'sha256':hashlib.sha256(b'deleted').hexdigest()}}
            with self.assertRaises(ValueError):verify_source_snapshot(root,['assets/keep.xml'],indexed)
            del indexed['source/assets/deleted.scar']
            (root/'assets/untracked.xml').write_bytes(b'new untracked input')
            with self.assertRaises(ValueError):verify_source_snapshot(root,['assets/keep.xml'],indexed)

    def test_changed_editable_source_cannot_rebuild_stored_old_payloads(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'assets').mkdir();(root/'assets/test.xml').write_bytes(b'new editable value')
            indexed={'source/assets/test.xml':{'sha256':hashlib.sha256(b'old editable value').hexdigest()}}
            with self.assertRaises(ValueError):verify_source_snapshot(root,['assets/test.xml'],indexed)
            indexed['source/assets/test.xml']['sha256']=hashlib.sha256(b'new editable value').hexdigest()
            self.assertEqual(verify_source_snapshot(root,['assets/test.xml'],indexed),1)

if __name__=='__main__':unittest.main()
