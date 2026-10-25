"""Detailed Trúng Foundry master, built only in the claimed live Blender scene.

The royal foundry plan is a historically bounded interpretation. Its asymmetry,
open casting lane, low vents, and timber/brick construction retain the approved
blockout silhouette. Part 0002 is ruins; 0003 is heavy damage, never healthy.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT=Path("E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison")
exec((ROOT/"tools/release_070/art/detail_core.py").read_text(encoding="utf-8"),globals())
SCENE=bpy.data.scenes.get("CCP070_Architecture_Blockouts")
BASE=bpy.data.collections.get("CCP070_Trung_Foundaries_Blockout")
NAME="CCP070_Trung_Foundries_Detailed_r1"
OFFSET=Vector((15,15,0))
ATLAS=ROOT/"art/exports/buildings_070/foundry/textures"
if SCENE is None or BASE is None or len(BASE.objects)<10:
    raise RuntimeError("Approved Foundry blockout missing")
if bpy.data.collections.get(NAME):
    raise RuntimeError("Foundry detail revision already exists")
for channel in ("albedo","normal","roughness","metalness"):
    if not (ATLAS/("foundry_"+channel+"_2048.png")).is_file():
        raise RuntimeError("Generate Foundry PBR source first")
bpy.context.window.scene=SCENE
detail=bpy.data.collections.new(NAME)
SCENE.collection.children.link(detail)
mat=atlas_material("CCP070_Foundry_PBR_r1",ATLAS,"foundry")
parts=[Batch("garrison_part_%04d"%i,detail,mat,OFFSET) for i in range(7)]
foundation,structure,ruins,damaged,roof,fixtures,court=parts

# Carry the exact approved massing into semantic healthy selectors.
for obj in BASE.objects:
    if obj.type!="MESH":
        continue
    if any(word in obj.name.lower() for word in
           ("furnace_base", "furnace_hearth", "casting_bed", "work_court")):
        # These approved volumes are replaced by physically open work cavities.
        continue
    local=[tuple(obj.matrix_world@v.co-OFFSET) for v in obj.data.vertices]
    key=obj.data.materials[0].name.lower() if obj.data.materials else "stone"
    category=next((c for c in CATEGORIES if key.endswith(c)),"stone")
    name=obj.name.lower()
    dst=(roof if "roof" in name else
         foundation if any(k in name for k in ("court","base","path","bed")) else
         fixtures if any(k in name for k in ("furnace","chimney","hearth","mould")) else
         structure)
    dst.add(local,[tuple(p.vertices) for p in obj.data.polygons],category)

# Forge hall: exposed columns, low stone sill, braced bays, shutters, crossbeam
# joinery, and a row of three low bronze vent ornaments.
for y in (2.25,7.95):
    for x in (-9.3,-6.9,-4.7,-2.5,-.1):
        structure.box((x,y,.62),(.46,.46,.28),"stone")
        structure.cylinder((x,y,.76),.17,3.11,"wood",12)
        structure.box((x,y,3.91),(.50,.50,.17),"wood")
    structure.box((-4.7,y,3.83),(9.65,.20,.20),"wood")
    structure.box((-4.7,y,2.48),(9.45,.14,.16),"wood")
for x in (-9.3,-6.9,-4.7,-2.5,-.1):
    structure.box((x,5.1,3.88),(.18,5.75,.16),"wood")
    for y in (2.25,7.95):
        direction=1 if y<5 else -1
        structure.tube([(x,y,2.90),(x+.45,y+direction*.5,3.65)],(.075,.075),"wood")
for x in (-7.8,-3.5):
    for z in (1.55,2.18):
        structure.box((x,2.19,z),(1.55,.08,.11),"wood")
    for dx in (-.66,0,.66):
        structure.box((x+dx,2.19,1.85),(.075,.08,1.08),"wood")
for x in (-8.0,-4.7,-1.4):
    roof.cylinder((x,5.1,5.2),.22,.28,"metal",10)

# Roof tile bands follow the two sloping planes. Every row is a genuine curved
# fired-clay pan with side ribs and end thickness, not a flat decal line.
for x in [(-9.45+i*.31) for i in range(31)]:
    for side in (-1,1):
        for row in range(8):
            y=5.1+side*(.33+row*.365)
            t=min(1.0,abs(y-5.1)/3.05)
            z=3.73+1.31*(1-t*t)
            roof.roof_tile((x,y,z),.29,.37)
for x in [(-9.65+i*.27) for i in range(38)]:
    roof.cylinder((x,5.1,5.00),.09,.12,"roof",8)

# Store hall is lower and quieter; shutters, measured racks, and a restrained
# carved fascia distinguish it from the open forge.
for y in (1.8,7.8):
    for x in (4.6,7.1,9.6):
        structure.box((x,y,.52),(.38,.38,.20),"stone")
        structure.cylinder((x,y,.62),.12,2.24,"wood",10)
for x in (5.8,8.3):
    for y in (2.3,7.3):
        structure.box((x,y,1.6),(1.2,.11,.85),"wood")
        for t in range(5):
            structure.box((x-.48+t*.24,y-.08,1.6),(.055,.055,.78),"wood")
for y in (3.2,4.8,6.4):
    fixtures.box((8.5,y,.72),(1.6,.53,.09),"wood")
    for x in (7.75,9.25):
        fixtures.box((x,y,.34),(.08,.54,.68),"wood")
for x in [4.4+i*.32 for i in range(17)]:
    for side in (-1,1):
        for row in range(6):
            y=4.8+side*(.27+row*.48)
            t=min(1.0,abs(y-4.8)/3.1)
            z=2.73+.86*(1-t*t)
            roof.roof_tile((x,y,z),.30,.45)

# The approved work-court outline is reconstructed as closed floor panels
# around two true voids. A lower floor and masonry curb reveal their depth.
pit_rects=((1.625,6.075,-6.38,-4.82),(2.25,5.95,-3.3,-2.1))
xs=sorted({-6.4,9.8,*(v for r in pit_rects for v in r[:2])})
ys=sorted({-9.6,4.6,*(v for r in pit_rects for v in r[2:])})
for a,b in zip(xs,xs[1:]):
    for c,d in zip(ys,ys[1:]):
        mx,my=(a+b)*.5,(c+d)*.5
        if any(x0<mx<x1 and y0<my<y1 for x0,x1,y0,y1 in pit_rects):
            continue
        foundation.box((mx,my,.10),(b-a,d-c,.20),"stone")
# Casting recesses use an actual open rim, four-sided masonry curb, and a
# lower closed floor. They are not black plates covering solid blockout slabs.
for x,y,w,d in ((3.85,-5.6,4.45,1.56),(4.1,-2.7,3.7,1.2)):
    foundation.box((x,y,-.14),(w-.38,d-.34,.16),"clay")
    for sx in (-1,1):
        foundation.box((x+sx*w*.5,y,.16),(.18,d,.30),"stone")
    for sy in (-1,1):
        foundation.box((x,y+sy*d*.5,.16),(w,.18,.30),"stone")
    for i in range(9):
        court.box((x-w*.42+i*w*.105,y,-.02),(.05,d*.63,.04),"clay")

# Two period-scale hearths: arched mouths formed by separate jamb/keystone
# stones, charcoal ledges, segmented squat vents, and bellows with timber arms.
for x in (-6.4,-.8):
    y=-5.2
    fixtures.box((x,y+.92,.65),(2.65,.34,1.30),"stone")
    for sx in (-1,1):
        fixtures.box((x+sx*1.14,y-.21,.67),(.37,2.03,1.34),"stone")
    fixtures.box((x,y-.24,1.28),(2.65,2.10,.25),"stone")
    fixtures.box((x,y-.65,.10),(1.75,1.28,.20),"clay")
    fixtures.box((x,y-1.35,.50),(2.55,.44,.78),"stone")
    for sx in (-1,1):
        fixtures.box((x+sx*.67,y-1.53,1.21),(.43,.46,1.12),"stone")
    fixtures.box((x,y-1.53,1.77),(1.80,.51,.34),"stone")
    fixtures.box((x,y-1.34,.43),(1.16,.12,.17),"metal")
    for i in range(5):
        z=1.65+i*.31
        fixtures.box((x-.80,y+.83,z),(.90-i*.08,.88-i*.07,.28),"stone")
    for z in (2.25,2.61,2.97,3.33):
        fixtures.box((x-.83,y+.84,z),(.63,.61,.055),"clay")
    # Tapered bellows body and lever in the access aisle.
    for shift in (-.19,.19):
        fixtures.slab([(x+1.08,y-.25+shift),(x+2.24,y-.68+shift),
                       (x+2.24,y+.42+shift)],.67,.12,"wood")
    fixtures.cylinder((x+1.08,y+.1,.45),.10,.67,"metal",10)
    fixtures.tube([(x+1.15,y+.12,.97),(x+2.3,y+1.02,1.24)],(.07,.06),"wood")

# Interpreted 17th-century cannon barrel: cast-bronze tapered tube, trunnions,
# mould bed, and separate cooling trough. No modern steel/industrial stack.
def cannon(x,y):
    points=[(x,y-1.05+j*.19,.73) for j in range(12)]
    radii=[.32-.07*j/11 for j in range(12)]
    court.tube(points,radii,"metal",14)
    court.tube([(x,y-1.12,.73),(x,y-.95,.73)],(.39,.39),"metal",14)
    court.tube([(x,y+.92,.73),(x,y+1.06,.73)],(.31,.31),"metal",14)
    for sx in (-1,1):
        court.tube([(x+sx*.28,y-.12,.73),(x+sx*.62,y-.12,.73)],(.12,.12),"metal",10)
        court.box((x+sx*.65,y-.12,.31),(.18,.55,.62),"wood")
cannon(4.4,-5.35)
for y in (-8.2,-7.25):
    court.box((7.8,y,.32),(2.5,.59,.22),"wood")
for i in range(6):
    fixtures.cylinder((8.35,-5.7+i*.53,.17),.19,.73,"clay",12)
for i in range(5):
    fixtures.tube([(-8.8+i*.43,-7.8,.16),(-8.7+i*.43,-6.15,1.2)],(.045,.045),"wood")

# Ruins are an authored persistent collapsed forge with surviving hearth
# mouths and a depressed casting bed; damage retains partial workshop frames.
ruins.box((1.7,-2.5,.09),(16.2,14.2,.18),"stone")
for x,y,w,d in ((-4.7,5.1,10,5.7),(7.1,4.8,5,6)):
    ruins.box((x,y,.18),(w,d,.36),"stone")
for x,y in ((-9.1,2.4),(-5.8,7.7),(-1.3,5.1),(5.4,7.5),(9.2,2.2)):
    ruins.cylinder((x,y,.36),.17,.62+(.5 if x<-3 else 0),"wood",9)
for x in (-6.4,-.8):
    ruins.box((x,-5.2,.47),(2.4,2.7,.92),"stone")
    ruins.box((x,-6.56,1.06),(2.0,.27,.27),"clay")
for x,y in ((-7.2,-2),(-3.5,4.1),(4.0,-5.4),(8.2,5.5)):
    ruins.slab([(x-.6,y-.3),(x+.3,y-.38),(x+.7,y+.3),(x-.1,y+.49)],.27,.12,"roof")
damaged.box((1.7,-2.5,.12),(16.2,14.2,.24),"stone")
for x,y,w,d in ((-4.7,5.1,10,5.7),(7.1,4.8,5,6)):
    damaged.box((x,y,.27),(w,d,.54),"stone")
for x,y,h in ((-9.3,2.25,3.5),(-4.7,2.25,2.0),(-.1,2.25,3.5),
              (-9.3,7.95,2.3),(-4.7,7.95,3.5),(-.1,7.95,1.4)):
    damaged.cylinder((x,y,.54),.16,h,"wood",10)
damaged.box((-4.7,7.95,3.87),(9.4,.18,.17),"wood")
for x in (-6.4,-.8):
    damaged.box((x,-5.2,.61),(2.6,2.9,1.22),"stone")

for part in parts:
    part.emit()
for obj in BASE.objects:
    obj.hide_set(True)
    obj.hide_render=True
for obj in detail.objects:
    hidden=obj.name.endswith("0002") or obj.name.endswith("0003")
    obj.hide_set(hidden)
    obj.hide_render=hidden
SCENE["ccp070_foundry_detail_revision"]="r1"
print({"collection":NAME,"parts":len(detail.objects),
       "triangles":sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in detail.objects)})
