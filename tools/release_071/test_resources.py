import gzip
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from resources import ResourceStore, deletion_gate


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        raw = b'{"mesh": [1, 2, 3]}'
        (self.root / 'blob.gz').write_bytes(gzip.compress(raw))
        self.row = dict(blob='blob.gz', codec='gzip', bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def tearDown(self):
        self.tmp.cleanup()

    def test_lossless_json(self):
        self.assertEqual(ResourceStore(self.root, {'F/input.json': self.row}).read_json('F/input.json'), {'mesh': [1, 2, 3]})

    def test_tampering(self):
        (self.root / 'blob.gz').write_bytes(gzip.compress(b'changed'))
        with self.assertRaises(ValueError):
            ResourceStore(self.root, {'x': self.row}).read('x')

    def test_path_escape(self):
        for blob in ('../other', str(self.root.parent / 'other')):
            with self.assertRaises(ValueError):
                ResourceStore(self.root, {'x': dict(self.row, blob=blob)}).read('x')

    def test_alias(self):
        self.assertEqual(ResourceStore(self.root, {'x': self.row, 'y': {'alias': 'x'}}).read_json('y')['mesh'], [1, 2, 3])

    def test_cycle(self):
        with self.assertRaises(ValueError):
            ResourceStore(self.root, {'a': {'alias': 'b'}, 'b': {'alias': 'a'}}).read('a')

    def test_ranged_snapshot_hierarchy_survives_materialization(self):
        keys=['E/art/exports/archer4/'+revision+'/authored-snapshot.json' for revision in ('v4','v5b','v5c')]
        store=ResourceStore(self.root,{k:self.row for k in keys})
        paths=store.materialize_tree(keys,self.root/'work')
        latest=paths[keys[-1]]
        self.assertEqual(latest.parent.name,'v5c')
        self.assertEqual((latest.parent.parent/'v5b/authored-snapshot.json').read_bytes(),store.read(keys[1]))

    def test_materialized_tree_rejects_traversal(self):
        with self.assertRaises(ValueError):
            ResourceStore(self.root,{'../outside':self.row}).materialize_tree(['../outside'],self.root/'work')

    def test_bundled_input_is_lossless_and_hash_checked(self):
        raw=b'native donor bytes'
        with zipfile.ZipFile(self.root/'inputs.zip','w',zipfile.ZIP_DEFLATED) as z:z.writestr('payload',raw)
        row=dict(blob='inputs.zip',codec='zip',member='payload',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        store=ResourceStore(self.root,{'F/old/native.rrtex':row})
        self.assertEqual(store.read('F/old/native.rrtex'),raw)
        row['sha256']='0'*64
        with self.assertRaises(ValueError):store.read('F/old/native.rrtex')

    def test_cleanup_refuses_incomplete_proof(self):
        with self.assertRaises(ValueError):
            deletion_gate({'package': True})

    def test_cleanup_requires_budget(self):
        proof = {k: True for k in ('package', 'rollback', 'native_source', 'asset_cooks', 'resources', 'editable', 'normal_unchanged', 'review')}
        proof['retained_bytes'] = 3000000001
        with self.assertRaises(ValueError):
            deletion_gate(proof)
        proof['retained_bytes'] = 2000000000
        deletion_gate(proof)


if __name__ == '__main__':
    unittest.main()
