"""Actual failed-source guard and SCAR eligibility lifecycle; not native proof."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as E
import zipfile
import json
import test_systems_20261022 as systems

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=ROOT/'work/vietnam_redesign/runtime_v7_20261023/before.zip'
ABILITY='assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'

def assert_entity_gate(case, data):
    root=E.fromstring(data)
    gate=root.find(".//list[@name='requirements']/template_reference")
    case.assertEqual(gate.get('value'),r'requirements\required_statemodelbool')
    case.assertEqual(gate.find("enum[@name='key']").get('value'),'is_in_stealth_aura_mal')
    case.assertEqual(gate.find("enum[@name='data_source_type']").get('value'),'entity_datasource',
                     'The eligibility value is written on the ENTITY; do not depend on original executor/target datasource')

class HeadquartersEligibilityV7(systems.HeadquartersTests):
    def setUp(self):
        super().setUp()
        self.runlua('''
        function Entity_GetStateModelBool(e,k)
          if k=='landmark_active' then return e.active~=false end
          return e.flags and e.flags[k]==true or false
        end
        ''')

    def test_departure_and_reentry_use_requirements_without_abrupt_passive_stop(self):
        self.runlua('v.hasAbility=true;v.doing=true')
        for x, expected in [(30,True),(100,False),(30,True),(100,False),(30,True)]:
            self.runlua(f'v.x={x}')
            self.tick()
            self.assertEqual(self.g.v.flags['is_in_stealth_aura_mal'],expected)
            self.assertTrue(self.g.v.hasAbility)
            self.assertIsNone(self.g.v.stopped)
            self.assertIsNone(self.g.v.added)
            self.assertIsNone(self.g.v.removed)

    def test_hold_exits_and_release_reenters_without_rebinding_or_orders(self):
        self.runlua('v.hasAbility=true;function Entity_IsInHold(e) return e.held==true end')
        self.tick()
        self.runlua('v.held=true');self.tick()
        self.assertFalse(self.g.v.flags['is_in_stealth_aura_mal'])
        self.runlua('v.held=false');self.tick()
        self.assertTrue(self.g.v.flags['is_in_stealth_aura_mal'])
        self.assertIsNone(self.g.v.stopped)
        self.assertIsNone(self.g.v.added)

    def test_delayed_native_state_is_observed_without_forcing_reveal_state(self):
        self.tick()
        self.assertFalse(self.g.v.flags['is_toggled_stealth'] or False)
        self.runlua("v.flags.is_toggled_stealth=true;v.doing=true")
        self.tick()
        self.assertTrue(self.g.v.flags['is_toggled_stealth'])
        self.runlua("v.flags.is_toggled_stealth=false;v.doing=false")
        self.tick()
        self.assertFalse(self.g.v.flags['is_toggled_stealth'])
        self.assertTrue(self.g.v.flags['is_in_stealth_aura_mal'])
        self.assertIsNone(self.g.v.stopped)

    def test_town_centers_and_feudal_headquarters_never_supply_stealth(self):
        self.runlua("hq.bp='a743d7d1d7534cf78817e29d8ded7366:vn_building_town_center_capital_chi'")
        self.tick()
        self.assertIsNone(self.g.v.flags)
        self.runlua("hq.bp='a743d7d1d7534cf78817e29d8ded7366:vn_building_landmark_age1_headquarters_control_chi'")
        self.tick()
        self.assertIsNone(self.g.v.flags)

class HeadquartersDataV7(unittest.TestCase):
    def test_current_receiver_explicitly_reads_entity_state(self):
        assert_entity_gate(self,(ROOT/ABILITY).read_bytes())

    def test_actual_failed_source_fails_entity_gate_contract(self):
        with zipfile.ZipFile(SNAPSHOT) as z:
            with self.assertRaisesRegex(AssertionError,'entity_datasource'):
                assert_entity_gate(self,z.read(ABILITY))

    def test_only_data_source_selector_changes_from_failed_ability(self):
        with zipfile.ZipFile(SNAPSHOT) as z:before=z.read(ABILITY)
        expected=before.replace(b'name="data_source_type" value="self_datasource"',
                                b'name="data_source_type" value="entity_datasource"')
        self.assertEqual((ROOT/ABILITY).read_bytes(),expected)

    def test_receiver_ebps_sbps_and_schema_preserved_from_actual_failed_source(self):
        with zipfile.ZipFile(SNAPSHOT) as z:
            for name in z.namelist():
                if not name.startswith('assets/attrib/instances/'):continue
                if any(key in name for key in ('vn_unit_villager_','vn_unit_trade_cart_chi','vn_headquarters_')):
                    self.assertEqual((ROOT/name).read_bytes(),z.read(name),name)

    def test_script_never_abruptly_stops_or_removes_static_receiver(self):
        current=(ROOT/'assets/scar/vietnam/landmarks.scar').read_text()
        self.assertNotIn('Entity_StopAbility(',current)
        self.assertNotIn('Entity_RemoveAbility(',current)
        self.assertNotIn('Cmd_',current)
        self.assertNotIn('Entity_SetStateModelBool(e,"is_toggled_stealth"',current)

    def test_current_official_native_graph_enables_stealth_and_owns_toggle_and_teardown(self):
        evidence=ROOT/'work/vietnam_redesign/runtime_v7_20261023/stealth'
        receipts=json.loads((evidence/'official-receipts.json').read_text())
        self.assertTrue(any(r.get('matches_reflected_trace') for r in receipts),
                        'Reflected simulation graph must match the current installed Data.sga')
        rows=json.loads((evidence/'selected-native-tree.json').read_text())
        objects={r['id']:r for r in rows}
        path=r'activate_stealth_mal/Master/Defer_EnableStealth/EnableStealth'
        enable=[r for r in rows if r['path']==path]
        self.assertTrue(any(r['type']=='StateTree::MasterTrack' and r['fields']['m_timeEnd']==-1 for r in enable))
        self.assertTrue(any(r['type']=='StateTree::EntityTrack_SetStealthAllowed' and r['fields']['m_setStealthAllowed'] for r in enable))
        properties={r['owner']:r for r in enable if r['type'].startswith('PropertyBagGroupSchema')}
        toggles=[]
        for prop in enable:
            if prop['type']!='StateTree::BoolStateModelProperty':continue
            schema=properties[prop['id']]['fields']['m_schemaKey']['text']
            provider=objects[prop['fields']['m_sourceValueProvider']['target_id']]
            toggles.append((schema,provider['fields']['m_value']))
        self.assertIn(('is_toggled_stealth',True),toggles)
        self.assertIn(('is_toggled_stealth',False),toggles)
        disable=[r for r in rows if r['path']==path+'/DisableStealth']
        self.assertTrue(any(r['type']=='StateTree::Provider_StateModelProperty_Bool'
                            and r['fields']['m_key']['text']=='is_in_stealth_aura_mal' for r in disable))
        self.assertTrue(any(r['type']=='StateTree::EntityTrack_SetStealthAllowed'
                            and r['fields']['m_setStealthAllowed'] is False for r in disable))

if __name__=='__main__':unittest.main()
