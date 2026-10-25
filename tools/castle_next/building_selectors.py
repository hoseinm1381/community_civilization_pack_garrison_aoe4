"""Exact stock RGM construction/lifecycle source-object mapping for Castle art."""
from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

from common import CFG, sha

sys.path.insert(0, str(Path(CFG['garrison_extension'])))
from garrison_shared import relic_chunky as rc


def native_path(path):
    raw = str(path)
    return Path('\\\\?\\' + raw) if os.name == 'nt' and len(raw) >= 240 else Path(raw)


def parse_set(payload):
    name, at = rc.read_lp_string(payload, 0)
    count = struct.unpack_from('<I', payload, at)[0]
    at += 4
    members = []
    for _ in range(count):
        value, at = rc.read_lp_string(payload, at)
        members.append(value)
    assert at == len(payload)
    return {'name': name, 'members': members}


def parse_state(payload):
    count = struct.unpack_from('<I', payload)[0]
    at = 4
    conditions = []
    for _ in range(count):
        op, flag, one = struct.unpack_from('<IBI', payload, at)
        at += 9
        prop, at = rc.read_lp_string(payload, at)
        value, at = rc.read_lp_string(payload, at)
        conditions.append((op, flag, one, prop, value))
    assert at == len(payload)
    return conditions


def source_map(donor):
    doc = donor['decoded_static']
    model = native_path(doc['structure_collection_contract']['source']['path'])
    assert sha(model) == doc['structure_collection_contract']['source']['sha256']
    chunks = list(rc.walk(rc.load(model).roots))
    sets = [parse_set(c.payload) for c in chunks if c.tag == b'MSD ' and len(c.payload) > 4]
    states = [parse_state(c.payload) for c in chunks if c.tag == b'CNBP']
    assert len(sets) in (len(states), len(states)+1)
    healthy, allnames = set(), set()
    for i, item in enumerate(sets):
        allnames.update(item['members'])
        conditions = states[i] if i < len(states) else []
        if (2, 0, 1, 'life_cycle_state', 'healthy') in conditions:
            healthy.update(item['members'])
    assert healthy
    mscl = next(c for c in chunks if c.tag == b'MSCL')
    assert len(mscl.children) == 1 and mscl.children[0].tag == b'DATA'
    payload = mscl.children[0].payload
    count = struct.unpack_from('<H', payload)[0]
    offsets = {n: payload.find(rc.lp_string(n)) for n in allnames}
    assert count == len(allnames)
    assert all(o >= 2 for o in offsets.values()) and len(set(offsets.values())) == count
    ordered = sorted(allnames, key=offsets.get)
    contract = doc['structure_collection_contract']
    group_sources = []
    index = 0
    for mapping, span in zip(contract['maps'], contract['geometry_group_spans']):
        inverse = {bone: ordered[i] for i, bone in enumerate(mapping['source_to_local_bone']) if bone >= 0}
        for group in doc['geometry']['groups'][index:index+span]:
            sources = []
            bones = group['collection_bone_indices']
            for tri in group['triangles']:
                a, b, c = (bones[v] for v in tri)
                assert a == b == c and a in inverse
                sources.append(inverse[a])
            group_sources.append(sources)
        index += span
    assert index == len(group_sources) == len(doc['geometry']['groups'])
    table = [{'name': item['name'], 'members': item['members'],
              'conditions': states[i] if i < len(states) else []}
             for i, item in enumerate(sets)]
    return group_sources, {'selector_sets': len(sets), 'selector_table': table,
                           'healthy_selector_names': sorted(healthy),
                           'all_selector_names': sorted(allnames)}
