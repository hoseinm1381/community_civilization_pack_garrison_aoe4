"""Overlay only separately qualified Castle visuals onto corrected unit mounts."""
import argparse
from common import *


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repair',type=Path,required=True)
    args=ap.parse_args();guard();frozen=baseline();repair=read(owned(args.repair))
    rows=repair['payloads']
    if not rows:raise ValueError('Castle repair must be qualified before final assembly')
    members=set()
    for row in rows:
        member=row['member']
        if member in members:raise ValueError('Duplicate Castle member')
        members.add(member)
        if row['before_sha256']!=frozen['archive_members'].get(member,{}).get('sha256'):raise ValueError('Different repair basis')
        if sha(owned(row['path']))!=row['sha256']:raise ValueError('Castle source payload changed')
        if row['sha256']==row['before_sha256']:raise ValueError('Unchanged payload should not be overlaid')
    mount=read(OUT/'qualification/mount-fix-r1/receipt.json')
    current=owned(mount['candidate'])
    if sha(current)!=mount['candidate_sha256']:raise ValueError('Mount candidate changed')
    if mount['changed_members'] or len(mount['mount_changes'])!=80:raise ValueError('Unqualified mount candidate')
    folder=owned(OUT/'final-r1')
    if folder.exists():raise FileExistsError('Preserve previous final assembly')
    folder.mkdir(parents=True);mapping=folder/'members.txt'
    mapping.write_text(''.join(r['member']+'='+r['path']+'\n' for r in rows),encoding='utf-8')
    candidate=folder/'community_civilization_pack.sga'
    result=command('set-members',current,mapping,candidate,'--alias','data',timeout=240)
    write(folder/'assembly.json',{'schema':'ccp-061-final-assembly/v1','candidate':str(candidate),
        'candidate_sha256':sha(candidate),'repair':str(args.repair),'repair_sha256':sha(args.repair),
        'mount_candidate_sha256':sha(current),'archive_result':result,
        'native_appearance_verified':False})
    print(candidate);print(sha(candidate))


if __name__=='__main__':main()
