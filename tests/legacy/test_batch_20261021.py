"""Source contracts for the exact cattle diagnostic and Royal Elephant batch.

Native creation, auras, shot damage and timing remain engine acceptance gates.
"""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import copy
import json
import unittest
import xml.etree.ElementTree as E
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets/attrib/instances'
W=ROOT/'work/vietnam_redesign'
B=W/'batch_20261021'

def tree(kind,name):
    if name=='vn_unit_water_buffalo_vit':
        from buffalo_source_helpers import effective_cattle
        return effective_cattle(kind)
    return parse_current_xml(A/kind/'vietnam'/(name+'.xml')).getroot()
def semantic(n):return n.tag,sorted(n.attrib.items()),(n.text or '').strip(),[semantic(c) for c in n]

def expected_cattle(kind):
    filename='gaia_herdable_cattle_mal' if kind=='ebps' else 'herdable_cattle_mal'
    r=parse_current_xml(B/'evidence'/f'{kind}__{filename}.xml').getroot()
    r.find('uniqueid').set('value','2147481899' if kind=='ebps' else '2147481925')
    if kind=='ebps':
        r.find('.//float[@name="hitpoints"]').set('value','125')
        r.find('.//float[@name="vehicle_pop"]').set('value','0')
    else:
        info=r.find('list/template_reference[@value="sbpextensions\\squad_ui_ext"]/list/group/group[@name="info"]')
        for name,value in [('screen_name','3020'),('help_text','3021'),('extra_text','3022')]:
            node=info.find('locstring[@name="'+name+'"]')
            node.set('value',value)
            node.set('mod','a743d7d1d7534cf78817e29d8ded7366')
        formatter=info.find('template_reference[@name="help_text_formatter"]')
        formatter.clear()
        formatter.attrib.update({'name':'help_text_formatter','value':'','overrideParent':'True'})
        loadout=r.find('list/template_reference[@value="sbpextensions\\squad_loadout_ext"]')
        ref=loadout.find('.//instance_reference[@name="type"]')
        ref.set('value','ebps\\vietnam\\units\\economy\\experimental_cattle\\vn_unit_water_buffalo_vit')
        ref.set('mod','a743d7d1d7534cf78817e29d8ded7366')
        req=r.find('.//template_reference[@value="requirements\\required_squad"]')
        req.find('float[@name="max_squad_cap"]').set('value','15')
        ref=req.find('instance_reference[@name="squad_name"]')
        ref.set('value','sbps\\vietnam\\units\\economy\\experimental_cattle\\vn_unit_water_buffalo_vit')
        ref.set('mod','a743d7d1d7534cf78817e29d8ded7366')
    return r

@unittest.skip('Exact-cattle diagnostic retired by user; active elephant unit covered by test_elephant_buffalo.')
class ExactCattleTests(unittest.TestCase):
    def test_cattle_matches_current_native_donor_except_allowed_clone_fields(self):
        for kind in ['ebps','sbps']:
            with self.subTest(kind=kind):
                self.assertEqual(semantic(tree(kind,'vn_unit_water_buffalo_vit')),semantic(expected_cattle(kind)))

    def test_cattle_is_unarmed_and_starting_worker_elephant_is_retained(self):
        r=tree('ebps','vn_unit_water_buffalo_vit')
        self.assertIsNone(r.find('list/template_reference[@value="ebpextensions\\combat_ext"]'))
        self.assertEqual(r.find('.//float[@name="hitpoints"]').get('value'),'125')
        source=(current_path(ROOT/'assets/scar/vietnam/initialization.scar')).read_text()
        self.assertIn(':vn_unit_war_elephant_1_vit',source)
        self.assertNotIn(':vn_unit_water_buffalo_vit',source)

