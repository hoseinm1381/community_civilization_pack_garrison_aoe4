"""Regression contracts for the two user-reported 087 issues."""
import unittest
import xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/attrib/instances'
TOWER=BASE/'ebps/vietnam/buildings/landmarks/feudal/vn_building_landmark_age1_gatehouse_control_chi.xml'
DONOR=BASE/'ebps/vietnam/buildings/hideouts/vn_building_defense_outpost_chi.xml'
def ext(n,s):
 return n.find("./list[@name='extensions']/template_reference[@value='"+s+"']")
def variants(n):return [n,*n.findall('variant')]
class Regression087(unittest.TestCase):
 def test_tower_accepts_the_same_resources_as_hideout(self):
  for t,d in zip(variants(E.parse(TOWER).getroot()),variants(E.parse(DONOR).getroot())):
   with self.subTest(variant=t.get('name','default')):
    te=ext(t,r'ebpextensions\resource_drop_off_ext');de=ext(d,r'ebpextensions\resource_drop_off_ext')
    self.assertIsNotNone(te,'Tower has no drop-off extension')
    self.assertEqual([(e.tag,e.attrib) for e in te.iter()][1:],[(e.tag,e.attrib) for e in de.iter()][1:])
    tags=ext(t,r'ebpextensions\type_ext').find("list[@name='unit_type_list']")
    self.assertTrue({'economy_building','resource_drop_off'} <= {e.get('value') for e in tags if e.tag=='enum'})
 def test_skirmisher_selection_is_distinct_at_every_age_and_variant(self):
  for age in (2,3,4):
   path=BASE/f'sbps/vietnam/units/ranged/skirmishers/vn_unit_skirmisher_{age}_vit.xml'
   for n in variants(E.parse(path).getroot()):
    with self.subTest(age=age,variant=n.get('name','default')):
     ui=ext(n,r'sbpextensions\squad_ui_ext')
     group=ui.find(".//group[@name='info']/string[@name='selection_group']")
     self.assertIsNotNone(group,'Inherits Archer selection group')
     self.assertEqual(group.get('value'),'vn_skirmisher')
 def test_only_authorized_source_fields_changed(self):
  import json,hashlib,zipfile,copy
  before=json.loads((ROOT/'output/release_085/087-source-before.json').read_text())
  policy=json.loads((ROOT/'output/release_085/087-source-change-policy.json').read_text())
  now={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'assets').rglob('*') if p.is_file()}
  self.assertEqual(set(now),set(before))
  self.assertEqual(sorted(k for k in now if now[k]!=before[k]),sorted(policy['changed']))
  def canonical(n):return(n.tag,sorted(n.attrib.items()),[canonical(c) for c in n])
  with zipfile.ZipFile(ROOT/'output/release_085/087-before-source.zip') as z:
   for f in policy['changed']:
    old=E.fromstring(z.read(f));current=E.parse(ROOT/f).getroot()
    for n in variants(current):
     if '/ebps/' in f:
      extensions=n.find("list[@name='extensions']")
      extensions.remove(ext(n,r'ebpextensions\resource_drop_off_ext'))
      tags=ext(n,r'ebpextensions\type_ext').find("list[@name='unit_type_list']")
      for tag in list(tags):
       if tag.get('value') in ('resource_drop_off','economy_building'):tags.remove(tag)
     else:
      info=ext(n,r'sbpextensions\squad_ui_ext').find(".//group[@name='info']")
      info.remove(info.find("string[@name='selection_group']"))
    self.assertEqual(canonical(current),canonical(old),f)

if __name__=='__main__':unittest.main()
