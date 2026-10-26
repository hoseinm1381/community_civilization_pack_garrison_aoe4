"""Working elephant-backed Buffalo contracts; native stability is user-tested."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
from test_farm_repair import assert_campaign_worker
from pathlib import Path
import unittest,zipfile,xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'work/vietnam_redesign/elephant_buffalo_20261022'
UNIT='vn_unit_war_elephant_1_vit'
def tree(kind):return parse_current_xml(ROOT/f'assets/attrib/instances/{kind}/vietnam/{UNIT}.xml').getroot()
def scopes(r):return [r,*r.findall('variant')]
def ext(r,name):return r.find('list/template_reference[@value="'+name+'"]')

class ElephantBuffaloTests(unittest.TestCase):
    def test_stats_cost_population_in_both_scopes(self):
        for scope in scopes(tree('ebps')):
            self.assertEqual(scope.find('.//float[@name="hitpoints"]').get('value'),'125')
            hp=ext(scope,r'ebpextensions\health_ext')
            for damage in ['Melee','Ranged']:
                self.assertEqual(hp.find('enum_table[@name="armor_scaler_by_damage_type"]/float[@name="'+damage+'"]').get('value'),'0')
            pop=ext(scope,r'ebpextensions\population_ext')
            self.assertEqual(pop.find('float[@name="personnel_pop"]').get('value'),'0')
            self.assertEqual(pop.find('float[@name="vehicle_pop"]').get('value'),'0')
            self.assertEqual(pop.find('float[@name="medic_pop"]').get('value'),'0')
            self.assertEqual(scope.find('.//enum_table[@name="speed_scaling_table"]/float[@name="default_speed"]').get('value'),'3.68')
            cost=ext(scope,r'ebpextensions\cost_ext').find('group[@name="time_cost"]')
            self.assertEqual(cost.find('float[@name="time_seconds"]').get('value'),'30')
            for key,value in [('food','50'),('wood','50'),('gold','0')]:
                self.assertEqual(cost.find('enum_table/float[@name="'+key+'"]').get('value'),value)

    def test_unarmed_no_charge_supervision_or_mobile_dropoff(self):
        for scope in scopes(tree('ebps')):
            combat=ext(scope,r'ebpextensions\combat_ext')
            self.assertEqual(combat.find('bool[@name="reject_attack_command"]').get('value'),'True')
            self.assertEqual(len(combat.find('list[@name="hardpoints"]')),0)
            self.assertEqual(combat.find('list[@name="hardpoints"]').get('overrideParent'),'True')
            self.assertEqual(combat.find('group[@name="attack_move"]/float[@name="attack_move_targeting_range"]').get('value'),'0')
            self.assertEqual(combat.find('group[@name="idle_targeting"]/float[@name="idle_targeting_range"]').get('value'),'0')
            self.assertIsNone(combat.find('.//float[@name="idle_targeting_targeting_range"]'))
            drop=ext(scope,r'ebpextensions\resource_drop_off_ext')
            self.assertTrue(all(n.get('value')=='False' for n in drop.findall('enum_table[@name="accepted_resources"]/bool')))
        for scope in scopes(tree('sbps')):
            ability=ext(scope,r'sbpextensions\squad_ability_ext')
            refs=[x.get('value','') for x in ability.findall('.//instance_reference[@name="ability"]')]
            self.assertFalse(any('military_charge' in x or 'vn_elephant_worker_boost' in x for x in refs))
            for order in ['attack_ground','attack_move','prefer_melee','prefer_ranged']:
                self.assertEqual(ability.find('group[@name="squad_orders"]/group[@name="'+order+'"]/bool[@name="available"]').get('value'),'False')

    def test_legacy_cap_is_preserved_and_actual_buffalo_owns_active_production(self):
        for scope in scopes(tree('sbps')):
            req=ext(scope,r'sbpextensions\squad_requirement_ext').find('list[@name="requirement_table"]')
            self.assertEqual(len(req),1)
            self.assertEqual(req[0].get('value'),r'requirements\required_squad')
            self.assertEqual(req[0].find('float[@name="max_squad_cap"]').get('value'),'15')
            self.assertEqual(req[0].find('instance_reference[@name="squad_name"]').get('value'),blueprint_key('sbps',UNIT))
            ui=ext(scope,r'sbpextensions\squad_ui_ext')
            self.assertEqual(ui.find('.//locstring[@name="screen_name"]').get('value'),'3020')
        source=(current_path(ROOT/'assets/scar/vietnam/initialization.scar')).read_text()
        self.assertIn(':vn_unit_water_buffalo_vit',source)
        self.assertNotIn(':'+UNIT,source)
        count=0
        for p in (ROOT/'assets/attrib/instances').rglob('*.xml'):
            for item in parse_current_xml(p).findall('.//list[@name="spawn_items"]/group'):
                ref=item.find('instance_reference[@name="squad"]')
                if ref is None:continue
                self.assertNotIn(ref.get('value'),[blueprint_key('sbps',UNIT),r'sbps\races\malian\animals\herdable_cattle_mal'])
                if ref.get('value')==blueprint_key('sbps','vn_unit_water_buffalo_vit'):
                    count+=1
                    for n in item.findall('enum_table[@name="item_cost_adjustment"]/float'):
                        if n.get('name') in ['food','wood','gold','stone']:
                            free=p.stem in ['vn_building_landmark_age1_vit_one_pilar_pagoda','vn_building_landmark_age1_headquarters_control_chi']
                            self.assertEqual(n.get('value'),'-50' if free and n.get('name') in ['food','wood'] else '0')
        self.assertEqual(count,17)

    def test_native_worker_visuals_inherit_with_private_identity_and_loadout(self):
        # User authorized replacing the old war-elephant donor with the complete
        # Tughlaq worker. Keep the historical freeze and the private PBGs.
        inherited={
            'ebps':['tier_ext','entity_blueprint_ext','action_tree_ext','animation_action_tree_ext','statemodel_ext','hit_react_tree_ext'],
            'sbps':['squad_blueprint_ext','squad_statemodel_ext','squad_audio_ext','squad_speech_ext','squad_command_forwarding_ext']}
        with zipfile.ZipFile(B/'before.zip') as z:
            for kind,names in inherited.items():
                name=f'assets/attrib/instances/{kind}/vietnam/{UNIT}.xml'
                old=remap_xml_references(E.fromstring(z.read(name)));new=tree(kind)
                self.assertEqual(old.find('uniqueid').attrib,new.find('uniqueid').attrib)
                parent=(r'ebps\races\sultanate_ha_tug\units' if kind=='ebps' else r'sbps\races\sultanate_ha_tug')+r'\unit_worker_elephant_2_sul_ha_tug'
                for b in scopes(new):
                    if kind=='ebps' and b.get('name')=='campaign':
                        assert_campaign_worker(self,b)
                        continue
                    self.assertEqual(b.find('instance_reference[@name="parent_pbg"]').get('value'),parent)
                    for suffix in names:
                        prefix='ebpextensions' if kind=='ebps' else 'sbpextensions'
                        extension=ext(b,prefix+'\\'+suffix)
                        if kind=='ebps' and suffix=='animation_action_tree_ext':
                            # Native elephant physical actions lack the Construct track.
                            # Permit only the authorized native builder opening branch.
                            self.assertIsNotNone(extension)
                            self.assertEqual(extension.attrib,{
                                'name':'exts','value':r'ebpextensions\animation_action_tree_ext',
                                'List.ItemID':'823311120','List.ParentItemID':'823311120'})
                            self.assertEqual(len(extension),1)
                            self.assertEqual(extension[0].tag,'state_tree_node')
                            self.assertEqual(extension[0].attrib,{
                                'name':'ActionTree_OpeningBranch','value':'infantry','overrideParent':'True'})
                        else:
                            self.assertIsNone(extension,(kind,suffix))
                    if kind=='sbps':
                        refs=b.findall('list/template_reference[@value="sbpextensions\\squad_loadout_ext"]/list/group/instance_reference[@name="type"]')
                        self.assertEqual(len(refs),1)
                        self.assertEqual(refs[0].get('value'),blueprint_key('ebps',UNIT))

if __name__=='__main__':unittest.main()
