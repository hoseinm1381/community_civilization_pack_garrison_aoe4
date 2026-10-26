"""Source contracts for the first cleanup batch; run by the project owner.

These checks cannot prove model loading, UI armor, or native queue behavior.
"""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
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
        cls.manifest = json.loads((current_path(ROOT / 'docs/cleanup-stage1-manifest.json')).read_text())

    def test_retired_files_and_private_references_are_absent(self):
        removed_keys = set()
        removed_names = set()
        for record in self.manifest['removed_files']:
            path = ROOT / record['path']
            self.assertFalse(current_path(path).exists(), str(path))
            if record['pbg_id'] is not None:
                removed_keys.add(str(path.relative_to(INSTANCES).with_suffix('')).replace('/', '\\'))
                removed_names.add(self.manifest['guid'] + ':' + path.stem)
            if record['replacement']:
                self.assertTrue((current_path(ROOT / record['replacement'])).exists(), record['replacement'])
        for path in INSTANCES.rglob('*.xml'):
            for ref in parse_current_xml(path).getroot().iter('instance_reference'):
                self.assertNotIn(ref.get('value'), removed_keys, str(path))
        rdo = parse_current_xml(ROOT / 'assets/scar/winconditions/VietnamMode.rdo').getroot()
        for node in rdo.iter('DataProperty'):
            if node.get('Name') == 'm_fileName':
                self.assertNotIn(node.get('Value'), removed_names)
        for path in (ROOT / 'assets/scar').rglob('*.scar'):
            source = current_path(path).read_text()
            for name in removed_names:
                self.assertNotIn('"' + name + '"', source, str(path))

    def test_consolidated_producers_have_one_entry_per_squad(self):
        for name in PRODUCERS:
            root = parse_current_xml(INSTANCES / 'ebps/vietnam' / (name + '.xml')).getroot()
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
            for path in (INSTANCES / category / 'vietnam').rglob('vn_unit_*.xml'):
                checked += 1
                refs = [n.get('value') for n in parse_current_xml(path).getroot().iter('instance_reference')]
                self.assertNotIn(TECH, refs, str(path))
        self.assertGreater(checked, 0)

    def test_normal_age_progression_matches_precleanup_source(self):
        for relative, expected in self.manifest['preserved_age_progression'].items():
            # The approved Fire Lance retirement removes a separate weapon
            # conversion group, while retaining every normal age-up path.
            retired_firelance = 'upgrade\\vietnam\\vn_upgrade_spearman_firelance_vit'
            expected = [entry for entry in expected
                        if entry['statetree_tier_requirements_pbg'] != retired_firelance]
            expected = [{key:relocated(value) for key,value in entry.items()} for entry in expected]
            root = parse_current_xml(ROOT / relative).getroot()
            actual = []
            for tier in root.iter('group'):
                if tier.get('name') != 'tier':
                    continue
                refs = {n.get('name'): n.get('value', '') for n in tier
                        if n.tag == 'instance_reference'}
                requirement = refs.get('statetree_tier_requirements_pbg', '')
                # Lobed Maces adds a separate native weapon-variant tier;
                # its graph is checked in test_lobed_maces. Preserve the
                # original age-up paths against this historical manifest.
                weapon_upgrade = 'upgrade\\vietnam\\vn_upgrade_lobed_maces_vit'
                if requirement and requirement not in (TECH, weapon_upgrade):
                    actual.append({key: refs.get(key, '') for key in (
                        'statetree_tier_requirements_pbg',
                        'statetree_tier_pgb_upgrade_target_entity',
                        'statetree_tier_pgb_upgrade_target_squad')})
            self.assertEqual(actual, expected, relative)

    def test_regular_handcannon_available_and_retired_cheap_alias_retains_requirement(self):
        landmark = 'ebps\\vietnam\\buildings\\landmarks\\imperial\\vn_building_landmark_age3_trung_foundaries_vit'
        for name, negated in (('vn_unit_handcannon_4_chi', None),
                              ('vn_unit_handcannon_4_chi_cheap', False)):
            root = parse_current_xml(INSTANCES / 'sbps/vietnam' / (name + '.xml')).getroot()
            parents = {child: parent for parent in root.iter() for child in parent}
            refs = [n for n in root.iter('instance_reference')
                    if n.get('name') == 'structure_name' and n.get('value') == landmark]
            if negated is None:
                self.assertFalse(refs, name)
                continue
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
        tree = parse_current_xml(path).getroot()
        # Approved Serpentine research adds a separate native conversion group;
        # preserve this historical assertion for every original visual tier.
        for groups in tree.findall('.//list[@name="tier_group_list"]'):
            for group in list(groups):
                if any(n.get('value') == 'upgrade\\vietnam\\vn_upgrade_serpentine_powder_vit'
                       for n in group.iter('instance_reference')):
                    groups.remove(group)
        tiers = [signature(node) for node in tree.iter('group')
                 if node.get('name') == 'tier']
        self.assertEqual(tiers, self.manifest['preserved_handcannon_base_tiers'])

    def test_visible_rattan_research_uses_approved_redesign_values(self):
        tech = parse_current_xml(INSTANCES / 'upgrade/vietnam/vn_ratten_shield_vit.xml').getroot()
        cost = tech.find("group[@name='upgrade_bag']/group[@name='time_cost']/enum_table[@name='cost']")
        values = {node.get('name'): node.get('value') for node in cost}
        self.assertEqual(values['wood'], '50')
        self.assertEqual(values['gold'], '150')
        self.assertEqual(tech.find("group[@name='upgrade_bag']/group[@name='time_cost']/float[@name='time_seconds']").get('value'), '30')
        requirements = tech.find("group[@name='upgrade_bag']/list[@name='requirements']")
        self.assertTrue(any(node.get('value') == 'upgrade\\dev\\ages\\feudal_age'
                            for node in requirements.iter('instance_reference')))
        building = parse_current_xml(INSTANCES / 'ebps/vietnam/vn_building_unit_ranged_control_chi.xml').getroot()
        refs = [n for n in building.iter('instance_reference')
                if n.get('name') == 'upgrade' and n.get('value') == TECH]
        self.assertTrue(refs)


if __name__ == '__main__':
    unittest.main()
