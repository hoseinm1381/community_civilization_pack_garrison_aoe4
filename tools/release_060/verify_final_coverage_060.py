"""Read-only final media, private graph, candidate, and roster scope audit."""
from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

from common import CFG, OUT, guard, owned, read, sha, write

sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd

HANDOFF = OUT/'integration/final-binding-handoff-v3.json'
MEDIA = OUT/'integration/qualified-media-selection-r1.json'
ASSEMBLY = OUT/'assembly/candidate-r2/assembly.json'
ALLOWLIST = OUT/'assembly/candidate-r2/allowlist.json'
AUDIT = OUT/'qualification/final-archive-r2/receipt.json'
GRAPH = OUT/'integration/private-land-graph/plan-v3.json'
TARGET = OUT/'qualification/final-coverage-r1.json'


def norm_model(value):
    return value.replace('/', '\\').removesuffix('.rgm').casefold()


def main():
    guard()
    if TARGET.exists():
        raise FileExistsError('Preserve final coverage proof')
    h,media,assembly,allow,audit,graph = map(read,(HANDOFF,MEDIA,ASSEMBLY,ALLOWLIST,AUDIT,GRAPH))
    if h['baseline_sga_sha256'] != assembly['baseline_sga_sha256']:
        raise ValueError('Candidate and handoff use different baseline')
    if assembly['candidate_sha256'] != audit['candidate_sha256'] or sha(Path(assembly['candidate'])) != audit['candidate_sha256']:
        raise ValueError('Candidate archive hash differs from archive audit')
    if sha(ALLOWLIST) != assembly['allowlist_sha256'] or sha(HANDOFF) != assembly['stage_sha256']:
        raise ValueError('Candidate input receipt differs from v3 handoff')
    payloads = {x['member']:x for x in h['payloads']}
    expected_delta = {m:(x['before_sha256'],x['sha256']) for m,x in payloads.items()}
    actual_delta = {x['member']:(x['before_sha256'],x['after_sha256']) for x in allow['entries']}
    if expected_delta != actual_delta:
        raise ValueError('Candidate allowlist differs from final v2 payload delta')
    if set(audit['changed']) | set(audit['added']) != set(payloads) or audit['removed']:
        raise ValueError('Candidate archive audit changed-member set differs')
    if len(audit['members']) != 1196:
        raise ValueError('Candidate archive member count differs')
    for member,row in payloads.items():
        if audit['members'][member] != {'sha256':row['sha256'],'bytes':row['bytes']}:
            raise ValueError('Candidate member differs '+member)
    expected_art = {x['member']:x['sha256'] for model in media['models'].values() for x in model['payloads']}
    actual_art = {m:x['sha256'] for m,x in payloads.items() if m.startswith('art/')}
    if len(media['models']) != 57 or len(expected_art) != 305 or expected_art != actual_art:
        raise ValueError('Qualified art coverage differs from final aggregate')

    private_members = {m for m in payloads if m.startswith('attrib/') and '/vietnam/release_060/' in m}
    existing_members = {m for m in payloads if m.startswith('attrib/') and m not in private_members}
    if len(private_members) != 80 or len(existing_members) != 62:
        raise ValueError('Private/Vietnamese graph count differs')
    guid = CFG['project_guid'].replace('-','')
    refs = {guid+':'+Path(m).stem:m for m in private_members}
    if len(refs) != 80:
        raise ValueError('Private references collide')
    model_lookup = {norm_model(v['private_model']):key for key,v in media['models'].items()}
    if len(model_lookup) != 57:
        raise ValueError('Qualified model paths collide')
    model_consumers = defaultdict(list)
    graph_edges = defaultdict(list)
    private_ref_hits = 0
    unknown_private_refs=[]
    for member in sorted(private_members|existing_members):
        data = Path(payloads[member]['path']).read_bytes()
        parsed=rgd.read(data)
        if rgd.write(parsed)!=data:
            raise ValueError('Final graph RGD native codec roundtrip differs '+member)
        for path,node in rgd.flatten(parsed.nodes):
            if node.kind.startswith('List') or not isinstance(node.value,str):
                continue
            value=node.value
            key=model_lookup.get(norm_model(value))
            if key is not None:
                model_consumers[key].append({'member':member,'leaf':path})
            if path.endswith('/$PBGNAME') and value in refs:
                private_ref_hits+=1
                graph_edges[member].append({'target':refs[value],'leaf':path})
            elif path.endswith('/$PBGNAME') and (':v6i' in value or ':vn060_' in value):
                unknown_private_refs.append({'member':member,'leaf':path,'value':value})
    if unknown_private_refs:
        raise ValueError('Unresolved private binding reference '+str(unknown_private_refs[:3]))
    if set(model_consumers)!=set(media['models']):
        raise ValueError('Qualified models not all referenced by final native graph: '+str(set(media['models'])-set(model_consumers)))
    reachable=set(existing_members)
    queue=deque(existing_members)
    while queue:
        for edge in graph_edges[queue.popleft()]:
            target=edge['target']
            if target not in reachable:
                reachable.add(target)
                queue.append(target)
    unreachable=private_members-reachable
    if unreachable:
        raise ValueError('Unreachable private binding resource '+str(sorted(unreachable)))
    changed_local_actors={Path(m).stem for m in existing_members if m.startswith('attrib/ebps/vietnam/')}
    required_local=set(graph['reachable_local_entity_ids'])
    excluded_local=set(graph['excluded_unlinked_local_entity_ids'])
    if not required_local.issubset(changed_local_actors) or changed_local_actors & excluded_local:
        raise ValueError('Reachable local roster scope differs')
    source_new=[x for x in h['source_rows'] if x['source_sha256'] is None]
    if len(source_new)!=80 or len(h['source_rows'])!=140:
        raise ValueError('Source private identity closure differs')
    evidence={
        'schema':'ccp-060-final-private-roster-coverage/v1',
        'status':'offline_candidate_media_graph_roster_coverage_verified',
        'static_coverage_verified':True,
        'handoff_sha256':sha(HANDOFF),'media_registry_sha256':sha(MEDIA),
        'assembly_sha256':sha(ASSEMBLY),'archive_audit_sha256':sha(AUDIT),
        'candidate_sha256':audit['candidate_sha256'],'baseline_sga_sha256':h['baseline_sga_sha256'],
        'candidate_member_count':len(audit['members']),'candidate_changed_count':len(audit['changed']),
        'candidate_added_count':len(audit['added']),'candidate_removed_count':len(audit['removed']),
        'payload_count':len(payloads),'art_member_count':len(actual_art),
        'private_rgd_count':len(private_members),'changed_vietnamese_rgd_count':len(existing_members),
        'source_row_count':len(h['source_rows']),'new_source_identity_count':len(source_new),
        'qualified_model_count':len(media['models']),
        'qualified_model_native_consumers':dict(sorted(model_consumers.items())),
        'private_reference_edge_count':private_ref_hits,
        'private_graph_reachable_count':len(reachable & private_members),
        'reachable_local_entity_count':len(required_local),
        'excluded_unlinked_local_entity_count':len(excluded_local),
        'included_inherited_stock_actor_count':len(graph['included_inherited_stock_actor_ids']),
        'scope':'Vietnamese reachable land roster; Officials I-IV and unlinked local actor files excluded',
        'stock_retained':'Native siege crew/animation owners and unqualified attached crew visuals retained; Monk IV staff remains stock',
        'deferred':'Rattan and custom crate geometry are not in this qualified media selection',
        'native_runtime_acceptance':False,
        'native_gate':'Producer dependency/precache, siege crew render/runtime consumers, spawn, appearance, gameplay and multiplayer require native match testing',
    }
    write(owned(TARGET),evidence)
    print(json.dumps({k:evidence[k] for k in ('status','payload_count','art_member_count','private_rgd_count','qualified_model_count','private_graph_reachable_count','private_reference_edge_count','reachable_local_entity_count')},indent=2))


if __name__=='__main__':
    main()
