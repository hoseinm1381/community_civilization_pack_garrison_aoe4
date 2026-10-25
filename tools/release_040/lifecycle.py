"""Qualify a native ruined landmark selector in freshly cooked combined geometry.

The installed Garrison house writer supplies a coherent MSCL and six typed
construction selector pairs. All authored parts enter a construction selector;
this transform moves the named ruin parts into the otherwise empty final set.
The stock model owner supplies the native lifecycle/death/repair actions.
"""
from __future__ import annotations

import struct

from garrison_shared import relic_chunky as rc


def _selector(chunk):
    name, at = rc.read_lp_string(chunk.payload, 0)
    count = struct.unpack_from('<I', chunk.payload, at)[0]
    at += 4
    members = []
    for _ in range(count):
        value, at = rc.read_lp_string(chunk.payload, at)
        members.append(value)
    assert at == len(chunk.payload), (name, at, len(chunk.payload))
    return name, members


def _conditions(chunk):
    count = struct.unpack_from('<I', chunk.payload, 0)[0]
    at = 4
    rows = []
    for _ in range(count):
        operator, flag, one = struct.unpack_from('<IBI', chunk.payload, at)
        at += 9
        prop, at = rc.read_lp_string(chunk.payload, at)
        value, at = rc.read_lp_string(chunk.payload, at)
        rows.append((operator, flag, one, prop, value))
    assert at == len(chunk.payload)
    return rows


def _pack_selector(name, members):
    return rc.lp_string(name) + struct.pack('<I', len(members)) + b''.join(rc.lp_string(x) for x in members)


def _pack_conditions(states):
    return struct.pack('<I', len(states)) + b''.join(
        struct.pack('<IBI', 2, 0, 1) + rc.lp_string('life_cycle_state') + rc.lp_string(state)
        for state in states)


def _pairs(raw):
    document = rc.parse(raw)
    model = next(c for c in document.roots if c.tag == b'MODL')
    bp = next(c for c in model.children if c.tag == b'MSBP')
    items = bp.children
    sets = [c for c in items if c.tag == b'MSD ' and len(c.payload) > 4]
    predicates = [c for c in items if c.tag == b'CNBP']
    assert len(sets) == len(predicates) == 6
    return document, list(zip(sets, predicates))


def install_ruins(raw: bytes, ruin_names: set[str], healthy_names: set[str]):
    """Return a typed RGM with ruin geometry shown only in native ruins state.

    Caller first runs the established intact_damage_conditions transform, so
    healthy geometry is available throughout damage_1..5. This function only
    moves already cooked geometry groups between native selector tables.
    """
    assert ruin_names and healthy_names and ruin_names.isdisjoint(healthy_names)
    document, pairs = _pairs(raw)
    table = [(_selector(s), _conditions(c)) for s, c in pairs]
    seen = set().union(*(set(members) for (_, members), _ in table))
    assert seen == ruin_names | healthy_names, (seen ^ (ruin_names | healthy_names))
    empty = [(i, s, c) for i, ((s, members), c) in enumerate(table)
             if s == 'sel_healthy' and not members]
    assert len(empty) == 1, empty
    index = empty[0][0]
    assert all(not any(row[-1] == 'ruins' for row in conditions) for _, conditions in table)
    assert any(any(row[-1] == 'healthy' for row in conditions) for _, conditions in table)
    edits = {}
    removed = set()
    for i, ((name, members), conditions) in enumerate(table):
        selector, predicate = pairs[i]
        if i == index:
            edits[selector.offset] = _pack_selector('sel_ruins', sorted(ruin_names))
            edits[predicate.offset] = _pack_conditions(['ruins'])
        else:
            keep = [member for member in members if member not in ruin_names]
            removed.update(set(members) - set(keep))
            if keep != members:
                edits[selector.offset] = _pack_selector(name, keep)
    assert removed == ruin_names, (removed, ruin_names)
    result = rc.rebuild(document, lambda chunk: edits.get(chunk.offset))
    _, final = _pairs(result)
    parsed = [(_selector(s), _conditions(c)) for s, c in final]
    for state in ['healthy', *(f'damage_{i}' for i in range(1, 6)), 'ruins']:
        enabled = {member for (_, members), conditions in parsed
                   if any(row == (2, 0, 1, 'life_cycle_state', state) for row in conditions)
                   for member in members}
        assert enabled == (ruin_names if state == 'ruins' else healthy_names), (state, enabled)
    assert [name for (name, _), _ in parsed].count('sel_ruins') == 1
    proof = {'ruin_parts': sorted(ruin_names), 'healthy_parts': sorted(healthy_names),
             'ruins_only_native_selector': True, 'healthy_and_five_damage_states': True,
             'native_rgo': 'retained from the exact stock landmark owner; check separately',
             'runtime': 'unverified'}
    return result, proof
