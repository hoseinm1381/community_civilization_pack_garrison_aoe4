"""Inspect native source-object intersections with replacement monastery roof."""
from collections import defaultdict
from common import OUT, read
from building_selectors import source_map

for age in (3, 4):
    donor = read(OUT / 'donors/donor-manifest.json')['donors'][f'monastery{age:02}']
    groups = donor['decoded_static']['geometry']['groups']
    names, meta = source_map(donor)
    healthy = set(meta['healthy_selector_names'])
    eave = 3.24 if age == 3 else 4.32
    rise = 2.28 if age == 3 else 2.32
    spans = defaultdict(lambda: [-1e9, 0, 0])
    for group, sources in zip(groups, names):
        if group['preview_material'] != 'extra':
            continue
        for face, name in zip(group['triangles'], sources):
            if name not in healthy:
                continue
            row = spans[name]
            row[1] += 1
            for index in face:
                x, y, z = group['positions'][index]
                roof_z = eave + rise * max(0.0, min(1-abs(x)/4.575,
                                                    1-abs(y-2.32)/3.59))
                row[0] = max(row[0], z-roof_z)
                row[2] = max(row[2], z)
    print('MONASTERY', age)
    for name, (excess, triangles, z) in sorted(spans.items(), key=lambda p: -p[1][0]):
        if excess > .05:
            print(round(excess,2), triangles, round(z,2), name)

donor = read(OUT / 'donors/donor-manifest.json')['donors']['keep03']
groups = donor['decoded_static']['geometry']['groups']
names, meta = source_map(donor)
healthy = set(meta['healthy_selector_names'])
for cx in (-5.43, 5.43):
    for cy in (-5.43, 5.43):
        values = []
        for group, sources in zip(groups, names):
            for face, name in zip(group['triangles'], sources):
                if name not in healthy:
                    continue
                for vertex in face:
                    x, y, z = group['positions'][vertex]
                    if abs(x-cx)<1.6 and abs(y-cy)<1.6:
                        values.append(z)
        values.sort()
        print('KEEP_TOWER',cx,cy,'count',len(values),'top20',
              [round(x,2) for x in values[-20:]],
              'p99',round(values[int(len(values)*.99)],2))
