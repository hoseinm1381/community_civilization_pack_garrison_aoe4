"""Measure target native props under shared native lock; preserve unresolved costs."""
from pathlib import Path
import json,sys,hashlib,msvcrt,sqlite3
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/release_075/comparators'
sys.path.insert(0,str(ROOT/'tools/release_075'));import native_io as io
sys.path.insert(0,str(ROOT/'tools/castle_next'));import selector_probe_castle as probe
probe.OUT=OUT;probe._native.WORK=ROOT/'output/release_075/schema'
data=json.loads((OUT/'target-closure.json').read_text());existing=json.loads((OUT/'closure.json').read_text())['models']
path=OUT/'target-models.json';report=json.loads(path.read_text()) if path.exists() else {}
models={v['model']+'.rgm' for f in data['families'].values() for a in f['actors'] for e in a['attachments'] for s in e['stamps'] for v in s['visuals']}
lockpath=Path(io.CFG['external_root'])/'output/release_020/native-build.lock'
for model in sorted(models):
 if model.startswith('art/scenario/'):continue
 if report.get(model,{}).get('status')=='bounded_model_geometry':continue
 if existing.get(model,{}).get('status')=='bounded_model_geometry':report[model]=existing[model];continue
 with lockpath.open('r+b') as lock:
  try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  except OSError:print('Native lock busy; resume later',flush=True);break
  try:
   manifest,decoded,rgm=probe.decoded_model(model,OUT/'target-decoded-rgm')
   report[model]={'status':'bounded_model_geometry','metric':probe.selectors(rgm,decoded),'decode_manifest':str(manifest),'decode_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'native_rgm':str(rgm)}
   print(model,report[model]['metric']['upper'],flush=True)
  except Exception as exc:
   report[model]={'status':'blocked','error':str(exc)};print('BLOCKED',model,str(exc)[:150],flush=True)
  finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
 path.write_text(json.dumps(report,indent=2)+'\n')
path.write_text(json.dumps(report,indent=2)+'\n')
