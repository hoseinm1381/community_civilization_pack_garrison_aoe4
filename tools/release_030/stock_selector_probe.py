"""Read official model-state predicates without treating all geometry as simultaneous."""
import collections
import glob
import json
import struct
import sys

from common import OUT, sha, write
from inventory import native
from garrison_shared import relic_chunky as rc

native.CACHEWORK = OUT / 'inventory'
STEMS = {
    'academy': 'art/civilizations/chinese/structures/wonder_imperial_academy/chi_wonder_imperial_academy_control_age02/chi_wonder_imperial_academy_control_age02',
    'gate': 'art/civilizations/chinese/structures/wonder_zhengyangmen_gate/chi_wonder_zhengyangmen_gate_control_age03/chi_wonder_zhengyangmen_gate_control_age03',
    'aachen': 'art/civilizations/hre/structures/wonder_aachen_cathedral/hre_wonder_aachen_cathedral_control_age01/hre_wonder_aachen_cathedral_control_age01',
}


def parse_state(chunk):
    payload = chunk.payload
    count = struct.unpack_from('<I', payload)[0]
    at, conditions = 4, []
    for _ in range(count):
        op, flag, one = struct.unpack_from('<IBI', payload, at)
        at += 9
        prop, at = rc.read_lp_string(payload, at)
        value, at = rc.read_lp_string(payload, at)
        conditions.append({'op': op, 'flag': flag, 'one': one, 'property': prop, 'value': value})
    assert at == len(payload)
    return conditions


def parse_set(chunk):
    name, at = rc.read_lp_string(chunk.payload, 0)
    count = struct.unpack_from('<I', chunk.payload, at)[0]
    at += 4
    members = []
    for _ in range(count):
        value, at = rc.read_lp_string(chunk.payload, at)
        members.append(value)
    assert at == len(chunk.payload)
    return {'name': name, 'members': members}


def run():
    result = {}
    for key, stem in STEMS.items():
        source = native.stock(stem + '.rgm')
        chunks = list(rc.walk(rc.load(source).roots))
        sets = [parse_set(c) for c in chunks if c.tag == b'MSD ' and len(c.payload) > 4]
        states = [parse_state(c) for c in chunks if c.tag == b'CNBP']
        assert len(sets) in (len(states), len(states) + 1)
        pair = [{'set': s, 'conditions': states[i] if i < len(states) else []}
                for i, s in enumerate(sets)]
        result[key] = {'source': str(source), 'pairs': pair,
                       'predicate_values': dict(collections.Counter(c['value'] for state in states for c in state)),
                       'unconditional_set_count': len(sets) - len(states)}
    write(OUT / 'inventory/stock-selector-probe.json', result)
    count_completed(result)
    print(json.dumps({k: {'sets': len(v['pairs']), 'predicates': v['predicate_values'],
                          'unconditional': v['unconditional_set_count'],
                          'first_pairs': v['pairs'][:3]} for k, v in result.items()}, indent=2))


