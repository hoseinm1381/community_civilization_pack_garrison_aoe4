"""Recover/read back a fresh identity cook without allocating or cooking again.

The first cook wrapper rejected the expected generated attrib/v60ids.rgd
manifest. Its failed receipt is retained. This checks the actual successful
native cook and excludes all diagnostic project scaffolding from final payloads.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path
from common import ARCH, CFG, guard, owned, read, sha, write
from unit_binding_plan import EVIDENCE, PROJECT, PLAN, prepare_plan


def main():
    guard();plan=prepare_plan()
    sys.path.insert(0,CFG['garrison_extension'])
    from garrison_shared import rgd
    receipt=EVIDENCE/'registered-identities.json'
    if receipt.exists():raise FileExistsError('Private IDs are immutable once registered')
    config=read(PROJECT/'mod-project.json')
    if len(config['cooks'])!=1:raise ValueError('One fresh native identity cook required')
    cook=config['cooks'][0];archive=owned(cook['archive'])
    if sha(archive)!=cook['sha256']:raise ValueError('Native archive changed')
    listing=json.loads(subprocess.check_output([str(ARCH),'list','--verify',str(archive)],text=True))
    if not listing['archive']['verification']['verified']:raise ValueError('Archive verification failed')
    expected={f'attrib/attachments/attachment_lists/garrison/v60ids/{r["derived_name"]}.rgd'
              for r in plan['entries']}
    actual={m['path'] for m in listing['members'] if m['path'].startswith('attrib/')}
    if actual!=expected|{'attrib/v60ids.rgd'}:raise ValueError('Private identity set differs')
    back=owned(EVIDENCE/'readback-v4');back.mkdir(exist_ok=True)
    rows=[]
    for row in plan['entries']:
        member=f'attrib/attachments/attachment_lists/garrison/v60ids/{row["derived_name"]}.rgd'
        target=owned(back/(row['slug']+'.rgd'))
        if target.exists():raise FileExistsError(target)
        subprocess.run([str(ARCH),'extract-member',str(archive),member,str(target)],
                       capture_output=True,text=True,check=True)
        native=rgd.read(target.read_bytes())
        pbgid=rgd.find(native.nodes,'default/pbgid').value
        source=Path(row['stock_slots'][0]['raw_archive_member_path'])
        original=rgd.read(source.read_bytes())
        restored=copy.deepcopy(native)
        identity_metadata=[]
        for path,node in rgd.flatten(restored.nodes):
            if node.key=='pbgid':
                if node.value!=pbgid:raise ValueError('Private PBG ID differs between variants')
                node.value=rgd.find(original.nodes,path).value
            elif path.endswith(('/parent_pbg/$PBGNAME','/parent_pbg/$PBGMAP')):
                stock_value=rgd.find(original.nodes,path).value
                if node.value!=stock_value:
                    if node.value!='':raise ValueError('Unexpected derived parent identity metadata')
                    identity_metadata.append({'path':path,'generated':node.value,'stock':stock_value})
                    node.value=stock_value
        equal=rgd.write(restored)==rgd.write(original)
        if not equal:raise ValueError('Private native body list changed beyond identity metadata: '+row['slug'])
        rows.append({'slug':row['slug'],'pbgid':pbgid,'generated_member':member,
                     'path':str(target),'sha256':sha(target),
                     'final_private_reference':row['private_reference'],
                     'stock_member':row['stock_member'],'stock_sha256':sha(source),
                     'derived_parent_identity_metadata':identity_metadata,
                     'all_other_native_list_bytes_exact_after_identity_reversal':equal,
                     'final_payload_policy':'Copy original native list and change private pbgid/model slots only; do not integrate generated parent metadata.'})
    if len({x['pbgid'] for x in rows})!=10:raise ValueError('Private identity collision')
    write(receipt,{'schema':'ccp-060-registered-private-foot-identities/v1',
                   'status':'native_identities_registered_no_art_or_source_activation',
                   'plan_sha256':sha(PLAN),'archive':str(archive),'archive_sha256':sha(archive),
                   'entries':rows,
                   'excluded_scaffolding':[m['path'] for m in listing['members'] if m['path'] not in expected],
                   'native_game_acceptance':False})
    print(json.dumps({'status':'registered','identities':len(rows),'receipt':str(receipt)},indent=2))


if __name__=='__main__':
    main()
