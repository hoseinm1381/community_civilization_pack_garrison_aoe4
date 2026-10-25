"""Prepare isolated evidence jobs without modifying authoring inputs."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/release_071'))
from resources import ResourceStore
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
cfg=json.loads((ROOT/'workspace.json').read_text());check_storage(ROOT,cfg)
out=ROOT/'output/building_style_audit_077';out.mkdir(exist_ok=True)
store=ResourceStore(Path(cfg['external_root'])/'resources_071')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):
 p=Path(p).resolve()
 try:return 'E/'+p.relative_to(ROOT).as_posix()
 except ValueError:return 'F/'+p.relative_to(Path(cfg['external_root'])).as_posix()
def get(p):
 p=Path(p)
 return p.read_bytes() if p.exists() else store.read(key(p))
def doc(p):return json.loads(get(p))
jobs=[]
def add(family,variant,source,**kw):
 p=ROOT/source if not Path(source).is_absolute() else Path(source)
 assert p.exists(),p
 jobs.append(dict(id=family+'-'+str(variant),family=family,variant=str(variant),source=str(p),source_sha256=sha(p),**kw))

tables=['F/output/release_020/barracks_tc/model-validation.json','F/output/release_040/buildings/model-validation.json','F/output/castle_next/buildings/model-validation.json']
for table in tables:
 for row in store.read_json(table)['models']:
  family,age=row['family'],row['age'];d=doc(row['donor_manifest'])
  dest=out/'inputs'/f'{family}{age}';dest.mkdir(parents=True,exist_ok=True)
  model=d.get('structure_collection_contract',{}).get('source',{}).get('path')
  if model:
   raw=get(model);rp=dest/'model.rgm';rp.write_bytes(raw)
   d['structure_collection_contract']['source']['path']=str(rp)
  manifest=dest/'donor.json';manifest.write_text(json.dumps(d),encoding='utf-8')
  details=[]
  if table==tables[1]:
   details=[str(ROOT/f'art/authoring/buildings_040/{family}/details_age{age:02}/vn_{family}_details_age{age:02}.blend')]
  elif table==tables[2]:
   details=[str(ROOT/f'art/authoring/castle_next/buildings/{family}/age{age:02}/details/vn_{family}_details_age{age:02}.blend')]
  add(family,age,row['editable_blend'],donor_manifest=str(manifest),extras=details,donor=row['donor_blend'],notes='Donor-derived source; native healthy selectors used. Monastery final 051 geometry differs from this older source; score confidence reduced unless final proof supplements it.')

for age in range(1,5):
 add('house',age,f'art/authoring/houses_010/Vietnam_Kinh_House_Age{age:02}.blend',notes='Source assembly; lifecycle selector scope recorded in render metrics.')
for state in ('default','stone'):
 p=next(k for k in store.index if k.startswith('F/stock-cache/release_020/hideout/'+state+'/') and k.endswith('decoded-static.json'))
 d=store.read_json(p);dest=out/'inputs'/('hideout-'+state);dest.mkdir(parents=True,exist_ok=True)
 model=d.get('structure_collection_contract',{}).get('source',{}).get('path')
 if model:
  rp=dest/'model.rgm';rp.write_bytes(get(model));d['structure_collection_contract']['source']['path']=str(rp)
 manifest=dest/'donor.json';manifest.write_text(json.dumps(d),encoding='utf-8')
 add('hideout',state,f'art/authoring/buildings_020/hideout/{state}/Vietnam_Hideout_{state}.blend',donor_manifest=str(manifest),extras=[str(ROOT/f'art/authoring/buildings_020/hideout/shelter_{state}/shelter_{state}.blend')],notes='Private remodeled outpost plus custom shelter; final passability/upgrade behaviour requires native view.')
add('rice_paddy','shared','art/authoring/buildings_020/farm/farm.blend',notes='Custom edge only; stock central rice layer is not in this source preview.')
for form in ('stake_fan','stake_thicket'):
 add(form,'shared',f'art/authoring/traps_030/{form}/{form}.blend',notes='030 camouflage model, shared by passable children.')
selection=json.loads((ROOT/'output/release_075/final-selection.json').read_text())
for f,r in selection['sources'].items():
 if f=='ministry':continue
 add(f,'selected',r['blend'],notes='Exact selected 075 source. Flags and retained stock outskirts are separate runtime components.')
add('ministry','077','art/authoring/release_077/ministry/r1/ministry.blend',notes='077 current source with three decorative custom buffalo; native owner flags are separate.')
for f,c in [('wonder','CCP070_Kinh_Thien_Detailed_r4'),('university','CCP070_University_Detailed_Overlay_r6')]:
 add(f,'IV','art/authoring/buildings_070/architecture-final-r4.blend',collection=c,notes='070 selected collection. University native stock main building is retained; preview material is not native shader parity.')
# Include a matched native donor for each source-derived family at one late age.
for f in ('barracks','town_center','archery_range','stable','blacksmith','market','keep','monastery','siege_workshop'):
 j=next(j for j in reversed(jobs) if j['family']==f)
 add('stock_'+f,j['variant'],j['donor'],donor_manifest=j['donor_manifest'],notes='Official stock donor, geometry and preview-material reference only.')
(out/'jobs.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print('Prepared',len(jobs),'jobs; sources unchanged')
