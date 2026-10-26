"""Current inheritance audit; refresh from the installed official archive."""
import argparse,json,sys
from pathlib import Path
import extension_audit_current as audit
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--official-cache',type=Path,default=ROOT/'output/current/official-extensions.json');p.add_argument('--output',type=Path,default=ROOT/'output/current/inheritance.json');a=p.parse_args()
 official=audit.refresh(a.official_cache) if a.refresh else json.loads(a.official_cache.read_text(encoding='utf-8'))['records']
 local=audit.load_local(a.root);errors=audit.Resolver(local,official).audit();result={'local_blueprints':len(local),'official_blueprints':len(official),'errors':errors};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));sys.exit(bool(errors))
