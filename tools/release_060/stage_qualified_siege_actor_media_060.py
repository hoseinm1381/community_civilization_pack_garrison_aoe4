"""Patch exact private siege actor alternate_sua slots proved by stock audit."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from common import OUT, ROOT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd

UPSTREAM = OUT/'integration/qualified-list-media-stage-r1/stage.json'
PROOF = OUT/'qualification/siege-exact-consumers-r1/report.json'
IDS = OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
B03 = OUT/'integration/material-components-b03/registry.json'
DEST = OUT/'integration/qualified-siege-actor-media-stage-r1'


def main():
    guard()
    if DEST.exists():
        raise FileExistsError('Preserve existing siege actor media stage')
    upstream, proof, ids, registry = read(UPSTREAM), read(PROOF), read(IDS), read(B03)
    if proof['status'] != 'all_four_saved_models_exactly_match_reachable_native_visual_slots':
        raise ValueError('Exact siege consumer proof is not qualified')
    private = {x['stock_member']:x for x in ids['entries']}
    payloads = {x['member']:x for x in upstream['payloads']}
    if len(payloads) != len(upstream['payloads']):
        raise ValueError('Upstream payload collision')
    actor_edits = defaultdict(list)
    selected = []
    list_checks = []
    for model in proof['models']:
        key = model['key']
        media = registry['models'].get(key)
        if not media or media['required_geometry_replacement']:
            raise ValueError('Siege media absent or unqualified '+key)
        receipt = Path(media['receipt'])
        if sha(receipt) != media['receipt_sha256']:
            raise ValueError('Siege composition receipt drift '+key)
        composition = read(receipt)
        logical = composition['model_logical_path'].removesuffix('.rgm').replace('/','\\')
        original = model['model'].removesuffix('.rgm').replace('/','\\')
        for match in model['matches']:
            if match['before_value'] != original:
                raise ValueError('Saved siege proof model mismatch '+key)
            stock_member = match['member']
            identity = private.get(stock_member)
            if not identity:
                raise ValueError('Siege stock actor/list lacks registered private identity '+stock_member)
            row = {'stock_member':stock_member,'private_member':identity['private_member'],
                   'path':match['leaf'],'before':match['before_value'],'after':logical,
                   'media_key':key}
            if stock_member.startswith('attrib/ebps/'):
                actor_edits[identity['private_member']].append(row)
            else:
                list_checks.append(row)
        selected.append((key,composition))
    # The exact native list slots were patched by the preceding list-media stage.
    for check in list_checks:
        row = payloads[check['private_member']]
        from common import CFG
        import sys
        sys.path.insert(0, CFG['garrison_extension'])
        from garrison_shared import rgd
        doc = rgd.read(Path(row['path']).read_bytes())
        if rgd.find(doc.nodes,check['path']).value != check['after']:
            raise ValueError('Trebuchet list visual proof not satisfied '+check['private_member'])
    changed=[]
    for member,edits in sorted(actor_edits.items()):
        previous=payloads[member]
        source=Path(previous['path'])
        if sha(source)!=previous['sha256']:
            raise ValueError('Private siege actor payload drift '+member)
        changes=[{'path':x['path'],'before':x['before'],'after':x['after']} for x in edits]
        approved={x['path'] for x in edits}
        updated,inverse=patch_visual_rgd(source.read_bytes(),changes,'actor_media',
                                         approved_paths=approved)
        target=owned(DEST/'payload'/member)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(updated)
        changed.append({'member':member,'path':str(target),'sha256':sha(target),
                        'bytes':target.stat().st_size,'before_sha256':None,
                        'kind':'qualified_private_siege_actor_media',
                        'upstream_sha256':sha(source),'edits':inverse})
    if len(changed)!=5 or sum(len(v) for v in actor_edits.values())!=10:
        raise ValueError('Expected five private siege actors and ten exact slots')
    for row in changed:
        payloads[row['member']]=row
    new_assets=set()
    for key,composition in selected:
        for asset in composition['payloads']:
            member=asset['member'];path=Path(asset['path'])
            if sha(path)!=asset['sha256']:
                raise ValueError('Siege media payload drift '+member)
            if member in payloads:
                if payloads[member]['sha256']!=asset['sha256']:
                    raise ValueError('Siege media collision '+member)
                continue
            new_assets.add(member)
            payloads[member]={**asset,'bytes':path.stat().st_size,
                              'before_sha256':None,'kind':'qualified_private_siege_media'}
    freeze=read(OUT/'baseline/final053/freeze.json')
    aggregate=[]
    for member,row in sorted(payloads.items()):
        path=Path(row['path'])
        if sha(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:
            raise ValueError('Aggregate siege payload drift '+member)
        before=freeze['archive_members'].get(member)
        aggregate.append({**row,'before_sha256':before['sha256'] if before else None})
    for row in upstream['source_rows']:
        if row['source_sha256'] is not None and sha(ROOT/row['relative'])!=row['source_sha256']:
            raise ValueError('Active source drift '+row['relative'])
        if sha(row['staged_path'])!=row['staged_sha256']:
            raise ValueError('Staged source drift '+row['relative'])
    write(DEST/'stage.json',{'schema':'ccp-060-qualified-siege-actor-media-stage/v1',
          'status':'all_four_saved_siege_models_bound_to_exact_private_native_slots',
          'upstream_stage_sha256':sha(UPSTREAM),'exact_consumer_proof_sha256':sha(PROOF),
          'material_registry_sha256':sha(B03),
          'baseline_sga_sha256':freeze['sga_sha256'],
          'private_actor_count':len(changed),'actor_leaf_count':sum(len(v) for v in actor_edits.values()),
          'already_patched_list_leaf_count':len(list_checks),
          'added_media_asset_count':len(new_assets),
          'payloads':aggregate,'source_rows':upstream['source_rows'],
          'full_baseline_to_aggregate_changed_member_allowlist':sorted(payloads),
          'active_source_or_final_archive_changed':False,
          'rebuild_policy':'Replay this pinned original-native compiled overlay and qualified media after Content Editor build.'})
    print(json.dumps({'stage':str(DEST/'stage.json'),'payloads':len(aggregate),
                      'private_actors':len(changed),'actor_leaves':sum(len(v) for v in actor_edits.values()),
                      'list_leaves_checked':len(list_checks),'new_assets':len(new_assets)},indent=2))


if __name__=='__main__':main()
