"""Explicit baseline, reversible typed native visual patches, no active source writes."""
import copy,struct,re
from common import *
from inventory import official
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd,relic_chunky as rc
sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
from read_official_members import members
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check as identity

def main(base,expected,label):
 guard();assert re.fullmatch('[a-z0-9-]{1,20}',label)
 assert sha(base)==expected;identity(ROOT,base)
 dest=OUT/'integration'/label
 if dest.exists():raise FileExistsError('Immutable integration label already exists')
 dest.mkdir(parents=True)
 before=read(base.parent/'verification.json');assert before['sga_sha256']==expected
 back=base.parent/'readback'
 for name,digest in before['member_sha256'].items():assert sha(back/name)==digest
 write(dest/'baseline.json',{'archive':str(base),'sha256':expected,'verification_sha256':sha(base.parent/'verification.json'),'version':'0.7.5','source_policy':'active source retained; all integration is a version-owned native overlay'})
 # Current official archive inventory, not a stale numeric-ID guess.
 ids=set();stock={};official_archive=Path(CFG['content_editor']).parent/'cardinal/archives/Attrib.sga';official_hash=sha(official_archive)
 for name,raw in members('Attrib.sga',lambda n:n.endswith('.rgd')):
  doc=rgd.read(raw)
  ids.update(int(n.value) for p,n in rgd.flatten(doc.nodes) if re.fullmatch('[^/]+/pbgid',p))
  if name=='projectile_javelin.rgd':
   kind='attachment' if any(n.key=='attachment_lists' for n in doc.nodes[0].value) else 'ebps';assert kind not in stock;stock[kind]=raw
 assert set(stock)=={'attachment','ebps'}
 for p in (back/'attrib').rglob('*.rgd'):
  ids.update(int(n.value) for s,n in rgd.flatten(rgd.read(p.read_bytes()).nodes) if re.fullmatch('[^/]+/pbgid',s))
 nextid=2147407600;assigned={};payload={};patches=[];guid=CFG['project_guid'].replace('-','')
 def alloc(name):
  nonlocal nextid
  while nextid in ids:nextid-=1
  value=nextid;ids.add(value);assigned[name]=value;nextid-=1;return value
 def put(member,raw):
  assert member not in payload
  p=dest/'payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  payload[member]={'file':str(p),'sha256':sha(p)}
 def patch(raw,member,changes,newid=None):
  original=rgd.read(raw);assert rgd.write(original)==raw
  doc=copy.deepcopy(original);edits=[]
  for path,node in list(rgd.flatten(doc.nodes)):
   value=changes(path,node)
   if newid is not None and re.fullmatch('[^/]+/pbgid',path):value=newid
   if value is not None and value!=node.value:
    edits.append({'path':path,'kind':node.kind,'before':copy.deepcopy(node.value),'after':copy.deepcopy(value)});node.value=value
  assert edits,member
  result=rgd.write(doc);reread=rgd.read(result)
  restored=copy.deepcopy(reread)
  for e in reversed(edits):rgd.find(restored.nodes,e['path']).value=e['before']
  assert rgd.write(restored)==raw,(member,'nonvisual drift')
  put(member,result);patches.append({'member':member,'donor_sha256':hashlib.sha256(raw).hexdigest(),'changes':edits,'exact_reversal':True})
  # Typed editable JSON is the source for these compiled-only overlays.
  run('decode-'+Path(member).stem,[CFG['archive_tool'],'decode-rgd',payload[member]['file'],dest/'decoded'/Path(member).name],dest/'logs')
 def private(category,name):return f'attrib/{category}/vietnam/release_076/{name}.rgd'
 def attach(name,donor,fn):patch(donor,private('attachments/attachment_lists',name),fn,alloc(name))
 def ref(name):return guid+':'+name
 # Private age body lists keep the native humanoid animation owner.
 for age in (2,3,4):
  name=f'vn076_skirmisher_body_{age}';raw=official(f'attrib/attachments/attachment_lists/civilizations/malian/units/tier{age}_javelin_mal.rgd').read_bytes()
  attach(name,raw,lambda p,n,a=age: f'art\\scenario\\garrison\\cc076\\skirmisher{a}\\model' if n.key=='animator0' else None)
  name=f'vn076_skirmisher_weapon_{age}';raw=official(f'attrib/attachments/attachment_lists/races/core/weapons/wpn_range_javelin_{age}.rgd').read_bytes()
  attach(name,raw,lambda p,n,a=age:f'art\\scenario\\garrison\\cc076\\javelin{a}\\model' if p.endswith('/parent_animator') else None)
  name=f'vn076_projectile_visual_{age}'
  attach(name,stock['attachment'],lambda p,n,a=age:f'art\\scenario\\garrison\\cc076\\projectile{a}\\model' if p.endswith('/parent_animator') else None)
  name=f'vn076_projectile_javelin_{age}'
  patch(stock['ebps'],private('ebps',name),lambda p,n,a=age:ref(f'vn076_projectile_visual_{a}') if p.endswith('/animator_attachments/$PBGNAME') else None,alloc(name))
 # Buffalo presentation only, with empty tier visuals so no inherited elephant meshes attach.
 cow=official('attrib/attachments/attachment_lists/gaia/animals/gaia_herdable_cattle_mal.rgd').read_bytes()
 attach('vn076_water_buffalo',cow,lambda p,n:'art\\scenario\\garrison\\cc076\\buffalo\\model' if p.endswith('/animator_skin_attachment/animator') else None)
 empty=copy.deepcopy(rgd.read(cow))
 for p,n in list(rgd.flatten(empty.nodes)):
  if p.endswith('/attachment_lists/parent_animator'):n.value=''
  if re.fullmatch('[^/]+/attachment_lists/attachment_lists',p):n.value=[]
 raw=rgd.write(empty)
 attach('vn076_empty_tier',raw,lambda p,n:None)
 replacements={f'tier{a}_javelin_mal':ref(f'vn076_skirmisher_body_{a}') for a in (2,3,4)}
 replacements.update({f'wpn_range_javelin_{a}':ref(f'vn076_skirmisher_weapon_{a}') for a in (2,3,4)})
 for p in sorted((back/'attrib/ebps/vietnam/units/ranged/skirmishers').glob('*.rgd')):
  patch(p.read_bytes(),p.relative_to(back).as_posix(),lambda path,n:replacements.get(n.value) if n.kind=='CString' and path.endswith('/$PBGNAME') and ('/attachments/' in path or '/animator_attachments/' in path) else None)
 for age in (2,3,4):
  p=back/f'attrib/weapon/vietnam/vn_weapon_skirmisher_{age}_vit.rgd'
  patch(p.read_bytes(),p.relative_to(back).as_posix(),lambda path,n,a=age:ref(f'vn076_projectile_javelin_{a}') if path.endswith('/projectile/projectile/$PBGNAME') else None)
 p=back/'attrib/ebps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.rgd'
 patch(p.read_bytes(),p.relative_to(back).as_posix(),lambda path,n:ref('vn076_water_buffalo') if path.endswith('/entity_blueprint_ext/animator_attachments/$PBGNAME') else ref('vn076_empty_tier') if '/tier_ext/' in path and path.endswith('/attachments/$PBGNAME') else None)
 # Freshly cooked media, with native throw/hide selector and RGO retained privately.
 manifest=read(OUT/'manifest.json');assert manifest['cook_label']=='v5'
 throw='art/civilizations/malian/weapons/mal_javelin_throwing/mal_javelin_throwing'
 donor=official(throw+'.rgm').read_bytes();donordoc=rc.parse(donor);msbp=next(c for c in rc.walk(donordoc.roots) if c.tag==b'MSBP')
 selector_old=rc.lp_string('mal_javelin_throwing');selector_new=rc.lp_string('body')
 # Replace only typed length-prefixed mesh names; CNBP condition bytes are exact.
 edits={c.offset:c.payload.replace(selector_old,selector_new) for c in rc.walk([msbp]) if c.tag in (b'MSA ',b'MSD ')}
 selected=rc.rebuild(donordoc,lambda c:edits.get(c.offset));newms=next(c for c in rc.walk(rc.parse(selected).roots) if c.tag==b'MSBP')
 assert [c.payload for c in rc.walk([msbp]) if c.tag==b'CNBP']==[c.payload for c in rc.walk([newms]) if c.tag==b'CNBP']
 for asset in manifest['payloads']:
  for row in asset['files']:
   source=OUT/row['source'];assert sha(source)==row['sha256'];raw=source.read_bytes();member=row['destination']
   if asset['asset'].startswith('javelin'):
    if member.endswith('.rgm'):
     doc=rc.parse(raw);node=next(c for c in rc.walk(doc.roots) if c.tag==b'MSBP');raw=rc.rebuild(doc,lambda c:newms.payload if c.offset==node.offset else None)
    elif member.endswith('.rgo'):raw=official(throw+'.rgo').read_bytes()
   put(member,raw)
 # Binding changes are only CString visual references. Existing numerical gameplay is exact.
 assert all(e['kind']=='CString' for p in patches if p['member'] in before['member_sha256'] for e in p['changes'])
 assert sha(official_archive)==official_hash
 write(dest/'recipe.json',{'schema':'cc076-integration/v1','baseline':str(base),'baseline_sha256':expected,'art_manifest':str(OUT/'manifest.json'),'art_manifest_sha256':sha(OUT/'manifest.json'),'official_attrib_sha256':official_hash,'allocated_ids':assigned,'patches':patches,'payload':payload,'native_selector_condition_bytes_preserved':True,'native_rgo_source':throw+'.rgo','all_existing_gameplay_numeric_fields_unchanged':True,'supervision_action':'source_only_disabled','native_acceptance':False})
 print('INTEGRATION_PREPARED',len(payload),len(patches),str(dest/'recipe.json'))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--baseline-sha256',required=True);p.add_argument('--label',required=True);a=p.parse_args();main(a.baseline,a.baseline_sha256,a.label)
