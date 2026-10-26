import copy,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/compact'))
import portable
from store import Writer


class GitBackedStoreTests(unittest.TestCase):
    def test_verify_omitted_pack_and_reject_wrong_pack_hash(self):
        git=os.environ.get('GIT_EXECUTABLE') or shutil.which('git')
        if not git and (ROOT/'workspace.json').exists():
            git=json.loads((ROOT/'workspace.json').read_text())['git_path']
        self.assertIsNotNone(git,'Git is required for this integration regression')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'development-data/current-084-v1'
            writer=Writer(folder);writer.add('source/test.txt',b'preserved rebuild input');doc=writer.finish()
            def run(*args):subprocess.run([git,'-c','safe.directory='+str(root),'-C',str(root),*args],check=True,capture_output=True)
            run('init');run('add','development-data');run('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
            pack=folder/next(iter(doc['packs']));pack.unlink()
            with patch.object(portable,'ROOT',root),patch.dict(os.environ,{'GIT_EXECUTABLE':str(git)}):
                r=portable.AliasReader(folder,doc)
                try:
                    self.assertEqual(r.read('source/test.txt'),b'preserved rebuild input')
                    self.assertEqual(r.verify(),{'files':1,'chunks':1,'packs':1})
                    self.assertFalse(pack.exists(),'Verification must not materialize omitted packs')
                finally:r.close()
                # The supported F: setup uses workspace.local.json, without
                # requiring either a legacy workspace.json or Git on PATH.
                (root/'workspace.local.json').write_text(json.dumps({'git_path':str(git)}))
                with patch.dict(os.environ,{'GIT_EXECUTABLE':''}),patch.object(portable.shutil,'which',return_value=None):
                    r=portable.AliasReader(folder,doc)
                    try:self.assertEqual(r.read('source/test.txt'),b'preserved rebuild input')
                    finally:r.close()
                bad=copy.deepcopy(doc);bad['packs'][pack.name]['sha256']='0'*64
                r=portable.AliasReader(folder,bad)
                try:
                    with self.assertRaises(ValueError):r.verify()
                finally:r.close()

class NativePayloadRefreshTests(unittest.TestCase):
    def test_new_burn_replaces_stale_compiled_payload(self):
        from native_payloads import refresh_native_member
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'attrib/persia/test.rgd';target.parent.mkdir(parents=True);target.write_bytes(b'old burn')
            def extract(archive,member,dest):
                self.assertEqual((archive,member),('new.sga','attrib/persia/test.rgd'))
                dest.write_bytes(b'new burn')
            refresh_native_member('new.sga','attrib/persia/test.rgd',target,extract)
            self.assertEqual(target.read_bytes(),b'new burn')

    def test_failed_extraction_preserves_previous_payload(self):
        from native_payloads import refresh_native_member
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'test.rgd';target.write_bytes(b'old burn')
            def extract(archive,member,dest):raise RuntimeError('burn extraction failed')
            with self.assertRaises(RuntimeError):refresh_native_member('new.sga','test.rgd',target,extract)
            self.assertEqual(target.read_bytes(),b'old burn')

if __name__=='__main__':unittest.main()

