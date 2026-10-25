"""Create private Castle RGMs with focused stock-roof selector replacement.

Only monastery roof source-object membership is removed from selector sets.
RRGeom/index/UV/weights, RGO markers, all native predicates and all nonselector
RGM leaf chunks are retained byte for byte. Native nonroof ruin sources remain;
roof debris source names omitted from ruins are listed in the receipt.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from common import OUT, ROOT, guarded, read, sha, write
from building_selectors import rc, source_map, parse_set, parse_state, native_path

JOBS = (('monastery', 3), ('monastery', 4), ('siege_workshop', 3),
        ('siege_workshop', 4), ('keep', 3))
VALID_PATH = ROOT / 'output/castle_next/buildings/model-validation.json'


def pack_set(name, members):
    return rc.lp_string(name) + struct.pack('<I', len(members)) + b''.join(
        rc.lp_string(member) for member in members)


def make(donor, family, age):
    decoded = donor['decoded_static']
    source = native_path(decoded['resources']['model']['cache_path'])
    assert sha(source) == decoded['resources']['model']['sha256']
    raw = source.read_bytes()
    doc = rc.parse(raw)
    chunks = list(rc.walk(doc.roots))
    sets = [c for c in chunks if c.tag == b'MSD ' and len(c.payload) > 4]
    predicates = [c for c in chunks if c.tag == b'CNBP']
    assert len(sets) in (len(predicates), len(predicates)+1)
    names, _ = source_map(donor)
    roof_names = {name for group, group_names in zip(decoded['geometry']['groups'], names)
                  if group['preview_material'] == 'roof' for name in group_names}
    # The stock roof's ornaments/outer rafters are stored in the separate
    # "extra" group. Remove only native source objects whose triangles cross
    # the new hip surface, measured in donor model coordinates.
    intersecting = set()
    if family == 'monastery':
        eave, rise = (3.24, 2.28) if age == 3 else (4.32, 2.32)
        for group, group_names in zip(decoded['geometry']['groups'], names):
            if group['preview_material'] != 'extra':
                continue
            for tri, name in zip(group['triangles'], group_names):
                for vertex in tri:
                    x, y, z = group['positions'][vertex]
                    roof_z = eave + rise * max(0.0, min(1-abs(x)/4.575,
                                                        1-abs(y-2.32)/3.59))
                    if z > roof_z + .05:
                        intersecting.add(name)
                        break
        roof_names |= intersecting
    assert roof_names if family == 'monastery' else True
    edits, changes, omitted_ruin = {}, [], []
    if family == 'monastery':
        for i, chunk in enumerate(sets):
            selected = parse_set(chunk.payload)
            conditions = parse_state(predicates[i].payload) if i < len(predicates) else []
            values = {c[-1] for c in conditions if c[-2] == 'life_cycle_state'}
            overlap = [name for name in selected['members'] if name in roof_names]
            if not overlap:
                continue
            remaining = [name for name in selected['members'] if name not in roof_names]
            edits[chunk.offset] = pack_set(selected['name'], remaining)
            changes.append({'selector': selected['name'],
                            'conditions': conditions,
                            'before_members': selected['members'],
                            'after_members': remaining,
                            'removed': overlap,
                            'remaining_count': len(remaining)})
            if 'ruins' in values:
                omitted_ruin.append({'selector': selected['name'],
                                     'omitted_roof_members': overlap})
        assert changes and omitted_ruin
    rebuilt = rc.rebuild(doc, lambda chunk: edits.get(chunk.offset)) if edits else raw
    after = list(rc.walk(rc.parse(rebuilt).roots))
    assert len(chunks) == len(after)
    for before_chunk, after_chunk in zip(chunks, after):
        assert (before_chunk.tag, before_chunk.decoded_name) == (after_chunk.tag, after_chunk.decoded_name)
        if before_chunk.children:
            continue
        if before_chunk.offset not in edits:
            assert before_chunk.payload == after_chunk.payload
    if family == 'monastery':
        assert rebuilt != raw
    else:
        assert rebuilt == raw
    target = ROOT / f'art/exports/castle_next/buildings/{family}/age{age:02}/vn_model.rgm'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(rebuilt)
    return {'native_model': str(target), 'native_model_sha256': sha(target),
            'donor_model_sha256': sha(source),
            'hidden_native_selector_names': sorted({n for c in changes for n in c['removed']}),
            'intersecting_native_roof_trim_names': sorted(intersecting),
            'selector_changes': changes,
            'omitted_roof_debris': omitted_ruin,
            'nonselector_leaf_chunks_byte_identical': True,
            'marker_rgo_unchanged': True}


def main():
    guarded()
    donors = read(OUT / 'donors/donor-manifest.json')['donors']
    result = read(VALID_PATH)
    assert len(result['models']) == 5
    for family, age in JOBS:
        row = next(r for r in result['models'] if (r['family'],r['age']) == (family,age))
        row.update(make(donors[f'{family}{age:02}'], family, age))
        print('PRIVATE_MODEL_SELECTORS', family, age,
              len(row['hidden_native_selector_names']))
    write(VALID_PATH, result)


if __name__ == '__main__':
    main()
