"""Native nonmodal multiselect carrier shape matches current official analogues."""
import json,unittest,xml.etree.ElementTree as E
from test_runtime_repairs import ROOT
PATH=ROOT/'assets/attrib/instances/abilities/vietnam/vn_vietnam_unit_mov_vit.xml'
EVIDENCE=ROOT/'work/vietnam_redesign/runtime_v6_20261023/tunnels/multicast-official.json'

class NativeTunnelTuningV6(unittest.TestCase):
    def test_mass_cast_shape_matches_three_current_official_timed_abilities(self):
        tree=E.parse(PATH).getroot();bag=tree.find("group[@name='ability_bag']")
        evidence=json.loads(EVIDENCE.read_text())
        self.assertEqual(len(evidence['donors']),3)
        for donor in evidence['donors']:
            for key,expected in donor['values'].items():
                with self.subTest(donor=donor['member'],field=key):
                    self.assertEqual(bag.find("enum[@name='"+key+"']").get('value'),expected)

    def test_carrier_preserves_identity_and_has_no_native_effect_trees_or_target_requirements(self):
        tree=E.parse(PATH).getroot();bag=tree.find("group[@name='ability_bag']")
        self.assertEqual(tree.find("uniqueid[@name='pbgid']").get('value'),'1073741849')
        self.assertEqual(tree.find("instance_reference[@name='parent_pbg']").get('value'),'')
        self.assertTrue(all(not n.get('value') for n in tree.iter('state_tree_node')))
        self.assertEqual(len(bag.find("list[@name='requirements_target']")),0)
        self.assertEqual(bag.find("float[@name='entity_busy_time']").get('value'),'0')
        self.assertEqual(bag.find("bool[@name='can_move_to_cast']").get('value'),'False')

    def test_multiselect_uses_multi_and_all_entities_not_single_cast(self):
        bag=E.parse(PATH).getroot().find("group[@name='ability_bag']")
        self.assertEqual(bag.find("enum[@name='ui_group_cast_type']").get('value'),'multi')
        self.assertEqual(bag.find("enum[@name='squad_caster']").get('value'),'all_entities')

if __name__=='__main__':unittest.main()