def count_completed(selector_probe):
    """Count LOD0 triangles drawn by official completed-healthy predicates."""
    decoded_paths = [__import__('pathlib').Path(p) for p in glob.glob(str(OUT / 'budget/decode/*/decoded-static.json'))]
    decoded = [(path, json.loads(path.read_text(encoding='utf-8'))) for path in decoded_paths]
    report = {}
    for key, stem in STEMS.items():
        probe = selector_probe[key]
        source = __import__('pathlib').Path(probe['source'])
        document = rc.load(source)
        tables = probe['pairs']
        names = set().union(*(set(pair['set']['members']) for pair in tables))
        healthy = set().union(*(set(pair['set']['members']) for pair in tables
            if any(condition == {'op': 2, 'flag': 0, 'one': 1,
                                 'property': 'life_cycle_state', 'value': 'healthy'}
                   for condition in pair['conditions'])))
        assert len(names) - len(healthy) == 1
        assert names - healthy == {'geo_sel_base_001'}
        matches = [(path, data) for path, data in decoded if stem.replace('/', '\\').lower() in data['geometry']['source']['path'].lower()
                   or stem.lower() in data['geometry']['source']['path'].replace('\\', '/').lower()]
        assert len(matches) == 1, (key, len(matches))
        decoded_path, data = matches[0]
        groups = data['geometry']['groups']
        by_slot = []
        if key == 'academy':
            assert data['structure_collection_contract'] is None
            assert {group['name'] for group in groups} == names
            active = sum(group['triangle_count'] for group in groups if group['name'] in healthy)
            raw = sum(group['triangle_count'] for group in groups)
            assert len(groups) == 250 and len(names) == 225 and active == 59496 and raw == 59652
            by_slot.append({'slot': 'named_geometry', 'group_instances': len(groups),
                            'active_group_instances': sum(group['name'] in healthy for group in groups),
                            'triangles': raw, 'healthy_triangles': active})
        else:
            mscl = next(chunk for chunk in rc.walk(document.roots) if chunk.tag == b'MSCL')
            assert len(mscl.children) == 1 and mscl.children[0].tag == b'DATA'
            payload = mscl.children[0].payload
            source_count = struct.unpack_from('<H', payload)[0]
            assert source_count == len(names)
            offsets = {name: payload.find(rc.lp_string(name)) for name in names}
            assert all(offset >= 2 for offset in offsets.values())
            assert len(set(offsets.values())) == source_count
            ordered = sorted(names, key=offsets.get)
            assert offsets[ordered[0]] == 2
            contract = data['structure_collection_contract']
            assert contract['schema'] == 'garrison.rgm-structure-collection/v1'
            assert sum(contract['geometry_group_spans']) == len(groups)
            assert len(contract['maps']) == len(contract['geometry_group_spans'])
            group_index = active = raw = 0
            for mapping, span in zip(contract['maps'], contract['geometry_group_spans']):
                assert mapping['source_object_count'] == source_count
                assert mapping['geometry_group_span'] == span
                source_to_bone = mapping['source_to_local_bone']
                assert len(source_to_bone) == source_count
                inverse = {bone: ordered[i] for i, bone in enumerate(source_to_bone) if bone >= 0}
                assert len(inverse) == mapping['active_object_count']
                assert set(inverse) == set(range(mapping['active_object_count']))
                slot_raw = slot_active = 0
                for group in groups[group_index:group_index + span]:
                    bones = group['collection_bone_indices']
                    assert len(bones) == group['vertex_count']
                    assert len(group['triangles']) == group['triangle_count']
                    for triangle in group['triangles']:
                        a, b, c = (bones[i] for i in triangle)
                        assert a == b == c and a in inverse, (key, mapping['slot'], triangle)
                        slot_raw += 1
                        slot_active += inverse[a] in healthy
                group_index += span
                raw += slot_raw
                active += slot_active
                by_slot.append({'slot': mapping['slot'], 'geometry_group_span': span,
                                'active_source_objects': len(inverse),
                                'healthy_source_objects': sum(name in healthy for name in inverse.values()),
                                'triangles': slot_raw, 'healthy_triangles': slot_active,
                                'all_triangles_single_mapped_bone': True})
            assert group_index == len(groups)
            assert (source_count, active, raw) == {'gate': (213, 98762, 98898),
                                                  'aachen': (230, 90258, 91068)}[key]
        report[key] = {'status': 'qualified_static_drawgraph', 'native_runtime': 'unverified',
                       'rgm': str(source), 'rgm_sha256': sha(source),
                       'decoded_manifest': str(decoded_path), 'decoded_manifest_sha256': sha(decoded_path),
                       'rrgeom_sha256': data['geometry']['source']['sha256'],
                       'selector_names': len(names), 'healthy_selector_names': len(healthy),
                       'lod0_raw_triangles': raw, 'completed_healthy_lod0_triangles': active,
                       'slots': by_slot,
                       'method': 'official CNBP healthy OR predicate union; every decoded LOD0 draw instance or MSCL source-object local bone counted once per triangle'}
    write(OUT / 'inventory/stock-completed-budget.json', report)
    print(json.dumps({key: {'healthy_lod0_triangles': value['completed_healthy_lod0_triangles'],
                            'slots': value['slots']} for key, value in report.items()}, indent=2))


if __name__ == '__main__': run()
