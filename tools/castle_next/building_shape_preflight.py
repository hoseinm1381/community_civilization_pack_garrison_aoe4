"""Check all five stock Castle donor shape maps before Blender authoring."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np

from common import OUT, ROOT, guarded, read, write


def main():
    guarded()
    source = (ROOT / 'tools/castle_next/building_native.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {'smooth', 'shape'}]
    scope = {'np': np}
    exec(compile(ast.Module(body=functions, type_ignores=[]),
                 'building_native.shape', 'exec'), scope)
    shape = scope['shape']
    donors = read(OUT / 'donors/donor-manifest.json')['donors']
    rows = []
    for key in ('monastery03', 'monastery04', 'siege_workshop03',
                'siege_workshop04', 'keep03'):
        row = donors[key]
        family, age = key[:-2], int(key[-2:])
        doc = read(row['decoded_static_manifest'])
        points = np.concatenate([np.asarray(g['positions'], dtype=np.float64)
                                 for g in doc['geometry']['groups']])
        after = shape(points, family, age)
        assert np.isfinite(after).all()
        ground = points[:, 2] <= 0
        assert np.array_equal(after[ground], points[ground])
        sample = points[::max(1, len(points)//1800)]
        jac = np.empty((len(sample), 3, 3), dtype=np.float64)
        epsilon = 1e-4
        for axis in range(3):
            plus, minus = sample.copy(), sample.copy()
            plus[:, axis] += epsilon
            minus[:, axis] -= epsilon
            jac[:, :, axis] = (shape(plus, family, age) -
                                shape(minus, family, age))/(2*epsilon)
        determinant = np.linalg.det(jac)
        assert determinant.min() > .10
        movement = np.linalg.norm(after-points, axis=1)
        rows.append({'key': key, 'donor_manifest': row['decoded_static_manifest'],
                     'vertices': len(points),
                     'ground_vertices_fixed': int(np.count_nonzero(ground)),
                     'moved_over_3mm': int(np.count_nonzero(movement > .003)),
                     'max_displacement_m': float(movement.max()),
                     'min_sampled_jacobian': float(determinant.min()),
                     'stock_bounds_m': {'minimum': points.min(axis=0).tolist(),
                                        'maximum': points.max(axis=0).tolist()},
                     'remodel_bounds_m': {'minimum': after.min(axis=0).tolist(),
                                          'maximum': after.max(axis=0).tolist()}})
    write(OUT / 'buildings/shape-preflight.json',
          {'schema': 'ccp.castle-next.building-shape-preflight/v1',
           'status': 'passed', 'models': rows,
           'proof': 'Decoded donor numerical map only; no Blender/export/cook'})
    for row in rows:
        print('SHAPE_PREFLIGHT', row['key'], row['vertices'],
              row['moved_over_3mm'], round(row['max_displacement_m'], 3))


if __name__ == '__main__':
    main()
