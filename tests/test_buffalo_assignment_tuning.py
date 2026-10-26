"""Approved tuning deltas against immutable immediately-before evidence."""
from pathlib import Path
import unittest,zipfile,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
BUILD_REPAIR=ROOT/'work/vietnam_redesign/command_card_build_repair_20261022'

def command_card_errors(root):
 schema=E.parse(BUILD_REPAIR/'ui_command_card_info.xml').getroot()
 bounds={n.get('name'):(int(n.get('min')),int(n.get('max'))) for n in schema.findall("group[@name='ui_position']/int")}
 errors=[]
 for card in root.findall(".//template_reference[@value='ui_command_card_info']"):
  for n in card.findall("group[@name='ui_position']/int"):
   low,high=bounds[n.get('name')]
   if not low<=int(n.get('value'))<=high:errors.append((n.get('name'),n.get('value')))
 return errors

class AssignmentTuningTests(unittest.TestCase):
 def test_actual_failed_build_coordinates_violate_current_native_schema(self):
  with zipfile.ZipFile(BUILD_REPAIR/'before.zip') as z:
   errors=[error for name in z.namelist() if name.endswith('.xml') for error in command_card_errors(E.fromstring(z.read(name))) ]
  self.assertEqual(len(errors),24)
  self.assertEqual({value for field,value in errors},{'-1'})

 def test_all_authored_command_card_coordinates_match_native_bounds(self):
  errors=[(p.relative_to(ROOT).as_posix(),issue) for p in (ROOT/'assets/attrib/instances').rglob('*.xml') for issue in command_card_errors(E.parse(p).getroot())]
  self.assertEqual(errors,[])

 def test_build_repair_preserves_every_other_villager_value_and_identity(self):
  changed=0
  # Verify that historical repair against its preserved output, not later
  # authorized removal of Paddy construction from these same menus.
  with zipfile.ZipFile(BUILD_REPAIR/'before.zip') as z, zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_feedback_v4_20261022/before.zip') as repaired:
   for name in z.namelist():
    if not name.endswith('.xml'):continue
    old,new=E.fromstring(z.read(name)),E.fromstring(repaired.read(name))
    old_cards=old.findall(".//template_reference[@value='ui_command_card_info']")
    new_cards=new.findall(".//template_reference[@value='ui_command_card_info']")
    self.assertEqual(len(old_cards),len(new_cards))
    for a,b in zip(old_cards,new_cards):
     for before,after in zip(a.findall("group[@name='ui_position']/int"),b.findall("group[@name='ui_position']/int")):
      if before.get('value')=='-1':
       self.assertEqual(after.get('value'),'0');after.set('value','-1');changed+=1
    self.assertEqual(E.tostring(old),E.tostring(new),name)
  self.assertEqual(changed,24)

 def test_user_villager_entities_and_completed_food_source_are_byte_preserved(self):
  # V5 explicitly authorizes Buffalo migration and Villager MENU removal.
  # Their actual entities and the completed food deposit remain protected.
  with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v5_20261023/before.zip') as z:
   for name in z.namelist():
    if name.endswith('.xml') and name.startswith('assets/attrib/instances/ebps/') and ('/villagers/' in name or name.endswith('/vn_building_resource_farm_chi.xml') or name.endswith('/vn_unit_war_elephant_1_vit.xml')):
     self.assertEqual((ROOT/name).read_bytes(),z.read(name),name)
 def test_abilities_free_effectless_and_work_has_official_target_approach(self):
  for mode in ['work','leave']:
   r=E.parse(ROOT/f'assets/attrib/instances/abilities/vietnam/vn_buffalo_{mode}_paddy_vit.xml').getroot()
   self.assertEqual(r.find(".//enum[@name='activation']").get('value'),'targeted' if mode=='work' else 'timed')
   self.assertTrue(all(n.get('value')=='0' for n in r.findall(".//enum_table[@name='cost_to_player']/float")))
   self.assertTrue(all(n.get('value')=='' for n in r.findall('.//state_tree_node')))
   self.assertFalse(any(len(n) for n in r.findall("group/list[@name='requirements']")))
   if mode=='work':
    for name,value in [('target','tp_entity'),('range','1'),('range_ignore','False'),('can_move_to_cast','True'),('pending_ability_out_of_range_behaviour','chase'),('use_simbox_to_simbox_range','False')]:
     self.assertTrue(all(n.get('value')==value for n in r.findall(f".//*[@name='{name}']")),name)
    self.assertTrue(all(n.get('value')=='options\\none' for n in r.findall(".//template_reference[@name='channeling']")))
 def test_work_carrier_only_changes_approved_scalars_and_preserves_identities(self):
  name='assets/attrib/instances/abilities/vietnam/vn_buffalo_work_paddy_vit.xml'
  with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_feedback_v4_20261022/before.zip') as z:
   old=E.fromstring(z.read(name))
  # Later v6 explicitly authorizes native target-filter reparenting. Keep
  # this earlier scalar-only preservation gate against its frozen output.
  with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v6_20261023/before.zip') as z:
   new=E.fromstring(z.read(name))
  allowed={'activation','target','range','range_ignore','use_simbox_to_simbox_range','can_move_to_cast','facing_ignore','recharge_time','cursor_good','cursor_nonmodal_good','cursor_bad'}
  def normalized(node):
   attrs=dict(node.attrib)
   if attrs.get('name') in allowed:attrs['value']='<approved scalar>'
   return node.tag,tuple(sorted(attrs.items())),tuple(normalized(c) for c in node)
  self.assertEqual(normalized(old),normalized(new))
 def test_villager_menus_have_no_paddy_or_hidden_assist_entries(self):
  for p in (ROOT/'assets/attrib/instances/sbps/vietnam/units/economy/villagers').glob('*.xml'):
   r=E.parse(p).getroot()
   self.assertFalse([n for n in r.findall(".//group[@name='construction_item']") if n.get('comment','').startswith('Hidden native')])
   self.assertFalse([n for n in r.findall(".//group[@name='construction_item']/instance_reference[@name='ebp']") if 'building_resource_farm' in n.get('value','')])
