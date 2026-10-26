"""Native research source contracts; in-game torch damage still needs testing."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTR = ROOT / 'assets/attrib/instances'
TECH = 'upgrade\\vietnam\\vn_upgrade_scorched_earth_vit'


class ScorchedEarthTests(unittest.TestCase):
    def setUp(self):
        self.root = parse_current_xml(ATTR / (TECH + '.xml').replace('\\', '/')).getroot()
        self.bag = self.root.find('group[@name="upgrade_bag"]')

    def test_research_contract_and_repeat_guard(self):
        cost = self.bag.find('group[@name="time_cost"]/enum_table')
        for key, value in dict(food='50', wood='0', gold='50', stone='0').items():
            self.assertEqual(cost.find(f'float[@name="{key}"]').get('value'), value)
        self.assertEqual(self.bag.find('group[@name="time_cost"]/float').get('value'), '30')
        reqs = self.bag.find('list[@name="requirements"]')
        self.assertIsNotNone(reqs.find('.//instance_reference[@value="upgrade\\dev\\ages\\feudal_age"]'))
        guard = next(n for n in reqs if n.find('instance_reference').get('value') == TECH)
        self.assertEqual(guard.find('bool[@name="is_present"]').get('value'), 'False')
        self.assertEqual(guard.find('bool[@name="include_queued"]').get('value'), 'True')

    def test_only_light_infantry_torch_damage_changes(self):
        filters = self.bag.find('group[@name="filter_conditions"]')
        self.assertEqual([n.get('value') for n in filters.findall('list/enum')], ['infantry_light'])
        self.assertEqual(filters.find('enum[@name="apply_to_future_units"]').get('value'), 'current_and_future_units')
        effects = self.bag.find('group[@name="state_tree_references"]')
        active = [n.get('value') for n in effects.iter('state_tree_node') if n.get('value')]
        self.assertEqual(active, [])  # Failed donor effect retired; one SCAR weapon-type owner.
        floats = {n.find('enum').get('value'): n.find('float').get('value')
                  for n in self.bag.find('list[@name="float_properties"]')}
        self.assertEqual(floats, {})
        source=(current_path(ROOT/'assets/scar/vietnam/scorched_earth.scar')).read_text(encoding='utf-8')
        self.assertIn('MAT_WeaponType, "damage_weapon_modifier"',source)
        self.assertIn('MUT_Multiplication, false, 1.2, torch',source)

    def test_blacksmith_access_both_scopes(self):
        smith = parse_current_xml(ATTR / 'ebps/vietnam/vn_building_tech_unit_infantry_control_chi.xml').getroot()
        for scope in [smith, smith.find('variant')]:
            refs = scope.findall('list/template_reference/list[@name="standard_upgrades"]/instance_reference')
            self.assertEqual(sum(n.get('value') == TECH for n in refs), 1)


if __name__ == '__main__':
    unittest.main()
