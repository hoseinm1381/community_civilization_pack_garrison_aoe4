"""Consumer and inheritance regressions for the actual playable Water Buffalo."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'assets/attrib/instances'
BUFFALO = 'vn_unit_water_buffalo_vit'
FOUNDATION = 'vn_building_resource_farm2_chi'
FARM = 'vn_building_resource_farm_chi'

def instance(name, category):
    paths = list((BASE/category).rglob(name + '.xml'))
    assert len(paths) == 1, paths
    return E.parse(paths[0]).getroot()

class RuntimeV5Tuning(unittest.TestCase):
    def test_buffalo_uses_native_worker_behavior_without_cattle_resource_deposit(self):
        r = instance(BUFFALO, 'ebps')
        self.assertIn('vn_unit_war_elephant_1_vit', r.find("instance_reference[@name='parent_pbg']").get('value'))
        self.assertFalse(r.findall(".//template_reference[@value='ebpextensions\\resource_deposit_ext']"))
        for scope in [r, *r.findall('variant')]:
            visual = scope.find(".//instance_reference[@name='animator_attachments']")
            self.assertIn('gaia_herdable_cattle_mal', visual.get('value'))
            self.assertFalse(scope.findall(".//instance_reference[@name='attachments']"), 'elephant tier must not render over cattle')

    def test_buffalo_loadout_and_supervision_and_self_cap_are_the_same_identity(self):
        r = instance(BUFFALO, 'sbps')
        for scope in [r, *r.findall('variant')]:
            self.assertTrue(all(BUFFALO in x.get('value') for x in scope.findall(".//instance_reference[@name='type']")))
            for action in ['work', 'leave']:
                self.assertTrue(scope.findall(f".//instance_reference[@value='abilities\\vietnam\\vn_buffalo_{action}_paddy_vit']"))
            cap = scope.find(".//instance_reference[@name='squad_name']")
            self.assertIn(BUFFALO, cap.get('value'))

    def test_only_buffalo_has_foundation_and_nobody_builds_completed_paddy(self):
        found = []
        for p in (BASE/'sbps').rglob('*.xml'):
            r = E.parse(p).getroot()
            for item in r.findall(".//group[@name='construction_item']"):
                ref = item.find("instance_reference[@name='ebp']")
                if ref is None: continue
                v = ref.get('value', '')
                if FOUNDATION in v: found.append(p.stem)
                # Ordinary native farms remain valid for the private Delhi/Persia
                # conversion probe. This contract owns Vietnamese Rice Paddies.
                if 'building_resource_farm' in v and (p.stem.startswith('vn_') or '\\vietnam\\' in v):
                    self.assertEqual(p.stem, BUFFALO, str(p))
                    self.assertIn(FOUNDATION, v)
        self.assertEqual(found, [BUFFALO, BUFFALO])

    def test_foundation_is_standalone_building_without_farm_state_or_income(self):
        r = instance(FOUNDATION, 'ebps')
        for scope in [r, *r.findall('variant')]:
            self.assertEqual(scope.find("instance_reference[@name='parent_pbg']").get('value'), '')
            self.assertEqual(scope.find(".//enum[@name='subclass_type']").get('value'), 'Building')
            self.assertFalse(scope.findall(".//template_reference[@value='ebpextensions\\resource_deposit_ext']"))
            self.assertFalse(scope.findall(".//template_reference[@value='ebpextensions\\hold_ext']"))
            self.assertEqual(scope.find(".//instance_reference[@name='schema']").get('value'), 'statemodel_schema\\buildings\\house')
            self.assertFalse(any('farm_action_apply' in x.get('value','') for x in scope.iter()))
            self.assertFalse(any('farm_field_' in x.get('value','') for x in scope.iter()))
            requirements=scope.find(".//template_reference[@value='ebpextensions\\requirement_ext']/list[@name='requirement_table']")
            self.assertEqual(len(requirements),0,'foundation must not retain the old impossible 99999-Paddy prerequisite')
            self.assertFalse(scope.findall(".//enum[@name='unit_type'][@value='farm']"))
            self.assertEqual(scope.find(".//float[@name='time_seconds']").get('value'), '60')
            self.assertEqual(scope.find(".//float[@name='hitpoints']").get('value'), '450')

    def test_all_paid_producers_reference_actual_buffalo(self):
        producers = []
        for p in (BASE/'ebps/vietnam/buildings').rglob('*.xml'):
            r = E.parse(p).getroot()
            for ref in r.findall(".//instance_reference[@name='squad']"):
                self.assertNotIn('vn_unit_war_elephant_1_vit', ref.get('value',''), str(p))
                if BUFFALO in ref.get('value',''): producers.append(p.stem)
        self.assertGreaterEqual(len(producers), 4)

    def test_starting_and_free_production_use_actual_buffalo(self):
        for path in ['initialization.scar', 'pagoda_buffalo.scar']:
            text = (ROOT/'assets/scar/vietnam'/path).read_text()
            self.assertIn('prefix .. "'+BUFFALO+'"' if path=='pagoda_buffalo.scar' else ':'+BUFFALO+'"', text)
            self.assertNotIn(':vn_unit_war_elephant_1_vit"', text)

    def test_working_stealth_action_has_script_eligibility_gate(self):
        r=instance('vn_activate_stealth_forvills_vit','abilities')
        self.assertEqual(r.find(".//state_tree_node[@name='entity_tree']").get('value'), 'activate_stealth_mal\\Master\\Defer_EnableStealth\\EnableStealth')
        gate=r.find(".//template_reference[@value='requirements\\required_statemodelbool']")
        self.assertIsNotNone(gate)
        self.assertEqual(gate.find("enum[@name='key']").get('value'),'is_in_stealth_aura_mal')

if __name__ == '__main__': unittest.main()
