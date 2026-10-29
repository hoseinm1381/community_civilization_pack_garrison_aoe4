"""Extend the accepted Flooded Citadel admission catalog with Korean movers.

Keep every existing entry. Add only private Korean entities whose full current
official/private parent chains contain moving_ext in every supported variant.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import check_extension_inheritance as audit

ROOT=Path(__file__).resolve().parents[1]
GUID='b7fcea91257b408fb9e8ae4d8bc402e1'


def generate(cache):
    evidence=json.loads(cache.read_text())
    local=audit.load_local(ROOT)
    resolver=audit.Resolver(local,evidence['records'])
    assert not resolver.audit()
    admitted=[];excluded=[]
    for key,record in sorted(local.items()):
        if not key.startswith('ebps\\korea\\'):continue
        variants=set(record)|{'default','campaign'}
        valid=all(any(n.get('value')=='ebpextensions\\moving_ext'
                      for n in resolver.effective(key,v,True)) for v in variants)
        (admitted if valid else excluded).append(key.rsplit('\\',1)[-1])
    path=ROOT/'assets/scar/vietnam/flooded_citadel.scar'
    code=path.read_text(encoding='utf-8-sig')
    pattern=r'(for name in string.gmatch\(\[\[\n)(.*?)(\n\]\], "%S\+"\) do knownMoving\[name\] = true end)'
    match=re.search(pattern,code,re.S)
    assert match,'Accepted generated mobility block not found'
    prior=set(match.group(2).split())
    added={n for name in admitted for n in (name,GUID+':'+name)}-prior
    final=prior|added
    assert not any(name in final or GUID+':'+name in final for name in excluded)
    code=code[:match.start(2)]+'\n'.join(sorted(final))+code[match.end(2):]
    path.write_text(code,encoding='utf-8',newline='\n')
    return dict(official_archive_sha256=evidence['archive_sha256'],
        admitted_korean_entities=admitted,excluded_korean_entities=excluded,
        preserved_existing_names=len(prior),added_names=sorted(added),
        final_names=len(final),all_parent_variants_checked=True,
        script_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--official-cache',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=generate(a.official_cache)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('KOREA_MOBILITY_ADMISSION',len(result['admitted_korean_entities']),
          'movers;',len(result['excluded_korean_entities']),'excluded')
