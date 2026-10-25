"""Preparation guards: external storage and byte-level gameplay preservation."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import workspace_support as support


class WorkspaceGuardTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'workspace.json').read_text())

    def test_missing_external_drive_fails_without_creating_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            absent = Path(directory) / 'absent'
            config = copy.deepcopy(self.config)
            config['external_root'] = str(absent)
            with self.assertRaisesRegex(ValueError, 'External storage unavailable'):
                support.check_storage(ROOT, config)
            self.assertFalse(absent.exists())

    def test_normal_directory_cannot_replace_a_junction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / 'external'
            external.mkdir()
            (external / 'cache').mkdir()
            (root / 'cache').mkdir()
            config = {'external_root': str(external), 'links': {'cache': 'cache'}}
            with self.assertRaisesRegex(ValueError, 'Expected junction'):
                support.check_storage(root, config)

    def test_real_storage_targets_are_available_and_exact(self):
        links = support.check_storage(ROOT, self.config)
        self.assertEqual(len(links), 7)

    def test_identity_normalization_does_not_hide_gameplay_changes(self):
        # Use an untouched actor for the historical identity-only migration guard.
        # Trap/house/keep visual changes have their own strict release source policy.
        relative = 'assets/attrib/instances/ebps/vietnam/vn_building_econ_wood_control_chi.xml'
        original = (Path(self.config['source_root']) / relative).read_bytes()
        migrated = (ROOT / relative).read_bytes()
        self.assertEqual(support.baseline_bytes(relative, migrated, self.config), original)
        changed = migrated.replace(b'<instance ', b'<instance migration_accident="true" ', 1)
        self.assertNotEqual(changed, migrated)
        self.assertNotEqual(support.baseline_bytes(relative, changed, self.config), original)

    def test_wrong_project_guid_is_rejected(self):
        config = copy.deepcopy(self.config)
        config['project_guid'] = '00000000-0000-0000-0000-000000000000'
        with self.assertRaisesRegex(ValueError, 'Project GUID mismatch'):
            support.check_identity(ROOT, config)


if __name__ == '__main__':
    unittest.main()
