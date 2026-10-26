import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUID = 'a743d7d1d7534cf78817e29d8ded7366'


class ProbeDataTests(unittest.TestCase):
    def test_six_private_children_and_no_global_override(self):
        files = list((ROOT / 'assets/attrib/instances').glob('*/persia/ps_probe_*.xml'))
        self.assertEqual(len(files), 6, 'Native conversion probe must be present')
        ids = []
        for file in files:
            root = ET.parse(file).getroot()
            parent = root.find("instance_reference[@name='parent_pbg']")
            self.assertTrue(parent.get('value').startswith(file.parts[-3] + '\\races\\sultanate\\'))
            self.assertIsNone(parent.get('mod'))
            ids.append(root.find("uniqueid[@name='pbgid']").get('value'))
            for variant in root.findall('variant'):
                self.assertEqual(variant.find("uniqueid[@name='pbgid']").get('value'), ids[-1])
        self.assertEqual(len(set(ids)), 6)

    def test_town_centers_and_squad_loadouts_refer_to_private_units(self):
        files = list((ROOT / 'assets/attrib/instances').glob('*/persia/ps_probe_*.xml'))
        self.assertEqual(len(files), 6)
        for file in files:
            root = ET.parse(file).getroot()
            for ref in root.iter('instance_reference'):
                if ref.get('name') in ('squad', 'type'):
                    self.assertEqual(ref.get('mod'), GUID)
                    self.assertIn('\\persia\\ps_probe_', ref.get('value'))
            for node in root.iter('template_reference'):
                self.assertNotEqual(node.get('List.ListAction'), 'Append')

    def test_migration_inventory_and_source_preservation(self):
        path = ROOT / 'work/persia_port_20261026/migration-map.json'
        self.assertTrue(path.exists(), 'Migration ledger must be present')
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(len(data['instances']), 281)
        self.assertEqual(data['overlapping_id_values'], 122)
        self.assertEqual(data['starting_army']['resource_delta'], {'food': 0.0, 'wood': 0.0, 'gold': 0.0, 'stone': 0.0})


if __name__ == '__main__':
    unittest.main()
