"""Record observed external normal-edition changes, without editing that root.

This is an exception report, not a refreshed baseline or a claim of frozen
normal preservation. 070 never consumes these normal-edition files.
"""
from pathlib import Path
import sys,json,datetime
sys.path.insert(0,str(Path(__file__).parent))
from freeze_070 import ROOT,OUT,CFG,inventory,sha,check_storage
check_storage(ROOT,CFG)
target=OUT/'external-normal-drift.json'
assert not target.exists(),'Preserve original drift observation'
freeze=OUT/'baseline/freeze.json';f=json.loads(freeze.read_text());root=Path(CFG['source_root']);a=inventory(root);b=f['normal']
changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
assert changed=={'assets/attrib/instances/ai/ai_economy/complete/default_economy.xml','.aoe4/Vietnam_v2/Layout.xml','archives/Vietnam_v2.sga'},changed
r={'schema':'ccp-070-external-normal-drift/v1','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freeze_sha256':sha(freeze),'normal_root':str(root),'normal_frozen_preservation_passed':False,'scope_statement':'No normal-edition writes performed by 070 tools; observed changes are retained and excluded from 070 integration. Actor package is assembled from immutable delivered061, not this normal root. Cause not attributed.','changed_paths':sorted(changed),'differences':{k:{'frozen':b.get(k),'observed':a.get(k),'observed_mtime_ns':(root/k).stat().st_mtime_ns} for k in sorted(changed)},'normal_observed_inventory':a,'frozen_unchanged_file_count':sum(a.get(k)==v for k,v in b.items()),'observed_file_count':len(a)}
target.write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='normal_observed_inventory'},indent=2))
