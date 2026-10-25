"""Current official reads and typed stamp inspection, confined to 075 evidence."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,struct
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text(encoding='utf-8'))
OUT=ROOT/'output/release_075'
sys.path.insert(0,str(ROOT/'tools/release_010'))
import integration_native
integration_native.WORK=OUT/'schema'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def extract(archive,member,destination):
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
 if destination.exists():return destination
 result=subprocess.run([CFG['archive_tool'],'extract-member',str(archive),member,str(destination)],capture_output=True,text=True,encoding='utf-8',errors='replace')
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 return destination
def schema():
 return extract(Path(CFG['content_editor']).parent/'engine/archives/reflect.sga','reflect.db',OUT/'schema/reflect.db')
def official(member):
 with sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True) as db:
  row=db.execute('select archive_path from resolved_assets where lower(logical_path)=?',(member.lower(),)).fetchone()
 archive=Path(row[0]) if row else Path(CFG['content_editor']).parent/'cardinal/archives/Data.sga'
 return extract(archive,member,OUT/'official'/member)
def visuals(path):
 schema();tree=integration_native.NativeTree(path)
 root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
 arr=tree.field(root,root['fields']['m_blueprints']);rows=[]
 for i in range(arr['count']):
  slot=arr['data_address']+8*i
  obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
  if obj['type']=='VisualStampBlueprint':
   rows.append(dict(id=str(obj['id']),model=tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/'),transform=list(struct.unpack('<10f',bytes.fromhex(tree.field(obj,obj['fields']['m_transform'])['raw'])))))
 return tree,rows
if __name__=='__main__':
 current=json.loads((OUT/'inspection/current-consumers.json').read_text())
 back=Path(CFG['external_root'])/'staging/r74/v1/readback';result={}
 for family,row in current['families'].items():
  result[family]=[]
  for member in row['private_stamps']:
   tree,v=visuals(back/member);result[family].append(dict(member=member,sha256=sha(back/member),visuals=v,object_count=len(tree.objects)))
 donor=official('art/stamps/civ_chinese/chi_town_center_age_03.bin')
 tree,v=visuals(donor);flags=[x for x in v if '/flags/' in x['model']]
 result['flag_donor']={'member':'art/stamps/civ_chinese/chi_town_center_age_03.bin','sha256':sha(donor),'visuals':flags}
 (OUT/'inspection/stamps.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:([{'stamp':s['member'],'visuals':len(s['visuals'])} for s in a] if isinstance(a,list) else a) for k,a in result.items()},indent=2))
