from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
from pathlib import Path
import unittest, xml.etree.ElementTree as E

R=Path(__file__).resolve().parents[1];A=R/'assets/attrib/instances'
def xml(cat,name):return parse_current_xml(A/cat/'vietnam'/(name+'.xml')).getroot()

class SkirmisherRedesign(unittest.TestCase):
    def test_archer_stock_body_and_no_stealth(self):
        for age in [2,3,4]:
            t=xml('ebps',f'vn_unit_archer_{age}_vit')
            self.assertEqual(t.find('instance_reference[@name="parent_pbg"]').get('value'),rf'ebps\races\chinese\units\unit_archer_{age}_chi')
            self.assertEqual({x.get('value') for x in t.findall('list/template_reference')},{r'ebpextensions\tier_ext'})
            for suffix in ['vit','chi']:
                s=xml('sbps',f'vn_unit_archer_{age}_{suffix}')
                self.assertFalse(any('activate_stealth_for_archer' in n.get('value','') for n in s.iter()))

    def test_skirmisher_stealth_and_stats(self):
        for age,hp,armor in [(2,80,2),(3,95,3),(4,110,4)]:
            t=xml('ebps',f'vn_unit_skirmisher_{age}_vit')
            self.assertEqual(t.find('.//float[@name="hitpoints"]').get('value'),str(hp))
            self.assertEqual(t.find('.//float[@name="Ranged"]').get('value'),str(armor))
            self.assertEqual(t.find('.//float[@name="time_seconds"]').get('value'),'20')
            self.assertEqual(t.find('.//float[@name="default_speed"]').get('value'),'5.5')
            self.assertEqual(t.find('.//float[@name="revealed_time"]').get('value'),'8')
            s=xml('sbps',f'vn_unit_skirmisher_{age}_vit')
            self.assertTrue(any('activate_stealth_for_archer' in n.get('value','') for n in s.iter()))
            self.assertFalse(any('upgrade_unit_archer_' in n.get('value','') for n in s.iter()))

    def test_native_torch_and_no_melee_javelin_or_incendiary(self):
        for age in [2,3,4]:
            t=xml('ebps',f'vn_unit_skirmisher_{age}_vit')
            weapons=[x.get('value') for x in t.findall('.//instance_reference[@name="non_entity_weapon_wrapper_pbg"]')]
            self.assertEqual(weapons,[rf'weapon\vietnam\vn_weapon_skirmisher_{age}_vit',r'weapon\vietnam\vn_weapon_light_infantry_torch_vit'])

    def test_weapon_bonus_and_cycle(self):
        for age,dmg,bonus in [(2,6,6),(3,8,8),(4,9,9)]:
            t=xml('weapon',f'vn_weapon_skirmisher_{age}_vit');b=t.find('group')
            self.assertEqual(b.find('group[@name="damage"]/float[@name="max"]').get('value'),str(dmg))
            self.assertEqual(b.find('group[@name="range"]/float[@name="max"]').get('value'),'20')
            self.assertEqual(b.find('list/group/enum').get('value'),'ranged')
            self.assertEqual(b.find('list/group/float').get('value'),str(bonus))
            total=sum(float(b.find(p).get('value')) for p in ['group[@name="fire"]/float[@name="wind_up"]','group[@name="fire"]/float[@name="wind_down"]','group[@name="aim"]/group/float[@name="max"]','group[@name="reload"]/group/float[@name="max"]'])
            self.assertEqual(total,1.875)  # + reported native 0.125 overhead: target 2 seconds.

    def test_producers_offer_both_families(self):
        for name in ['vn_building_unit_ranged_control_chi','vn_building_defense_outpost_chi','vn_building_defense_outpost_2_chi','vn_building_landmark_age1_gatehouse_control_chi']:
            t=xml('ebps',name)
            for table in t.findall('.//list[@name="spawn_items"]'):
                roster=[x.get('value') for x in table.findall('group/instance_reference[@name="squad"]')]
                for age in [2,3,4]:
                    old=blueprint_key('sbps',f'vn_unit_archer_{age}_vit')
                    if old in roster:self.assertIn(blueprint_key('sbps',f'vn_unit_skirmisher_{age}_vit'),roster)
        text=(current_path(R/'assets/scar/vietnam/rattan_armor.scar')).read_text(encoding='utf-8')
        for age in [2,3,4]:self.assertIn(f'vn_unit_skirmisher_{age}_vit',text)

    def test_independent_research_and_controller_links(self):
        for age in [3,4]:
            t=xml('upgrade',f'vn_upgrade_skirmisher_{age}_vit')
            for s in [t,t.find('variant[@name="campaign"]')]:
                req=s.find('group/list[@name="requirements"]')
                self.assertIsNotNone(req)
                self.assertFalse(any('upgrade_unit_archer_' in n.get('value','') for n in req.iter()))
                self.assertTrue(any(n.get('value')==rf'upgrade\vietnam\vn_upgrade_skirmisher_{age}_vit' for n in req.iter()))
        t=xml('ebps','vn_building_unit_ranged_control_chi')
        for item in t.findall('.//list[@name="spawn_items"]/group'):
            ref=item.find('instance_reference[@name="squad"]')
            if ref is None or 'vn_unit_skirmisher_' not in ref.get('value',''):continue
            self.assertEqual(item.find('group[@name="ui_position"]/int[@name="ui_position_column"]').get('value'),'4')
            self.assertFalse(any('upgrade_unit_archer_' in n.get('value','') for n in item.iter()))

    def test_conversions_stay_in_family_and_stealth_donor_unchanged(self):
        import hashlib, json
        before=json.loads((current_path(R/'work/vietnam_redesign/rollback/2026-10-20_pre_skirmisher/assets-sha256.json')).read_text(encoding='utf-8'))
        ability='assets/attrib/instances/abilities/vietnam/vn_activate_stealth_for_archer.xml'
        self.assertEqual(hashlib.sha256((current_path(R/ability)).read_bytes()).hexdigest(),before[ability])
        for age in [2,3,4]:
            for family in ['archer','skirmisher']:
                t=xml('ebps',f'vn_unit_{family}_{age}_vit')
                targets=[n.get('value') for n in t.findall('.//instance_reference[@name="statetree_tier_pgb_upgrade_target_entity"]') if n.get('value')]
                self.assertTrue(all(v.split('\\')[-1].startswith(f'vn_unit_{family}_') for v in targets))
                self.assertEqual(set(targets),{blueprint_key('ebps',f'vn_unit_{family}_{next_age}_vit') for next_age in range(age+1,5)})
        # Scorched Earth already targets the native class inherited by stock Javelins.
        donor=parse_current_xml(R/'work/vietnam_redesign/evidence/skirmisher/ebps_unit_javelin_2.xml').getroot()
        self.assertTrue(any(n.get('name')=='unit_type' and n.get('value')=='infantry_light' for n in donor.iter()))

if __name__=='__main__':unittest.main()
