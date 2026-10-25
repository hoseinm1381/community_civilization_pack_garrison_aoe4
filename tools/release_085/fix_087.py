"""Narrow 087 editable patch; native compile and owning-resource assembly are separate."""
import copy,gzip,hashlib,json,re
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_085'
TOWER='assets/attrib/instances/ebps/vietnam/buildings/landmarks/feudal/vn_building_landmark_age1_gatehouse_control_chi.xml'
DONOR='assets/attrib/instances/ebps/vietnam/buildings/hideouts/vn_building_defense_outpost_chi.xml'
SKIRMS=[f'assets/attrib/instances/sbps/vietnam/units/ranged/skirmishers/vn_unit_skirmisher_{a}_vit.xml' for a in (2,3,4)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ext(n,s):return n.find("./list[@name='extensions']/template_reference[@value='"+s+"']")
def variants(n):return [n,*n.findall('variant')]
def main():
 receipt=OUT/'087-source-before.json'
 assert not receipt.exists(),'One-time source edit; preserve earlier evidence'
 files=[TOWER,*SKIRMS]
 before={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
 receipt.write_text(json.dumps(before,indent=2),encoding='utf-8')
 import zipfile
 with zipfile.ZipFile(OUT/'087-before-source.zip','x',zipfile.ZIP_DEFLATED) as z:
  for f in files:z.write(ROOT/f,f)
 # New list items only: reserve a locally unused descending signed-32 range.
 # No PBG identity or inherited extension identity is allocated/changed.
 used=set()
 for p in (ROOT/'assets/attrib/instances').rglob('*.xml'):
  used.update(re.findall(r'List\.(?:ItemID|ParentItemID)="(-?\d+)"',p.read_text(encoding='utf-8')))
 allocated=[];nextid=2147469800
 def allocate():
  nonlocal nextid
  while str(nextid) in used:nextid-=1
  value=str(nextid);nextid-=1;used.add(value);allocated.append(value);return value
 tower=E.parse(ROOT/TOWER);donor=E.parse(ROOT/DONOR)
 for t,d in zip(variants(tower.getroot()),variants(donor.getroot())):
  assert ext(t,r'ebpextensions\resource_drop_off_ext') is None
  drop=copy.deepcopy(ext(d,r'ebpextensions\resource_drop_off_ext'))
  drop.set('List.ItemID',allocate());drop.attrib.pop('List.ParentItemID',None)
  t.find("list[@name='extensions']").append(drop)
  tags=ext(t,r'ebpextensions\type_ext').find("list[@name='unit_type_list']")
  for value in ('resource_drop_off','economy_building'):
   assert value not in {x.get('value') for x in tags}
   E.SubElement(tags,'enum',{'name':'unit_type','value':value,'List.ItemID':allocate(),'List.ListAction':'Append'})
 # Source preservation is checked structurally against the frozen original.
 E.indent(tower,space='\t');tower.write(ROOT/TOWER,encoding='utf-8',xml_declaration=True)
 for f in SKIRMS:
  tree=E.parse(ROOT/f)
  for n in variants(tree.getroot()):
   info=ext(n,r'sbpextensions\squad_ui_ext').find(".//group[@name='info']")
   assert info.find("string[@name='selection_group']") is None
   E.SubElement(info,'string',{'name':'selection_group','value':'vn_skirmisher','overrideParent':'True'})
  E.indent(tree,space='\t');tree.write(ROOT/f,encoding='utf-8',xml_declaration=True)
 (OUT/'087-source-change-policy.json').write_text(json.dumps({'changed':files,'new_list_item_ids':allocated,'new_pbg_ids':[], 'selection_group':'vn_skirmisher','donor':DONOR},indent=2),encoding='utf-8')
 print('087_SOURCE_PATCHED',files)
if __name__=='__main__':main()
