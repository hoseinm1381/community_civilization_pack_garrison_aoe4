"""Extract exact official RGD sources and enumerate private graph reference leaves."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from common import ARCH, CFG, OUT, guard, owned, read, sha, write

PLAN=OUT/'integration/private-land-identities/derive-plan-v5.json'
DEST=OUT/'integration/private-land-graph/native-reference-plan-v1'
OFFICIAL=Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga')


def main():
    guard()
    if DEST.exists():
        raise FileExistsError('Preserve exact native graph evidence')
    sys.path.insert(0,CFG['garrison_extension'])
    from garrison_shared import rgd
    plan=read(PLAN)
    sources=sorted({x['stock_member'] for x in plan['entries']})
    listing=json.loads(subprocess.check_output([str(ARCH),'list',str(OFFICIAL)],text=True))
    available={x['path'] for x in listing['members']}
    if set(sources)-available:
        raise ValueError('Exact official source member missing')
    rows=[]
    for index,member in enumerate(sources):
        target=owned(DEST/'stock'/(f'{index:02d}.rgd'))
        target.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(ARCH),'extract-member',str(OFFICIAL),member,str(target)],
                       check=True,capture_output=True,text=True)
        raw=target.read_bytes()
        document=rgd.read(raw)
        if rgd.write(document)!=raw:
            raise ValueError('Native codec roundtrip differs '+member)
        links=[]
        for path,node in rgd.flatten(document.nodes):
            if node.kind!='CString':
                continue
            if node.key=='$PBGNAME':
                parent=path.rsplit('/',1)[0]
                try:
                    name_map=rgd.find(document.nodes,parent+'/$PBGMAP').value
                except (KeyError,ValueError):
                    continue
                if node.value:
                    links.append({'path':path,'name_map':name_map,
                                  'before_value':node.value})
            elif node.key=='alternate_sua':
                links.append({'path':path,'name_map':None,
                              'before_value':node.value})
        rows.append({'member':member,'path':str(target),'sha256':sha(target),
                     'bytes':target.stat().st_size,'links':links})
    write(DEST/'plan.json',{'schema':'ccp-060-private-native-reference-plan/v1',
          'status':'exact_official_native_edges_no_private_mutation',
          'derive_plan_sha256':sha(PLAN),'official_archive':str(OFFICIAL),
          'official_archive_sha256':sha(OFFICIAL),'resources':rows,
          'active_source_or_archive_changed':False})
    print(json.dumps({'receipt':str(DEST/'plan.json'),'resources':len(rows),
                      'reference_leaves':sum(len(x['links']) for x in rows)}))


if __name__=='__main__':main()
