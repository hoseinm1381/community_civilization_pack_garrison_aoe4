"""Shared Serpentine research and native weapon variant ownership checks."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
from pathlib import Path
import unittest,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];A=R/'assets/attrib/instances';W=R/'work/vietnam_redesign'
KEY=r'upgrade\vietnam\vn_upgrade_serpentine_powder_vit';BASE='vn_unit_handcannon_4_chi';UP=BASE+'_serpentine'
def load(cat,n):return parse_current_xml(A/cat/'vietnam'/(n+'.xml')).getroot()
def sig(x):return x.tag,sorted(x.attrib.items()),[sig(n) for n in x]
class SerpentinePowderTests(unittest.TestCase):
 def test_shared_research_and_native_baseline(self):
  t=load('upgrade','vn_upgrade_serpentine_powder_vit');self.assertEqual(t.find('instance_reference').get('value'),r'upgrade\races\common\research\upgrade_ranged_leadshot')
  b=t.find('group');self.assertEqual(b.find('float[@name="global_max_limit"]').get('value'),'1')
  req=b.find('list[@name="requirements"]');self.assertEqual(len(req),2)
  for item in req:
   self.assertEqual(item.find('instance_reference').get('value'),KEY)
  self.assertEqual(b.find('group[@name="state_tree_references"]/template_reference/state_tree_node').get('value'),'')
  d=parse_current_xml(W/'evidence/serpentine/upgrade__upgrade_ranged_leadshot.xml').getroot();cost=d.find('group/group[@name="time_cost"]')
  self.assertEqual([cost.find('enum_table/float[@name="'+k+'"]').get('value') for k in ['food','gold']],['300','500']);self.assertEqual(cost.find('float').get('value'),'60')
  self.assertIsNone(b.find('group[@name="time_cost"]'))
 def test_both_producers_share_same_upgrade(self):
  for name in ['vn_building_tech_university_control_chi','vn_building_landmark_age3_trung_foundaries_vit']:
   t=load('ebps',name);root=t.find('list/template_reference[@value="ebpextensions\\upgrade_ext"]/list')
   self.assertEqual(sum(n.get('value')==KEY for n in root),1)
   for s in t.findall('variant'):
    table=s.find('list/template_reference[@value="ebpextensions\\upgrade_ext"]/list')
    if table is not None and table.get('overrideParent')=='True':self.assertEqual(sum(n.get('value')==KEY for n in table),1)
 def test_native_weapon_additions_do_not_replace_balance_or_penetration(self):
  t=load('weapon','vn_weapon_handcannon_4_serpentine_vit');self.assertEqual(t.find('instance_reference').get('value'),r'weapon\vietnam\vn_weapon_handcannon_4_vit')
  b=t.find('group');self.assertEqual({n.get('name') for n in b},{'damage','target_type_table'})
  self.assertIsNone(b.find('group[@name="damage"]/float'))
  bonus=b.find('list/group');self.assertEqual(bonus.find('enum').get('value'),'melee_infantry');self.assertEqual(bonus.find('float').get('value'),'5')
  self.assertEqual(b.find('group/list/group/string').get('value'),r'leadshot_slow_on_hit\leadshot_slow_on_hit')
 def test_native_conversion_consumed_without_self_loop(self):
  base=load('ebps',BASE);child=load('ebps',UP)
  for src,dst in zip([base,*base.findall('variant')],[child,*child.findall('variant')]):
   groups=src.find('list/template_reference[@value="ebpextensions\\tier_ext"]/list');g=groups[-1];self.assertEqual(len(g),2)
   self.assertEqual(g[1].find('instance_reference[@name="statetree_tier_requirements_pbg"]').get('value'),KEY)
   self.assertEqual(g[1].find('instance_reference[@name="statetree_tier_pgb_upgrade_target_entity"]').get('value'),blueprint_key('ebps',UP))
   self.assertEqual(dst.find('list/template_reference[@value="ebpextensions\\tier_ext"]/list').get('removedIds'),g.get('List.ItemID'))
   self.assertEqual(g[1].find('template_reference[@name="blueprint_conversion_parameters"]/bool[@name="reissue_commands"]').get('value'),'True')
 def test_upgraded_squad_and_rattan_coverage(self):
  s=load('sbps',UP)
  for scope in [s,*s.findall('variant')]:
   ref=scope.find('list/template_reference/list/group/instance_reference[@name="type"]');self.assertEqual(ref.get('value'),blueprint_key('ebps',UP))
  text=(current_path(R/'assets/scar/vietnam/rattan_armor.scar')).read_text(encoding='utf-8');self.assertEqual(text.count('"'+UP+'"'),1)
 def test_actor_and_squad_are_precached(self):
  t=parse_current_xml(R/'assets/scar/winconditions/VietnamMode.rdo').getroot();name='a743d7d1d7534cf78817e29d8ded7366:'+UP
  for kind in ['EntityPrecacheItem','SquadPrecacheItem']:
   self.assertEqual(sum(any(p.get('Value')==name for p in n.iter('DataProperty')) for n in t.iter('DataObject') if n.get('Type')==kind),1)
if __name__=='__main__':unittest.main()
