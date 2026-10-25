"""Fresh official inheritance audit using an installed Garrison archive CLI."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
import extension_audit as audit
sys.path.insert(0,str(ROOT/'tools/collaboration'))
from store import file_sha, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--official-archive',type=Path,required=True)
    p.add_argument('--archive-tool',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    audit.GUID = 'b7fcea91257b408fb9e8ae4d8bc402e1'
    official = {}
    # TemporaryDirectory owns cleanup; no project paths or links are removed.
    with tempfile.TemporaryDirectory(prefix='ccp-official-') as temp:
        folder = Path(temp)
        for category in ('ebps','sbps'):
            proc = subprocess.run([str(args.archive_tool),'extract',str(args.official_archive),str(folder),
                                   '--filter','instances/'+category+'/'],capture_output=True,text=True)
            if proc.returncode:
                raise RuntimeError('Official archive extraction failed: '+proc.stderr[-2000:])
            for file in (folder/'instances'/category).rglob('*.xml'):
                key = file.relative_to(folder/'instances').with_suffix('').as_posix().replace('/','\\')
                official[key] = audit.summarize(file.read_bytes())
    if not official:
        raise ValueError('No official EBPS/SBPS evidence; audit refused')
    local = audit.load_local(args.root)
    if not local:
        raise ValueError('No local EBPS/SBPS source')
    errors = audit.Resolver(local,official).audit()
    write_json(args.output,dict(official_archive_sha256=file_sha(args.official_archive),
        official_blueprints=len(official),local_blueprints=len(local),errors=errors,
        refreshed=True,native_compile=False))
    print(json.dumps(dict(official_blueprints=len(official),local_blueprints=len(local),errors=errors)))
    sys.exit(bool(errors))


if __name__ == '__main__':
    main()
