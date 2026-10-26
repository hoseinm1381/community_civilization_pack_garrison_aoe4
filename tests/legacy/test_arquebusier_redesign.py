"""Arquebusier native penetration and retained ownership contracts; no runtime claims."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
from pathlib import Path
import unittest, xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]; A=R/'assets/attrib/instances'; W=R/'work/vietnam_redesign'
P='ebps\\vietnam\\projectiles\\vn_projectile_arquebusier_vit'
def load(cat,name):return parse_current_xml(A/cat/'vietnam'/(name+'.xml')).getroot()
def ext(s,name):return s.find('list/template_reference[@value="ebpextensions\\'+name+'"]')
def val(s,path):return s.find(path).get('value')
class ArquebusierRedesign(unittest.TestCase):
 def test_root_and_campaign_match_approved_stats(self):
  t=load('ebps','vn_unit_handcannon_4_chi')
  for s in [t,*t.findall('variant')]:
   with self.subTest(variant=s.get('name','root')):
    c=ext(s,'cost_ext');self.assertEqual([val(c,'group/enum_table/float[@name="'+k+'"]') for k in ['food','wood','gold']],['120','40','80'])
    self.assertEqual(val(c,'group/float[@name="time_seconds"]'),'35')
    h=ext(s,'health_ext');self.assertEqual(val(h,'float[@name="hitpoints"]'),'130')
    self.assertEqual([val(h,'enum_table[@name="armor_scaler_by_damage_type"]/float[@name="'+k+'"]') for k in ['Melee','Ranged']],['0','0'])
    self.assertEqual(val(ext(s,'moving_ext'),'enum_table/float[@name="default_speed"]'),'4.5')
    self.assertEqual(val(ext(s,'population_ext'),'float[@name="personnel_pop"]'),'1')
 def test_gunpowder_weapon_uses_native_piercing_not_circle(self):
  t=load('weapon','vn_weapon_handcannon_4_vit')
  for s in [t,*t.findall('variant')]:
   b=s.find('group');self.assertEqual(val(b,'group[@name="behaviour"]/bool[@name="piercing"]'),'True')
   self.assertEqual(val(b,'group[@name="projectile"]/instance_reference[@name="projectile"]'),P)
   self.assertEqual(val(b,'group[@name="area_effect"]/template_reference[@name="area_info"]'),r'options\area_info_options\point_area_option')
   self.assertEqual(val(b,'group[@name="damage"]/float[@name="max"]'),'19')
   self.assertEqual(val(b,'group[@name="range"]/float[@name="max"]'),'16')
   self.assertIsNone(b.find('list[@name="target_type_table"]'))
   self.assertEqual(val(s,'instance_reference[@name="parent_pbg"]'),r'weapon\races\common\ranged\weapon_handcannon_3')
 def test_authored_timing_budget(self):
  t=load('weapon','vn_weapon_handcannon_4_vit')
  for s in [t,*t.findall('variant')]:
   b=s.find('group'); timings=[float(val(b,p)) for p in ['group[@name="fire"]/float[@name="wind_up"]','group[@name="fire"]/float[@name="wind_down"]','group[@name="aim"]/group[@name="fire_aim_time"]/float[@name="max"]','group[@name="reload"]/group[@name="duration"]/float[@name="max"]']]
   self.assertEqual(sum(timings),2.0);self.assertGreater(timings[-1],sum(timings[:-1]))
 def test_private_projectile_keeps_donor_collision_across_variants(self):
  t=load('ebps','vn_projectile_arquebusier_vit');d=parse_current_xml(W/'evidence/arquebusier/ebps__projectile_bolt_springald.xml').getroot()
  self.assertEqual(val(t,'instance_reference[@name="parent_pbg"]'),r'ebps\projectiles\projectile_bolt_springald')
  for s in t.findall('variant'):
   actual=ext(s,'projectile_ext'); expected=ext(d,'projectile_ext')
   self.assertEqual([(n.tag,n.get('name'),n.get('value')) for n in actual.iter()],[(n.tag,n.get('name'),n.get('value')) for n in expected.iter()])
  for s in [t,*t.findall('variant')]:
   self.assertEqual(val(ext(s,'entity_blueprint_ext'),'bool[@name="is_visible_in_game"]'),'False')
   self.assertEqual(val(ext(s,'entity_blueprint_ext'),'instance_reference[@name="animator_attachments"]'),'')
 def test_all_production_paths_share_private_entity_and_weapon(self):
  for name in ['vn_unit_handcannon_4_chi','vn_unit_handcannon_4_chi_cheap']:
   t=load('sbps',name)
   for s in [t,*t.findall('variant')]:
    self.assertEqual(val(s,'list/template_reference[@value="sbpextensions\\squad_loadout_ext"]/list/group/instance_reference[@name="type"]'),'ebps\\vietnam\\units\\ranged\\heavy_arquebusiers\\vn_unit_handcannon_4_chi')
  t=load('ebps','vn_unit_handcannon_4_chi')
  for s in [t,*t.findall('variant')]:
   self.assertIn(r'weapon\vietnam\vn_weapon_handcannon_4_vit',[n.get('value') for n in s.findall('.//instance_reference[@name="non_entity_weapon_wrapper_pbg"]')])
 def test_new_projectile_is_precached(self):
  name='a743d7d1d7534cf78817e29d8ded7366:vn_projectile_arquebusier_vit'
  t=parse_current_xml(R/'assets/scar/winconditions/VietnamMode.rdo').getroot()
  self.assertEqual(sum(n.get('Value')==name for n in t.iter('DataProperty')),1)
  self.assertEqual((current_path(R/'assets/scar/vietnam/prematch_precache.scar')).read_text(encoding='utf-8').count('"'+name+'"'),1)
if __name__=='__main__':unittest.main()
