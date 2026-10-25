"""Record exact source consumers and reviewable deferred visual substitutions."""
import xml.etree.ElementTree as ET
from common import *
def main():
 guard();rows=[]
 base=ROOT/'assets/attrib/instances'
 for p in sorted(base.rglob('*.xml')):
  if not (p.name.startswith('vn_unit_skirmisher_') or p.name.startswith('vn_tower_train_skirmisher_') or p.name in ('vn_unit_water_buffalo_vit.xml','vn_weapon_skirmisher_2_vit.xml','vn_weapon_skirmisher_3_vit.xml','vn_weapon_skirmisher_4_vit.xml','vn_upgrade_skirmisher_3_vit.xml','vn_upgrade_skirmisher_4_vit.xml')):continue
  tree=ET.parse(p);references=[]
  def walk(node,path,variant='default'):
   if node.tag=='variant':variant=node.get('name')
   part=node.tag+'['+(node.get('name') or '')+']'
   if node.get('List.ItemID'):part+='@'+node.get('List.ItemID')
   path=path+'/'+part
   if node.get('value') and ('skirmisher' in node.get('value') or 'javelin' in node.get('value') or node.get('name') in ('animator_attachments','parent_pbg')):
    references.append({'variant':variant,'node':path,'value':node.get('value'),'mod':node.get('mod')})
   for c in node:walk(c,path,variant)
  walk(tree.getroot(),'')
  rows.append({'source':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'references':references})
 changes=[]
 for age in (2,3,4):
  changes.append({'asset':'skirmisher'+str(age),'stock_attachment':f'attachments/attachment_lists/civilizations/malian/units/tier{age}_javelin_mal','private_attachment_name':f'vn076_skirmisher_body_{age}','field':'attachment_lists/attachment_lists/attachment_list/attachment_list/animator_merge_mesh_attachment/meshes/animator0','model':f'art/scenario/garrison/cc076/skirmisher{age}/model','preserve':'parent animator, list identities, speech, upgrade selectors and all gameplay fields'})
  changes.append({'asset':'javelin'+str(age),'private_attachment_name':f'vn076_skirmisher_weapon_{age}','model':f'art/scenario/garrison/cc076/javelin{age}/model','socket':'MetaRig_RArmPalmSocket','owner_to_preserve':'art/civilizations/malian/weapons/mal_javelin_throwing/mal_javelin_throwing','integration_gate':'Clone native throwing lifecycle privately; replace its geometry references, not the stock animation owner with a static model. Inspect held/throwing age selectors in selected baseline.'})
  changes.append({'asset':'projectile'+str(age),'private_projectile_name':f'vn076_projectile_javelin_{age}','model':f'art/scenario/garrison/cc076/projectile{age}/model','consumer':f'weapon/vietnam/vn_weapon_skirmisher_{age}_vit','field':'weapon_bag/projectile/projectile','preserve':'clone exact native projectile; change visual only, preserve motion/collision/damage and private owner qualification'})
 changes.append({'asset':'buffalo','consumer':'vn_unit_water_buffalo_vit','private_attachment_name':'vn076_water_buffalo','native_visual_donor':'attachments/attachment_lists/gaia/animals/gaia_herdable_cattle_mal','parent_animator':'art/civilizations/common/animals/archetypes/base_cattle/base_cattle','model':'art/scenario/garrison/cc076/buffalo/model','field':'attachment_lists/attachment_lists/attachment_list/attachment_list/animator_skin_attachment/animator','preserve':'Existing Worker Elephant gameplay parent; replace only buffalo presentation; never convert entity to herdable cattle. Do not alter shared v6i93139eb if used by other elephants.','integration_gate':'Bovine movement/death/build-response coverage in native game remains unverified; custom supervision action disabled.'})
 write(RECIPES/'bindings.json',{'schema':'ccp076-bindings/v1','status':'deferred_visual_patch_specification_not_applied','destination_guid':CFG['project_guid'],'source_consumers':rows,'changes':changes,'baseline_policy':'Resolve effective compiled consumers from explicitly selected completed release. Compare these source hashes, detect compiled-only overrides, allocate private identities through supported tools, and stage a copied candidate. Never overwrite live source.','extension_policy':'No new EBPS/SBPS singleton extensions. If a future binding needs one, resolve full private and official variant chain first.','scar_patch':None,'supervision_animation':'source_only_not_enabled'})
 print('CONSUMER_MAP_WRITTEN',len(rows))
if __name__=='__main__':main()
