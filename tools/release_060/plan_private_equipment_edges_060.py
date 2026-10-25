"""Pin exact compiled weapon-list leaves on the staged Vietnamese graph."""
from __future__ import annotations

import sys
from pathlib import Path

from common import CFG, OUT, guard, owned, read, sha, write

sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd

PLAN = OUT/'integration/private-equipment-graph/derive-plan-v1.json'
UPSTREAM = OUT/'integration/private-inherited-graph-stage-r1/stage.json'
TARGET = OUT/'integration/private-equipment-graph/compiled-edges-v1.json'


def main():
    guard()
    plan, upstream = read(PLAN), read(UPSTREAM)
    payloads = {p['member']:p for p in upstream['payloads']}
    edges = []
    by_actor = {}
    for row in plan['entries']:
        name = row['stock_source'].rsplit('/', 1)[-1]
        for consumer in row['source_consumers']:
            by_actor.setdefault(consumer['actor'], []).append((name, row))
    for actor, targets in sorted(by_actor.items()):
        member = f'attrib/ebps/vietnam/{actor}.rgd'
        payload = payloads.get(member)
        if not payload or sha(payload['path']) != payload['sha256']:
            raise ValueError('Upstream Vietnamese actor absent or drifted '+member)
        doc = rgd.read(Path(payload['path']).read_bytes())
        for name, target in targets:
            hits = []
            for path, node in rgd.flatten(doc.nodes):
                if node.key != '$PBGNAME' or node.value != name:
                    continue
                parent = path.rsplit('/', 1)[0]
                try:
                    name_map = rgd.find(doc.nodes, parent+'/$PBGMAP').value
                except KeyError:
                    continue
                if name_map == 'attachments\\attachment_lists':
                    hits.append({'owner_member':member, 'path':path,
                                 'before_value':name, 'name_map':name_map,
                                 'target_private_member':target['private_member']})
            if not hits:
                raise ValueError('No compiled weapon selector '+actor+' '+name)
            edges.extend(hits)
    paths = [(e['owner_member'],e['path']) for e in edges]
    if len(paths) != len(set(paths)):
        raise ValueError('Compiled weapon edge collision')
    data = {'schema':'ccp-060-private-equipment-compiled-edges/v1',
            'status':'offline_exact_edges_native_ids_pending', 'derive_plan_sha256':sha(PLAN),
            'upstream_stage_sha256':sha(UPSTREAM), 'edges':edges,
            'actor_count':len(by_actor), 'compiled_edge_count':len(edges),
            'native_cook_or_active_source_changed':False}
    if TARGET.exists():
        if read(TARGET) != data:
            raise ValueError('Preserve equipment edges plan')
    else:
        write(owned(TARGET), data)
    print({'plan':str(TARGET), 'actors':len(by_actor), 'compiled_edges':len(edges)})


if __name__ == '__main__':
    main()
