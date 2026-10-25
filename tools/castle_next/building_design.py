"""Measured, native-compatible Northern Dai Viet Castle detail recipes.

The Chinese building remains the complete native lifecycle owner. These pieces
are one extra nonblocking stamp, selected only for construction/healthy/damage.
Coordinates are in the decoded donor's Blender metre frame, with the entrance
facing -Y. No native footprint, attack marker, production exit, or RGO is edited.
"""
from __future__ import annotations

import math

from mathutils import Vector

from model_ministry_farm_hideout_runner import (
    box, faceted_vessel, hipped_tile_roof, join_stage,
)


def build(family, age, material, donor):
    assert (family, age) in {
        ('monastery', 3), ('monastery', 4),
        ('siege_workshop', 3), ('siege_workshop', 4), ('keep', 3),
    }
    assert donor['logical_path'].endswith(f'chi_{family}_control_age{age:02}.rgm')
    groups = donor['decoded_static']['geometry']['groups']
    minimum = [min(p[i] for g in groups for p in g['positions']) for i in range(3)]
    maximum = [max(p[i] for g in groups for p in g['positions']) for i in range(3)]
    stages = {0: [], 40: [], 80: []}
    contacts = []

    def limits(obj):
        points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        return ([min(p[i] for p in points) for i in range(3)],
                [max(p[i] for p in points) for i in range(3)])

    def vertical_contact(parent, child, label):
        parent_lo, _ = limits(parent)
        _, child_hi = limits(child)
        gap = parent_lo[2] - child_hi[2]
        contacts.append({'parent': parent.name, 'child': child.name,
                         'interface': label, 'gap_m': round(gap, 6)})
        assert -.18 <= gap <= .01, contacts[-1]

    def on_pad(pad, child, label):
        _, pad_hi = limits(pad)
        child_lo, _ = limits(child)
        gap = child_lo[2] - pad_hi[2]
        contacts.append({'parent': pad.name, 'child': child.name,
                         'interface': label, 'gap_m': round(gap, 6)})
        assert -.18 <= gap <= .01, contacts[-1]

    def put(obj, stage):
        stages[stage].append(obj)
        return obj

    def block(name, center, dimensions, tile, stage=40):
        assert all(d > 0 for d in dimensions)
        return put(box(name, center, dimensions, material, tile), stage)

    def roof(name, center, width, depth, eave, rise, stage=40):
        assert rise > 0 and eave > 0
        return put(hipped_tile_roof(name, center, width, depth,
                                    eave, rise, .16, material), stage)

    def frame(name, xs, y, bottom, top, depth=.18):
        """One repeatable post-lintel module with exact face contact."""
        assert len(xs) >= 2 and xs == sorted(xs)
        posts = [block(f'{name} post {index}', (x, y, (bottom+top)/2),
                       (.20, depth, top-bottom), 'timber', 0)
                 for index, x in enumerate(xs)]
        lintel = block(f'{name} lintel', ((xs[0]+xs[-1])/2, y, top-.08),
                       (xs[-1]-xs[0]+.38, depth+.04, .16), 'timber', 40)
        for post in posts:
            vertical_contact(lintel, post, 'post top to lintel bottom')
        return posts, lintel

    if family == 'monastery':
        # Truc Lam monastery: a brick entry court, tiled timber teaching hall,
        # sheltered gate, modest bell shrine, and lotus basin. UNESCO identifies
        # Truc Lam's Dai Viet setting and pagoda/temple/shrine ensemble; this is
        # an original game-scale interpretation, not a replica of one monument.
        assert minimum[0] < -5.5 and maximum[0] > 5.5
        assert minimum[1] < -5.9 and maximum[1] > 5.7
        hall_eave = 3.24 if age == 3 else 4.32
        hall_rise = 2.28 if age == 3 else 2.32
        # Thin pavement stays inside the exact native donor plan. Visual only.
        block('brick court centre', (0, -3.15, .025),
              (7.20, 3.90, .05), 'brick', 0)
        for x in (-4.12, 4.12):
            block('courtyard brick edging', (x, -3.15, .11),
                  (.25, 4.30, .22), 'brick', 0)
        hall_posts, _ = frame('three-bay teaching hall',
                              [-3.73, -1.24, 1.24, 3.73],
                              -1.25, .10, hall_eave-.02)
        hall_roof = roof('broad Dai Viet hall tiled hip', (0, 2.32),
                         9.15, 7.18, hall_eave, hall_rise)
        # Front eave underside meets the measured post tops. The pitched roof
        # is continuous, closed and visibly supported by the entire beam line.
        for post in hall_posts:
            post_lo, post_hi = limits(post)
            x = (post_lo[0]+post_hi[0])/2
            bottom_vertices = hall_roof.data.vertices[len(hall_roof.data.vertices)//2:]
            edge = [v.co for v in bottom_vertices if abs(v.co.y + 1.27) < 1e-4]
            nearest = min(edge, key=lambda v: abs(v.x-x))
            gap = nearest.z-post_hi[2]
            contacts.append({'parent': hall_roof.name, 'child': post.name,
                             'interface': 'front eave underside to post top',
                             'gap_m': round(gap, 6),
                             'sample_x_error_m': round(abs(nearest.x-x), 6)})
            assert -.08 <= gap <= .08, contacts[-1]
        block('hall ridge', (0, 2.32, hall_eave+hall_rise+.035),
              (6.70, .14, .09), 'tile', 80)
        # Entry remains open between the central gateway columns.
        frame('open monastery gate', [-2.37, 2.37], -4.85, .04, 2.52)
        roof('entry gate terracotta hip', (0, -4.83),
             5.30, 1.58, 2.49, .68)
        for x in (-1.80, 0, 1.80):
            block('carved hall screen', (x, -1.09, 2.02),
                  (.11, .11, 2.32), 'timber', 80)
        # Side shrines sit at the court edges and do not close the gate axis.
        shrine_x = 3.93
        bell_pad = block('bell shrine brick pad', (shrine_x, -2.35, .19),
                         (1.38, 1.42, .38), 'brick', 0)
        for x in (shrine_x-.56, shrine_x+.56):
            bell_post = block('bell shrine timber post', (x, -2.35, 1.37),
                              (.15, .15, 1.98), 'timber', 40)
            on_pad(bell_pad, bell_post, 'post bottom to pad top')
        roof('bell shrine miniature tile roof', (shrine_x, -2.35),
             1.72, 1.78, 2.18, .48)
        put(faceted_vessel('hanging faceted bell',
                           (shrine_x, -2.35, 1.04),
                           [(0,.17), (.14,.27), (.61,.31), (.74,.22)],
                           material, 'timber', sides=12), 80)
        basin_x = -3.75
        basin_pad = block('lotus basin stone plinth', (basin_x, -2.38, .12),
                          (1.26, 1.26, .24), 'plaster', 0)
        basin = put(faceted_vessel('lotus basin', (basin_x, -2.38, .24),
                                   [(0,.49), (.23,.57), (.30,.55), (.32,.43)],
                                   material, 'water', sides=12), 80)
        on_pad(basin_pad, basin, 'basin bottom to plinth top')
        for i in range(8):
            a = 2*math.pi*i/8
            block(f'lotus petal {i}',
                  (basin_x+.34*math.cos(a), -2.38+.34*math.sin(a), .61),
                  (.19, .19, .18), 'plaster', 80)

    elif family == 'siege_workshop':
        assert minimum[0] < -5.8 and maximum[0] > 4.8
        assert minimum[1] < -5.19 and maximum[1] > 4.84
        eave = 4.56 if age == 3 else 5.39
        # Four-bay workshop canopy: the central 4.2-metre exit is open.
        frame('open siege assembly arcade', [-4.34, -2.25, 2.25, 4.34],
              -3.92, -.02, eave-.15)
        roof('weathered siege assembly tiled canopy', (-.05, -2.97),
             9.25, 3.02, eave, .58)
        block('assembly roof ceramic ridge', (-.05, -2.97, eave+.61),
              (7.28, .13, .12), 'tile', 80)
        # Screens and racks attach to the outer side bays; no centre blocker.
        for side in (-1, 1):
            x = side*4.35
            for y in (-1.75, .10, 1.95):
                block('workshop side upright', (x, y, 1.28),
                      (.14, .15, 2.52), 'timber', 40)
                block('workshop slatted side shutter',
                      (x-side*.09, y+.52, 1.72),
                      (.08, .93, .92), 'thatch', 80)
            block('outer siege stock rack', (side*3.62, -3.50, .65),
                  (.84, .32, 1.28), 'timber', 80)
        for x in (-3.56, 3.56):
            block('brick pier shoe', (x, -3.92, .26),
                  (.55, .62, .52), 'brick', 0)
        if age == 4:
            block('imperial carved workshop fascia', (-.05, -4.48, 4.29),
                  (5.82, .14, .31), 'timber', 80)

    else:  # keep03: stock shell, towers and attack markers remain untouched.
        assert minimum[0] < -8.4 and maximum[0] > 7.9
        assert minimum[1] < -7.9 and maximum[1] > 8.4
        # The native towers already have complete, differently elevated roofs.
        # Preserve their functional silhouette; the new gate canopy and low
        # wall courses regionalize the roofline without suspended tower caps.
        # The source gate/stair faces -X, as established in the six stock
        # orthographic views. Its central passage remains open.
        gate_cheeks = [block('gate brick cheek', (-7.12, y, 2.03),
                             (.43, .47, 4.06), 'brick', 0)
                       for y in (-2.90, 2.90)]
        gate_lintel = block('gate timber lintel', (-7.12, 0, 4.10),
                            (.52, 6.18, .28), 'timber', 40)
        for cheek in gate_cheeks:
            vertical_contact(gate_lintel, cheek,
                             'cheek top to lintel bottom')
        gate_roof = roof('open gate Dai Viet tiled hip', (-7.10, 0),
                         6.92, 1.70, 4.24, .72)
        for vertex in gate_roof.data.vertices:
            dx, dy = vertex.co.x + 7.10, vertex.co.y
            vertex.co.x, vertex.co.y = -7.10-dy, dx
        gate_roof.data.update()
        for side in (-1, 1):
            x = side*6.75
            block('keep masonry belt', (x, -3.05, 6.79),
                  (.22, 6.06, .30), 'brick', 80)
            for y in (-5.46, -3.28, -1.10):
                block('keep timber bracket', (x-side*.11, y, 6.98),
                      (.28, .32, .50), 'timber', 80)

    assert all(-.18 <= c['gap_m'] <= .08 for c in contacts), contacts
    objects = [join_stage(stages[stage],
                          f'vn_{family}_age{age:02}_castle_detail_{stage}', stage)
               for stage in (0, 40, 80)]
    return objects, {'interfaces': contacts,
                     'entrance_axis': '-X' if family == 'keep' else '-Y',
                     'donor_bounds_m': {'minimum': minimum, 'maximum': maximum},
                     'native_markers': 'untouched; detail export is visual only'}
