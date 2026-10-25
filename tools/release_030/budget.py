"""Decode and verify native stock landmark LOD0 static drawgraph budgets."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from common import OUT, CORE, guarded, write
INDEX=Path(r'C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.sqlite3')
CONFIG_FILE=Path(r'C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.local.json')
DECODE=OUT/'budget'/'decode'
REPORT=OUT/'budget'/'stock-budget.json'
EVIDENCE=OUT/'inventory'/'stock-completed-budget.json'
ASSETS=[('academy','Imperial Academy','art/civilizations/chinese/structures/wonder_imperial_academy/chi_wonder_imperial_academy_control_age02/chi_wonder_imperial_academy_control_age02.rgm'),('gate','Barbican gate / Zhengyangmen principal gate visual','art/civilizations/chinese/structures/wonder_zhengyangmen_gate/chi_wonder_zhengyangmen_gate_control_age03/chi_wonder_zhengyangmen_gate_control_age03.rgm'),('aachen','Aachen Cathedral','art/civilizations/hre/structures/wonder_aachen_cathedral/hre_wonder_aachen_cathedral_control_age01/hre_wonder_aachen_cathedral_control_age01.rgm')]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def decode(logical):
 # Use the already-produced Garrison core decode in the owned cache. Avoid a
 # concurrent overwrite when another worker is reading the same decode receipt.
 matches=[]
 for p in DECODE.glob('*/decoded-static.json'):
  d=json.loads(p.read_text(encoding='utf-8'))
  if d.get('request',{}).get('logical_path')==logical:matches.append(p)
 if not matches:raise FileNotFoundError(f'Run Garrison core decode-static first: {logical}')
 p=max(matches,key=lambda x:x.stat().st_mtime_ns);d=json.loads(p.read_text(encoding='utf-8'))
 if d.get('status')!='decoded' or d.get('blockers'):raise RuntimeError(f'Incomplete decode: {logical}')
 return p,d

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify-only',action='store_true');args=ap.parse_args();guarded()
 ev=json.loads(EVIDENCE.read_text(encoding='utf-8')); rows=[]
 for key,name,logical in ASSETS:
  p,d=decode(logical); proof=ev[key]
  if proof.get('status')!='qualified_static_drawgraph':raise RuntimeError(f'Unqualified selector evidence: {key}')
  if proof['decoded_manifest_sha256']!=sha(p) or proof['rrgeom_sha256']!=d['geometry']['source']['sha256']:
   raise RuntimeError(f'Decoded evidence no longer matches selector proof: {key}')
  if proof['rgm_sha256']!=sha(Path(proof['rgm'])):raise RuntimeError(f'Native RGM hash mismatch: {key}')
  rows.append({'id':key,'display_name':name,'logical_path':logical,'native_rgm_path':proof['rgm'],'native_rgm_sha256':proof['rgm_sha256'],'rrgeom_sha256':proof['rrgeom_sha256'],'decoded_manifest_path':str(p),'decoded_manifest_sha256':sha(p),'selector_names':proof['selector_names'],'healthy_selector_names':proof['healthy_selector_names'],'raw_lod0_triangles':proof['lod0_raw_triangles'],'completed_healthy_lod0_triangles':proof['completed_healthy_lod0_triangles'],'slots':proof['slots'],'selector_method':proof['method'],'native_runtime':'unverified'})
 counts=sorted(r['completed_healthy_lod0_triangles'] for r in rows)
 report={'schema':'community-civilization-pack/release-030-stock-budget/v3','status':'qualified_static_drawgraph_budget','method':{'tool':str(CORE),'tool_version':'Garrison 0.1.4 bundled core (CLI decode-static); official RGM/RGO selector probe and MSCL mapping','game_asset_index':str(INDEX),'index_sha256':sha(INDEX),'index_read_mode':'read-only SQLite lookup by core; official SGA members extracted read-only','config_path':str(CONFIG_FILE),'config_sha256':sha(CONFIG_FILE),'decode_output_root':str(DECODE),'geometry_metric':'completed healthy LOD0 triangles from exact native lifecycle selectors; mapped collection triangles are counted once by source object; duplicated geometry records remain separate draw instances','selector_evidence':str(EVIDENCE),'selector_evidence_sha256':sha(EVIDENCE)},'assets':rows,'budget':{'measured_triangle_counts':counts,'median_target_triangles':counts[1],'maximum_cap_triangles':max(counts),'meaning':'Per-landmark complete healthy static geometry target/cap from three native stock drawgraph exemplars; additive attachment props must be included when part of the exact owner graph.'},'limits':['Static source drawgraph evidence; runtime visibility, GPU submission and native match behavior remain unverified.','Zhengyangmen is the principal gate visual budget candidate; the Vietnam Barbican owner references separate outskirts attachment resources, which are excluded.','No Blender, Content Editor build, or native cook was run for this budget.']}
 if args.verify_only:
  old=json.loads(REPORT.read_text(encoding='utf-8'))
  for k in ('method','assets','budget'):
   if old.get(k)!=report[k]:raise RuntimeError(f'Budget verification mismatch: {k}')
  print(json.dumps({'status':'verified','counts':counts,'median_target':counts[1],'maximum_cap':max(counts),'runtime':'unverified'},indent=2))
 else:
  if REPORT.exists():
   old=json.loads(REPORT.read_text(encoding='utf-8'))
   if old.get('schema') not in ('community-civilization-pack/release-030-stock-budget/v1','community-civilization-pack/release-030-stock-budget/v2'):raise FileExistsError(REPORT)
  write(REPORT,report);print(json.dumps({'status':report['status'],'report':str(REPORT),'counts':counts,'median_target':counts[1],'maximum_cap':max(counts)},indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())
