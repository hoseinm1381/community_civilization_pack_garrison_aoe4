"""Verify retired access paths and unchanged ordinary Spearman combat/age data."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ATTR = ROOT / 'assets/attrib/instances'
KEY = 'upgrade\\vietnam\\vn_upgrade_spearman_firelance_vit'
BACKUP = ROOT / 'work/vietnam_redesign/rollback/2026-10-20_pre_firelance_retirement'


def canonical(node):
    return node.tag, sorted(node.attrib.items()), [canonical(c) for c in node]


class FireLanceRetirementTests(unittest.TestCase):
    def test_no_production_access_to_research_or_fire_spearmen(self):
        for path in (ATTR / 'ebps/vietnam').rglob('*.xml'):
            t = parse_current_xml(path).getroot()
            for n in t.findall('.//list[@name="standard_upgrades"]/instance_reference'):
                self.assertNotEqual(n.get('value'), KEY, path.name)
            for n in t.findall('.//group[@name="spawn_item"]/instance_reference[@name="squad"]'):
                self.assertNotIn('vn_unit_spearman_fire_', n.get('value', ''), path.name)

    def test_normal_spearman_weapons_and_age_groups_preserved(self):
        for age in [1, 2, 3, 4]:
            name = f'vn_unit_spearman_{age}_chi.xml'
            relative = 'assets/attrib/instances/ebps/vietnam/' + name
            old = parse_current_xml(BACKUP / relative).getroot()
            new = parse_current_xml(ROOT / relative).getroot()
            for original, current in zip([old, *old.findall('variant')], [new, *new.findall('variant')]):
                xpath = 'list/template_reference[@value="ebpextensions\\combat_ext"]'
                # Later Scorched Earth repair isolates an otherwise stock torch
                # under a private weapon ID. Normalize only that approved binding.
                for n in current.find(xpath).iter('instance_reference'):
                    if n.get('value')==r'weapon\vietnam\vn_weapon_light_infantry_torch_vit':
                        n.set('value',r'weapon\races\common\ranged\weapon_torch');n.attrib.pop('mod',None)
                self.assertEqual(canonical(original.find(xpath)), canonical(current.find(xpath)))
                weapons = current.find(xpath).findall('.//instance_reference[@name="non_entity_weapon_wrapper_pbg"]')
                self.assertEqual([n.get('value') for n in weapons], [
                    f'weapon\\races\\common\\melee\\weapon_spearman_{age}',
                    'weapon\\races\\common\\ranged\\weapon_torch',
                    f'weapon\\races\\common\\melee\\weapon_spearwall_{age}',
                    f'weapon\\races\\common\\melee\\weapon_spearman_{age}_charge',
                ])
                xpath = 'list/template_reference/list[@name="tier_group_list"]'
                self.assertEqual(len(current.find(xpath)), 1)
                self.assertEqual(canonical(original.find(xpath)[0]), canonical(current.find(xpath)[0]))
                self.assertFalse(any(n.get('value') == KEY for n in current.iter('instance_reference')))

    def test_normal_squad_not_hidden_by_retired_upgrade(self):
        for age in [1, 2, 3, 4]:
            path = ATTR / 'sbps/vietnam' / f'vn_unit_spearman_{age}_chi.xml'
            t = parse_current_xml(path).getroot()
            self.assertFalse(any(n.get('value') == KEY for n in t.iter('instance_reference')))

    def test_scorched_earth_preserved_in_blacksmith(self):
        t = parse_current_xml(ATTR / 'ebps/vietnam/vn_building_tech_unit_infantry_control_chi.xml').getroot()
        for scope in [t, *t.findall('variant')]:
            refs = scope.findall('list/template_reference/list[@name="standard_upgrades"]/instance_reference')
            self.assertEqual(sum(n.get('value') == 'upgrade\\vietnam\\vn_upgrade_scorched_earth_vit' for n in refs), 1)


if __name__ == '__main__':
    unittest.main()
