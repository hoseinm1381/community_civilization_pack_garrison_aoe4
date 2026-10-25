"""Add Garden r2 healthy, damaged, and ruin geometry to the approved scene.

Run only through the claimed, live Blender MCP instance. This script creates
one new, owned collection and never deletes or rewrites the approved blockout.
Its mesh modules share one 2048 object-PBR atlas and remain individually editable.
"""
from pathlib import Path
import math
import random
import bpy
from mathutils import Vector

ROOT = Path("E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison")
SCENE = bpy.data.scenes.get("CCP070_Architecture_Blockouts")
BASE = bpy.data.collections.get("CCP070_Imperial_Garden_Blockout")
NAME = "CCP070_Imperial_Garden_Detailed_r2"
ATLAS = ROOT / "art/exports/buildings_070/garden/textures"
OFFSET = Vector((-15.0, 15.0, 0.0))
CATEGORIES = ("stone", "wood", "plaster", "roof", "water", "clay", "metal", "foliage")
VIEW_COLORS = ((.48,.44,.37,1),(.32,.17,.10,1),(.76,.69,.55,1),
               (.48,.24,.15,1),(.19,.41,.42,1),(.57,.34,.20,1),
               (.29,.31,.30,1),(.25,.43,.25,1))
if SCENE is None or BASE is None or len(BASE.objects) != 39:
    raise RuntimeError("Approved r2 Garden scene/39-object checkpoint is unavailable")
if bpy.context.window.scene != SCENE:
    bpy.context.window.scene = SCENE
if bpy.data.collections.get(NAME):
    raise RuntimeError("Detail r1 already exists; preserve it and use a new revision")
for suffix in ("albedo", "normal", "roughness", "metalness"):
    if not (ATLAS / ("garden_" + suffix + "_2048.png")).is_file():
        raise RuntimeError("Missing Garden PBR source: " + suffix)

detail = bpy.data.collections.new(NAME)
SCENE.collection.children.link(detail)
mat = bpy.data.materials.new("CCP070_Garden_PBR_r2")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial")
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
out.location = (680, 80)
bsdf.location = (390, 80)
mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
for suffix, socket, y in (("albedo", "Base Color", 320),
                          ("roughness", "Roughness", 20),
                          ("metalness", "Metallic", -120)):
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ATLAS / ("garden_" + suffix + "_2048.png")), check_existing=True)
    tex.label = "Garden " + suffix
    tex.location = (-400, y)
    if suffix != "albedo":
        tex.image.colorspace_settings.name = "Non-Color"
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs[socket])
normal_tex = nodes.new("ShaderNodeTexImage")
normal_tex.image = bpy.data.images.load(str(ATLAS / "garden_normal_2048.png"), check_existing=True)
normal_tex.image.colorspace_settings.name = "Non-Color"
normal_tex.location = (-400, -290)
normal_map = nodes.new("ShaderNodeNormalMap")
normal_map.location = (80, -250)
normal_map.inputs["Strength"].default_value = 0.42
mat.node_tree.links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
mat.node_tree.links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])


