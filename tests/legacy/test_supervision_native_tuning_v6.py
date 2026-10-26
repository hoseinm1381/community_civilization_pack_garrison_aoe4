"""Native XML target requirements and identity contracts; no engine claim."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as E
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ABILITY=ROOT/'assets/attrib/instances/abilities/vietnam'
DONOR=ROOT/'work/vietnam_redesign/runtime_v6_20261023/supervision/xml/production_building_enhance_abb.xml'
PADDY='ebps\\vietnam\\buildings\\economy\\rice_paddies\\vn_building_resource_farm_chi'

def parse(action):return E.parse(ABILITY/f'vn_buffalo_{action}_paddy_vit.xml').getroot()

def accepts(node,pbg,owner,complete):
    kind=node.get('value','').split('\\')[-1]
    if kind=='required_all_in_list':return all(accepts(x,pbg,owner,complete) for x in node.find("list[@name='requirements']"))
    if kind=='required_is_entity_pbg':return pbg==node.find("instance_reference[@name='is_entity_pbg']").get('value')
    if kind=='required_ownership':return owner=='self'
    if kind=='required_constructionstate':return complete
    raise AssertionError('Unexpected inherited target condition: '+kind)

class SupervisionNativeV6(unittest.TestCase):
    def test_work_has_exact_completed_owned_target_filter(self):
        requirements=parse('work').find("group/list[@name='requirements_target']")
        self.assertTrue(len(requirements),'the old ability accepted arbitrary entity targets')
        def match(pbg=PADDY,owner='self',complete=True):return all(accepts(n,pbg,owner,complete) for n in requirements)
        self.assertTrue(match())
        self.assertFalse(match(owner='ally'));self.assertFalse(match(owner='enemy'));self.assertFalse(match(complete=False))
        self.assertFalse(match(pbg=PADDY.replace('_farm_chi','_farm2_chi')))
        self.assertFalse(match(pbg='ebps\\races\\chinese\\buildings\\building_resource_farm_chi'))
        self.assertFalse(match(pbg='ebps\\gaia\\tree'))

    def test_requirements_override_exact_native_list_identities_without_append(self):
        root=parse('work')
        self.assertEqual(root.find("instance_reference[@name='parent_pbg']").get('value'),'abilities\\modal_abilities\\abbasid_ha_01\\production_building_enhance_abb')
        native=E.parse(DONOR).getroot();self.assertFalse(native.findall('variant'))
        self.assertEqual(native.find("instance_reference[@name='parent_pbg']").get('value'),'')
        wanted=root.find("group/list[@name='requirements_target']")
        original=native.find("group/list[@name='requirements_target']")
        def check(local,parent):
            self.assertEqual(local.get('overrideParent'),'True')
            for node in local:
                identity=node.get('List.ItemID');self.assertEqual(node.get('List.ParentItemID'),identity)
                self.assertIsNone(node.get('List.ListAction'))
                base=next((n for n in parent if n.get('List.ItemID')==identity),None)
                self.assertIsNotNone(base,identity)
                for sub in node.findall('list'):
                    check(sub,base.find("list[@name='"+sub.get('name')+"']"))
        check(wanted,original)

    def test_parent_effects_are_explicitly_neutralized_and_private_identities_kept(self):
        for action,pbgid in [('work','2147482514'),('leave','2147482517')]:
            root=parse(action)
            self.assertEqual(root.find("uniqueid[@name='pbgid']").get('value'),pbgid)
            self.assertTrue(all(x.get('value')=='' for x in root.findall('.//state_tree_node')))
            self.assertTrue(all(x.get('value')=='0' for x in root.findall(".//enum_table[@name='cost_to_player']/float")))
        root=parse('work');native=E.parse(DONOR).getroot()
        for node in native.find('group'):
            self.assertIsNotNone(root.find("group/*[@name='"+node.get('name')+"']"),node.get('name'))
        for node in root.findall('.//state_tree_node'):self.assertEqual(node.get('overrideParent'),'True')

    def test_v9_normal_and_extended_command_slots_and_five_metre_range_snapshot(self):
        # v10 intentionally narrows the native cast to the centre; retain the
        # accepted v9 range/slot contract against its actual preserved source.
        def snapshot(action):
            with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v10_20261023/before.zip') as archive:
                return E.fromstring(archive.read(f'assets/attrib/instances/abilities/vietnam/vn_buffalo_{action}_paddy_vit.xml'))
        for action,column in [('work','3'),('leave','4')]:
            root=snapshot(action)
            for position in root.findall(".//group[@name='ui_position']"):
                self.assertEqual(position.find("int[@name='ui_position_row']").get('value'),'1')
                self.assertEqual(position.find("int[@name='ui_position_column']").get('value'),column)
        work=snapshot('work')
        for name,value in [('range','5'),('use_simbox_to_simbox_range','False'),('range_ignore','False'),('can_move_to_cast','True')]:
            self.assertEqual(work.find("group/*[@name='"+name+"']").get('value'),value)
