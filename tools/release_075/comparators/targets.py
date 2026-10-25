"""Read-only current target attachment closure. Never substitutes missing costs with zero."""
from pathlib import Path
import json,sys,sqlite3,collections,subprocess
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/release_075'))
import native_io as io
sys.path.insert(0,io.CFG['garrison_extension'])
from garrison_shared import rgd
sys.path.insert(0,str(ROOT/'tools/castle_next'))
import selector_probe_castle as probe
probe._native.WORK=ROOT/'output/release_075/schema'
OUT=ROOT/'output/release_075/comparators'
BACK=Path(io.CFG['external_root'])/'staging/r74/v1/readback'
inventory=json.loads((ROOT/'output/release_075/inspection/current-consumers.json').read_text())
with sqlite3.connect('file:'+probe.INDEX.as_posix()+'?mode=ro',uri=True) as db:
 names={x[0].lower() for x in db.execute("select logical_path from resolved_assets where logical_path like 'attrib/%'")}
names|={p.relative_to(BACK).as_posix().lower() for p in (BACK/'attrib').rglob('*.rgd')}
names|={x['path'].lower() for x in json.loads(subprocess.run([io.CFG['archive_tool'],'list',str(Path(io.CFG['content_editor']).parent/'cardinal/archives/Attrib.sga')],capture_output=True,text=True,check=True).stdout)['members']}
def resource(member):
 p=BACK/member
 if not p.exists() and member.startswith('attrib/'):
  return io.extract(Path(io.CFG['content_editor']).parent/'cardinal/archives/Attrib.sga',member,OUT/'target-official'/member)
 return p if p.exists() else io.official(member)
def listmember(ref):
 ref='/'.join(part.split(':')[-1] for part in ref.split('/'))
 exact='attrib/'+ref.lower().removesuffix('.rgd')+'.rgd'
 if exact in names:return exact
 return probe.resolve_attachment(ref,'chinese',names)
report={'schema':'ccp075-target-closure/v1','families':{},'limits':['Every listed stamp instance retained; branch alternatives are not summed as exact simultaneous draws. Generic attachment references and unresolved nested resources remain explicit.']}
for family,info in inventory['families'].items():
 row=report['families'][family]={'actors':[]}
 for actor in info['consumers']:
  p=resource(actor['member']); doc=rgd.read(p.read_bytes()); ar={'member':actor['member'],'sha256':io.sha(p),'attachments':[]};row['actors'].append(ar)
  for field,node in rgd.flatten(doc.nodes):
   if node.key!='attachments' or not isinstance(node.value,list):continue
   vals={c.key:c.value for c in node.value};name=vals.get('$PBGNAME');mapping=vals.get('$PBGMAP','')
   if not name:continue
   entry={'field':field,'name':name,'mapping':mapping,'stamps':[]};ar['attachments'].append(entry)
   if 'attachment_lists' not in mapping:
    entry['non_stamp_reference']=True;continue
   try:
    member=listmember(mapping.replace('\\','/')+'/'+name);p=resource(member);entry.update(member=member,sha256=io.sha(p))
    ad=rgd.read(p.read_bytes())
    for sf,sn in rgd.flatten(ad.nodes):
     if sn.key!='stamp' or not isinstance(sn.value,str) or not sn.value:continue
     sm=sn.value.replace('\\','/').lower().removesuffix('.bin')+'.bin'
     sp=resource(sm);tree,visuals=io.visuals(sp)
     entry['stamps'].append({'field':sf,'member':sm,'sha256':io.sha(sp),'visuals':visuals,'typed_objects':dict(collections.Counter(o['type'] for o in tree.objects.values()))})
   except Exception as exc:entry['blocker']=str(exc)
(OUT/'target-closure.json').write_text(json.dumps(report,indent=2)+'\n')
for family,row in report['families'].items():
 entries=[e for a in row['actors'] for e in a['attachments']]
 print(family, 'lists',len(entries),'instances',sum(len(s['visuals']) for e in entries for s in e['stamps']),'blockers',[e['blocker'] for e in entries if 'blocker'in e])
