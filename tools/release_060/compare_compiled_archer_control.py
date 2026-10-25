"""Exhaustive donor-versus-private-cook bind, LOD1 topology and weight check."""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from common import OUT, guard, owned, read, sha, write

DONOR = OUT / 'donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json'
PRIVATE = OUT / 'qualification/archer-matched-control-decoded/3652c5bb34aef03e9f49/decoded-static.json'
DECODE_RECEIPT = OUT / 'qualification/archer-matched-control-decode.json'
READBACK = OUT / 'qualification/archer-matched-control-readback.json'
REPORT = OUT / 'qualification/archer-matched-control-comparison.json'


def nums(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from nums(item)
    elif isinstance(value, list):
        for item in value:
            yield from nums(item)
    elif isinstance(value, (int, float)):
        yield float(value)


def max_delta(left, right, field):
    a = [v for item in left for v in nums(item[field])]
    b = [v for item in right for v in nums(item[field])]
    if len(a) != len(b):
        raise ValueError(f'{field}: unequal transform scalar counts')
    return max(abs(x-y) for x,y in zip(a,b))


def main():
    guard()
    owned(REPORT)
    if REPORT.exists():
        raise FileExistsError('Preserve earlier complete bind comparison')
    receipt = read(DECODE_RECEIPT)
    archived = read(READBACK)
    if receipt['status'] != 'decoded' or sha(archived['archive']) != archived['archive_sha256']:
        raise ValueError('Private native decode or archive identity changed')
    donor = read(DONOR)
    built = read(PRIVATE)
    if donor['status'] != 'decoded' or built['status'] != 'decoded':
        raise ValueError('One model is not decoded')
    bones_a, bones_b = donor['skeleton']['bones'], built['skeleton']['bones']
    palette_a = donor['skeleton']['skin_palettes'][0]['bones']
    palette_b = built['skeleton']['skin_palettes'][0]['bones']
    hierarchy_equal = len(bones_a) == len(bones_b) == 48 and all(
        (x['index'],x['name'],x['parent_index'],x['parent_name']) ==
        (y['index'],y['name'],y['parent_index'],y['parent_name'])
        for x,y in zip(bones_a,bones_b))
    palette_equal = len(palette_a) == len(palette_b) == 46 and all(
        (x['palette_index'],x['name'],x['parent_index'],x['parent_name'],x['skeleton_index']) ==
        (y['palette_index'],y['name'],y['parent_index'],y['parent_name'],y['skeleton_index'])
        for x,y in zip(palette_a,palette_b))
    if not hierarchy_equal or not palette_equal:
        raise ValueError('Compiled control skeleton/palette hierarchy differs')
    ga, gb = donor['geometry']['groups'], built['geometry']['groups']
    if len(ga) != len(gb) != 3 or len(ga) != 3:
        raise ValueError('Expected exactly three donor and cooked LOD groups')
    # FBX-native cook explodes LOD1 into triangle corners. Match each of the
    # 746 unique source positions to one cooked position, then compare triangle
    # and (bone,byte-weight) multisets independent of indexing/influence order.
    source = ga[0]
    output = gb[0]
    positions_a = list({tuple(p) for p in source['positions']})
    positions_b = list({tuple(p) for p in output['positions']})
    if len(positions_a) != len(positions_b):
        raise ValueError('LOD1 unique position count changed')
    index_b = {p:i for i,p in enumerate(positions_b)}
    matching = {}
    distances = []
    for position in positions_a:
        i = min(range(len(positions_b)), key=lambda n:
                sum((q-t)**2 for q,t in zip(position,positions_b[n])))
        matching[position] = i
        distances.append(math.dist(position,positions_b[i]))
    if len(set(matching.values())) != len(positions_a):
        raise ValueError('LOD1 position nearest-neighbour match is not bijective')
    source_tris = Counter(tuple(sorted(matching[tuple(source['positions'][i])] for i in tri))
                          for tri in source['triangles'])
    output_tris = Counter(tuple(sorted(index_b[tuple(output['positions'][i])] for i in tri))
                          for tri in output['triangles'])
    def corner(group, index, from_donor):
        p = (matching[tuple(group['positions'][index])] if from_donor
             else index_b[tuple(group['positions'][index])])
        weighted = tuple(sorted((int(bone), round(weight*255))
                                for bone,weight in zip(group['skin_indices'][index],
                                                       group['skin_weights'][index]) if weight > 0))
        return p, weighted
    source_corners = Counter(corner(source,i,True) for tri in source['triangles'] for i in tri)
    output_corners = Counter(corner(output,i,False) for tri in output['triangles'] for i in tri)
    lods = []
    for index,(old,new) in enumerate(zip(ga,gb),1):
        old_indices = old['rig_projection']['lod_palette']['skin_indices']
        new_indices = new['rig_projection']['lod_palette']['skin_indices']
        lods.append({'lod': index, 'stock_vertices': old['vertex_count'],
                     'stock_triangles': old['triangle_count'],
                     'cooked_vertices': new['vertex_count'],
                     'cooked_triangles': new['triangle_count'],
                     'stock_skin_indices': old_indices,
                     'cooked_skin_indices': new_indices,
                     'skin_palette_indices_exact': old_indices == new_indices,
                     'skin_weight_status': new['skin_projection']['status'],
                     'bounds_exact': old['bounds'] == new['bounds']})
    report = {
        'schema': 'ccp-060-archer-matched-control-comparison/v1',
        'status': 'compiled_lod1_topology_weights_and_rig_near_match_lod2_lod3_different',
        'donor_manifest': str(DONOR), 'donor_manifest_sha256': sha(DONOR),
        'compiled_manifest': str(PRIVATE), 'compiled_manifest_sha256': sha(PRIVATE),
        'archive_sha256': archived['archive_sha256'],
        'hierarchy': {'ordered_48_bones_names_parents_exact': hierarchy_equal,
                      'max_local_transform_scalar_delta': max_delta(bones_a,bones_b,'local_reference_transform'),
                      'max_global_transform_scalar_delta': max_delta(bones_a,bones_b,'global_reference_transform')},
        'skin_palette': {'ordered_46_bones_identity_exact': palette_equal,
                         'max_global_transform_scalar_delta': max_delta(palette_a,palette_b,'global_reference_transform'),
                         'max_inverse_bind_scalar_delta': max_delta(palette_a,palette_b,'inverse_bind_transform')},
        'lod1_geometry': {'source_unique_positions': len(positions_a),
                          'cooked_unique_positions': len(positions_b),
                          'position_match_bijective': True,
                          'maximum_position_distance_m': max(distances),
                          'triangle_topology_multiset_exact': source_tris == output_tris,
                          'weighted_corner_multiset_exact_after_influence_order_normalization': source_corners == output_corners,
                          'weighted_triangle_corners_compared': sum(source_corners.values()),
                          'bounds_exact': source['bounds'] == output['bounds']},
        'lods': lods,
        'compiled_rig_projection_status': built['rig_projection']['status'],
        'compiled_unresolved_rig_groups': built['rig_projection']['unresolved_group_count'],
        'compiled_completeness': built['completeness']['status'],
        'animator_boundary': archived['animator_boundary'],
        'qualification_limit': 'Garrison normal validator, unit-add, cook, archive readback and private model decode pass. Cooked LOD1 preserves stock topology and byte-quantized weights with sub-millimetre position drift, but LOD2/3 are cloned full-detail geometry with different bone partitions. Generated Spearman animator is not the Archer animator. Original Archer animator consuming this private model has not been native-tested or approved.'
    }
    write(REPORT, report)
    print(json.dumps({'status': report['status'], 'lod1_topology': report['lod1_geometry']['triangle_topology_multiset_exact'],
                      'lod1_weights': report['lod1_geometry']['weighted_corner_multiset_exact_after_influence_order_normalization'],
                      'max_position_m': report['lod1_geometry']['maximum_position_distance_m']}, indent=2))


if __name__ == '__main__':
    main()
