"""Source contracts for the first cleanup batch; run by the project owner.

These checks cannot prove model loading, UI armor, or native queue behavior.
"""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTANCES = ROOT / 'assets/attrib/instances'
TECH = 'upgrade\\vietnam\\vn_ratten_shield_vit'
PRODUCERS = (
    'vn_building_defense_outpost_chi',
    'vn_building_defense_outpost_2_chi',
    'vn_building_landmark_age1_gatehouse_control_chi',
    'vn_building_landmark_age3_trung_foundaries_vit',
    'vn_building_unit_ranged_control_chi',
)


class CleanupStageOneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'docs/cleanup-stage1-manifest.json').read_text())

    def test_retired_files_and_private_references_are_absent(self):
        removed_keys = set()
        removed_names = set()
        for record in self.manifest['removed_files']:
            path = ROOT / record['path']
            self.assertFalse(path.exists(), str(path))
            if record['pbg_id'] is not None:
                removed_keys.add(str(path.relative_to(INSTANCES).with_suffix('')).replace('/', '\\'))
                removed_names.add(self.manifest['guid'] + ':' + path.stem)
            if record['replacement']:
                self.assertTrue((ROOT / record['replacement']).exists(), record['replacement'])
        for path in INSTANCES.rglob('*.xml'):
            for ref in ET.parse(path).getroot().iter('instance_reference'):
                self.assertNotIn(ref.get('value'), removed_keys, str(path))
        rdo = ET.parse(ROOT / 'assets/scar/winconditions/VietnamMode.rdo').getroot()
        for node in rdo.iter('DataProperty'):
            if node.get('Name') == 'm_fileName':
                self.assertNotIn(node.get('Value'), removed_names)
        for path in (ROOT / 'assets/scar').rglob('*.scar'):
            source = path.read_text()
            for name in removed_names:
                self.assertNotIn('"' + name + '"', source, str(path))

    def test_consolidated_producers_have_one_entry_per_squad(self):
        for name in PRODUCERS:
            root = ET.parse(INSTANCES / 'ebps/vietnam' / (name + '.xml')).getroot()
            for items in root.iter('list'):
                if items.get('name') != 'spawn_items':
                    continue
                squads = [ref.get('value') for item in items for ref in item
                          if ref.tag == 'instance_reference' and ref.get('name') == 'squad'
                          and ref.get('value')]
                self.assertEqual(len(squads), len(set(squads)), name)
                self.assertFalse(any('_ratten' in squad or '_outpost_' in squad for squad in squads), name)

    def test_research_does_not_hide_or_convert_regular_units(self):
        checked = 0
        for category in ('ebps', 'sbps'):
            for path in (INSTANCES / category / 'vietnam').glob('vn_unit_*.xml'):
                checked += 1
                refs = [n.get('value') for n in ET.parse(path).getroot().iter('instance_reference')]
                self.assertNotIn(TECH, refs, str(path))
        self.assertGreater(checked, 0)

    def test_normal_age_progression_matches_precleanup_source(self):
        for relative, expected in self.manifest['preserved_age_progression'].items():
            root = ET.parse(ROOT / relative).getroot()
            actual = []
            for tier in root.iter('group'):
                if tier.get('name') != 'tier':
                    continue
                refs = {n.get('name'): n.get('value', '') for n in tier
                        if n.tag == 'instance_reference'}
                requirement = refs.get('statetree_tier_requirements_pbg', '')
                if requirement and requirement != TECH:
                    actual.append({key: refs.get(key, '') for key in (
                        'statetree_tier_requirements_pbg',
                        'statetree_tier_pgb_upgrade_target_entity',
                        'statetree_tier_pgb_upgrade_target_squad')})
            self.assertEqual(actual, expected, relative)

    def test_discounted_handcannon_still_depends_on_trung_foundries(self):
        landmark = 'ebps\\vietnam\\vn_building_landmark_age3_trung_foundaries_vit'
        for name, negated in (('vn_unit_handcannon_4_chi', True),
                              ('vn_unit_handcannon_4_chi_cheap', False)):
            root = ET.parse(INSTANCES / 'sbps/vietnam' / (name + '.xml')).getroot()
            parents = {child: parent for parent in root.iter() for child in parent}
            refs = [n for n in root.iter('instance_reference')
                    if n.get('name') == 'structure_name' and n.get('value') == landmark]
            self.assertTrue(refs, name)
            for ref in refs:
                node = parents[ref]
                self.assertEqual(node.get('value'), 'requirements\\required_structure')
                ancestors = []
                while node in parents:
                    node = parents[node]
                    ancestors.append(node.get('value'))
                self.assertEqual('requirements\\required_not' in ancestors, negated, name)

    def test_handcannon_default_visual_tiers_are_preserved(self):
        def signature(node):
            return {'tag': node.tag, 'attributes': dict(node.attrib),
                    'children': [signature(child) for child in node]}
        path = INSTANCES / 'ebps/vietnam/vn_unit_handcannon_4_chi.xml'
        tiers = [signature(node) for node in ET.parse(path).getroot().iter('group')
                 if node.get('name') == 'tier']
        self.assertEqual(tiers, self.manifest['preserved_handcannon_base_tiers'])

    def test_visible_rattan_research_is_retained_with_original_cost(self):
        tech = ET.parse(INSTANCES / 'upgrade/vietnam/vn_ratten_shield_vit.xml').getroot()
        cost = tech.find("group[@name='upgrade_bag']/group[@name='time_cost']/enum_table[@name='cost']")
        values = {node.get('name'): node.get('value') for node in cost}
        self.assertEqual(values['wood'], '100')
        self.assertEqual(values['gold'], '200')
        building = ET.parse(INSTANCES / 'ebps/vietnam/vn_building_unit_ranged_control_chi.xml').getroot()
        refs = [n for n in building.iter('instance_reference')
                if n.get('name') == 'upgrade' and n.get('value') == TECH]
        self.assertTrue(refs)


if __name__ == '__main__':
    unittest.main()
