"""Native cattle dependency/cap contracts; actual crash stability needs a match."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest
import xml.etree.ElementTree as E
from buffalo_source_helpers import ROOT,NATIVE,raw_cattle,effective_cattle

@unittest.skip('Cattle-based Buffalo retired by user; active elephant unit covered by test_elephant_buffalo.')
class BuffaloNativeChildTests(unittest.TestCase):
    def test_native_ancestry_and_only_balance_identity_overrides(self):
        allowed={'ebps':{r'ebpextensions\health_ext',r'ebpextensions\population_ext'},
                 'sbps':{r'sbpextensions\squad_ui_ext',r'sbpextensions\squad_loadout_ext',r'sbpextensions\squad_requirement_ext'}}
        for kind in allowed:
            r=raw_cattle(kind)
            self.assertEqual(r.find('instance_reference[@name="parent_pbg"]').get('value'),NATIVE[kind])
            self.assertFalse(r.findall('variant'))
            exts=r.find('list')
            self.assertEqual({x.get('value') for x in exts},allowed[kind])
            for ext in exts:
                self.assertEqual(ext.get('List.ItemID'),ext.get('List.ParentItemID'))
                self.assertNotIn('List.ListAction',ext.attrib)
            self.assertFalse(r.findall('.//state_tree_node'))
            self.assertFalse(r.findall('.//string[@name="state_tree"]'))
            self.assertFalse(r.findall('.//instance_reference[@name="schema"]'))

    def test_independent_native_fifteen_cap_and_zero_population_cost(self):
        e=effective_cattle('ebps');s=effective_cattle('sbps')
        self.assertEqual(e.find('.//float[@name="hitpoints"]').get('value'),'125')
        pop=e.find('list/template_reference[@value="ebpextensions\\population_ext"]')
        self.assertEqual({n:pop.find(f'float[@name="{n}"]').get('value') for n in ['personnel_pop','vehicle_pop','medic_pop']},
                         {'personnel_pop':'0','vehicle_pop':'0','medic_pop':'0'})
        req=s.find('.//template_reference[@value="requirements\\required_squad"]')
        self.assertEqual(req.find('float[@name="max_squad_cap"]').get('value'),'15')
        ref=req.find('instance_reference[@name="squad_name"]')
        self.assertEqual(ref.get('value'),'sbps\\vietnam\\units\\economy\\experimental_cattle\\vn_unit_water_buffalo_vit')
        self.assertEqual(ref.get('mod'),'a743d7d1d7534cf78817e29d8ded7366')
        self.assertIsNone(e.find('.//template_reference[@value="ebpextensions\\combat_ext"]'))

    def test_all_seventeen_production_routes_use_custom_squad(self):
        refs=[]
        for p in (ROOT/'assets/attrib/instances').rglob('*.xml'):
            for ref in parse_current_xml(p).findall('.//list[@name="spawn_items"]/group/instance_reference[@name="squad"]'):
                self.assertNotEqual(ref.get('value'),NATIVE['sbps'],p.name)
                if ref.get('value')=='sbps\\vietnam\\units\\economy\\experimental_cattle\\vn_unit_water_buffalo_vit':
                    refs.append(ref)
                    self.assertEqual(ref.get('mod'),'a743d7d1d7534cf78817e29d8ded7366')
        self.assertEqual(len(refs),17)

    def test_native_controller_schema_and_worker_start_remain(self):
        e=effective_cattle('ebps');s=effective_cattle('sbps')
        self.assertEqual(e.find('.//template_reference[@value="ebpextensions\\action_tree_ext"]/state_tree_node').get('value'),'unit_ownedgaia')
        self.assertEqual(e.find('.//string[@name="state_tree"]').get('value'),r'unit_action_apply\gaia\cattle')
        self.assertEqual(s.find('.//instance_reference[@name="schema"]').get('value'),r'statemodel_schema\units\civilizations\malian\cattle_mal')
        source=(current_path(ROOT/'assets/scar/vietnam/initialization.scar')).read_text()
        self.assertIn(':vn_unit_war_elephant_1_vit',source)
        self.assertNotIn(':vn_unit_water_buffalo_vit',source)
        lifecycle=(current_path(ROOT/'assets/scar/vietnam/lifecycle.scar')).read_text()
        self.assertNotIn('VietnamBuffalo_Start',lifecycle)

if __name__=='__main__':unittest.main()
