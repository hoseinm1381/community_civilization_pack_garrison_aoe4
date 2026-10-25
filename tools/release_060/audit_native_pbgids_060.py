"""Inventory every installed native PBGID for private identity collision checks."""
import hashlib
import json
from pathlib import Path
import re
import sys
import warnings

from common import OUT, guard, owned, read, sha, write
from audit_stock_identity_refs_060 import rgd
from audit_stock_identity_refs_direct_060 import RUNTIME


def main():
    guard();target=owned(OUT/'inventory/stock-pbgid-audit-r1/report.json')
    if target.exists():raise FileExistsError('Preserve prior native PBGID inventory')
    source=OUT/'inventory/stock-reference-closure-direct-r2/report.json';proof=read(source)
    hashes_path=source.parent/'all-member-hashes.json';hashes=read(hashes_path)
    archive=Path(proof['archive'])
    if sha(archive)!=proof['archive_sha256'] or sha(hashes_path)!=proof['all_member_hashes_sha256']:
        raise ValueError('Independent stock archive inventory changed')
    warnings.filterwarnings('ignore');sys.path[:0]=[str(RUNTIME/'site-packages'),str(RUNTIME/'SGA-V10/src')]
    from relic.sga.v10 import EssenceFSHandler
    from relic.sga.core.definitions import Version
    EssenceFSHandler.version=Version(10,0);identities={};missing=[]
    with archive.open('rb') as stream:
        fs=EssenceFSHandler.read(stream);paths=sorted(fs.walk.files())
        if {p.lstrip('/') for p in paths}!=set(hashes):raise ValueError('Stock record inventory differs')
        for number,path in enumerate(paths,1):
            member=path.lstrip('/');data=fs.readbytes(path)
            if hashlib.sha256(data).hexdigest()!=hashes[member]['sha256']:raise ValueError('Independent native hash differs')
            document=rgd.read(data)
            pbgids={int(node.value) for node_path,node in rgd.flatten(document.nodes)
                    if re.fullmatch(r'[^/]+/pbgid',node_path) and node.kind=='Int'}
            for identity in sorted(pbgids):identities.setdefault(str(identity),[]).append(member)
            if not pbgids:missing.append(member)
            if number%5000==0:print('PBGID_RECORDS',number,flush=True)
    if sha(archive)!=proof['archive_sha256']:raise ValueError('Stock archive changed during audit')
    write(target,{'schema':'ccp-060-all-installed-native-pbgids/v1',
        'status':'all_installed_rgds_decoded_and_top_level_pbgids_inventoried',
        'archive':str(archive),'archive_sha256':proof['archive_sha256'],
        'independent_member_hashes_sha256':sha(hashes_path),'member_count':len(paths),
        'unique_pbgids':len(identities),'identities':identities,
        'records_without_top_level_pbgid':missing,'native_acceptance':False})
    print(json.dumps({'report':str(target),'stock_pbgids':len(identities),'records_without_pbgid':len(missing)}))


if __name__=='__main__':main()
