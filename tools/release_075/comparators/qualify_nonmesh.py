"""Qualify zero *model-mesh* costs using native chunk absence; not zero decal workload."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/release_075/comparators'
sys.path.insert(0,str(ROOT/'tools/release_075'));import native_io as io
sys.path.insert(0,io.CFG['garrison_extension']);from garrison_shared import relic_chunky as rc
p=OUT/'target-models.json';data=json.loads(p.read_text())
for model,e in data.items():
 if e['status']!='blocked':continue
 native=io.official(model);chunks=list(rc.walk(rc.load(native).roots));tags={c.tag for c in chunks}
 if not tags.intersection({b'SKMS',b'MSCL',b'LGEO',b'\x00GEO'}):
  msd=[c.payload for c in chunks if c.tag==b'MSD '];mrd=[c.payload for c in chunks if c.tag==b'MRD ']
  if msd==[b'\0'*4] and mrd==[b'\0'*4]:
   e.update(status='proven_no_model_mesh',metric={'lower':0,'upper':0,'raw':0},native_rgm=str(native),rgm_sha256=io.sha(native),evidence={'tags':[str(c.tag)for c in chunks],'empty_mesh_selector_and_render_definition':True,'no_geometry_or_collection_chunks':True},limit='Zero native model mesh only; splats/strips/effects are separate rendering workload, not assumed free.')
 else:
  key=hashlib.sha256(model.encode()).hexdigest()[:16];manifests=list((OUT/'inventory/model-decode'/key).rglob('decoded-static.json'))
  if len(manifests)==1:
   manifest=manifests[0];d=json.loads(manifest.read_text());groups=d.get('geometry',{}).get('groups',[])
   if groups:
    raw=sum(len(g['triangles']) for g in groups)
    e.update(status='conservative_raw_geometry',metric={'lower':0,'upper':raw,'raw':raw},decode_manifest=str(manifest),decode_manifest_sha256=io.sha(manifest),limit='Selector mapping unresolved; include every decoded triangle, including all states, in upper bound.')
p.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:v['status'] for k,v in data.items() if v['status']!='bounded_model_geometry'},indent=2))
