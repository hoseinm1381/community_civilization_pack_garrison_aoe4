"""Prove three compiled-only inherited producer refs replay exactly from 0.5.3."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from common import OUT, ROOT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd

INHERITED = OUT/'integration/private-inherited-graph-stage-r1/stage.json'
FINAL = OUT/'integration/worker-elephant-owner-stage-r2/stage.json'
TARGET = OUT/'integration/private-land-graph/compiled-only-producer-replay-v1.json'


def main():
    guard()
    inherited, final = read(INHERITED), read(FINAL)
    baseline = read(OUT/'baseline/final053/freeze.json')
    payloads = {x['member']:x for x in final['payloads']}
    grouped = defaultdict(list)
    for edge in inherited['inherited_producer_compiled_overlays_without_source_elements']:
        grouped[edge['compiled_member']].append(edge)
    if sum(map(len,grouped.values())) != 3 or len(grouped) != 2:
        raise ValueError('Compiled-only producer closure changed')
    receipts = []
    for member,edges in sorted(grouped.items()):
        original = OUT/'baseline/final053/archive-members'/member
        before_sha = baseline['archive_members'][member]['sha256']
        if sha(original) != before_sha:
            raise ValueError('Frozen producer drift '+member)
        approved = {x['path'] for x in edges}
        edits = [{'path':x['path'],'before':x['before_value'],'after':x['after_value']}
                 for x in edges]
        replay, inverse_proof = patch_visual_rgd(original.read_bytes(),edits,'graph',
                                                 approved_paths=approved)
        target = payloads[member]
        staged = Path(target['path'])
        if sha(staged) != target['sha256'] or replay != staged.read_bytes():
            raise ValueError('Compiled-only producer overlay does not replay '+member)
        for edge in edges:
            source = Path(edge['source'])
            if not source.is_relative_to(ROOT) or sha(source) != edge['source_sha256']:
                raise ValueError('Producer active XML drift '+member)
            if edge['direct_source_match_count'] != 0:
                raise ValueError('Producer unexpectedly has direct source element')
        receipts.append({'member':member,'baseline_sha256':before_sha,
                         'final_payload_sha256':target['sha256'],
                         'replay_equals_final_payload':True,
                         'original_native_inverse_byte_proof':inverse_proof,
                         'source_sha256':edges[0]['source_sha256']})
    data = {'schema':'ccp-060-compiled-only-producer-replay/v1',
            'status':'exact_053_baseline_to_final_payload_replay_and_inverse_verified',
            'baseline_sga_sha256':baseline['sga_sha256'],
            'inherited_stage_sha256':sha(INHERITED),'aggregate_stage_sha256':sha(FINAL),
            'producer_members':receipts,'producer_edge_count':3,
            'active_source_or_final_archive_changed':False}
    if TARGET.exists():
        if read(TARGET) != data:
            raise ValueError('Preserve prior producer replay proof')
    else:
        write(owned(TARGET),data)
    print({'proof':str(TARGET),'members':len(receipts),'edges':3})


if __name__ == '__main__':
    main()
