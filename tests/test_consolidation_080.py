import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/consolidation_080'))
from store import ResourceStore, owned_key, retirement_gate
from retire import candidate_path, retire_sequence, retire_with_journal
from package import verify_package
from common import safe_label


class RecoverySafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.roots = {k: self.base / k for k in ('E', 'F')}
        for p in self.roots.values():
            p.mkdir()
        self.data = b'original native donor\x00' * 100
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.bundle = self.base / 'recovery.zip'
        with zipfile.ZipFile(self.bundle, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr(self.digest, self.data)
        self.index = {k: {'member': self.digest, 'bytes': len(self.data),
                         'sha256': self.digest} for k in ('F/older/v4/input.json',
                                                        'F/older/v5b/input.json')}
        self.store = ResourceStore(self.bundle, self.index, self.roots)
        self.addCleanup(self.store.close)

    def test_restore_preserves_predecessor_hierarchy(self):
        for key in self.index:
            p = self.store.restore(key)
            self.assertEqual(p, self.roots['F'] / key[2:])
            self.assertEqual(p.read_bytes(), self.data)

    def test_duplicate_payload_aliases_restore_independent_files(self):
        a, b = [self.store.restore(k) for k in self.index]
        a.write_bytes(b'edited')
        self.assertEqual(b.read_bytes(), self.data)

    def test_refuses_overwrite_of_edited_destination(self):
        p = self.store.restore(next(iter(self.index)))
        p.write_bytes(b'user edits')
        with self.assertRaises(ValueError):
            self.store.restore(next(iter(self.index)))
        self.assertEqual(p.read_bytes(), b'user edits')

    def test_idempotent_restore_of_exact_bytes(self):
        k = next(iter(self.index))
        self.assertEqual(self.store.restore(k), self.store.restore(k))

    def test_required_fixture_restore_tracks_only_new_copies_and_refuses_edits(self):
        keys = list(self.index)
        paths = self.store.restore_required(keys)
        self.assertEqual(set(paths), {str(self.roots['F'] / k[2:]) for k in keys})
        self.assertEqual(self.store.restore_required(keys), [])
        changed = Path(paths[0])
        changed.write_bytes(b'user edit')
        with self.assertRaises(ValueError):
            self.store.restore_required(keys)
        self.assertEqual(changed.read_bytes(), b'user edit')

    def test_rejects_traversal(self):
        for key in ('F/../escape', 'E/a/../../escape', 'Q/file', 'F/C:/evil'):
            self.store.index[key] = self.index[next(iter(self.index))]
            with self.assertRaises(ValueError):
                self.store.restore(key)

    def test_rejects_corrupt_payload(self):
        self.store.index[next(iter(self.index))]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.store.read(next(iter(self.index)))

    def test_rejects_wrong_length(self):
        self.store.index[next(iter(self.index))]['bytes'] += 1
        with self.assertRaises(ValueError):
            self.store.read(next(iter(self.index)))

    def test_rejects_outside_owned_roots(self):
        with self.assertRaises(ValueError):
            owned_key(self.base / 'foreign/file', self.roots)

    def test_normalizes_windows_extended_prefix(self):
        p = self.roots['F'] / 'folder/file'
        self.assertEqual(owned_key('\\\\?\\' + str(p), self.roots), 'F/folder/file')

    def test_rejects_missing_owned_storage(self):
        bad = ResourceStore(self.bundle, self.index, {'E': self.roots['E'],
                                                    'F': self.base / 'missing'})
        with self.assertRaises(ValueError):
            bad.restore(next(iter(self.index)))

    def test_retirement_requires_all_evidence(self):
        proof = dict.fromkeys(('approved', 'package', 'rollbacks', 'native_source',
                              'asset_cooks', 'recovery', 'editable', 'normal',
                              'review'), True)
        proof['projected_allocated'] = 5_600_000_000
        retirement_gate(proof)
        for gate in list(proof):
            bad = dict(proof)
            bad[gate] = 6_000_000_001 if gate == 'projected_allocated' else False
            with self.assertRaises(ValueError, msg=gate):
                retirement_gate(bad)

    def test_restore_into_clean_owned_attempt(self):
        attempt = self.roots['F'] / 'staging/clean/E/input'
        self.assertEqual(self.store.restore(next(iter(self.index)), attempt), attempt)
        self.assertEqual(attempt.read_bytes(), self.data)

    def test_custom_restore_cannot_escape_owned_roots(self):
        with self.assertRaises(ValueError):
            self.store.restore(next(iter(self.index)), self.base / 'foreign')

    def test_retirement_rejects_modified_or_unknown_file(self):
        key = 'F/generated/file'
        p = self.roots['F'] / 'generated/file'
        p.parent.mkdir()
        p.write_bytes(self.data)
        row = {'bytes': len(self.data), 'sha256': self.digest, 'mtime_ns': p.stat().st_mtime_ns}
        self.assertEqual(candidate_path(key, row, self.roots, set(), {key}), p)
        with self.assertRaises(ValueError):
            candidate_path(key, row, self.roots, {key}, {key})
        with self.assertRaises(ValueError):
            candidate_path(key, row, self.roots, set(), set())
        p.write_bytes(b'new user work')
        with self.assertRaises(ValueError):
            candidate_path(key, row, self.roots, set(), {key})
        self.assertEqual(p.read_bytes(), b'new user work')

    def test_retirement_stops_immediately_and_records_completed_files(self):
        rows = {}
        for name in ('one', 'two', 'three'):
            p = self.roots['F'] / name
            p.write_bytes(self.data)
            rows['F/' + name] = {'bytes': len(self.data), 'sha256': self.digest,
                                 'mtime_ns': p.stat().st_mtime_ns, 'allocated': 4096}
        (self.roots['F'] / 'two').write_bytes(b'changed by user')
        records = []
        with self.assertRaises(ValueError):
            retire_sequence(rows, self.roots, set(), records.append)
        self.assertFalse((self.roots['F'] / 'one').exists())
        self.assertEqual((self.roots['F'] / 'two').read_bytes(), b'changed by user')
        self.assertTrue((self.roots['F'] / 'three').exists())
        self.assertEqual(records[-1]['operation'], 'removed_verified_copy')
        self.assertEqual(records[-1]['key'], 'F/one')

    def test_interrupted_unlink_resumes_only_from_matching_durable_intent(self):
        key = 'F/prior'
        row = {'bytes': len(self.data), 'sha256': self.digest, 'mtime_ns': 0, 'allocated': 4096}
        log = self.roots['E'] / 'operations.jsonl'
        log.write_text(json.dumps(dict(row, key=key, operation='intent_remove_verified_copy')) + '\n')
        self.assertEqual(retire_with_journal({key: row}, self.roots, set(), log), 1)
        records = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertTrue(records[-1]['recovered_after_interruption'])
        missing = 'F/unknown-missing'
        with self.assertRaises(ValueError):
            retire_with_journal({missing: row}, self.roots, set(), self.roots['E'] / 'new.jsonl')

    def test_completed_retirement_reappearance_stops_resume(self):
        p = self.roots['F'] / 'prior'
        p.write_bytes(self.data)
        row = {'bytes': len(self.data), 'sha256': self.digest, 'mtime_ns': p.stat().st_mtime_ns, 'allocated': 4096}
        log = self.roots['E'] / 'reappeared.jsonl'
        log.write_text(json.dumps(dict(row, key='F/prior', operation='removed_verified_copy')) + '\n')
        with self.assertRaises(ValueError):
            retire_with_journal({'F/prior': row}, self.roots, set(), log)
        self.assertEqual(p.read_bytes(), self.data)

    def test_delivery_verifies_actual_zip_metadata_layout_and_embedded_archive(self):
        def fixture(version='0.8.0', native=None, extra=False):
            native = self.data if native is None else native
            path = self.base / 'delivery.zip'
            manifest = {'schema': 'garrison.mod/v1', 'bundle_key': 'community_civilization_pack',
                'members': [{'mod_key': 'community_civilization_pack', 'role': 'tuning',
                             'path': 'community_civilization_pack.sga', 'sha256': self.digest}],
                'details': {'id': 'community_civilization_pack', 'version': version, 'author': 'hosein81 and chilly5'}}
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('garrison.json', json.dumps(manifest))
                z.writestr('community_civilization_pack.sga', native)
                z.writestr('START-HERE.txt', 'instructions')
                if extra:
                    z.writestr('unexpected', 'extra')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            return path, digest
        path, digest = fixture()
        verify_package(path, digest, self.digest)
        with self.assertRaises(ValueError):
            verify_package(path, '0' * 64, self.digest)
        for params in ({'version': '0.7.12'}, {'native': b'wrong archive'}, {'extra': True}):
            path, digest = fixture(**params)
            with self.assertRaises(ValueError):
                verify_package(path, digest, self.digest)

    def test_attempt_labels_cannot_escape_output_root(self):
        self.assertEqual(safe_label('final-v1'), 'final-v1')
        for value in ('../elsewhere', 'C:/outside', '/absolute', '', 'a' * 25):
            with self.assertRaises(ValueError):
                safe_label(value)

    def test_generated_delivery_rule_is_exact_and_preserves_other_deliveries(self):
        from verify import is_generated
        key = 'F/output/consolidation_080/delivery/post1/community_civilization_pack-0.8.0.zip'
        self.assertTrue(is_generated(key))
        for other in (key.replace('/post1/', '/final-v1/'),
                      key.replace('/post1/', '/user-work/'),
                      key.replace('community_civilization_pack-0.8.0.zip', 'delivery-proof.json'),
                      key + '.edited'):
            self.assertFalse(is_generated(other), other)

    def test_post_budget_counts_existing_evidence_without_weakening_pre_gate(self):
        from verify import projected_budget
        self.assertEqual(projected_budget(5_600_000_000, 'pre'), 5_650_000_000)
        with self.assertRaises(AssertionError):
            projected_budget(5_660_000_000, 'pre')
        self.assertEqual(projected_budget(5_660_000_000, 'post'), 5_710_000_000)
        with self.assertRaises(AssertionError):
            projected_budget(5_950_000_000, 'post')


if __name__ == '__main__':
    unittest.main()
