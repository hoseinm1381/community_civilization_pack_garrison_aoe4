"""Read current official sources and freeze active gameplay; never modifies them."""
import sqlite3
from common import *
INDEX=Path.home()/'AppData/Local/Garrison/Kit/game-assets.sqlite3'
CONFIG=INDEX.with_name('game-assets.local.json')
def official(member):
 with sqlite3.connect('file:'+INDEX.as_posix()+'?mode=ro',uri=True) as db:
  rows=db.execute('select archive_path from resolved_assets where lower(logical_path)=?',(member.lower(),)).fetchall()
 if not rows and member.startswith('attrib/'):
  rows=[(str(Path(CFG['content_editor']).parent/'cardinal/archives/Attrib.sga'),)]
 if len(rows)!=1:raise ValueError((member,rows))
 target=OUT/'official'/member
 if not target.exists():
  target.parent.mkdir(parents=True,exist_ok=True)
  run('extract-'+target.stem,[CFG['archive_tool'],'extract-member',rows[0][0],member,target])
 return target
def decode(name,member):
 dest=OUT/'donors'/name
 manifests=list(dest.glob('*/decoded-static.json'))
 if not manifests:
  run('decode-'+name,[CFG['garrison_core'],'convert','decode-static','--logical-path',member,'--config',CONFIG,'--index',INDEX,'--output-root',dest])
  manifests=list(dest.glob('*/decoded-static.json'))
 if len(manifests)!=1:raise ValueError(manifests)
 d=read(manifests[0])
 return {'logical_path':member,'manifest':str(manifests[0]),'sha256':sha(manifests[0]),'bones':len((d.get('skeleton') or {}).get('bones',[])), 'groups':[{k:g.get(k) for k in ('name','vertex_count','triangle_count','material','bounds')} for g in d.get('geometry',{}).get('groups',[])]}
if __name__=='__main__':
 guard()
 freeze=OUT/'source-freeze.json'
 if not freeze.exists():
  paths=list((ROOT/'assets').rglob('*.xml'))+list((ROOT/'assets').rglob('*.scar'))+[ROOT/'workspace.json',ROOT/'assets/_default.burnproj',ROOT/'community_civilization_pack.aoe4mod']
  write(freeze,{str(p):sha(p) for p in paths})
 for age in (2,3,4):
  m=f'attrib/attachments/attachment_lists/civilizations/malian/units/tier{age}_javelin_mal.rgd'
  p=official(m);xml=p.with_suffix('.xml')
  if not xml.exists():run('attachment-'+str(age),[CFG['archive_tool'],'decode-rgd',p,xml])
 donors={'buffalo':'art/civilizations/gaia/animals/cow/cow.rgm','javelin2':'art/civilizations/malian/weapons/mal_javelin_held/mal_javelin_held.rgm','projectile':'art/civilizations/malian/weapons/projectiles/mal_javelin_projectile/mal_javelin_projectile.rgm'}
 donors['skirmisher2']='art/civilizations/malian/humans/mal_ranged_crossbow_age02/mal_ranged_crossbow_age02.rgm'
 if len(sys.argv)>1:
  donors={sys.argv[1]:sys.argv[2]}
 result=read(OUT/'donors.json') if (OUT/'donors.json').exists() else {}
 for name,member in donors.items():
  result[name]=decode(name,member);write(OUT/'donors.json',result)
 print(json.dumps(result,indent=2))
