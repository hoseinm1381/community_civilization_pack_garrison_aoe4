from pathlib import Path
import json
import unittest
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[2]
GUID = 'b7fcea91257b408fb9e8ae4d8bc402e1'


class CompletePersiaDataTests(unittest.TestCase):
    def test_complete_private_roster_and_no_global_army_override(self):
        files = [p for p in (ROOT/'assets/attrib/instances').glob('*/persia/ps_*.xml') if not p.stem.startswith('ps_probe_')]
        self.assertGreaterEqual(len(files), 280)
        self.assertFalse(list((ROOT/'assets/attrib/instances/army').rglob('normal_sultanate.xml')))
        self.assertFalse(list((ROOT/'assets/attrib/instances').glob('*/persia/ps_probe_*.xml')))

    def test_every_private_reference_resolves_and_localization_translated(self):
        files = list((ROOT/'assets/attrib/instances').glob('*/persia/ps_*.xml'))
        self.assertGreaterEqual(len(files), 280)
        base = ROOT/'assets/attrib/instances'
        keys = {p.relative_to(base).with_suffix('').as_posix().replace('/', '\\') for p in base.rglob('*.xml')}
        for p in files:
            root = E.parse(p).getroot()
            for n in root.iter():
                if n.get('mod'):
                    self.assertEqual(n.get('mod'), GUID, str(p))
                if n.tag == 'instance_reference' and n.get('mod') == GUID:
                    self.assertIn(n.get('value'), keys, str(p))

    def test_full_migration_ledger_has_source_and_destination_identities(self):
        path = ROOT/'docs/persia-import.json'
        self.assertTrue(path.exists())
        data = json.loads(path.read_text())
        self.assertEqual(len(data['instances']), 280)
        ids = [row['pbg_id'] for row in data['instances']]
        self.assertEqual(len(set(ids)), 280)
        self.assertTrue(all(row['source_sha256'] for row in data['instances']))


if __name__ == '__main__':
    unittest.main()
