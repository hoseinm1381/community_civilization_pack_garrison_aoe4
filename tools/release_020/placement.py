"""Numeric Y-up world-space bounds after each retained native stamp transform."""
import math
import struct
import sys
from pathlib import Path
from common import OUT, guarded, read, sha, write
from inventory import native
from integrate import WORK
from garrison_shared import relic_chunky as rc

sys.dont_write_bytecode = True
native.CACHEWORK = OUT / 'inventory'


def native_bounds(path):
    points = []
    for chunk in rc.walk(rc.load(path).roots):
        if chunk.tag != b'GEOB': continue
        count, _, stride, _ = struct.unpack_from('<4I', chunk.payload)
        if stride not in (20, 24, 32) or len(chunk.payload) < 16 + count * stride: continue
        points.extend(struct.unpack_from('<3e', chunk.payload, 16 + i * stride)
                      for i in range(count))
    assert points, path
    return {'min': [min(p[i] for p in points) for i in range(3)],
            'max': [max(p[i] for p in points) for i in range(3)],
            'vertices': len(points)}


def transformed_bounds(bounds, transform):
    x, y, z, w = transform[:4]
    tx, ty, tz = transform[4:7]
    sx, sy, sz = transform[7:10]
    assert abs(x*x + y*y + z*z + w*w - 1) < .002
    points = []
    for a in (bounds['min'][0], bounds['max'][0]):
        for b in (bounds['min'][1], bounds['max'][1]):
            for c in (bounds['min'][2], bounds['max'][2]):
                px, py, pz = a*sx, b*sy, c*sz
                # Standard xyzw quaternion rotation in Essence Y-up coordinates.
                ix =  w*px + y*pz - z*py
                iy =  w*py + z*px - x*pz
                iz =  w*pz + x*py - y*px
                iw = -x*px - y*py - z*pz
                points.append((ix*w + iw*-x + iy*-z - iz*-y + tx,
                               iy*w + iw*-y + iz*-x - ix*-z + ty,
                               iz*w + iw*-z + ix*-y - iy*-x + tz))
    return {'min': [min(p[i] for p in points) for i in range(3)],
            'max': [max(p[i] for p in points) for i in range(3)]}


def rows(stamp_path, private=False):
    result = []
    for visual in native.active_visuals(native.NativeTree(stamp_path)):
        stem = visual['model'].replace('\\', '/').lower()
        if stem == 'art/environment/biome_temperate_deciduous/splats/blank_marker_a': continue
        model_path = WORK / 'payload' / (stem + '.rrgeom') if stem.startswith('art/scenario/cc020/') else native.stock(stem + '.rrgeom')
        if not model_path.is_file(): continue  # Native blank marker has no geometry.
        local = native_bounds(model_path)
        result.append({'model': stem, 'model_sha256': sha(model_path),
                       'transform': visual['transform'], 'local': local,
                       'world': transformed_bounds(local, visual['transform'])})
    return result


def verify():
    guarded()
    graph = read(OUT / 'inventory/native-graph.json')
    result = {'status': 'passed', 'coordinate_contract': 'Essence model GEOB Y-up; xyzw stamp quaternion; world X/Z horizontal',
              'stamps': {}, 'runtime': 'unverified'}
    for key in ('economy_ministry', 'farm_rice_back', 'farm_rice_front', 'farm_rice_left', 'farm_rice_right',
                'hideout_default', 'hideout_stone', 'hideout_shelter_default', 'hideout_shelter_stone'):
        final = WORK / 'payload' / f'art/stamps/cc020/{key}.bin'
        if not final.exists():
            assert key.startswith('hideout_'), key
            continue
        if key.startswith('hideout_shelter_'):
            final_rows = rows(final, True)
            principal = [row for row in final_rows if row['model'].startswith('art/scenario/cc020/')]
            assert len(principal) == 1 and principal[0]['model'] == 'art/scenario/cc020/' + key + '/model'
            assert -.05 <= principal[0]['world']['min'][1] <= .15, (key, 'ground contact', principal[0]['world'])
            result['stamps'][key] = {'original_principal': [], 'final_principal': principal,
                                     'original_active_visual_count': 0,
                                     'final_active_visual_count': len(final_rows)}
            continue
        original_rows = rows(graph['stamps'][key]['file'])
        final_rows = rows(final, True)
        original_principal = [row for row in original_rows if row['model'] ==
                              ('art/civilizations/chinese/structures/dynasty_pagoda/chi_dynasty_pagoda_control_age03/chi_dynasty_pagoda_control_age03'
                               if key == 'economy_ministry' else
                               'art/environment/biome_tropical_dry/bushes/sagebush_row/sagebush_row'
                               if key.startswith('farm_') else graph['stamps'][key]['visuals'][0]['model'])]
        final_principal = [row for row in final_rows if row['model'].startswith('art/scenario/cc020/')]
        assert len(original_principal) == len(final_principal) == (2 if key == 'farm_rice_back' else 1)
        for new in final_principal:
            if key.startswith('hideout_'):
                old_floor = original_principal[0]['world']['min'][1]
                assert abs(new['world']['min'][1] - old_floor) <= .002, (key, 'native buried foundation changed', new['world'], old_floor)
                assert new['world']['min'][1] <= .15
            else:
                assert -.05 <= new['world']['min'][1] <= .15, (key, 'ground contact', new['world'])
        if key == 'economy_ministry':
            old, new = original_principal[0]['world'], final_principal[0]['world']
            for axis in (0, 2):
                assert old['min'][axis] - .01 <= new['min'][axis]
                assert new['max'][axis] <= old['max'][axis] + .01
            assert -4.05 <= new['min'][0] <= new['max'][0] <= 4.05
            assert -4.05 <= new['min'][2] <= new['max'][2] <= 4.05
        result['stamps'][key] = {'original_principal': original_principal,
                                 'final_principal': final_principal,
                                 'original_active_visual_count': len(original_rows),
                                 'final_active_visual_count': len(final_rows)}
    write(WORK / 'placement-world-bounds.json', result)
    print('PLACEMENT_WORLD_BOUNDS_020', len(result['stamps']))
    return result


if __name__ == '__main__': verify()
