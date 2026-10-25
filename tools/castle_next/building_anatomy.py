"""Read-only selector-level donor anatomy for roof replacement placement."""
from __future__ import annotations

import collections
import sys

from common import OUT, guarded, read
from building_selectors import source_map


def main():
    guarded()
    key = sys.argv[1] if len(sys.argv) > 1 else 'monastery03'
    donor = read(OUT / 'donors/donor-manifest.json')['donors'][key]
    groups = donor['decoded_static']['geometry']['groups']
    sources, meta = source_map(donor)
    healthy = set(meta['healthy_selector_names'])
    if '--states' in sys.argv:
        roof_names = {n for group, names in zip(groups, sources)
                      if group['preview_material'] == 'roof' for n in names}
        for row in meta['selector_table']:
            overlap = roof_names.intersection(row['members'])
            if overlap:
                print('SELECTOR', row['name'], len(overlap), row['conditions'])
        return
    for group, names in zip(groups, sources):
        rows = {}
        for tri, name in zip(group['triangles'], names):
            if name not in healthy:
                continue
            row = rows.setdefault(name, {'triangles': 0,
                                         'minimum': [float('inf')]*3,
                                         'maximum': [float('-inf')]*3})
            row['triangles'] += 1
            for vertex in tri:
                point = group['positions'][vertex]
                for axis in range(3):
                    row['minimum'][axis] = min(row['minimum'][axis], point[axis])
                    row['maximum'][axis] = max(row['maximum'][axis], point[axis])
        print(key, group['name'], group['preview_material'])
        for name, row in sorted(rows.items(), key=lambda r: -r[1]['triangles'])[:30]:
            lo = [round(v, 2) for v in row['minimum']]
            hi = [round(v, 2) for v in row['maximum']]
            print(' ', name, row['triangles'], lo, hi)


if __name__ == '__main__':
    main()
