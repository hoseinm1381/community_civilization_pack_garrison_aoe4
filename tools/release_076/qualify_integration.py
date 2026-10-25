"""Independent current-official provenance and native selector qualification."""
import sqlite3,struct
from common import *
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd,relic_chunky as rc
sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
from read_official_members import members

def main(recipe):
 guard();recipe=Path(recipe);r=read(recipe);dest=recipe.parent/'qualification';dest.mkdir(exist_ok=True)
 attrib=Path(CFG['content_editor']).parent/'cardinal/archives/Attrib.sga'
 assert sha(attrib)==r['official_attrib_sha256'];wanted={}
 for age in (2,3,4):
  wanted[f'tier{age}_javelin_mal.rgd']=f'attachments/attachment_lists/civilizations/malian/units/tier{age}_javelin_mal.rgd'
  wanted[f'wpn_range_javelin_{age}.rgd']=f'attachments/attachment_lists/races/core/weapons/wpn_range_javelin_{age}.rgd'
 wanted['gaia_herdable_cattle_mal.rgd']='attachments/attachment_lists/gaia/animals/gaia_herdable_cattle_mal.rgd'
 found={};projectiles=[]
 for name,relative in wanted.items():
  target=dest/'attrib'/relative;target.parent.mkdir(parents=True,exist_ok=True)
  run('official-'+name,[CFG['archive_tool'],'extract-member',attrib,'attrib/'+relative,target],dest/'logs')
  cached=OUT/'official/attrib'/relative;assert cached.read_bytes()==target.read_bytes()
  found[name]={'member':'attrib/'+wanted[name],'sha256':sha(cached),'cached_matches_current_archive':True}
 for name,raw in members('Attrib.sga',lambda n:n=='projectile_javelin.rgd'):projectiles.append(hashlib.sha256(raw).hexdigest())
 assert set(found)==set(wanted)
 for p in r['patches']:
  if '/release_076/vn076_projectile_' in p['member']:assert p['donor_sha256'] in projectiles
 # Fresh archive extraction verifies both cached lifecycle files.
 stem='art/civilizations/malian/weapons/mal_javelin_throwing/mal_javelin_throwing';sources={};archive_hashes={}
 with sqlite3.connect('file:'+str(Path.home()/'AppData/Local/Garrison/Kit/game-assets.sqlite3').replace('\\','/')+'?mode=ro',uri=True) as db:
  for ext in ('.rgm','.rgo'):
   member=stem+ext;rows=db.execute('select archive_path from resolved_assets where logical_path=?',(member,)).fetchall();assert len(rows)==1
   archive=Path(rows[0][0]);out=dest/('current'+ext)
   run('official-lifecycle-'+ext[1:],[CFG['archive_tool'],'extract-member',archive,member,out],dest/'logs')
   assert out.read_bytes()==(OUT/'official'/member).read_bytes()
   if str(archive) not in archive_hashes:archive_hashes[str(archive)]=sha(archive)
   sources[member]={'archive':str(archive),'sha256':sha(out),'cached_matches_current_archive':True}
 donor=rc.parse((dest/'current.rgm').read_bytes());native_msbp=next(c for c in rc.walk(donor.roots) if c.tag==b'MSBP')
 native_conditions=[c.payload for c in rc.walk([native_msbp]) if c.tag==b'CNBP'];checks={}
 for age in (2,3,4):
  stem=f'art/scenario/garrison/cc076/javelin{age}/model'
  model=Path(r['payload'][stem+'.rgm']['file']).read_bytes();doc=rc.parse(model);ms=next(c for c in rc.walk(doc.roots) if c.tag==b'MSBP')
  assert [c.payload for c in rc.walk([ms]) if c.tag==b'CNBP']==native_conditions
  names=[]
  for c in rc.walk([ms]):
   if c.tag==b'MSA ':count=struct.unpack_from('<I',c.payload)[0];pos=4
   elif c.tag==b'MSD ' and len(c.payload)>4:_,pos=rc.read_lp_string(c.payload,0);count=struct.unpack_from('<I',c.payload,pos)[0];pos+=4
   else:continue
   for _ in range(count):name,pos=rc.read_lp_string(c.payload,pos);names.append(name)
   assert pos==len(c.payload)
  assert names and set(names)=={'body'}
  meshes={c.name.rstrip(b'\0').decode() for c in rc.walk(doc.roots) if c.tag==b'STMS'};assert set(names)<=meshes
  assert Path(r['payload'][stem+'.rgo']['file']).read_bytes()==(dest/'current.rgo').read_bytes()
  checks[str(age)]={'selector_targets_exist':True,'selector_condition_bytes_exact':True,'throw_hide_rgo_exact':True,'native_playback':False}
 report={'status':'current_official_provenance_and_selector_checks_passed','recipe_sha256':sha(recipe),'official_attrib_sha256':sha(attrib),'cached_attrib_donors':found,'projectile_donor_hashes':projectiles,'lifecycle_sources':sources,'archive_sha256':archive_hashes,'ages':checks,'runtime_acceptance':False,'python_required':CFG['blender_python']}
 write(dest/'proof.json',report);print(report['status'])
if __name__=='__main__':main(sys.argv[1])
