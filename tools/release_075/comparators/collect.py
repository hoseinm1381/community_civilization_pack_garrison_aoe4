"""Current official comparator closure and conservative geometry evidence.

Writes only release_075/comparators. Optional decoding uses the shared native
lock nonblockingly: a running cook yields a pending report, never a concurrent
decode. Bounds are not promoted to simultaneous-visibility proof.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import msvcrt
import sqlite3
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
CFG = json.loads((ROOT / 'workspace.json').read_text())
OUT = ROOT / 'output/release_075/comparators'
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import check_storage
sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd
sys.path.insert(0, str(ROOT / 'tools/castle_next'))
import selector_probe_castle as probe
probe.OUT = OUT
probe._native.WORK = ROOT / 'output/release_075/schema'
BASE = Path(CFG['content_editor']).parent / 'cardinal/archives'
LOCK = Path(CFG['external_root']) / 'output/release_020/native-build.lock'

# Exact game actor leaves, not inferred from visual model age suffixes.
CHOICES = {
 'academy': ('building_landmark_age1_academy_control_chi.rgd', 'chinese', ['pho_minh','one_pillar','ministry'], 'Feudal educational/economic landmark; Ministry comparison is thematic only'),
 'gate': ('building_landmark_age1_gatehouse_control_chi.rgd', 'chinese', ['pho_minh','one_pillar'], 'Feudal defensive landmark'),
 'aachen': ('building_landmark_age1_palantine_chapel_hre.rgd', 'hre', ['pho_minh','one_pillar'], 'Feudal religious/economic landmark'),
 'palace': ('building_landmark_age2_palace_control_chi.rgd', 'chinese', ['garden','hq'], 'Castle official Palace; Garden visual donor only, not same-age proof'),
 'white_tower': ('building_landmark_age2_white_tower_eng.rgd', 'english', ['citadel','hq'], 'Castle defensive landmark comparator'),
 'clocktower': ('building_landmark_age2_clocktower_control_chi.rgd', 'chinese', ['citadel','hq','foundry'], 'Castle military production; Foundry thematic comparison only'),
 'great_wall': ('building_landmark_age3_great_wall_control_chi.rgd', 'chinese', ['citadel'], 'Imperial visual-owner reference, not Castle budget comparator'),
 'forbidden_palace': ('building_wonder_age4_forbidden_control_chi.rgd', 'chinese', ['foundry'], 'Wonder visual-owner reference; not a same-function landmark budget comparator'),
}


def sha(data):
 return hashlib.sha256(data).hexdigest()


def write(path, data):
 path = OUT / path
 if not path.resolve().is_relative_to(OUT.resolve()): raise ValueError('Output escape')
 path.parent.mkdir(parents=True, exist_ok=True)
 if isinstance(data, (dict,list)): data=(json.dumps(data,indent=2)+'\n').encode()
 path.write_bytes(data)
 return path


def extract(archive, member):
 path=OUT/'official'/archive/member
 if not path.exists():
  path.parent.mkdir(parents=True,exist_ok=True)
  p=subprocess.run([CFG['archive_tool'],'extract-member',str(BASE/archive),member,str(path)],capture_output=True,text=True)
  if p.returncode: raise RuntimeError(p.stderr or p.stdout)
 return path


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--decode-max',type=int,default=0);args=ap.parse_args()
 check_storage(ROOT,CFG)
 prior_path=OUT/'closure.json'
 prior=json.loads(prior_path.read_text()) if prior_path.exists() else {}
 listing=subprocess.run([CFG['archive_tool'],'list',str(BASE/'Attrib.sga')],capture_output=True,text=True,check=True)
 names={x['path'].lower() for x in json.loads(listing.stdout)['members']}
 report={'schema':'ccp075-comparator-closure/v1','status':'incomplete_no_complete_compound_caps','choices':[],
         'models':{},'budgets':None,'native_tested':False,'decode_attempts':0,
         'limits':['No actor-tier visibility evaluator is assumed. Attachment occurrences and stamp instances are retained individually.',
                   'Healthy model bounds do not establish simultaneous visibility across alternative attachments.',
                   'A material/texture/alpha budget is separate from triangle counts.',
                   'Historical 50-percent-overstock allowance is not used.']}
 for key,(leaf,race,families,role) in CHOICES.items():
  row={'id':key,'families':families,'role':role,'attachments':[],'blockers':[]}
  report['choices'].append(row)
  candidates=[n for n in names if n.endswith('/'+leaf) and n.startswith('attrib/ebps/')]
  if len(candidates)!=1:
   row['blockers'].append({'actor_resolution':candidates});continue
  actor_path=extract('Attrib.sga',candidates[0]);raw=actor_path.read_bytes();doc=rgd.read(raw)
  row.update(actor=candidates[0],actor_sha256=sha(raw))
  row['age_requirement_evidence']=[{'path':p,'value':n.value} for p,n in rgd.flatten(doc.nodes)
                                 if p.startswith('default/') and isinstance(n.value,str) and 'landmark' in n.value and n.key not in ('$REF','$PBGNAME')]
  refs=[]
  for path,node in rgd.flatten(doc.nodes):
   if not path.startswith('default/') or node.key!='attachments' or not isinstance(node.value,list):continue
   vals={x.key:x.value for x in node.value};name=vals.get('$PBGNAME');mapping=vals.get('$PBGMAP','')
   if name and 'attachment_lists' in mapping:refs.append((path,mapping.replace('\\','/')+'/'+name))
  if not refs:row['blockers'].append('No default tier attachments resolved')
  for field,ref in refs:
   entry={'actor_field':field,'reference':ref,'stamps':[]};row['attachments'].append(entry)
   try:
    member=probe.resolve_attachment(ref,race,names);path=extract('Attrib.sga',member);data=path.read_bytes();attachment=rgd.read(data)
    entry.update(member=member,sha256=sha(data))
    # Do not set-union stamp occurrences: repeated draws are separate instances.
    for stamp_field,node in rgd.flatten(attachment.nodes):
     if not stamp_field.startswith('default/') or node.key!='stamp' or not node.value:continue
     member=node.value.replace('\\','/').lower().removesuffix('.bin')+'.bin'
     path=extract('Data.sga',member);tree=probe.NativeTree(path)
     root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
     array=tree.field(root,root['fields']['m_blueprints']);instances=[]
     for index in range(array['count']):
      slot=array['data_address']+8*index;obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
      if obj['type']!='VisualStampBlueprint':continue
      model=tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/').lower().removesuffix('.rgm')+'.rgm'
      transform=list(struct.unpack('<10f',bytes.fromhex(tree.field(obj,obj['fields']['m_transform'])['raw'])))
      instances.append({'object_id':str(obj['id']),'model':model,'transform':transform})
      report['models'].setdefault(model,{'status':'pending_decode','occurrences':0})['occurrences']+=1
     entry['stamps'].append({'field':stamp_field,'member':member,'sha256':sha(path.read_bytes()),'visual_instances':instances})
   except Exception as exc:entry['blocker']=str(exc);row['blockers'].append(str(exc))
  row['simultaneous_visibility']='unqualified_actor_attachment_selection_and_per_model_predicates'
 write('closure.json',report)
 db=sqlite3.connect('file:'+probe.INDEX.as_posix()+'?mode=ro',uri=True)
 try:
  for model,entry in report['models'].items():
   provider=db.execute('select archive_path from resolved_assets where lower(logical_path)=?',(model,)).fetchone()
   geometry=db.execute('select archive_path from resolved_assets where lower(logical_path)=?',(model.removesuffix('.rgm')+'.rrgeom',)).fetchone()
   if not provider or not geometry:
    entry['status']='unresolved_or_non_geometry_reference';continue
   native=extract(Path(provider[0]).name,model);entry['rgm_sha256']=sha(native.read_bytes());entry['native_rgm']=str(native)
   previous=prior.get('models',{}).get(model,{})
   if previous.get('status')=='bounded_model_geometry' and previous.get('rgm_sha256')==entry['rgm_sha256']:
    manifest=Path(previous['decode_manifest'])
    if manifest.is_file() and sha(manifest.read_bytes())==previous['decode_manifest_sha256']:
     occurrences=entry['occurrences'];entry.update(previous);entry['occurrences']=occurrences
     continue
   if report['decode_attempts']>=args.decode_max:continue
   with LOCK.open('r+b') as lock:
    try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
     report['decode_deferred']='shared native lock busy';break
    try:
     report['decode_attempts']+=1
     manifest,decoded,rgm_path=probe.decoded_model(model,OUT/'official/decoded-rgm')
     metric=probe.selectors(rgm_path,decoded)
     entry.update(status='bounded_model_geometry',metric=metric,decode_manifest=str(manifest),
                  decode_manifest_sha256=sha(manifest.read_bytes()),rrgeom_sha256=decoded['geometry']['source']['sha256'])
    except Exception as exc:entry.update(status='decode_or_selector_blocked',error=str(exc))
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
   write('closure.json',report)
 finally:db.close()
 summaries=[]
 for row in report['choices']:
  occurrences=[i for a in row['attachments'] for s in a['stamps'] for i in s['visual_instances']]
  pending=[i['model'] for i in occurrences if report['models'][i['model']]['status']!='bounded_model_geometry']
  row['model_instances']=len(occurrences);row['unmeasured_models']=sorted(set(pending))
  measured=[report['models'][i['model']]['metric'] for i in occurrences if report['models'][i['model']]['status']=='bounded_model_geometry']
  summaries.append(dict(id=row['id'],role=row['role'],instances=len(occurrences),measured_instances=len(measured),
                        sum_of_measured_model_lower=sum(m['lower'] for m in measured),
                        sum_of_measured_model_upper=sum(m['upper'] for m in measured),
                        unresolved=sorted(set(pending)),blockers=row['blockers']))
  if not pending and not row['blockers']:
   row['all_listed_instances_upper_bound']=sum(report['models'][i['model']]['metric']['upper'] for i in occurrences)
   row['exact_simultaneously_visible_triangles']=None
 write('closure.json',report)
 write('summary.json',{'schema':'ccp075-comparator-partial-sums/v1','status':'not_complete_compound_budgets',
                       'meaning':'Sums preserve duplicate stamp instances but exclude unresolved resource types and do not resolve alternative actor attachments. These are not accepted caps or complete simultaneous visibility counts.',
                       'rows':summaries})
 print(json.dumps({'choices':len(report['choices']),'unique_models':len(report['models']),
                   'instances':sum(r.get('model_instances',0) for r in report['choices']),
                   'decode_attempts':report['decode_attempts'],'decode_deferred':report.get('decode_deferred'),
                   'complete_compound_caps':None}))


if __name__=='__main__':main()