class Batch:
    def __init__(self, label):
        self.label = label
        self.verts = []
        self.faces = []
        self.face_cats = []

    def add(self, verts, faces, category):
        start = len(self.verts)
        self.verts.extend(tuple(map(float, v)) for v in verts)
        self.faces.extend(tuple(start + i for i in face) for face in faces)
        self.face_cats.extend([category] * len(faces))

    def box(self, loc, size, cat):
        x, y, z = loc
        w, d, h = (v * .5 for v in size)
        v = [(x + sx*w, y + sy*d, z + sz*h)
             for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
             (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        self.add(v, f, cat)

    def cylinder(self, center, radius, height, cat, sides=10):
        x, y, z = center
        v = [(x + radius*math.cos(i*2*math.pi/sides),
              y + radius*math.sin(i*2*math.pi/sides), z + j*height)
             for j in (0, 1) for i in range(sides)]
        f = [tuple(reversed(range(sides))), tuple(range(sides, 2*sides))]
        f += [(i, (i+1)%sides, (i+1)%sides+sides, i+sides)
              for i in range(sides)]
        self.add(v, f, cat)

    def roof_pan(self, center, width, depth, cat):
        x, y, z = center
        # Thin closed fired-clay pan: raised edge ribs, shallow central trough,
        # and a solid exposed end. This is physical tile geometry, not stripes.
        top = [(x+sx*width*.5, y+sy*depth*.5, z+(.07 if sx else 0))
               for sy in (-1, 1) for sx in (-1, 0, 1)]
        lower = [(a, b, c-.045) for a, b, c in top]
        v = top + lower
        f = [(0, 1, 4, 3), (1, 2, 5, 4),
             (6, 9, 10, 7), (7, 10, 11, 8),
             (0, 6, 7, 1), (1, 7, 8, 2),
             (3, 4, 10, 9), (4, 5, 11, 10),
             (0, 3, 9, 6), (2, 8, 11, 5)]
        self.add(v, f, cat)

    def small_tree(self, x, y, height, canopy):
        trunk = height * .56
        self.cylinder((x, y, 0), .115, trunk, "wood", 9)
        sides = 9
        rings = ((trunk*.80, canopy*.36),
                 (trunk+.10, canopy*.81),
                 (height-.26, canopy),
                 (height, canopy*.47))
        v = [(x+r*math.cos(i*2*math.pi/sides),
              y+r*math.sin(i*2*math.pi/sides), z)
             for z, r in rings for i in range(sides)]
        v += [(x, y, height+.11)]
        f = [tuple(reversed(range(sides)))]
        for j in range(len(rings)-1):
            for i in range(sides):
                k = (i+1)%sides
                f.append((j*sides+i, j*sides+k,
                          (j+1)*sides+k, (j+1)*sides+i))
        f += [(3*sides+i, 3*sides+(i+1)%sides, len(v)-1)
              for i in range(sides)]
        self.add(v, f, "foliage")

    def tube(self, points, radii, cat, sides=8):
        # Continuous section rings keep every bend in one mesh.
        v = []
        for i, pt in enumerate(points):
            tangent = Vector(points[min(i+1, len(points)-1)]) - Vector(points[max(i-1, 0)])
            tangent.normalize()
            ref = Vector((0, 0, 1)) if abs(tangent.z) < .85 else Vector((0, 1, 0))
            a = tangent.cross(ref).normalized()
            b = tangent.cross(a).normalized()
            for j in range(sides):
                angle = 2*math.pi*j/sides
                v.append(Vector(pt) + radii[i]*(a*math.cos(angle)+b*math.sin(angle)))
        f = [tuple(reversed(range(sides)))]
        for i in range(len(points)-1):
            for j in range(sides):
                k = (j+1) % sides
                f.append((i*sides+j, i*sides+k, (i+1)*sides+k, (i+1)*sides+j))
        f.append(tuple(range((len(points)-1)*sides, len(points)*sides)))
        self.add(v, f, cat)

    def slab(self, xy, z, thickness, cat):
        lo = z - thickness
        v = [(x, y, lo) for x, y in xy] + [(x, y, z) for x, y in xy]
        n = len(xy)
        f = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
        f.extend((i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n))
        self.add(v, f, cat)

    def emit(self):
        mesh = bpy.data.meshes.new(NAME + "_" + self.label)
        mesh.from_pydata(self.verts, [], self.faces)
        mesh.update()
        obj = bpy.data.objects.new(NAME + "_" + self.label, mesh)
        detail.objects.link(obj)
        obj.location = OFFSET
        mesh.materials.append(mat)
        uv = mesh.uv_layers.new(name="UVMap")
        color = mesh.color_attributes.new(name="CCP070_Color", type="BYTE_COLOR", domain="CORNER")
        # Each material class occupies one 512x1024 atlas zone. UVs are based
        # on local face coordinates and tiled within the zone at 0.5 units.
        for poly, category in zip(mesh.polygons, self.face_cats):
            ci = CATEGORIES.index(category)
            cx, cy = ci % 4, ci // 4
            normal = poly.normal
            axes = (0, 1) if abs(normal.z) > .7 else ((0, 2) if abs(normal.y) > .7 else (1, 2))
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                u = cx*.25 + .005 + ((co[axes[0]]*.42) % 1)*.24
                v = cy*.5 + .005 + ((co[axes[1]]*.42) % 1)*.49
                uv.data[li].uv = (u, v)
                color.data[li].color = VIEW_COLORS[ci]
        obj["ccp070_category"] = self.label
        return obj


base_foundation = Batch("garrison_part_0000")
base_structure = Batch("garrison_part_0001")
ruins = Batch("garrison_part_0002")
damaged = Batch("garrison_part_0003")
roofs = Batch("garrison_part_0004")
architecture = base_structure
landscape = Batch("garrison_part_0005")
yard = Batch("garrison_part_0006")
for obj in BASE.objects:
    if obj.type != "MESH":
        continue
    key = obj.data.materials[0].name.lower() if obj.data.materials else "stone"
    category = next((c for c in CATEGORIES if key.endswith(c)), "stone")
    local = [tuple(obj.matrix_world @ v.co - OFFSET) for v in obj.data.vertices]
    name = obj.name.lower()
    target = (roofs if "roof" in name or "eave" in name else
              base_foundation if any(word in name for word in ("pond", "path", "threshold", "plinth")) else
              yard if "bridge" in name else
              base_structure)
    target.add(local, [tuple(p.vertices) for p in obj.data.polygons], category)

# Plinth, exposed columns, architrave and staggered brick joint geometry.
for z in (.12, .31, .49):
    architecture.box((-3, 4.8, z), (7.55, 4.75, .055), "stone")
for x in (-6.0, -3.0, 0.0):
    for y in (2.85, 6.75):
        architecture.box((x, y, .59), (.48, .48, .16), "stone")
        architecture.cylinder((x, y, .67), .18, 2.48, "wood", 12)
        architecture.box((x, y, 3.13), (.42, .42, .15), "wood")
        # Cantilever brackets form a visible timber connection under eaves.
        architecture.box((x, y, 3.03), (.92, .19, .17), "wood")
        architecture.box((x, y, 3.13), (.22, .92, .16), "wood")
for y in (2.85, 6.75):
    architecture.box((-3, y, 3.12), (7.35, .18, .20), "wood")
for x in (-6.0, 0.0):
    architecture.box((x, 4.8, 3.12), (.18, 4.15, .20), "wood")
# Lattice bays are set between structural posts; open entrance stays at south.
for side, x in (("W", -6.35), ("E", .35)):
    for y in (3.55, 4.6, 5.65):
        architecture.box((x, y, 2.03), (.08, .06, 1.58), "wood")
    for z in (1.35, 2.05, 2.75):
        architecture.box((x, 4.6, z), (.08, 3.2, .075), "wood")
for y in (3.0, 6.6):
    for x in (-5.4, -4.7, -4.0, -2.0, -1.3, -.6):
        architecture.box((x, y, 2.1), (.055, .07, 1.4), "wood")
# Stable wall is articulated as framed bays rather than a plain box.
for x in (5.3, 7.5, 9.8):
    for y in (7.05, 9.95):
        architecture.cylinder((x, y, 0.0), .13, 2.75, "wood", 10)
for y in (7.04, 9.96):
    architecture.box((7.55, y, 2.55), (5.15, .15, .18), "wood")
for x in (5.2, 10.0):
    architecture.box((x, 8.5, 2.55), (.15, 3.0, .18), "wood")
for x in (5.8, 6.6, 7.4, 8.2, 9.0):
    architecture.box((x, 7.025, 1.87), (.07, .08, 1.30), "wood")

def tile_roof(x, y, width, depth, eave, rise, step=.33):
    # Discrete laid clay pans follow the four declining hip fields. The
    # stepped surface is deliberately above the r2 thick roof, without gaps.
    nx = max(4, round(width/step))
    ny = max(4, round(depth/step))
    for ix in range(nx):
        px = x-width/2+(ix+.5)*width/nx
        for iy in range(ny):
            py = y-depth/2+(iy+.5)*depth/ny
            fx = abs(px-x)/(width/2)
            fy = abs(py-y)/(depth/2)
            distance = max(fx, fy)
            if distance > .96:
                continue
            z = eave + rise*(1-distance) + .095
            roofs.roof_pan((px, py, z), width/nx*.93, depth/ny*.96, "roof")
    roofs.tube([(x-width*.29, y, eave+rise+.10),
                (x, y, eave+rise+.13),
                (x+width*.29, y, eave+rise+.10)], [.12, .14, .12], "clay", 8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            roofs.tube([(x+sx*width*.28, y, eave+rise+.10),
                        (x+sx*width*.43, y+sy*depth*.36, eave+rise*.35+.09),
                        (x+sx*width*.49, y+sy*depth*.48, eave+.31)],
                       [.11, .10, .08], "clay", 8)

tile_roof(-3, 4.8, 8.0, 5.2, 3.2, 1.25, .33)
tile_roof(-3, 4.8, 4.3, 2.5, 4.67, .8, .29)
tile_roof(-3, 8.5, 8.0, 2.6, 2.05, .55, .32)
tile_roof(7.6, 8.5, 5.7, 3.7, 2.72, .85, .32)
for x, y, z in ((-7, 4.8, 3.5), (1, 4.8, 3.5), (-5.15, 4.8, 5.05), (-.85, 4.8, 5.05)):
    roofs.tube([(x, y, z), (x+.12, y, z+.3), (x-.02, y, z+.55)],
               [.16, .12, .025], "clay", 8)

rng = random.Random(70041)
# Two long stepped stone courses establish an actual pond edge and depth.
for inset, z in ((.16, .04), (.43, -.20)):
    for side in (-1, 1):
        landscape.box((-3, -2.8+side*(3-inset), z), (10-2*inset, .21, .12), "stone")
        landscape.box((-3+side*(5-inset), -2.8, z), (.21, 6-2*inset, .12), "stone")
# Lotus pads float at the recessed water level (-0.195 top); no flat texture discs.
for i in range(65):
    x = rng.uniform(-7.4, 1.3)
    y = rng.uniform(-5.0, -.58)
    if abs(x+3) < 1.25:  # clear the bridge and its water shadow
        continue
    radius = rng.uniform(.20, .38)
    points = [(x+radius*math.cos(k*2*math.pi/11),
               y+radius*math.sin(k*2*math.pi/11)) for k in range(10)]
    landscape.slab(points, -.135+rng.uniform(-.02, .02), .025, "foliage")
    if i % 5 == 0:
        landscape.cylinder((x, y, -.15), .045, .22, "foliage", 8)
        for k in range(8):
            a = 2*math.pi*k/8
            p = (x+.18*math.cos(a), y+.18*math.sin(a), .02)
            landscape.tube([(x, y, .04), p, (x+.22*math.cos(a),y+.22*math.sin(a),.14)],
                           [.028, .075, .01], "plaster", 6)
# Curved stepping-stone walk loops around the pond; heights touch ground.
for i in range(31):
    a = 2*math.pi*i/31
    x = -3+7.1*math.cos(a)
    y = -2.8+4.5*math.sin(a)
    if x > 2.2 and y > 2.3:  # preserve yard passage
        continue
    w = rng.uniform(.40, .68)
    xy = [(x+w*math.cos(k*2*math.pi/7), y+w*.69*math.sin(k*2*math.pi/7)) for k in range(7)]
    landscape.slab(xy, .055, .11, "stone")
# Layered earth beds and planted bamboo/low shrubs stay clear of entrance/yard.
for x, y, sx, sy in ((-9.3, 7.4, 1.1, 2.0), (-9.3, -.2, 1.1, 1.4),
                     (1.0, -7.4, 1.7, .9), (0.2, 8.9, 1.2, .9)):
    landscape.box((x, y, .12), (sx, sy, .24), "clay")
    for n in range(5):
        px = x+rng.uniform(-sx*.34, sx*.34)
        py = y+rng.uniform(-sy*.34, sy*.34)
        h = rng.uniform(.8, 1.7)
        landscape.cylinder((px, py, .2), .045, h, "foliage", 7)
        for az in (-1, 1):
            landscape.tube([(px, py, .2+h*.7),
                            (px+az*.28, py+.12, .2+h*.85),
                            (px+az*.48, py+.18, .2+h*.72)],
                           [.04, .035, .004], "foliage", 6)
for x, y, height, canopy in ((-9.25, 8.1, 3.25, .88),
                              (-9.1, 3.5, 2.55, .77),
                              (-9.2, -1.4, 2.8, .83),
                              (-8.45, -8.2, 2.65, .73),
                              (1.15, -8.7, 3.0, .84),
                              (4.25, -7.7, 2.6, .72),
                              (7.9, -7.2, 2.3, .72)):
    landscape.small_tree(x, y, height, canopy)
# The western promenade bends around the pond rather than forming a grid.
for i in range(18):
    y = -7.9+i*.90
    x = -8.65+.22*math.sin(i*.7)
    radius = .38 + .045*(i%3)
    xy = [(x+radius*math.cos(k*2*math.pi/7),
           y+radius*.8*math.sin(k*2*math.pi/7)) for k in range(7)]
    landscape.slab(xy, .055, .11, "stone")
# Low clipped hedges and bamboo clumps fill the broad exposed court edges.
for x, y in ((-6.8, 8.8), (-8.0, 6.7), (-8.0, 1.7), (-9.5, -5.8),
             (-6.9, -8.6), (0.6, -9.0), (3.6, -8.8), (6.0, -8.7),
             (8.9, -6.5), (8.3, -2.5), (5.3, -1.4)):
    landscape.box((x, y, .24), (.96, .62, .19), "clay")
    for j in range(4):
        px=x+(.22 if j%2 else -.22)
        py=y+(.18 if j//2 else -.18)
        landscape.cylinder((px,py,.29), .08, .42+(j%2)*.12, "foliage", 7)

# Bridge rail posts seat on the deck. Low rails preserve the open water view.
for x in (-3.77, -2.23):
    for y in (-6.7, -4.9, -3.1, -1.3, .5, 2.3):
        yard.cylinder((x, y, .55), .075, .77, "wood", 8)
    yard.box((x, -2.2, 1.23), (.12, 9.0, .13), "wood")
    yard.box((x, -2.2, .87), (.08, 9.0, .09), "wood")
    for y in (-6.7, -4.9, -3.1, -1.3, .5):
        # Joined diagonal members create shallow carved lattice in each bay.
        yard.tube([(x,y, .88), (x,y+.9,1.16), (x,y+1.8,.88)],
                  [.026,.032,.026], "wood", 6)
        yard.tube([(x,y,1.16), (x,y+.9,.88), (x,y+1.8,1.16)],
                  [.026,.032,.026], "wood", 6)
for y in (-6.55, -5.9, -5.25, -4.6, -3.95, -3.3, -2.65, -2.0,
          -1.35, -.7, -.05, .6, 1.25, 1.9, 2.5):
    yard.box((-3, y, .59), (1.65, .075, .08), "wood")
# A robust wide east gate opening is kept between y=4 and y=10.
for x, y in ((3.0, 3.4), (10.65, 3.4), (3.0, 10.1)):
    yard.cylinder((x, y, 0), .16, 1.65, "wood", 10)
    yard.box((x, y, 1.67), (.45, .45, .16), "wood")
for z in (.48, 1.08):
    yard.box((6.75, 3.4, z), (7.75, .10, .12), "wood")
    yard.box((3.0, 6.75, z), (.10, 6.75, .12), "wood")
# Yard equipment indicates elephant servicing without inventing a static animal.
yard.box((8.4, 4.9, .35), (2.3, .72, .50), "wood")
yard.box((8.4, 4.9, .63), (2.45, .86, .10), "wood")
for x in (6.15, 9.6):
    yard.cylinder((x, 5.75, 0), .16, 1.35, "wood", 10)
    yard.cylinder((x, 5.75, 1.35), .23, .12, "metal", 10)
for i in range(3):
    yard.box((6.0+i*.72, 9.35, .34), (.62, .62, .68), "clay")

# Native selector contract: 0002 appears alone as persistent ruins, while
# 0003 appears with only 0000 in heavy damage. Both are authored geometry;
# neither may be a renamed healthy module.
ruins.box((-3.0, 4.8, .19), (7.45, 4.65, .38), "stone")
ruins.box((7.6, 8.5, .14), (5.2, 3.25, .28), "stone")
for x, y, sx, sy in ((-10.7, 1.0, .45, 8.2), (-10.7, -7.5, .45, 5.0),
                     (-8.2, 10.8, 6.4, .45), (3.2, -10.8, 8.4, .45),
                     (10.8, -4.5, .45, 7.0), (10.8, 10.3, .45, 1.2)):
    ruins.box((x, y, .38), (sx, sy, .76), "stone")
# A dry, cracked pond outline remains the unmistakable Garden landmark cue.
ruins.box((-3.0, -2.8, -.27), (9.65, 5.65, .16), "clay")
for x in (-7.9, 1.9):
    ruins.box((x, -2.8, -.01), (.24, 6.0, .55), "stone")
for y in (-5.7, .1):
    ruins.box((-3.0, y, -.01), (10.0, .24, .55), "stone")
for x, y, h in ((-5.9, 2.9, 1.1), (-.1, 6.7, 1.65),
                (-5.9, 6.7, .7), (0.0, 2.9, 1.2),
                (5.4, 7.1, .8), (9.8, 9.8, .65)):
    ruins.cylinder((x, y, .38), .19, h, "wood", 9)
for x, y, a in ((-5.0, 4.1, .7), (-2.6, 5.5, -.8),
                (0.2, 3.2, .55), (7.2, 8.0, -.3)):
    ruins.tube([(x-.9,y-.35,.24), (x,y,.35+a*.1),
                (x+.8,y+.4,.17)], [.12,.17,.08], "wood", 8)
for x, y in ((-5.4, 5.6), (-2.0, 3.5), (0.1, 5.8),
             (7.6, 8.5), (-6.0, -4.9), (1.0, -.6)):
    ruins.slab([(x-.42,y-.28),(x+.3,y-.4),(x+.54,y+.2),(x-.24,y+.45)],
               .22, .08, "roof")
for x, y in ((-8.8, 4.7), (-6.4, 1.8), (3.8, -5.0), (9.2, 2.9)):
    ruins.box((x,y,.15),(.76,.47,.30),"stone")

damaged.box((-3.0, 4.8, .28), (7.45, 4.65, .56), "stone")
for x, y, h in ((-5.9,2.9,2.42),(-3.0,2.9,1.15),
                (-.1,2.9,2.52),(-5.9,6.7,2.05),
                (-3.0,6.7,2.6),(-.1,6.7,1.05)):
    damaged.cylinder((x,y,.56),.18,h,"wood",10)
damaged.box((-3.0,6.75,2.83),(6.6,.23,.20),"wood")
damaged.box((-5.6,4.65,2.25),(.20,3.9,.18),"wood")
for x, y in ((-5.7,4.0),(-4.6,5.7),(-2.7,4.7),(-1.0,3.2)):
    damaged.box((x,y,.50),(.85,.47,.16),"roof")
damaged.box((7.6,8.5,.25),(5.2,3.2,.5),"stone")
for x, y, h in ((5.3,7.05,1.4),(9.8,7.05,.9),
                (5.3,9.95,1.6),(9.8,9.95,.75)):
    damaged.cylinder((x,y,.5),.14,h,"wood",9)
for x, y, sx, sy in ((-10.8,-7,.45,6),(-10.8,6,.45,7),
                     (10.8,-4,.45,8),(3,-10.8,8,.45)):
    damaged.box((x,y,.48),(sx,sy,.96),"stone")


# The approved massing remains separately inspectable; this master draws the
# cloned base plus detailed modules, without deleting/rewriting original meshes.
for part in (base_foundation, base_structure, ruins, damaged,
             roofs, landscape, yard):
    part.emit()
old = bpy.data.collections.get("CCP070_Imperial_Garden_Detailed_r1")
if old:
    for obj in old.objects:
        obj.hide_set(True)
        obj.hide_render = True
for obj in BASE.objects:
    obj.hide_set(True)
    obj.hide_render = True
for obj in detail.objects:
    lifecycle_only = obj.name.endswith("garrison_part_0002") or obj.name.endswith("garrison_part_0003")
    obj.hide_set(lifecycle_only)
    obj.hide_render = lifecycle_only
SCENE["ccp070_garden_detail_revision"] = "r2"
SCENE["ccp070_garden_source_blockout"] = "architecture-blockouts-r2.blend"
print({"collection": NAME, "objects": len(detail.objects),
       "triangles": sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in detail.objects),
       "atlas": str(ATLAS)})
