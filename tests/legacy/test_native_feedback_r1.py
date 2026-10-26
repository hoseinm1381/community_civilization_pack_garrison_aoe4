"""Corrections from the user's native test feedback, 2026-10-20."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest,xml.etree.ElementTree as E
from pathlib import Path
from test_runtime_repairs import RuntimeFixture,ROOT,PREFIX
A=ROOT/'assets/attrib/instances'
TORCH=r'weapon\vietnam\vn_weapon_light_infantry_torch_vit'

class NativeFeedbackSourceTests(unittest.TestCase):
    def test_fortification_authored_time_six_seconds(self):
        t=parse_current_xml(A/'upgrade/vietnam/vn_upgrade_hideout_upgrade_vit.xml').getroot()
        for scope in [t,*t.findall('variant')]:
            self.assertEqual(scope.find('group/group[@name="time_cost"]/float[@name="time_seconds"]').get('value'),'6')

    def test_skirmisher_javelins_use_native_nonsiege_option_and_private_torch(self):
        for age in [2,3,4]:
            t=parse_current_xml(A/'weapon/vietnam'/f'vn_weapon_skirmisher_{age}_vit.xml').getroot()
            n=t.find('group/template_reference[@name="siege_option"]')
            self.assertIsNotNone(n);self.assertEqual(n.get('value'),r'options\none')
            t=parse_current_xml(A/'ebps/vietnam'/f'vn_unit_skirmisher_{age}_vit.xml').getroot()
            self.assertTrue(any(n.get('value')==TORCH for n in t.findall('.//instance_reference[@name="non_entity_weapon_wrapper_pbg"]')))

    def test_only_range_skirmisher_moves_to_column_four(self):
        for producer,column in [('vn_building_unit_ranged_control_chi',4),('vn_building_defense_outpost_chi',5)]:
            t=parse_current_xml(A/'ebps/vietnam'/(producer+'.xml')).getroot()
            for item in t.findall('.//list[@name="spawn_items"]/group'):
                ref=item.find('instance_reference[@name="squad"]')
                if ref is not None and 'skirmisher' in ref.get('value',''):
                    self.assertEqual(item.find('group/int[@name="ui_position_column"]').get('value'),str(column))

    def test_wood_research_uses_native_japanese_kura_layout(self):
        count=0
        for name in ['vn_building_econ_food_control_chi','vn_building_landmark_age1_vit_one_pilar_pagoda']:
            p=A/'ebps/vietnam'/(name+'.xml')
            for n in parse_current_xml(p).getroot().findall('.//list[@name="standard_upgrades"]/instance_reference'):
                value=n.get('value','')
                if 'wood_harvest_rate_' in value:
                    count+=1;self.assertTrue(value.endswith(('_2_kura_jpn','_3_kura_jpn','_4_kura_jpn')),value)
        self.assertEqual(count,12)

    def test_scorched_research_has_only_one_effect_owner(self):
        t=parse_current_xml(A/'upgrade/vietnam/vn_upgrade_scorched_earth_vit.xml').getroot()
        self.assertFalse(any(n.get('value') for n in t.findall('group/group[@name="state_tree_references"]//state_tree_node')))
        self.assertFalse(list(t.find('group/list[@name="float_properties"]')))
        t=parse_current_xml(A/'weapon/vietnam/vn_weapon_light_infantry_torch_vit.xml').getroot()
        self.assertEqual(t.find('instance_reference').get('value'),r'weapon\races\common\ranged\weapon_torch')
        self.assertIsNone(t.find('group'))

class ScorchedOwnerRuntimeTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        MAT_WeaponType=398;MUT_Multiplication=1;mods={};has={[11]=false,[22]=false}
        function BP_GetWeaponBlueprint(n) return n end
        function Player_HasUpgrade(p,bp) return has[p] end
        function Modifier_Create(kind,name,usage,exclusive,value,target)
            return {kind=kind,name=name,value=value,target=target}
        end
        function Modifier_ApplyToPlayer(m,p,duration) m.player=p;m.active=true;mods[#mods+1]=m;return m end
        function Modifier_Remove(m) m.active=false end
        ''')
        self.runlua((current_path(ROOT/'assets/scar/vietnam/scorched_earth.scar')).read_text(encoding='utf-8'))

    def test_owner_only_once_private_weapon_modifier_and_cleanup(self):
        self.runlua('VietnamScorchedEarth_Update(PLAYERS[1]);has[11]=true;VietnamScorchedEarth_Update(PLAYERS[1]);VietnamScorchedEarth_Update(PLAYERS[1]);VietnamScorchedEarth_Update(PLAYERS[2])')
        self.assertEqual(len(self.g.mods),1)
        m=self.g.mods[1]
        self.assertEqual((m.kind,m.name,m.value,m.player),(398,'damage_weapon_modifier',1.2,11))
        self.assertEqual(m.target,PREFIX+'vn_weapon_light_infantry_torch_vit')
        self.runlua('VietnamScorchedEarth_Cleanup()');self.assertFalse(m.active)

if __name__=='__main__':unittest.main()
