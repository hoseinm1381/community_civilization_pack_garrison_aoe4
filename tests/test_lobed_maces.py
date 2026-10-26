"""Native conversion graph and preservation checks; no engine behavior claim."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
from pathlib import Path
import json
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ATTR = ROOT / 'assets/attrib/instances'
WORK = ROOT / 'work/vietnam_redesign'
KEY = 'upgrade\\vietnam\\vn_upgrade_lobed_maces_vit'
GRAPH = json.loads((current_path(WORK / 'LOBED_GRAPH.json')).read_text(encoding='utf-8'))


def canonical(node):
    return node.tag, sorted(node.attrib.items()), [canonical(c) for c in node]


class LobedMacesTests(unittest.TestCase):
    def test_imperial_research_cost_time_and_once_only(self):
        t = parse_current_xml(ATTR / 'upgrade/vietnam/vn_upgrade_lobed_maces_vit.xml').getroot()
        bag = t.find('group')
        cost = bag.find('group[@name="time_cost"]/enum_table')
        for key, value in dict(food='150', gold='350', wood='0', stone='0').items():
            self.assertEqual(cost.find(f'float[@name="{key}"]').get('value'), value)
        self.assertEqual(bag.find('group[@name="time_cost"]/float').get('value'), '30')
        requirements = bag.find('list[@name="requirements"]')
        self.assertIsNotNone(requirements.find('.//instance_reference[@value="upgrade\\dev\\ages\\imperial_age"]'))
        guard = next(n for n in requirements if n.find('instance_reference').get('value') == KEY)
        self.assertEqual(guard.find('bool[@name="is_present"]').get('value'), 'False')
        self.assertEqual(guard.find('bool[@name="include_queued"]').get('value'), 'True')
        self.assertFalse(any(n.get('value') for n in bag.findall('group[@name="state_tree_references"]//state_tree_node')))

    def test_native_conversion_graph_no_self_conversion_or_age_bypass(self):
        for child in GRAPH['entities']:
            base_name = child.removesuffix('_lobed')
            base = parse_current_xml(ATTR / 'ebps/vietnam' / (base_name + '.xml')).getroot()
            upgraded = parse_current_xml(ATTR / 'ebps/vietnam' / (child + '.xml')).getroot()
            self.assertEqual(upgraded.find('instance_reference').get('value'), blueprint_key('ebps',base_name))
            for scope, dst in zip([base, *base.findall('variant')], [upgraded, *upgraded.findall('variant')]):
                groups = scope.find('list/template_reference[@value="ebpextensions\\tier_ext"]/list')
                group = groups[-1]
                self.assertEqual(len(group), 2)
                stage = group[1]
                self.assertEqual(stage.find('instance_reference[@name="statetree_tier_requirements_pbg"]').get('value'), KEY)
                for category in ['entity', 'squad']:
                    prefix = 'ebps' if category == 'entity' else 'sbps'
                    self.assertEqual(stage.find(f'instance_reference[@name="statetree_tier_pgb_upgrade_target_{category}"]').get('value'), blueprint_key(prefix,child))
                removed = dst.find('list/template_reference[@value="ebpextensions\\tier_ext"]/list').get('removedIds')
                self.assertEqual(removed, group.get('List.ItemID'))
                self.assertEqual(group[0].find('instance_reference[@name="statetree_tier_pgb_upgrade_target_entity"]').get('value'), '')

    def test_all_original_unit_properties_and_age_conversions_unchanged(self):
        for child in GRAPH['entities']:
            name = child.removesuffix('_lobed') + '.xml'
            original = parse_current_xml(WORK / 'rollback/2026-10-20_pre_lobed_maces/assets/attrib/instances/ebps/vietnam' / name).getroot()
            current = parse_current_xml(ATTR / 'ebps/vietnam' / name).getroot()
            for scope in [current, *current.findall('variant')]:
                groups = scope.find('list/template_reference[@value="ebpextensions\\tier_ext"]/list')
                groups.remove(groups[-1])
            self.assertEqual(canonical(original), canonical(current))

    def test_private_weapon_deltas_only_heavy_bonus_and_squad_loadouts(self):
        self.assertEqual(len(GRAPH['weapons']), 6)
        for original, key in GRAPH['weapons'].items():
            self.assertNotIn('torch', original)
            path = ATTR / (key.replace('\\', '/') + '.xml')
            t = parse_current_xml(path).getroot()
            self.assertEqual(t.find('instance_reference').get('value'), original)
            self.assertEqual([n.get('name') for n in t.find('group')], ['target_type_table'])
            item = t.find('group/list/group')
            self.assertEqual(item.find('enum').get('value'), 'heavy')
            self.assertEqual(item.find('float').get('value'), '10')
        for name in GRAPH['squads']:
            t = parse_current_xml(ATTR / 'sbps/vietnam' / (name + '.xml')).getroot()
            refs = t.findall('.//instance_reference[@name="type"]')
            self.assertTrue(refs)
            self.assertTrue(all(n.get('value') == blueprint_key('ebps',name) for n in refs))

    def test_barracks_access_and_prematch_precache(self):
        t = parse_current_xml(ATTR / 'ebps/vietnam/vn_building_unit_infantry_control_chi.xml').getroot()
        for scope in [t, *t.findall('variant')]:
            refs = scope.findall('list/template_reference/list[@name="standard_upgrades"]/instance_reference')
            self.assertEqual(sum(n.get('value') == KEY for n in refs), 1)
        rdo = parse_current_xml(ROOT / 'assets/scar/winconditions/VietnamMode.rdo').getroot()
        for category, kind in [('entities', 'EntityPrecacheItem'), ('squads', 'SquadPrecacheItem')]:
            records = [n for n in rdo.iter('DataObject') if n.get('Type') == kind]
            for name in GRAPH[category]:
                self.assertTrue(any(any(n.get('Value', '').endswith(':' + name) for n in record.iter('DataProperty')) for record in records))


if __name__ == '__main__':
    unittest.main()
