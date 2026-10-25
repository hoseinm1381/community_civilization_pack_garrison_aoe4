"""Connect the distinct Repeater IV body to its reached private actor contexts."""
from __future__ import annotations

import json
from pathlib import Path

from common import CFG, OUT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd

UPSTREAM=OUT/'integration/final-binding-source-complete-r2/stage.json'
IDS=OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
DEST=OUT/'integration/repeater-context-stage-r1'
GUID=CFG['project_guid'].replace('-','')


def main():
    guard()
    if (DEST/'stage.json').exists():
        raise FileExistsError('Preserve existing Repeater context stage')
    stage,ids=read(UPSTREAM),read(IDS)
    lookup={x['stock_source']:x for x in ids['entries']}
    actor=lookup['ebps/races/chinese/units/unit_repeater_crossbowman_4_chi']
    body=lookup['attachments/attachment_lists/civilizations/chinese/units/tier4_crossbowman_chi']
    member=actor['private_member']
    rows={x['member']:x for x in stage['payloads']}
    old=rows[member]
    source=Path(old['path'])
    if sha(source)!=old['sha256']:
        raise ValueError('Upstream Repeater actor bytes drift')
    before='tier4_repeater_crossbowman_chi'
    after=GUID+':'+body['derived_name']
    changes=[{'path':branch+'/tier_ext/tier_group_list/tier_group/tier/attachments/$PBGNAME',
              'before':before,'after':after} for branch in ('default','cordoba','campaign')]
    final,proof=patch_visual_rgd(source.read_bytes(),changes,'actor')
    target=owned(DEST/'payload'/member)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(final)
    if sha(target)==old['sha256']:
        raise ValueError('Repeater context patch produced no change')
    rows[member]={**old,'path':str(target),'sha256':sha(target),'bytes':len(final)}
    payloads=[rows[x['member']] for x in stage['payloads']]
    write(DEST/'stage.json',{'schema':'ccp-060-repeater-context-stage/v1',
          'status':'private_repeater_actor_selects_distinct_registered_body_all_native_tier_contexts',
          'upstream_stage_sha256':sha(UPSTREAM),'baseline_sga_sha256':stage['baseline_sga_sha256'],
          'actor_private_member':member,'body_private_member':body['private_member'],
          'expected_value_checked_inverse_byte_edits':proof,
          'payloads':payloads,'source_rows':stage['source_rows'],
          'full_baseline_to_aggregate_changed_member_allowlist':stage['full_baseline_to_aggregate_changed_member_allowlist'],
          'active_source_or_final_archive_changed':False,
          'rebuild_policy':'The distinct Repeater IV tier references are exact native overlays after CE source compilation.'})
    print(json.dumps({'stage':str(DEST/'stage.json'),'member':member,'body':body['private_member'],
                      'patched_native_contexts':len(proof),'payloads':len(payloads)},indent=2))


if __name__=='__main__':
    main()
