from pathlib import Path
import sys,copy,xml.etree.ElementTree as E,json
sys.path.insert(0,'tools/release_0710');from common import *
sys.path.insert(0,'tools/release_072/vendor');import extension_audit as a
a.ROOT=ROOT;a.GUID=CFG['project_guid'].replace('-','')
guard();local=a.load_local(ROOT);official=read(OUT/'hideout/official-extensions.json')['records'];resolver=a.Resolver(local,official)
ref=r'attachments\attachment_lists\vietnam\release_0710\vn_0710_hideout_fortified_visual'
rows=[]
for name in ['vn_building_defense_outpost_chi_fortified','vn_building_defense_outpost_2_chi_fortified']:
 path=ROOT/f'assets/attrib/instances/ebps/vietnam/buildings/hideouts/{name}.xml';doc=E.parse(path);root=doc.getroot();key='ebps\\vietnam\\buildings\\hideouts\\'+name
 for variant,node in [('default',root),('campaign',root.find('variant'))]:
  scope=node.find('list'); parent=node.find('instance_reference').get('value');parentdoc=E.parse(ROOT/'assets/attrib/instances'/Path(parent.replace('\\','/')+'.xml')).getroot();ps=parentdoc if variant=='default' else parentdoc.find('variant')
  effective=resolver.effective(key,variant);evidence=[]
  for extname in ['entity_blueprint_ext','tier_ext']:
   item=next((x for x in effective if x['value']=='ebpextensions\\'+extname),None)
   if item is None:
    assert extname=='tier_ext' and '_2_' in name;continue
   for existing in list(scope):
    if existing.get('value')==item['value']:scope.remove(existing)
   original=next(x for x in ps.find('list') if x.get('value')==item['value']); clone=copy.deepcopy(original)
   clone.attrib.pop('List.ListAction',None);clone.set('List.ParentItemID',item['List.ItemID'])
   if extname=='tier_ext':clone.find('list').set('overrideParent','True')
   for elem in list(clone):
    if extname=='entity_blueprint_ext' and elem.get('name')!='animator_attachments':clone.remove(elem)
   for val in clone.iter('instance_reference'):
    if val.get('name') in ['animator_attachments','attachments']:val.set('value',ref)
   scope.append(clone);evidence.append({'extension':extname,'inherited_id':item['List.ItemID'],'operation':'exact inherited override','parent':parent})
  rows.append({'file':str(path),'variant':variant,'extensions':evidence})
 E.indent(root,space='\t');doc.write(path,encoding='utf-8',xml_declaration=True)
identity=read(OUT/'hideout/allocated-identity.json')['pbgid']
assert not any(f'value="{identity}"' in p.read_text(encoding='utf-8-sig') for p in (ROOT/'assets/attrib/instances').rglob('*.xml') if p.name!='vn_0710_hideout_fortified_visual.xml')
root=E.Element('instance',version='2',description='Fortified-only visual identity. Complete native attachment overlay retained in release_0710 payload.',template=r'attachments\attachment_lists')
E.SubElement(root,'uniqueid',name='pbgid',value=str(identity));E.SubElement(root,'instance_reference',name='parent_pbg',value=r'attachments\attachment_lists\vietnam\release_020\vn_020_hideout_visual',mod=a.GUID)
p=ROOT/'assets/attrib/instances'/Path(ref.replace('\\','/')+'.xml');p.parent.mkdir(parents=True,exist_ok=True);E.indent(root,space='\t');E.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True)
write(OUT/'hideout/source-policy.json',{'status':'inherited extension identities proved before edits','changes':rows,'new_attachment':str(p),'pbgid':identity,'allowed_fields':['entity_blueprint_ext/animator_attachments','tier_ext/tier_group_list/tier_group/tier/attachments'],'official_sha256':read(OUT/'hideout/official-extensions.json')['archive_sha256']})

