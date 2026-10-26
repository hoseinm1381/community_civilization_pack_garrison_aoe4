import unittest,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets/attrib/instances'
KEY=r"upgrade\vietnam\vn_upgrade_champa_rice_vit"
class EconomyIntegrationTests(unittest.TestCase):
 def test_champa_cost_age_and_once_only(self):
  root=E.parse(A/(KEY.replace('\\','/')+'.xml')).getroot();b=root.find('group');cost=b.find('group[@name="time_cost"]')
  self.assertEqual([cost.find('enum_table/float[@name="'+n+'"]').get('value') for n in ['food','wood','gold','stone']],['0','100','250','0'])
  self.assertEqual(cost.find('float').get('value'),'30')
  self.assertEqual(b.find('group[@name="ui_info"]/string[@name="hotkey_name"]').get('value'),'X')
  for position in b.findall('.//group[@name="ui_position"]'):
   if position.find('int[@name="ui_position_row"]').get('value')!='-1':
    self.assertEqual([position.find('int[@name="'+n+'"]').get('value') for n in ['ui_position_row','ui_position_column']],['3','2'])
  self.assertEqual(b.find('float[@name="global_max_limit"]').get('value'),'1')
  req=b.find('list[@name="requirements"]')
  self.assertEqual(req[0].find('instance_reference').get('value'),r'upgrade\dev\ages\castle_age')
  self.assertEqual(req[1].find('instance_reference').get('value'),KEY)
  self.assertEqual(req[1].find('bool[@name="include_queued"]').get('value'),'True')
 def test_ministry_and_pagoda_shared_research(self):
  names=['vn_building_econ_food_control_chi','vn_building_landmark_age1_vit_one_pilar_pagoda','vn_building_landmark_age1_headquarters_control_chi']
  menus=[]
  for name in names:
   p=next((A/'ebps/vietnam').rglob(name+'.xml'));r=E.parse(p).getroot()
   for scope in [r,*r.findall('variant')]:
    refs=[x.get('value') for x in scope.findall('list/template_reference[@value="ebpextensions\\upgrade_ext"]/list/instance_reference')]
    self.assertEqual(refs.count(KEY),1)
    for age in [2,3,4]:self.assertIn(r'upgrade\races\japanese\research\economy\upgrade_econ_resource_wood_harvest_rate_'+str(age)+'_kura_jpn',refs)
    menus.append(set(refs))
  self.assertTrue(all(x==menus[0] for x in menus))
 def test_lifecycle_imports_and_cleanup(self):
  mode=(ROOT/'assets/scar/winconditions/VietnamMode.scar').read_text();life=(ROOT/'assets/scar/vietnam/lifecycle.scar').read_text()
  for module,prefix in [('paddy_food','VietnamPaddyFood'),('paddy_wood','VietnamPaddyWood'),('pagoda_buffalo','VietnamPagodaBuffalo')]:
   self.assertIn('import("vietnam/'+module+'.scar")',mode)
   self.assertEqual(life.count(prefix+'_Update('),1)
   self.assertEqual(life.count(prefix+'_Cleanup()'),1)
  self.assertEqual(life.count('VietnamPagodaBuffalo_Start(civilizations)'),1)
