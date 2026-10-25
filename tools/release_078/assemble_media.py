"""Fresh geometry/materials under existing private keys and exact old selectors."""
from pathlib import Path
import argparse,ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,CFG['garrison_extension'])
sys.path.insert(0,str(ROOT/'tools/release_010'))
sys.path.insert(0,str(ROOT/'tools/release_040'))
from garrison_shared import building_project as bp,model_variants as mv,relic_chunky as rc
from integration_codec import copy_native_markers
import lifecycle
sys.path.insert(0,str(ROOT/'tools/release_076'))
from inventory import official
def sha(raw):return hashlib.sha256(raw).hexdigest()
# Reuse only pure, audited functions; historical module-level release reads must
# not execute against retired evidence or produce historical outputs.
helper=ROOT/'tools/release_061/assemble_castle_object_061.py'
tree=ast.parse(helper.read_text());wanted={'selector_table','rebase_model','rebase_material'}
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in wanted],type_ignores=[]),str(helper),'exec'),globals())
def main(family,label):
 current=json.loads((ROOT/'output/release_075/inspection/current-consumers.json').read_text())
 row=current['families'][family];base=ROOT/'output/release_076/delivery/final-v1/readback'
 cookdir=ROOT/'output/release_078/cooks'/f'{family}-{label}';cook=json.loads((cookdir/'receipt.json').read_text())
 assert cook['status']=='fresh_native_cook_and_readback_complete_runtime_unverified'
 frozen=json.loads((cookdir/'input-freeze.json').read_text());parts=frozen['building']['parts'];names={p['name'] for p in parts}
 cooked=Path(cook['model_readback'])
 assert all(sha((cooked/n).read_bytes())==h for n,h in cook['media'].items())
 out=ROOT/'output/release_078/payloads'/f'{family}-{label}'
 if out.exists():raise FileExistsError('Retain previous assembly attempt')
 rows=[];proofs=[]
 def put(member,raw):
  found=next((x for x in rows if x['member']==member),None)
  if found:assert found['sha256']==sha(raw);return
  p=out/'payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  rows.append({'member':member,'file':str(p),'sha256':sha(raw),'bytes':len(raw),'before_sha256':sha((base/member).read_bytes()) if (base/member).exists() else None})
 for stem in row['all_variant_models']:
  old=(base/(stem+'.rgm')).read_bytes()
  oldsets=selector_table(old);assert {n for _,ns,_ in oldsets for n in ns}<=names
  donors={'citadel':'art/civilizations/chinese/structures/wonder_greatwall_mp/wonder_greatwall_mp',
   'hq':'art/civilizations/chinese_ha_01/structures/landmark_2b/chi_ha_01_landmark_b_age02/chi_ha_01_landmark_b_age02',
   'ministry':'art/civilizations/chinese/structures/dynasty_pagoda/chi_dynasty_pagoda_control_age03/chi_dynasty_pagoda_control_age03'}
  for owner in json.loads((ROOT/'output/release_075/references/retained/3-owners.json').read_text())['owners']:donors[owner['family']]=owner['stock_model']
  for key,entry in json.loads((ROOT/'output/release_075/references/retained/feudal-donor-graph.json').read_text())['landmarks'].items():donors[key]=next(iter(entry['stamps'].values()))['visuals'][0]['model']
  donor=official(donors[family]+'.rgm')
  raw=bp.construction_model((cooked/'model.rgm').read_bytes(),donor.read_bytes(),parts,profile_id='english-house')
  olddoc=rc.parse(old);newdoc=rc.parse(raw)
  oldms=[c for c in rc.walk(olddoc.roots) if c.tag==b'MSBP'];newms=[c for c in rc.walk(newdoc.roots) if c.tag==b'MSBP']
  assert len(oldms)==len(newms)==1
  raw=rc.rebuild(newdoc,lambda c:oldms[0].payload if c.offset==newms[0].offset else None)
  raw,markers=copy_native_markers(raw,old);raw=rebase_model(raw,stem)
  assert selector_table(raw)==oldsets,'Native selector drift'
  assert next(c.payload for c in rc.walk(rc.parse(raw).roots) if c.tag==b'MSBP')==oldms[0].payload
  oldchildren=rc.parse(old).roots[0].children;newchildren=rc.parse(raw).roots[0].children
  assert [(x.tag,x.name,x.version) for x in oldchildren]==[(x.tag,x.name,x.version) for x in newchildren]
  assert all(a.payload==b.payload for a,b in zip(oldchildren,newchildren) if a.tag!=b'MSCL'),'Nongeometry native model chunk drift'
  put(stem+'.rgm',raw);put(stem+'.rrgeom',(cooked/'model.rrgeom').read_bytes())
  texdir='art/scenario/cc078/'+family
  mat,refs=rebase_material((cooked/'model.rrmaterial').read_bytes(),f"art/scenario/garrison/{cook['temporary_key']}/buildings/{family}",texdir)
  put(stem+'.rrmaterial',mat)
  for leaf,member in refs.items():put(member,(cooked/leaf).read_bytes())
  proofs.append({'stem':stem,'official_donor':donors[family],'official_donor_sha256':sha(donor.read_bytes()),'all_model_chunks_except_MSCL_exact':True,'selector_bytes_exact':True,'selectors':oldsets,'native_rgo_unchanged_sha256':sha((base/(stem+'.rgo')).read_bytes()),'markers':markers})
 report={'status':'isolated_payload_static_checks_passed_runtime_unverified','family':family,'pure_helpers_source_sha256':sha(helper.read_bytes()),'cook_receipt_sha256':sha((cookdir/'receipt.json').read_bytes()),'models':proofs,'members':rows,'unchanged':'RGO, actor, stamps, attachment lists, PBG IDs, gameplay and functional footprint'}
 (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'family':family,'payload_members':len(rows),'selector_bytes_exact':True}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('family');p.add_argument('--label',default='v1');a=p.parse_args();main(a.family,a.label)
