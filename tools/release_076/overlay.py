"""Read-only overlay conflict gate; deliberately has no assembly/package operation."""
from pathlib import Path,PurePosixPath
from common import *
def validate_overlay(root,payloads,current,expected):
 for path,digest in expected.items():
  if current.get(path)!=digest:raise ValueError('baseline drift: '+path)
 result={}
 for payload in payloads:
  for row in payload['files']:
   dest=row['destination'];p=PurePosixPath(dest)
   if p.is_absolute() or '..' in p.parts or '\\' in dest or ':' in dest:raise ValueError('unsafe destination path')
   if not dest.startswith('art/'):raise ValueError('outside media allowlist')
   if dest in result:raise ValueError('destination collision: '+dest)
   if dest in current and dest not in expected:raise ValueError('unexpected overwrite: '+dest)
   source=(Path(root)/row['source']).resolve()
   if not source.is_relative_to(Path(root).resolve()):raise ValueError('unsafe source path')
   if sha(source)!=row['sha256']:raise ValueError('payload hash mismatch: '+str(source))
   result[dest]=row
 return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',required=True);p.add_argument('--baseline-sha256',required=True);p.add_argument('--manifest',required=True);a=p.parse_args()
 guard();archive=Path(a.baseline)
 if sha(archive)!=a.baseline_sha256:raise ValueError('baseline archive hash mismatch')
 m=read(a.manifest)
 listing=json.loads(run('baseline-list',[CFG['archive_tool'],'list',archive,'--verify']))
 if listing['archive']['name']!=CFG['project_guid'].replace('-',''):raise ValueError('baseline runtime namespace mismatch')
 # Existence catches all unexpected overwrites; expected compiled bytes must be independently hashed.
 current={r['path']:None for r in listing['members']}
 import tempfile
 with tempfile.TemporaryDirectory(prefix='verify-',dir=OUT) as tmp:
  for member in m.get('expected_baseline_members',{}):
   target=Path(tmp)/Path(member).name
   run('baseline-member-'+target.stem,[CFG['archive_tool'],'extract-member',archive,member,target]);current[member]=sha(target)
  rows=validate_overlay(Path(a.manifest).parent,m['payloads'],current,m.get('expected_baseline_members',{}))
 print(json.dumps({'status':'media_conflict_check_passed','baseline_sha256':a.baseline_sha256,'media_files':len(rows),'bindings_status':m.get('bindings_status'),'assembled':False},indent=2))
