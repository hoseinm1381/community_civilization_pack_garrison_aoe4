"""Check every frozen historical input and normal-edition file without edits."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check():
 out=ROOT/'output/release_075';protected=json.loads((out/'baseline/protected.json').read_text());normal=json.loads((out/'baseline/normal.json').read_text())
 failures=[]
 for owner,base,rows in [('garrison',ROOT,protected),('normal',Path(CFG['source_root']),normal)]:
  for name,digest in rows.items():
   p=base/name
   if not p.is_file() or sha(p)!=digest:failures.append({'owner':owner,'path':name})
 baseline=out/'baseline/community_civilization_pack.sga'
 if sha(baseline)!='becbd1caa38d64a7f0cbb2b428d382da59cc8015ce8bf98578c31f742f664384':failures.append({'owner':'baseline_sga'})
 report={'passed':not failures,'protected_files':len(protected),'normal_files':len(normal),'failures':failures}
 (out/'preservation-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 assert not failures,failures
 return report
if __name__=='__main__':print(json.dumps(check()))
