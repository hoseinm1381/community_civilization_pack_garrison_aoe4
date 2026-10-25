"""Current Garrison inheritance preflight; official evidence refresh is mandatory."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
import extension_audit as audit
audit.ROOT=ROOT;audit.GUID='b7fcea91257b408fb9e8ae4d8bc402e1'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--official-cache',type=Path,default=ROOT/'output/release_072/official-extensions.json');p.add_argument('--output',type=Path,default=ROOT/'output/release_072/inheritance.json');a=p.parse_args()
    official=audit.refresh(a.official_cache)if a.refresh else json.loads(a.official_cache.read_text())['records']
    local=audit.load_local(a.root);errors=audit.Resolver(local,official).audit();result={'local_blueprints':len(local),'official_blueprints':len(official),'errors':errors};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));sys.exit(bool(errors))
