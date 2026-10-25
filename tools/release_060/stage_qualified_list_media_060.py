"""Graft qualified model media only onto private, reached native lists."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from common import CFG, OUT, ROOT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd

sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd

UPSTREAM = OUT/'integration/worker-elephant-owner-stage-r2/stage.json'
LAND_IDS = OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
EQUIP_IDS = OUT/'integration/private-equipment-identities/native-batch-v1/registered-identities.json'
HUMANOID = OUT/'integration/humanoid-media-b01-r2.json'
MONK3 = OUT/'integration/humanoid-monk3-media-b03-r1.json'
CIVILIAN = OUT/'integration/civilian-media-primary-r2.json'
MOUNTED = OUT/'integration/material-components-b01/registry.json'
B03 = OUT/'integration/material-components-b03/registry.json'
DEST = OUT/'integration/qualified-list-media-stage-r1'


def donor_model(manifest):
    data = read(Path(manifest))
    return data['request']['logical_path'].removesuffix('.rgm').replace('/','\\')


def pair_payloads(row):
    result=[]
    for key in ('private_supported_variant_rgm','private_supported_variant_rgo',
                'private_albedo_only_rrmaterial','private_albedo_rrtex',
                'native_qualified_authored_rrgeom'):
        value=dict(row[key])
        if key=='native_qualified_authored_rrgeom':
            value['member']=row['replacement_rrgeom_logical_path']
        result.append(value)
    return result


def media_catalogue():
    entries={}
    for manifest in (HUMANOID,MONK3,CIVILIAN):
        for key,row in read(manifest).items():
            if key in entries:
                raise ValueError('Media key collision '+key)
            entries[key]={'key':key,'model':donor_model(row['stock_manifest']),
                          'replacement':row['model_logical_path'].removesuffix('.rgm').replace('/','\\'),
                          'payloads':pair_payloads(row),
                          'receipt':str(manifest),'receipt_sha256':sha(manifest)}
    for key,row in read(MOUNTED).items():
        if key=='tug_worker':
            continue  # Actor2 owner and media are already staged separately.
        receipt=Path(row['receipt'])
        composition=read(receipt)
        entries[key]={'key':key,'model':donor_model(row['donor_manifest']),
                      'replacement':composition['model_logical_path'].removesuffix('.rgm').replace('/','\\'),
                      'payloads':composition['payloads'],
                      'receipt':str(receipt),'receipt_sha256':sha(receipt)}
    for key,row in read(B03)['models'].items():
        if key=='monk3':
            continue  # Qualified authored geometry pair supersedes stock RRGeom.
        receipt=Path(row['receipt'])
        composition=read(receipt)
        spec=read(Path(composition['spec']))
        if row['required_geometry_replacement']:
            raise ValueError('Missing authored geometry qualification '+key)
        entries[key]={'key':key,'model':donor_model(spec['stock_manifest']),
                      'replacement':composition['model_logical_path'].removesuffix('.rgm').replace('/','\\'),
                      'payloads':composition['payloads'],
                      'receipt':str(receipt),'receipt_sha256':sha(receipt)}
    return entries


def choice(stock_member, role, matches):
    keys={x['key'] for x in matches}
    if len(matches)==1:
        return matches[0]
    name=Path(stock_member).stem
    if name=='tier3_manatarms_mon':
        wanted='maa3_female' if 'maa3_female' in keys else 'maa3'
    elif name=='tier4_manatarms_mon':
        wanted='maa4_female' if 'maa4_female' in keys else 'maa4'
    elif role=='repeater4_body_list':
        wanted='repeater4'
    else:
        raise ValueError('Ambiguous media donor for '+stock_member+' '+str(keys))
    chosen=[x for x in matches if x['key']==wanted]
    if len(chosen)!=1:
        raise ValueError('Context media missing '+stock_member+' '+wanted)
    return chosen[0]


def main():
    guard()
    if DEST.exists():
        raise FileExistsError('Preserve qualified list media stage')
    upstream=read(UPSTREAM)
    catalogue=media_catalogue()
    by_model=defaultdict(list)
    for row in catalogue.values():
        by_model[row['model']].append(row)
    identities=read(LAND_IDS)['entries']+read(EQUIP_IDS)['entries']
    private={x['private_member']:x for x in identities if x['stock_member'].startswith('attrib/attachments/')}
    payloads={x['member']:x for x in upstream['payloads']}
    changed=[]
    used=set()
    for member,identity in sorted(private.items()):
        prior=payloads.get(member)
        if not prior or sha(prior['path'])!=prior['sha256']:
            raise ValueError('Private native list missing or drifted '+member)
        raw=Path(prior['path']).read_bytes()
        doc=rgd.read(raw)
        edits=[]
        approved=set()
        for path,node in rgd.flatten(doc.nodes):
            if node.kind!='CString' or node.value not in by_model:
                continue
            selected=choice(identity['stock_member'],identity.get('role'),by_model[node.value])
            edits.append({'path':path,'before':node.value,'after':selected['replacement']})
            approved.add(path)
            used.add(selected['key'])
        if not edits:
            continue
        updated,proof=patch_visual_rgd(raw,edits,'body_media',approved_paths=approved)
        path=owned(DEST/'payload'/member)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(updated)
        changed.append({'member':member,'path':str(path),'sha256':sha(path),
                        'bytes':path.stat().st_size,'before_sha256':None,
                        'kind':'qualified_private_list_media',
                        'stock_member':identity['stock_member'],
                        'upstream_sha256':sha(prior['path']),'edits':proof})
    if not changed:
        raise ValueError('No qualified private list media selected')
    for row in changed:
        payloads[row['member']]=row
    asset_members=set()
    for key in sorted(used):
        entry=catalogue[key]
        for asset in entry['payloads']:
            member=asset['member']
            path=Path(asset['path'])
            if sha(path)!=asset['sha256']:
                raise ValueError('Qualified media payload drift '+member)
            if member in asset_members:
                continue
            if member in payloads and payloads[member]['sha256']!=asset['sha256']:
                raise ValueError('Media member collision '+member)
            asset_members.add(member)
            payloads[member]={**asset,'bytes':path.stat().st_size,
                              'before_sha256':None,'kind':'qualified_private_media'}
    freeze=read(OUT/'baseline/final053/freeze.json')
    aggregate=[]
    for member,row in sorted(payloads.items()):
        path=Path(row['path'])
        if sha(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:
            raise ValueError('Aggregate media payload drift '+member)
        before=freeze['archive_members'].get(member)
        aggregate.append({**row,'before_sha256':before['sha256'] if before else None})
    sources=upstream['source_rows']
    for row in sources:
        if row['source_sha256'] is not None and sha(ROOT/row['relative'])!=row['source_sha256']:
            raise ValueError('Active source drift '+row['relative'])
        if sha(row['staged_path'])!=row['staged_sha256']:
            raise ValueError('Staged source drift '+row['relative'])
    write(DEST/'stage.json',{'schema':'ccp-060-qualified-private-list-media-stage/v1',
          'status':'qualified_private_list_models_staged_actor_siege_media_pending',
          'upstream_stage_sha256':sha(UPSTREAM),
          'media_registry_sha256':{str(x):sha(x) for x in (HUMANOID,MONK3,CIVILIAN,MOUNTED,B03)},
          'baseline_sga_sha256':freeze['sga_sha256'],
          'qualified_media_keys':sorted(used),
          'private_list_count':len(changed),
          'media_asset_count':len(asset_members),
          'payloads':aggregate,'source_rows':sources,
          'full_baseline_to_aggregate_changed_member_allowlist':sorted(payloads),
          'active_source_or_final_archive_changed':False,
          'rebuild_policy':'After Content Editor build, replay this original-native compiled overlay and qualified media; source-only build cannot reconstruct visual bytes.'})
    print(json.dumps({'stage':str(DEST/'stage.json'),'private_lists':len(changed),
                      'media_keys':len(used),'media_assets':len(asset_members),
                      'payloads':len(aggregate)},indent=2))


if __name__=='__main__':
    main()
