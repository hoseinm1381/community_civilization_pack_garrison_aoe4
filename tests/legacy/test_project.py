from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import csv
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectContractTests(unittest.TestCase):
    def test_modes_and_tuning_share_new_project_identity(self):
        identity = json.loads((current_path(ROOT / 'docs/editor-identity.json')).read_text())
        guid = identity['project_guid'].replace('-', '')
        manifest = parse_current_xml(ROOT / 'assets/attrib/Vietnam_v2.xml').getroot()
        mode = parse_current_xml(ROOT / 'assets/scar/winconditions/VietnamMode.rdo').getroot()
        self.assertEqual(manifest.get('guid'), guid)
        self.assertEqual(mode.find("./DataObject/DataProperty[@Name='m_tuningModGUID']").get('Value'), guid)
        self.assertNotEqual(guid, '4df51f363d114b518cca8b22c21f28e7')

    def test_no_official_blueprint_overrides_in_migrated_pack(self):
        files = list((ROOT / 'assets/attrib/instances').rglob('*.xml'))
        self.assertGreaterEqual(len(files), 7)
        for path in files:
            self.assertIn('vietnam', path.parts)
            self.assertTrue(path.stem.startswith('vn_'), str(path))

    def test_every_own_reference_resolves_to_this_project(self):
        identity = json.loads((current_path(ROOT / 'docs/editor-identity.json')).read_text())
        guid = identity['project_guid'].replace('-', '')
        folder = ROOT / 'assets/attrib/instances'
        files = list(folder.rglob('*.xml'))
        self.assertTrue(files)
        keys = {str(p.relative_to(folder).with_suffix('')).replace('/', '\\').lower() for p in files}
        for path in files:
            for node in parse_current_xml(path).getroot().iter('instance_reference'):
                if node.get('mod'):
                    self.assertEqual(node.get('mod'), guid, str(path))
                    self.assertIn(node.get('value').lower(), keys, str(path))

    def test_every_mode_localization_key_has_english_text(self):
        with (ROOT / 'assets/locdb/Vietnam_v2_en.csv').open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        loc = {row['ID']: row['Text'] for row in rows}
        self.assertEqual(len(rows), len(loc))
        for path in [ROOT / 'assets/mod.rdo', ROOT / 'assets/scar/winconditions/VietnamMode.rdo']:
            for node in parse_current_xml(path).getroot().iter('DataProperty'):
                if node.get('Name') == 'm_locStringKey':
                    self.assertTrue(loc.get(node.get('Value')), str(path))
        metadata = parse_current_xml(ROOT / 'assets/locdb/Vietnam_v2.locdb').getroot()
        names = [n.text for n in metadata.iter() if n.tag.rsplit('}',1)[-1] == 'Name']
        self.assertEqual(names, ['en'])

    def test_precache_contains_every_active_private_entity(self):
        mode = parse_current_xml(ROOT / 'assets/scar/winconditions/VietnamMode.rdo').getroot()
        names = {n.get('Value') for n in mode.iter('DataProperty') if n.get('Name') == 'm_fileName'}
        guid = json.loads((current_path(ROOT / 'docs/editor-identity.json')).read_text())['project_guid'].replace('-', '')
        entities = {guid + ':' + p.stem for p in (ROOT / 'assets/attrib/instances/ebps/vietnam').rglob('*.xml')}
        self.assertTrue(entities)
        self.assertTrue(entities <= names)

    def test_new_rdo_object_identities_are_unique_and_not_template_ids(self):
        ids = []
        for path in [ROOT / 'assets/mod.rdo', ROOT / 'assets/scar/winconditions/VietnamMode.rdo']:
            ids.extend(n.get('Id') for n in parse_current_xml(path).getroot().iter('DataObject'))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreater(len(ids), 5)

    def test_package_archive_identity_is_the_new_project(self):
        guid = json.loads((current_path(ROOT / 'docs/editor-identity.json')).read_text())['project_guid'].replace('-', '')
        root = parse_current_xml(ROOT / 'assets/_default.burnproj').getroot()
        parents = {child:parent for parent in root.iter() for child in parent}
        nice_name = next(n for n in root.iter() if n.tag.rsplit('}',1)[-1] == 'NiceName')
        values = {n.tag.rsplit('}',1)[-1]:n.text for n in parents[nice_name]}
        self.assertEqual(values['NiceName'], guid)
        self.assertEqual(values['Name'], 'Vietnam_v2')

    def test_active_builders_do_not_offer_mongol_packed_buildings(self):
        for name in ('vn_unit_villager_1_chi', 'vn_unit_villager_3_chi'):
            p = ROOT / 'assets/attrib/instances/sbps/vietnam' / (name + '.xml')
            items = [n for n in parse_current_xml(p).getroot().iter('group')
                     if n.get('name') == 'construction_item']
            values = [n.get('value', '') for item in items for n in item
                      if n.tag == 'instance_reference' and n.get('name') == 'ebp']
            self.assertTrue(values, name)
            self.assertFalse(any('mongol' in value for value in values), name)


if __name__ == '__main__':
    unittest.main()
