import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('dev',Path(__file__).with_name('dev.py'))
dev=importlib.util.module_from_spec(spec);spec.loader.exec_module(dev)


class DevTests(unittest.TestCase):
    def test_original_junction_paths_resolve_to_external_data(self):
        doc={'provenance':{'source_root':'E:/old/mod','external_root':'F:/old/temp'}}
        self.assertEqual(dev.path_key(r'E:\old\mod\output\release_084\a.ogg',doc),'external/output/release_084/a.ogg')
        self.assertEqual(dev.path_key(r'E:\old\mod\art\garrison_library\a',doc),'external/garrison-library/a')
        self.assertEqual(dev.path_key('F:/old/temp/output/a',doc),'external/output/a')
        self.assertEqual(dev.path_key('E:/old/mod/assets/a',doc),'source/assets/a')
        with self.assertRaises(ValueError):dev.path_key('C:/other/a',doc)

    def test_profiles_keep_history_optional(self):
        self.assertTrue(dev.selected('source/art/authoring/unit.blend','development'))
        self.assertTrue(dev.selected('external/resources_080/index.json','development'))
        self.assertFalse(dev.selected('external/output/release_084/local/generation/a.wav','development'))
        self.assertTrue(dev.selected('external/output/release_084/local/generation/a.wav','voices'))
        self.assertTrue(dev.selected('external/output/release_084/integration/receipt.json','development'))

    def test_relocated_index_preserves_historical_roots(self):
        doc={'provenance':{'source_root':'G:/restored/source','external_root':'G:/restored/external',
            'path_roots':[{'source_root':'E:/old/mod','external_root':'F:/old/temp'}]}}
        self.assertEqual(dev.path_key('E:/old/mod/output/payload.ogg',doc),'external/output/payload.ogg')

    def test_nested_roots_refused(self):
        from prepare_handoff import validate_roots
        from pathlib import Path
        root=Path.cwd()
        for source,external,repo in [(root/'a',root/'b',root/'a/repo'),(root/'a/src',root/'b',root/'a')]:
            with self.assertRaises(ValueError):validate_roots(source,external,repo)

    def test_milestone_conflict_then_retry_preserves_prior_index(self):
        import tempfile,subprocess,sys
        from store import Writer,write_json,load,Reader,file_sha
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'active';external=root/'data';repo=root/'repo'
            source.mkdir();external.mkdir();(repo/'.git').mkdir(parents=True)
            folder=repo/'development-data/snapshot-084-v1';writer=Writer(folder)
            writer.add('source/a.txt',b'old');doc=writer.finish()
            doc['provenance']={'source_root':'E:/historical/source','external_root':'F:/historical/external'}
            write_json(folder/'index.json.gz',doc);before=file_sha(folder/'index.json.gz')
            (source/'a.txt').write_bytes(b'new');(repo/'a.txt').write_bytes(b'contributor edit')
            command=[sys.executable,'-B',str(Path(__file__).with_name('milestone.py')),
                '--source',str(source),'--external',str(external),'--repository',str(repo),'--label','next']
            failed=subprocess.run(command,capture_output=True)
            self.assertNotEqual(failed.returncode,0)
            self.assertEqual((repo/'a.txt').read_bytes(),b'contributor edit')
            self.assertEqual(file_sha(folder/'index.json.gz'),before)
            (repo/'a.txt').write_bytes(b'old')
            success=subprocess.run(command,capture_output=True)
            self.assertEqual(success.returncode,0,success.stderr.decode(errors='replace'))
            latest=load(folder/'index.json.gz');r=Reader(folder,latest)
            self.assertEqual(r.read('source/a.txt'),b'new');r.close()
            self.assertEqual(file_sha(folder/'index-initial-084-v1.json.gz'),before)
            self.assertEqual(dev.path_key('E:/historical/source/assets/a',latest),'source/assets/a')

    def test_source_nicename_is_checked_independently_of_project_guid(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'assets').mkdir()
            (root/'community_civilization_pack.aoe4mod').write_text('<project><ID>'+dev.NAMESPACE+'</ID></project>')
            burn=root/'assets/_default.burnproj';burn.write_text('<project><NiceName>'+dev.NAMESPACE+'</NiceName></project>')
            dev.check_source_identity(root)
            burn.write_text('<project><NiceName>normal-edition</NiceName></project>')
            with self.assertRaises(ValueError):dev.check_source_identity(root)

    def test_restore_can_split_source_and_external_drives(self):
        import tempfile,argparse
        from store import Writer,Reader
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);writer=Writer(root/'store')
            writer.add('source/art/model.blend',b'blend');writer.add('external/resources_080/index.json',b'{}')
            r=Reader(root/'store',writer.finish())
            args=argparse.Namespace(destination=root/'external-parent',source_parent=root/'source-parent',prefix=None,profile='development')
            dev.restore(args,r);r.close()
            self.assertTrue((root/'source-parent/source/art/model.blend').is_file())
            self.assertFalse((root/'external-parent/source').exists())
            self.assertTrue((root/'external-parent/external/resources_080/index.json').is_file())

    def test_exfat_configure_fails_before_mutating_workspace(self):
        import tempfile,argparse
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'source').mkdir();(root/'external').mkdir()
            config=root/'source/workspace.json';config.write_bytes(b'{}')
            args=argparse.Namespace(destination=root,source_parent=None,tools=None)
            with patch.object(dev,'filesystem',return_value='exFAT'):
                with self.assertRaisesRegex(ValueError,'NTFS'):dev.configure(args)
            self.assertEqual(config.read_bytes(),b'{}')
            self.assertFalse((root/'source/cache').exists())


if __name__=='__main__':unittest.main()
