"""Read-only, compact donor geometry survey for Castle building art."""
from __future__ import annotations

import json
from pathlib import Path

from common import OUT, guarded


def main():
    guarded()
    base = OUT / 'donors/decoded'
    for key in ('monastery03', 'monastery04', 'siege_workshop03',
                'siege_workshop04', 'keep03'):
        paths = list((base / key).glob('*/decoded-static.json'))
        assert len(paths) == 1, (key, paths)
        doc = json.loads(paths[0].read_text(encoding='utf-8'))
        groups = doc['geometry']['groups']
        coords = (p for g in groups for p in g['positions'])
        lo = [float('inf')] * 3
        hi = [float('-inf')] * 3
        for p in coords:
            for axis in range(3):
                lo[axis] = min(lo[axis], p[axis])
                hi[axis] = max(hi[axis], p[axis])
        print(key, 'bounds', [round(v, 3) for v in lo],
              [round(v, 3) for v in hi])
        for group in groups:
            points = group['positions']
            gmin = [min(p[i] for p in points) for i in range(3)]
            gmax = [max(p[i] for p in points) for i in range(3)]
            print(' ', group['name'], group.get('preview_material'),
                  len(points), 'bounds',
                  [round(v, 3) for v in gmin], [round(v, 3) for v in gmax])


if __name__ == '__main__':
    main()
