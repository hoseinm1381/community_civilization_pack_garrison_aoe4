"""Real temporary files and recovery bundles; never touches development data."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import cold_storage as cold
from store import Writer,write_json,file_sha


class ColdStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.ext=root/'external';self.ext.mkdir()
        self.store=root/'store';self.index=self.store/'index.json.gz';self.audit=self.ext/'consolidation_085';self.audit.mkdir()
        self.patches=[patch.object(cold,'EXT',self.ext),patch.object(cold,'STORE',self.store),patch.object(cold,'INDEX',self.index),patch.object(cold,'AUDIT',self.audit),patch.object(cold,'guard',lambda:None),patch.object(cold,'check_storage',lambda *a:None)]
        for p in self.patches:p.start();self.addCleanup(p.stop)

    def fixture(self):
        writer=Writer(self.store,chunk_size=16,pack_size=64)
        rel='output/release_084/local/generation/voice.wav'
        p=self.ext/rel;p.parent.mkdir(parents=True);p.write_bytes(b'original editable audio master')
        writer.add('external/'+rel,p.read_bytes());write_json(self.index,writer.finish())
        return p

    def test_retirement_recovers_original_master_and_retains_untracked_file(self):
        master=self.fixture();other=master.with_name('untracked.wav');other.write_bytes(b'unique')
        cold.make_plan();plan=cold.load(self.audit/'indexed-plan.json.gz')
        self.assertTrue(plan['all_recovery_files_reconstructed']);self.assertEqual(len(plan['files']),1)
        cold.apply_indexed();self.assertFalse(master.exists());self.assertEqual(other.read_bytes(),b'unique')
        row=cold.load(self.index)['files']['external/'+master.relative_to(self.ext).as_posix()]
        reader=cold.Reader(self.store,cold.load(self.index));data=reader.read('external/'+master.relative_to(self.ext).as_posix());reader.close()
        cold.write_restored(master.relative_to(self.ext).as_posix(),data,row['sha256'])
        self.assertEqual(master.read_bytes(),b'original editable audio master')

    def test_edited_master_between_plan_and_apply_is_preserved(self):
        master=self.fixture();cold.make_plan();master.write_bytes(b'user edit')
        with self.assertRaisesRegex(ValueError,'Edited file'):cold.apply_indexed()
        self.assertEqual(master.read_bytes(),b'user edit')

    def test_corrupt_recovery_prevents_retirement(self):
        master=self.fixture();cold.make_plan()
        pack=next(self.store.glob('pack-*.zip'));pack.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'Recovery pack changed'):cold.apply_indexed()
        self.assertTrue(master.exists())

    def test_restore_refuses_edited_destination_and_bad_paths(self):
        master=self.fixture();rel=master.relative_to(self.ext).as_posix()
        with self.assertRaisesRegex(ValueError,'Edited destination'):cold.write_restored(rel,b'other','0'*64)
        for bad in ('../escape','C:/escape','/absolute','a/../b','a\\b',''):
            with self.assertRaises(ValueError):cold.owned(bad)

    def runtime(self):
        prefix='tool-cache/local-voices-084/venv'
        self.patches.append(patch.object(cold,'RUNTIME_ROOTS',(prefix,)))
        self.patches[-1].start();self.addCleanup(self.patches[-1].stop)
        folder=self.ext/prefix;folder.mkdir(parents=True)
        (folder/'pyvenv.cfg').write_bytes(b'home = pinned-local-runtime\n')
        (folder/'binary.dll').write_bytes(bytes(range(256))*100)
        cold.pack_runtime()
        return prefix,folder

    def test_runtime_bundle_retire_restore_exact_binary_and_edited_destination(self):
        prefix,folder=self.runtime();before={p.name:p.read_bytes() for p in folder.iterdir()}
        cold.apply_runtime();self.assertEqual(list(folder.iterdir()),[])
        cold.restore(prefix,runtime=True)
        self.assertEqual({p.name:p.read_bytes() for p in folder.iterdir()},before)
        (folder/'binary.dll').write_bytes(b'user edit')
        with self.assertRaisesRegex(ValueError,'Edited destination'):cold.restore(prefix,runtime=True)
        self.assertEqual((folder/'binary.dll').read_bytes(),b'user edit')

    def test_corrupt_runtime_archive_preserves_installed_files(self):
        prefix,folder=self.runtime()
        (self.ext/'resources_085/local-voice-tools.zip').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'Runtime recovery changed'):cold.apply_runtime()
        self.assertTrue((folder/'binary.dll').exists())

    def test_local_voice_bundle_is_independent_and_restores_original_master(self):
        master=self.fixture();folder=master.parent.parent
        manifest=folder/'recording-manifest.json';manifest.write_bytes(b'{"saved":true}')
        cold.pack_bundle(cold.VOICE_ROOTS,'voice-development')
        # Contributor packs are unavailable; local recovery must still work.
        for p in self.store.glob('*'):p.unlink()
        cold.apply_bundle(cold.VOICE_ROOTS,'voice-development')
        self.assertFalse(master.exists());self.assertTrue(manifest.exists())
        cold.restore('output/release_084/local',True,'voice-development')
        self.assertEqual(master.read_bytes(),b'original editable audio master')

    def test_runtime_restore_streams_large_binary_members(self):
        prefix,folder=self.runtime();cold.apply_runtime()
        # CUDA DLLs and the saved installer are multi-gigabyte members. The
        # restorer must not load an entire member into RAM with ZipFile.read.
        with patch.object(cold.zipfile.ZipFile,'read',side_effect=AssertionError('Unbounded member allocation')):
            cold.restore(prefix,True)
        self.assertEqual((folder/'binary.dll').read_bytes(),bytes(range(256))*100)

    def test_current_package_guard_accepts_reused_folder_with_086(self):
        folder=self.ext/'output/release_085/final-v2';folder.mkdir(parents=True)
        sga=folder/'community_civilization_pack.sga';sga.write_bytes(b'current archive')
        package=folder/'community_civilization_pack-0.8.6.zip';package.write_bytes(b'current package')
        write_json(folder/'verification.json',dict(version='0.8.6',sga_sha256=file_sha(sga),zip_sha256=file_sha(package)))
        # Invoke the actual guard through its saved definition, rather than the
        # fixture's replacement used for unrelated archive/retirement tests.
        import importlib.util
        spec=importlib.util.spec_from_file_location('guard_probe',Path(cold.__file__))
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        with patch.object(probe,'EXT',self.ext),patch.object(probe,'check_storage',lambda *a:None):
            self.assertEqual(probe.guard()['version'],'0.8.6')

    def test_current_package_guard_accepts_reused_folder_with_087(self):
        folder=self.ext/'output/release_085/final-v2';folder.mkdir(parents=True)
        sga=folder/'community_civilization_pack.sga';sga.write_bytes(b'current archive')
        package=folder/'community_civilization_pack-0.8.7.zip';package.write_bytes(b'current package')
        write_json(folder/'verification.json',dict(version='0.8.7',sga_sha256=file_sha(sga),zip_sha256=file_sha(package)))
        # Invoke the actual guard through its saved definition, rather than the
        # fixture's replacement used for unrelated archive/retirement tests.
        import importlib.util
        spec=importlib.util.spec_from_file_location('guard_probe',Path(cold.__file__))
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        with patch.object(probe,'EXT',self.ext),patch.object(probe,'check_storage',lambda *a:None):
            self.assertEqual(probe.guard()['version'],'0.8.7')


if __name__=='__main__':unittest.main()
