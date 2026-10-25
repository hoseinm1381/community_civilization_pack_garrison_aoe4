"""Search every installed stock RGD in memory using the existing cached V10 reader."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import warnings

from common import OUT, STAGING, guard, owned, read, sha, write
from audit_stock_identity_refs_060 import NAMES, rgd

RUNTIME=Path(r'C:\Users\RS\.codex\cache\aoe4-sga-extractor-session-20260717\_skill_sga_live_runtime')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime',type=Path,default=RUNTIME,help='Existing or restored reader bundle runtime')
    runtime=ap.parse_args().runtime
    guard();folder=owned(OUT/'inventory/stock-reference-closure-direct-r2');target=folder/'report.json'
    if target.exists():raise FileExistsError('Preserve prior direct reference audit')
    listing_path=OUT/'inventory/stock-reference-closure-r1/listing.json';listing=read(listing_path)
    expected={r['path']:r for r in listing['members']}
    archive=Path(listing['archive']['path']);digest=sha(archive)
    warnings.filterwarnings('ignore');sys.path[:0]=[str(runtime/'site-packages'),str(runtime/'SGA-V10/src')]
    from relic.sga.v10 import EssenceFSHandler
    from relic.sga.core.definitions import Version
    EssenceFSHandler.version=Version(10,0)
    patterns={name:re.compile(r'(?<![a-z0-9_])'+name+r'(?![a-z0-9_])',re.I) for name in NAMES}
    inventory={};matches=[];crosschecked=0
    with archive.open('rb') as stream:
        contents=EssenceFSHandler.read(stream);paths=sorted(contents.walk.files())
        if {p.lstrip('/') for p in paths}!=set(expected):raise ValueError('Independent native/reader inventories differ')
        for number,path in enumerate(paths,1):
            member=path.lstrip('/');data=contents.readbytes(path)
            if len(data)!=expected[member]['size']:raise ValueError('Native decoded size differs: '+member)
            partial=STAGING/'a/refs'/member
            if partial.exists():
                if partial.read_bytes()!=data:raise ValueError('Independent native extraction differs: '+member)
                crosschecked+=1
            digest_data=hashlib.sha256(data).hexdigest();inventory[member]={'sha256':digest_data,'bytes':len(data)}
            candidates=[name for name in NAMES if name.encode() in data.lower()]
            if candidates:
                document=rgd.read(data);hits=[]
                for node_path,node in rgd.flatten(document.nodes):
                    if not isinstance(node.value,str):continue
                    names=[name for name in candidates if patterns[name].search(node.value)]
                    if names:hits.append({'path':node_path,'value':node.value,'kind':node.kind,'identities':names})
                if hits:
                    output=owned(folder/'matches'/member);output.parent.mkdir(parents=True,exist_ok=True)
                    if output.exists():raise FileExistsError('Preserve incomplete matched-member extraction')
                    output.write_bytes(data)
                    matches.append({'member':member,'path':str(output),'sha256':digest_data,'hits':hits})
            if number%5000==0:print('SEARCHED',number,flush=True)
    if sha(archive)!=digest:raise ValueError('Installed archive changed during reference audit')
    write(folder/'all-member-hashes.json',inventory)
    runtime_sources=[runtime/'SGA-V10/src/relic/sga/v10/serialization.py',
                     runtime/'site-packages/relic/sga/core/filesystem.py',
                     runtime/'site-packages/relic/sga/core/serialization.py']
    write(target,{'schema':'ccp-060-full-stock-identity-reference-audit/v1',
        'status':'all_installed_stock_rgds_searched_exact_identity_tokens',
        'archive':str(archive),'archive_sha256':digest,'listing_sha256':sha(listing_path),
        'all_member_hashes_sha256':sha(folder/'all-member-hashes.json'),'native_rgd_count':len(paths),
        'target_names':NAMES,'matches':matches,'matching_members':len(matches),
        'independent_native_extracted_members_byte_identical':crosschecked,
        'cached_reader_sources':[{'path':str(p),'sha256':sha(p)} for p in runtime_sources],
        'qualification_limit':'CString identity references; runtime logic and external numeric filters are not inferred',
        'native_acceptance':False})
    print(json.dumps({'report':str(target),'all_rgds':len(paths),'matching_members':len(matches),'crosschecked':crosschecked}))


if __name__=='__main__':main()