class RoyalRocketTests(unittest.TestCase):
    def test_rocket_bonus_targets_only_infantry_and_cavalry(self):
        r=tree('weapon','vn_weapon_elephant_rocket_vit')
        for scope in [r,*r.findall('variant')]:
            b=scope.find('group')
            targets=b.find('list[@name="target_type_table"]')
            bonuses={x.find('enum[@name="unit_type"]').get('value'):float(x.find('float[@name="base_damage_modifier"]').get('value')) for x in targets}
            self.assertEqual(bonuses,{'infantry':110,'cavalry':110})
            self.assertEqual(b.find('group[@name="damage"]/float[@name="min"]').get('value'),'80')
            self.assertEqual(b.find('group[@name="range"]/float[@name="max"]').get('value'),'28')
            self.assertEqual(b.find('group[@name="area_effect"]/template_reference[@name="area_info"]').get('value'),r'options\area_info_options\point_area_option')

    def test_rocket_has_explicit_four_second_timing_budget(self):
        r=tree('weapon','vn_weapon_elephant_rocket_vit')
        for scope in [r,*r.findall('variant')]:
            b=scope.find('group')
            for endpoint in ['min','max']:
                def value(path):
                    node=b.find(path)
                    self.assertIsNotNone(node,'Missing explicit timing field: '+path)
                    return float(node.get('value'))
                total=value('group[@name="aim"]/group[@name="fire_aim_time"]/float[@name="'+endpoint+'"]')
                total+=value('group[@name="reload"]/group[@name="duration"]/float[@name="'+endpoint+'"]')
                total+=value('group[@name="fire"]/float[@name="wind_up"]')+value('group[@name="fire"]/float[@name="wind_down"]')
                self.assertEqual(total,4)
            self.assertEqual(b.find('group[@name="burst"]/bool[@name="can_burst"]').get('value'),'False')

class MenuAndAuraTests(unittest.TestCase):
    def test_obsolete_worker_research_is_not_offered_by_feudal_hq(self):
        r=tree('ebps','vn_building_landmark_age1_headquarters_control_chi')
        refs=[x.get('value','') for x in r.findall('.//instance_reference')]
        self.assertFalse(any(x.endswith(('vn_overrseers_pagoda','vn_upgrade_elephant_limit')) for x in refs))

    def test_campaign_workshop_has_unique_retained_five_unit_roster(self):
        r=tree('ebps','vn_building_unit_siege_control_chi')
        for scope in [r,r.find('variant[@name="campaign"]')]:
            refs=[x.get('value','').split('\\')[-1] for x in scope.findall('list/template_reference[@value="ebpextensions\\spawner_ext"]/list[@name="spawn_items"]//instance_reference[@name="squad"]')]
            self.assertEqual(len(refs),5)
            self.assertEqual(refs.count('vn_unit_no_than_vit'),1)
            self.assertEqual(refs.count('vn_unit_culverin_4_chi'),1)
            self.assertEqual(refs.count('unit_workshop_ram_3_chi'),1)

    def test_each_royal_actor_attaches_all_three_native_always_on_auras(self):
        expected={r'abilities\always_on_abilities\japanese\bannerman_aura_'+kind+'_jpn' for kind in ['melee','range','cavalry']}
        for name in ['vn_unit_war_elephant_handcannon_4_vit','vn_unit_war_elephant_handcannon_4_vit_free']:
            r=tree('ebps',name)
            for scope in [r,*r.findall('variant')]:
                with self.subTest(actor=name,variant=scope.get('name','default')):
                    ext=scope.find('list/template_reference[@value="ebpextensions\\ability_ext"]')
                    self.assertIsNotNone(ext)
                    self.assertEqual({x.get('value') for x in ext.findall('list/instance_reference')},expected)
                    self.assertNotEqual(ext.find('list').get('overrideParent'),'True')
            # Cap-associated Bannerman action branches must not be installed on the Elephant.
            self.assertFalse(any('bannerman' in x.get('value','') for x in r.findall('.//string[@name="state_tree"]')))

if __name__=='__main__':unittest.main()
