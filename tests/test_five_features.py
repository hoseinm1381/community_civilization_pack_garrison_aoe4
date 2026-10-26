"""Native data ownership and mocked lifecycle checks; not native gameplay proof."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest,xml.etree.ElementTree as E
from test_runtime_repairs import RuntimeFixture,ROOT,PREFIX
A=ROOT/'assets/attrib/instances'
def tree(kind,name):
 if name=='vn_unit_water_buffalo_vit':
  from buffalo_source_helpers import effective_cattle
  return effective_cattle(kind)
 return parse_current_xml(A/kind/'vietnam'/(name+'.xml')).getroot()

class FiveFeaturesDataTests(unittest.TestCase):
 def test_weapon_required_enums_in_every_authored_scope(self):
  # Content Editor rejects partial variant bags without these required enums.
  for name,weapon_class,damage_type in [
   ('vn_weapon_no_than_vit','cdn_siege_projectile','Ranged'),
   ('vn_weapon_water_buffalo_vit','cdn_animal_horns','Melee')]:
   t=tree('weapon',name)
   for scope in [t,*t.findall('variant')]:
    with self.subTest(weapon=name,variant=scope.get('name','default')):
     bag=scope.find('group[@name="weapon_bag"]')
     cls=bag.find('enum[@name="weapon_class"]')
     dmg=bag.find('group[@name="damage"]/enum[@name="damage_type"]')
     self.assertIsNotNone(cls)
     self.assertIsNotNone(dmg)
     self.assertEqual(cls.get('value'),weapon_class)
     self.assertEqual(dmg.get('value'),damage_type)

 def test_native_production_replacements_and_explicit_loadouts(self):
  for p in (A/'ebps/vietnam').rglob('*.xml'):
   for x in parse_current_xml(p).findall('.//group[@name="spawn_item"]/instance_reference[@name="squad"]'):
    # Worker Elephant1 is now the user-approved active Buffalo identity.
    self.assertFalse(x.get('value','').endswith('vn_unit_war_elephant_2_vit'),p.name)
  for name in ['vn_unit_war_elephant_1_vit','vn_unit_no_than_vit','vn_unit_no_than_vit_reinforced']:
   for x in tree('sbps',name).findall('.//instance_reference[@name="type"]'):
    # The working standalone Worker Elephant loadout has no inherited item to override.
    if name!='vn_unit_war_elephant_1_vit':self.assertEqual(x.get('overrideParent'),'True')
    self.assertTrue(x.get('value','').endswith(name))
  source=(current_path(ROOT/'assets/scar/vietnam/initialization.scar')).read_text()
  self.assertIn(':vn_unit_water_buffalo_vit',source)
  self.assertNotIn(':vn_unit_war_elephant_1_vit',source)
  self.assertIn('VIETNAM_V5_INIT_BUFFALO_SPAWN_BEGIN',source)

 def test_reinforced_frames_uses_native_siege_research_panel(self):
  t=tree('upgrade','vn_upgrade_reinforced_frames_vit')
  self.assertEqual(t.find('.//instance_reference[@name="ui_menu"]').get('value'),r'menu\building_siege_upgrade')
  pos=t.find('group/group[@name="ui_position"]')
  self.assertEqual(pos.find('int[@name="ui_position_row"]').get('value'),'1')
  self.assertEqual(pos.find('int[@name="ui_position_column"]').get('value'),'1')

 def test_lobed_variants_use_native_mace_visual_without_replacing_torches(self):
  for p in (A/'ebps/vietnam').rglob('*manatarms*lobed.xml'):
   refs=[x.get('value','') for x in parse_current_xml(p).findall('.//instance_reference[@name="animator_attachments"]')]
   self.assertTrue(any('1handmace_hre' in x for x in refs),p.name)
   self.assertTrue(any('torch' in x for x in refs),p.name)
   self.assertFalse(any('wpn_melee_manatarms_' in x and '1handmace_hre' not in x for x in refs),p.name)

 @unittest.skip('Cattle contract retired; active Buffalo balance/cost/population covered by test_elephant_buffalo.')
 def test_buffalo_stock_cattle_population_cost_and_movement_contract(self):
  t=tree('ebps','vn_unit_water_buffalo_vit')
  pop=t.find('list/template_reference[@value="ebpextensions\\population_ext"]')
  self.assertEqual(pop.find('float[@name="personnel_pop"]').get('value'),'0')
  self.assertEqual(pop.find('float[@name="vehicle_pop"]').get('value'),'0')
  self.assertEqual(pop.find('float[@name="medic_pop"]').get('value'),'0')
  for c in [t,*t.findall('variant')]:
   self.assertEqual(c.find('.//float[@name="hitpoints"]').get('value'),'125')
   self.assertEqual(c.find('.//enum_table[@name="speed_scaling_table"]/float[@name="max_speed"]').get('value'),'8')
   self.assertEqual(c.find('.//enum_table[@name="speed_scaling_table"]/float[@name="default_speed"]').get('value'),'2.5')
   self.assertEqual(c.find('.//enum[@name="allegiance_override"]').get('value'),'none')
   self.assertEqual(c.find('.//template_reference[@name="armor_layout_option"]/float').get('value'),'1')
   cost=c.find('.//group[@name="time_cost"]');self.assertEqual(cost.find('float[@name="time_seconds"]').get('value'),'15')
   self.assertEqual(cost.find('enum_table/float[@name="food"]').get('value'),'0')
   self.assertEqual(cost.find('enum_table/float[@name="wood"]').get('value'),'0')
   self.assertEqual(cost.find('enum_table/float[@name="gold"]').get('value'),'90')

 @unittest.skip('Cattle systems retired; original elephant visual/controller preservation covered by test_elephant_buffalo.')
 def test_buffalo_control_animation_and_schema_match_owned_cattle(self):
  import json
  maps=json.loads((current_path(ROOT/'work/vietnam_redesign/STOCK_CATTLE_R7_LIST_ID_MAP.json')).read_text())
  for kind,filename in [('ebps','ebps__gaia_herdable_cattle_mal.xml'),('sbps','sbps__herdable_cattle_mal.xml')]:
   t=tree(kind,'vn_unit_water_buffalo_vit');donor=parse_current_xml(ROOT/'work/vietnam_redesign/evidence/selection_crash_r4'/filename).getroot()
   self.assertEqual(t.find('instance_reference[@name="parent_pbg"]').get('value'),donor.find('instance_reference[@name="parent_pbg"]').get('value'))
   reverse={v:k for k,v in maps[kind].items()}
   for path in ([r'ebpextensions\action_tree_ext',r'ebpextensions\animation_action_tree_ext',r'ebpextensions\action_apply_ext',r'ebpextensions\statemodel_ext',r'ebpextensions\entity_blueprint_ext'] if kind=='ebps' else [r'sbpextensions\squad_statemodel_ext',r'sbpextensions\squad_ambient_animal_type_ext']):
    actual=t.find('list/template_reference[@value="'+path+'"]');expected=donor.find('list/template_reference[@value="'+path+'"]')
    self.assertIsNotNone(actual)
    for x in actual.iter():
     for key in ['List.ItemID','List.ParentItemID']:
      if x.get(key) in reverse:x.set(key,reverse[x.get(key)])
    self.assertEqual(E.tostring(actual),E.tostring(expected))

 @unittest.skip('User explicitly keeps working elephant model/bounds; covered by test_elephant_buffalo.')
 def test_buffalo_uses_cattle_bounds_without_bone_lookup(self):
  t=tree('ebps','vn_unit_water_buffalo_vit')
  ui=t.find('list/template_reference[@value="ebpextensions\\ui_ext"]')
  self.assertEqual(ui.find('enum[@name="selection_method"]').get('value'),'obb_size')
  for axis in ['x','y','z']:self.assertEqual(ui.find('group[@name="selection_obb_size"]/float[@name="'+axis+'"]').get('value'),'2')
  self.assertIsNone(t.find('list/template_reference[@value="ebpextensions\\combat_ext"]'))
  squad=tree('sbps','vn_unit_water_buffalo_vit')
  cap=squad.find('.//template_reference[@value="requirements\\required_squad"]')
  self.assertEqual(cap.find('float[@name="max_squad_cap"]').get('value'),'15')
  self.assertEqual(cap.find('instance_reference[@name="squad_name"]').get('value'),'sbps\\vietnam\\units\\economy\\experimental_cattle\\vn_unit_water_buffalo_vit')

 def test_active_light_infantry_trap_build_access(self):
  names=['vn_unit_spearman_'+str(i)+'_chi' for i in range(1,5)]
  names+=['vn_unit_archer_'+str(i)+'_chi' for i in range(2,5)]
  names+=['vn_unit_skirmisher_'+str(i)+'_vit' for i in range(2,5)]
  names+=['vn_unit_crossbowman_3_chi','vn_unit_crossbowman_4_chi','vn_unit_handcannon_4_chi']
  for name in names:
   t=tree('sbps',name);self.assertTrue(any(x.get('value')=='ebps\\vietnam\\buildings\\traps\\stake_traps\\vn_building_bambo_outpost_chi' for x in t.findall('.//instance_reference')),name)
  for p in (A/'sbps/vietnam').rglob('*.xml'):
   if any(k in p.stem for k in ['manatarms','man_at_arms','horseman','knight','lancer']):
    self.assertFalse(any(x.get('value','').endswith('vn_building_bambo_outpost_chi') for x in parse_current_xml(p).findall('.//instance_reference')),p.name)

 def test_no_than_counts_and_nonweapon_inheritance(self):
  for name,count in [('vn_unit_no_than_vit',7),('vn_unit_no_than_vit_reinforced',9)]:
   t=tree('ebps',name)
   for c in [t,*t.findall('variant')]:
    # One firing source prevents multiplying a seven-shot burst by seven hardpoints.
    hard=c.find('list/template_reference[@value="ebpextensions\\combat_ext"]/list[@name="hardpoints"]');self.assertEqual(len(hard),1)
    refs=hard.findall('.//instance_reference[@name="non_entity_weapon_wrapper_pbg"]')
    self.assertEqual(len(refs),1)
    key='vn_weapon_no_than_vit'+('_reinforced' if count==9 else '')
    self.assertEqual(refs[0].get('value'),'weapon\\vietnam\\'+key)
    weapon=tree('weapon',key)
    scope=weapon if c is t else weapon.find('variant[@name="'+c.get('name')+'"]')
    burst=scope.find('group/group[@name="burst"]')
    self.assertEqual(burst.find('bool[@name="can_burst"]').get('value'),'True')
    duration=float(burst.find('group[@name="duration"]/float[@name="min"]').get('value'))
    rate=float(burst.find('group[@name="rate_of_fire"]/float[@name="min"]').get('value'))
    self.assertEqual(duration*rate,count)  # Authored budget; engine shot count still needs native testing.
   self.assertFalse(t.findall('.//template_reference[@value="ebpextensions\\cost_ext"]'))
   self.assertFalse(t.findall('.//template_reference[@value="ebpextensions\\moving_ext"]'))

 def test_no_than_damage_range_and_nonpiercing(self):
  t=tree('weapon','vn_weapon_no_than_vit')
  for c in [t,*t.findall('variant')]:
   b=c.find('group');self.assertEqual(b.find('group[@name="range"]/float[@name="max"]').get('value'),'32')
   self.assertEqual(b.find('group[@name="damage"]/float[@name="max"]').get('value'),'12')
   self.assertEqual(b.find('group[@name="behaviour"]/bool[@name="piercing"]').get('value'),'False')
   self.assertEqual(b.find('group[@name="scatter"]/float[@name="angle_scatter"]').get('value'),'30')
   area=b.find('group[@name="area_effect"]/template_reference[@name="area_info"]')
   self.assertEqual(area.get('value'),r'options\area_info_options\circle_area_option')
   self.assertEqual(area.find('float[@name="outer_radius"]').get('value'),'1')
   self.assertEqual(b.find('list/group/enum[@name="unit_type"]').get('value'),'melee_infantry')
   self.assertEqual(b.find('list/group/float[@name="base_damage_modifier"]').get('value'),'14')

 def test_no_than_name_reaches_squad_selection_and_production(self):
  # Actor-only names leave the inherited squad production tooltip as Springald.
  squad=tree('sbps','vn_unit_no_than_vit')
  for scope in [squad,*squad.findall('variant')]:
   ui=scope.find('list[@name="extensions"]/template_reference[@value="sbpextensions\\squad_ui_ext"]')
   self.assertIsNotNone(ui)
   for info in ui.findall('list/group/group[@name="info"]'):
    for key,value in [('screen_name','3023'),('help_text','3024'),('extra_text','3025')]:
     loc=info.find('locstring[@name="'+key+'"]')
     self.assertEqual(loc.get('value'),value)
     self.assertEqual(loc.get('mod'),'a743d7d1d7534cf78817e29d8ded7366')

 def test_no_than_direct_flight_and_lateral_spread(self):
  projectile=tree('ebps','vn_projectile_no_than_vit')
  for scope in [projectile,*projectile.findall('variant')]:
   flight=scope.find('list/template_reference[@value="ebpextensions\\projectile_ext"]')
   self.assertEqual(flight.find('group[@name="artillery"]/bool[@name="is_artillery"]').get('value'),'False')
   self.assertEqual(flight.find('bool[@name="force_max_range"]').get('value'),'False')
   self.assertEqual(flight.find('template_reference[@name="trajectory_option"]').get('value'),r'options\none')
   self.assertEqual(flight.find('float[@name="speed"]').get('value'),'65')
  for scope in [tree('weapon','vn_weapon_no_than_vit'),*tree('weapon','vn_weapon_no_than_vit').findall('variant')]:
   scatter=scope.find('group/group[@name="scatter"]/template_reference[@name="area_scatter_option"]/template_reference[@name="area_info"]')
   self.assertEqual(scatter.get('value'),r'options\area_info_options\rectangle_area_option')
   self.assertEqual(float(scatter.find('float[@name="width"]').get('value')),48)

 def test_workshop_replacement_and_research_marker(self):
  t=tree('ebps','vn_building_unit_siege_control_chi');refs=[x.get('value') for x in t.findall('.//instance_reference')]
  self.assertIn('sbps\\vietnam\\units\\siege\\no_than\\vn_unit_no_than_vit',refs)
  self.assertNotIn(r'sbps\races\chinese\unit_springald_3_chi',refs)
  self.assertNotIn(r'upgrade\races\common\research\upgrade_siege_roller_trigger',refs)
  t=tree('upgrade','vn_upgrade_reinforced_frames_vit');cost=t.find('group/group[@name="time_cost"]')
  self.assertEqual(cost.find('enum_table/float[@name="wood"]').get('value'),'150')
  self.assertEqual(cost.find('enum_table/float[@name="gold"]').get('value'),'250')
  self.assertEqual(cost.find('float[@name="time_seconds"]').get('value'),'30')
  self.assertIn(r'upgrade\dev\ages\imperial_age',[x.get('value') for x in t.findall('.//instance_reference')])

 def test_all_new_actor_squad_precaches(self):
  s=(current_path(ROOT/'assets/scar/vietnam/prematch_precache.scar')).read_text()
  for name in ['vn_unit_water_buffalo_vit','vn_unit_no_than_vit','vn_unit_no_than_vit_reinforced','vn_projectile_no_than_vit']:self.assertIn(PREFIX+name,s)

class FiveFeaturesRuntimeTests(RuntimeFixture):
 def setUp(self):
  super().setUp();self.runlua('''MAT_Player=1;MAT_Entity=2;CT_Medic=3;MUT_Addition=1;MUT_Multiplication=2
  mods={};researched=false
  function EGroup_CountSpawned(g) return #g end
  function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
  function Player_GetMaxPopulationCap(p,c) assert(c==CT_Medic);return 0 end
  function Player_GetCurrentPopulationCap(p,c) assert(c==CT_Medic);return 0 end
  function Modifier_Create(k,n,u,e,v,b) return {kind=k,name=n,value=v} end
  function Modifier_ApplyToPlayer(m,p,d) m.owner=p;m.active=true;mods[#mods+1]=m;return m end
  function Modifier_ApplyToEntity(m,e,d) m.id=e.id;m.active=true;mods[#mods+1]=m;return m end
  function Modifier_Remove(m) assert(m.active);m.active=false end
  function Player_GetAllEntities(p) local g={};Player_GetEntitiesEGroup(p,g);return g end
  function Player_HasUpgrade(p,b) return p==11 and researched end
  function active(id) local n=0;for _,m in ipairs(mods) do if m.active and m.id==id then n=n+1 end end;return n end
  ''')
  self.runlua((current_path(ROOT/'assets/scar/vietnam/buffalo.scar')).read_text())
  self.runlua((current_path(ROOT/'assets/scar/vietnam/siege_research.scar')).read_text())

 def test_buffalo_no_longer_activates_medical_cap_code(self):
  lifecycle=(current_path(ROOT/'assets/scar/vietnam/lifecycle.scar')).read_text()
  entry=(current_path(ROOT/'assets/scar/winconditions/VietnamMode.scar')).read_text()
  self.assertNotIn('VietnamBuffalo_Start(',lifecycle)
  self.assertNotIn('VietnamBuffalo_Cleanup(',lifecycle)
  self.assertNotIn('import("vietnam/buffalo.scar")',entry)

 def test_reinforced_uses_native_armor_without_stacking_runtime_multiplier(self):
  self.runlua('researched=true;VietnamSiegeResearch_Update(PLAYERS[1]);VietnamSiegeResearch_Update(PLAYERS[1]);VietnamSiegeResearch_Update(PLAYERS[2])')
  self.assertEqual(len(self.g.mods),0)
  self.runlua("old={active=true};VietnamSiegeResearchState.players[1]={handle=old};VietnamSiegeResearch_Update(PLAYERS[1])")
  self.assertFalse(self.g.old.active)
  self.runlua('VietnamSiegeResearch_Cleanup();VietnamSiegeResearch_Cleanup()')

if __name__=='__main__':unittest.main()
