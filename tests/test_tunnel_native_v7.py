"""Native targeted click and isolated empire cooldown data; no runtime claims."""
import unittest
import json
import zipfile
import xml.etree.ElementTree as ET
from test_runtime_repairs import ROOT

REL = 'assets/attrib/instances/abilities/vietnam/vn_vietnam_unit_mov_vit.xml'
EVIDENCE = ROOT / 'work/vietnam_redesign/runtime_v7_20261023/tunnel-contract'
ALLOWED = {'activation', 'target', 'recharge_time', 'shared_timer_player_wide'}


def values(root):
    return {n.get('name'): n.get('value') for n in root.find("group[@name='ability_bag']")
            if n.get('name') in ALLOWED}


def contract(root):
    return values(root) == {'activation': 'targeted', 'target': 'tp_position',
                            'recharge_time': '30', 'shared_timer_player_wide': 'True'}


class NativeTunnelV7(unittest.TestCase):
    def test_committed_ability_getter_type_and_key_match_current_official_schema(self):
        enums = ET.parse(EVIDENCE / 'EngineRef__enums.xml').getroot()
        entry = enums.find("enum[@name='statetree_commited_target_type']")
        self.assertIsNotNone(entry)
        self.assertIn('COMMITTED_ABILITY', [node.text for node in entry.findall('value')])
        source = (EVIDENCE / 'cardinal__targetconstants__cardinal.scar').read_text()
        self.assertIn('target_type="statetree_commited_target_type"', source)

    def test_current_native_ability_producers_copy_target_to_exact_committed_slot(self):
        native = json.loads((EVIDENCE / 'native-ability-producer.json').read_text())
        hashes = json.loads((EVIDENCE / 'current-native-tree-hash-proof.json').read_text())
        self.assertEqual([row['sha256'] for row in hashes if row['matches_trace']],
                         [native['source_sha256']])
        self.assertEqual(native['validated_objects'], 410924)
        self.assertEqual(len(native['objects']), 19)
        self.assertTrue(any(row['path'] == 'command_ability_target/ability_target'
                            for row in native['objects']))
        for row in native['objects']:
            self.assertEqual(row['type'], 'StateTree::Entity_ProcessAbilityCommand')
            self.assertEqual(row['fields']['m_copyToCommittedTargetEnum']['text'],
                             'COMMITTED_ABILITY')

    def test_native_targeted_ground_click_and_empire_cooldown(self):
        self.assertTrue(contract(ET.parse(ROOT / REL).getroot()))

    def test_actual_v6_regression_has_wrong_activation_and_no_cooldown(self):
        with zipfile.ZipFile(EVIDENCE.parent / 'before.zip') as before:
            old = ET.fromstring(before.read(REL))
        self.assertFalse(contract(old))
        self.assertEqual(values(old), {'activation': 'timed', 'target': 'tp_any',
                                     'recharge_time': '0', 'shared_timer_player_wide': 'False'})

    def test_exact_changes_preserve_native_identity_effects_and_other_data(self):
        with zipfile.ZipFile(EVIDENCE.parent / 'before.zip') as before:
            old = ET.fromstring(before.read(REL))
        new = ET.parse(ROOT / REL).getroot()
        for root in (old, new):
            bag = root.find("group[@name='ability_bag']")
            for child in list(bag):
                if child.get('name') in ALLOWED:
                    bag.remove(child)
        self.assertEqual(ET.tostring(old), ET.tostring(new))
        bag = new.find("group[@name='ability_bag']")
        self.assertEqual(bag.find("enum[@name='shared_timer']").get('value'), '')
        self.assertTrue(all(not node.get('value') for node in new.iter('state_tree_node')))

    def test_current_official_donors_prove_target_and_global_timer_schema(self):
        donor = ET.parse(EVIDENCE / 'ReferenceAttributes__shinobi_blink_jpn.xml').getroot()
        bag = donor.find("group[@name='ability_bag']")
        self.assertEqual(bag.find("enum[@name='activation']").get('value'), 'targeted')
        self.assertEqual(bag.find("enum[@name='target']").get('value'), 'tp_position')
        self.assertEqual(bag.find("float[@name='recharge_time']").get('value'), '30')
        template = ET.parse(EVIDENCE / 'EngineRef__abilities.xml').getroot()
        field = template.find("group[@name='ability_bag']/bool[@name='shared_timer_player_wide']")
        self.assertIn('all instances of THIS ability on ANY unit', field.get('description'))


if __name__ == '__main__':
    unittest.main()
