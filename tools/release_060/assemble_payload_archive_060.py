"""Overlay one fully reviewed private-visual payload stage onto exact final 053.

This creates an isolated candidate only. Qualification, source application and
ZIP delivery remain separate gates. It never rebuilds from generated scaffolds.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from common import ARCH, OUT, guard, owned, read, sha, write
from pin_final053 import PIN, SGA_SHA, verify as verify_baseline
from verify_archive_delta import safe_member


def validate_payload_rows(rows,baseline,protected):
    if not rows:raise ValueError('Empty final visual payload')
    seen=set();entries=[]
    for row in rows:
        member=safe_member(row['member'])
        if member.casefold() in seen:raise ValueError('Duplicate final payload member')
        seen.add(member.casefold())
        if member in protected:raise ValueError('Protected final053 resource cannot be overlaid')
        if 'before_sha256' not in row or row['before_sha256']!=baseline.get(member,{}).get('sha256'):
            raise ValueError('Final payload must declare exact baseline before hash or null')
        if member in baseline:
            if not member.startswith(('attrib/ebps/vietnam/','attrib/sbps/vietnam/')):
                raise ValueError('Existing member is outside Vietnamese actor/squad visual closure')
        elif not ((member.startswith('attrib/') and '/vietnam/release_060/' in member and member.endswith('.rgd'))
                  or member.startswith('art/scenario/garrison/v60')):
            raise ValueError('New payload is outside private Vietnamese 060 resource namespace')
        path=Path(row['path']);digest=sha(path)
        if row['sha256']!=digest or row['bytes']!=path.stat().st_size:
            raise ValueError('Pinned final payload bytes changed')
        if digest==row['before_sha256']:raise ValueError('Unchanged payload must not be declared as a delta')
        entries.append({'member':member,'before_sha256':row['before_sha256'],'after_sha256':digest})
    return sorted(entries,key=lambda r:r['member'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',type=Path,required=True)
    ap.add_argument('--label',required=True);args=ap.parse_args();guard()
    if not re.fullmatch('[a-z0-9-]{1,30}',args.label):raise ValueError('Safe unique candidate label required')
    baseline=verify_baseline();stage=read(owned(args.stage))
    if stage['baseline_sga_sha256']!=SGA_SHA:raise ValueError('Payload stage belongs to a different archive basis')
    rows=stage['payloads']
    for row in rows:owned(row['path'])
    entries=validate_payload_rows(rows,baseline['archive_members'],
                                 {r['member'] for r in baseline['preserved053_resources']})
    folder=owned(OUT/'assembly'/args.label)
    if folder.exists():raise FileExistsError('Preserve prior candidate assembly')
    folder.mkdir(parents=True);mapping=folder/'members.txt'
    mapping.write_text(''.join(r['member']+'='+str(Path(r['path']).resolve())+'\n' for r in rows),encoding='utf-8')
    allowlist=folder/'allowlist.json'
    write(allowlist,{'schema':'ccp-060-resource-allowlist/v1','entries':entries})
    candidate=folder/'community_civilization_pack.sga'
    command=[str(ARCH),'set-members',str(PIN/'community_civilization_pack.sga'),str(mapping),str(candidate),'--alias','data']
    result=subprocess.run(command,capture_output=True,text=True,timeout=240)
    (folder/'assemble.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Assembly failed; diagnostics preserved')
    # Rehash the exact same stage inputs after native archive writing.
    validate_payload_rows(rows,baseline['archive_members'],{r['member'] for r in baseline['preserved053_resources']})
    if sha(PIN/'community_civilization_pack.sga')!=SGA_SHA:raise ValueError('Frozen final053 archive changed')
    write(folder/'assembly.json',{'schema':'ccp-060-isolated-archive-assembly/v1',
        'status':'candidate_written_requires_independent_full_archive_readback',
        'baseline_sga_sha256':SGA_SHA,'stage':str(args.stage),'stage_sha256':sha(args.stage),
        'candidate':str(candidate),'candidate_sha256':sha(candidate),'payload_count':len(rows),
        'allowlist':str(allowlist),'allowlist_sha256':sha(allowlist),'active_source_changed':False,
        'native_acceptance':False})
    print(json.dumps({'candidate':str(candidate),'allowlist':str(allowlist),'payloads':len(rows)}))


if __name__=='__main__':main()
