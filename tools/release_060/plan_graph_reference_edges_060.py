"""Resolve exact native leaves between private stock actor/squad/list copies."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from common import OUT, guard, owned, read, sha, write

DERIVE=OUT/'integration/private-land-identities/derive-plan-v5.json'
NATIVE=OUT/'integration/private-land-graph/native-reference-plan-v1/plan.json'
TARGET=OUT/'integration/private-land-graph/private-reference-edges-v1.json'


def category(member):
    return member.split('/')[1]


def main():
    guard()
    plan,native=read(DERIVE),read(NATIVE)
    by_source={}
    by_target=defaultdict(list)
    for row in plan['entries']:
        by_source.setdefault(row['stock_member'],[]).append(row)
        by_target[(category(row['stock_member']),Path(row['stock_member']).stem)].append(row)
    if len(native['resources'])!=len({x['stock_member'] for x in plan['entries']}):
        raise ValueError('Exact native reference extraction incomplete')
    edges=[];states=[]
    for record in native['resources']:
        for owner in by_source[record['member']]:
            for leaf in record['links']:
                path=leaf['path'];name=leaf['before_value'];mapping=leaf['name_map']
                if leaf['name_map'] is None and path.endswith('/alternate_sua'):
                    states.append({'owner_private_member':owner['private_member'],
                                   'owner_stock_member':record['member'],**leaf})
                    continue
                if '/parent_pbg/' in path or mapping not in ('attachments\\attachment_lists','ebps','sbps'):
                    continue
                target_category='attachments' if mapping.startswith('attachments') else mapping
                candidates=by_target.get((target_category,name),[])
                if not candidates:
                    continue
                if len(candidates)>1:
                    # Repeater IV shares the Crossbow IV stock list but has
                    # independent authored art and a separate private identity.
                    desired='repeater4' if Path(record['member']).stem=='unit_repeater_crossbowman_4_chi' else None
                    candidates=[x for x in candidates if x['context']==desired]
                if len(candidates)!=1:
                    raise ValueError('Ambiguous private target '+record['member']+' '+path+' '+name)
                target=candidates[0]
                edges.append({'owner_private_member':owner['private_member'],
                              'owner_stock_member':record['member'],
                              'owner_stock_sha256':record['sha256'],
                              'path':path,'name_map':mapping,
                              'before_value':name,
                              'after_value':target['private_reference'].split('/')[-1],
                              'after_guid_required':True,
                              'target_private_member':target['private_member'],
                              'target_stock_member':target['stock_member']})
    if len({(x['owner_private_member'],x['path']) for x in edges})!=len(edges):
        raise ValueError('Duplicate native graph leaf')
    data={'schema':'ccp-060-private-native-reference-edges/v1',
          'status':'exact_native_before_leaves_private_identity_after_planned',
          'derive_plan_sha256':sha(DERIVE),'native_extraction_sha256':sha(NATIVE),
          'edges':edges,'alternate_sua_visual_states':states,
          'parent_metadata_policy':'Never change parent_pbg leaves; final private copies use original native resource bytes.',
          'active_source_or_final_archive_changed':False}
    if TARGET.exists():
        if read(TARGET)!=data:raise ValueError('Preserve existing graph edge plan')
    else:write(owned(TARGET),data)
    print({'edges':len(edges),'alternate_sua_states':len(states),'receipt':str(TARGET)})


if __name__=='__main__':main()
