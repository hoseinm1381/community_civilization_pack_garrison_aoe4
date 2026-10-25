"""University scholarly courtyard and restrained stock-building visual remix.

Four decoded stock mesh groups stay byte-identical in their source collection.
This overlay fits the measured L-shaped stock envelope and must not be exported
as a stock replacement until native material/selector retention is qualified.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT=Path("E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison")
exec((ROOT/"tools/release_070/art/detail_core.py").read_text(encoding="utf-8"),globals())
SCENE=bpy.data.scenes.get("CCP070_Architecture_Blockouts")
BASE=bpy.data.collections.get("CCP070_University_Additions_Blockout")
NAME="CCP070_University_Detailed_Overlay_r1"
OFFSET=Vector((15,-15,0))
ATLAS=ROOT/"art/exports/buildings_070/university/textures"
if SCENE is None or BASE is None:
    raise RuntimeError("Approved University blockout unavailable")
stock=[o for o in BASE.objects if o.get("stock_geometry_unchanged")]
if len(stock)!=4 or not all(o.get("stock_geometry_unchanged") for o in stock):
    raise RuntimeError("Four exact decoded stock groups must remain in source")
if bpy.data.collections.get(NAME):
    raise RuntimeError("University detail revision already exists")
for channel in ("albedo","normal","roughness","metalness"):
    if not (ATLAS/("university_"+channel+"_2048.png")).is_file():
        raise RuntimeError("Generate University PBR sources first")
bpy.context.window.scene=SCENE
detail=bpy.data.collections.new(NAME)
SCENE.collection.children.link(detail)
mat=atlas_material("CCP070_University_Overlay_PBR_r1",ATLAS,"university")
parts=[Batch("garrison_part_%04d"%i,detail,mat,OFFSET) for i in range(7)]
court,gate,ruins,damaged,roofs,stonework,joinery=parts

# Preserve the approved forecourt/gateway/stele masses, never the generic stock
# mesh material that was used only for the blockout viewport.
for obj in BASE.objects:
    if obj.type!="MESH" or obj in stock:
        continue
    n=obj.name.lower()
    dst=(court if "forecourt" in n else roofs if "roof" in n else
         stonework if "stele" in n else gate)
    key=obj.data.materials[0].name.lower() if obj.data.materials else "stone"
    category=next((c for c in CATEGORIES if key.endswith(c)),"stone")
    verts=[tuple(obj.matrix_world@v.co-OFFSET) for v in obj.data.vertices]
    dst.add(verts,[tuple(p.vertices) for p in obj.data.polygons],category)

# Dressed scholarly court: stepped stone border, deliberately irregular
# paving slabs, and surface drainage around the clear main access axis.
for x in (.24,5.76):
    court.box((x,-3.55,.20),(.15,4.28,.21),"stone")
for y in (-5.70,-1.45):
    court.box((3,y,.20),(5.45,.15,.21),"stone")
for i in range(8):
    for j in range(7):
        x=.48+i*.72+(.08 if j%2 else 0)
        y=-5.49+j*.56
        if abs(x-3.0)<.75 and y>-4.1:
            continue
        court.slab([(x-.31,y-.24),(x+.30,y-.25),
                    (x+.31,y+.24),(x-.29,y+.25)],.175,.035,"stone")
for x in (.63,5.37):
    for y in (-5.45,-4.2,-2.95,-1.7):
        court.box((x,y,.31),(.26,.36,.17),"stone")

# A sober scholarly gateway: bracket pairs, framed lattice rather than an
# invented 1805 Khuê Văn pavilion, and warm roof-tile crests.
for x in (.8,5.2):
    gate.box((x,-5.3,.34),(.55,.55,.36),"stone")
    gate.cylinder((x,-5.3,.51),.19,2.30,"wood",12)
    gate.box((x,-5.3,2.79),(.53,.53,.18),"wood")
    for side in (-1,1):
        gate.tube([(x,-5.3,2.51),(x+side*.42,-5.3,2.87)],(.07,.07),"wood")
gate.box((3,-5.3,2.72),(5.18,.28,.22),"wood")
gate.box((3,-5.34,2.25),(2.15,.10,.28),"wood")
for x in (1.7,4.3):
    for z in (.85,1.43,2.02):
        gate.box((x,-5.3,z),(.08,.12,.11),"wood")
    for dx in (-.35,0,.35):
        gate.box((x+dx,-5.3,1.52),(.08,.11,1.65),"wood")
for x in [(.25+i*.30) for i in range(19)]:
    for sy in (-1,1):
        for row in range(3):
            y=-5.3+sy*(.22+row*.30)
            z=3.49+.62*(1-abs(y+5.3)/1.0)
            roofs.roof_tile((x,y,z),.29,.30)
for x in [(.26+i*.26) for i in range(22)]:
    roofs.cylinder((x,-5.3,4.08),.08,.12,"roof",8)

# Four stelae each stand on an actual turtle silhouette: body is a low
# elliptical shell, head/legs project in front, and the tablet has a cut apex.
for x in (1.1,4.9):
    for y in (-3.1,-1.85):
        shell=[]
        for z,rx,ry in ((.38,.36,.28),(.50,.44,.33),(.64,.31,.24),(.70,.15,.13)):
            shell.extend((x+rx*math.cos(k*2*math.pi/12),
                          y+ry*math.sin(k*2*math.pi/12),z) for k in range(12))
        faces=[tuple(reversed(range(12)))]
        for ring in range(3):
            for k in range(12):
                nxt=(k+1)%12
                faces.append((ring*12+k,ring*12+nxt,
                              (ring+1)*12+nxt,(ring+1)*12+k))
        faces.append(tuple(range(36,48)))
        stonework.add(shell,faces,"stone")
        stonework.cylinder((x,y-.31,.44),.15,.16,"stone",10)
        for dx in (-.30,.30):
            for dy in (-.21,.21):
                stonework.box((x+dx,y+dy,.24),(.15,.19,.14),"stone")
        stonework.box((x,y,.78),(.49,.29,.16),"stone")
        stonework.box((x,y,1.52),(.39,.20,1.30),"stone")
        stonework.slab([(x-.19,y-.1),(x+.19,y-.1),
                        (x+.11,y+.10),(x-.11,y+.10)],2.21,.09,"stone")
        # Geometric carved text registers without fictitious readable script.
        for line in range(7):
            yy=y-.111
            zz=1.10+line*.12
            stonework.box((x,yy,zz),(.26,.015,.019),"stone")

# Existing building stays recognizable; selected visible roof/screen accents
# alter the silhouette by a bounded qualitative portion while source geometry
# and its native UV data remain intact. Coordinates stay within stock XY bounds.
for y in (1.65,3.15,4.65):
    for x in (-5.25,-3.75,-2.25,-.75):
        joinery.box((x,y,3.27),(1.28,.09,.11),"wood")
        for dx in (-.52,-.26,0,.26,.52):
            joinery.box((x+dx,y,2.69),(.07,.10,1.18),"wood")
for x in (-5.25,-3.75,-2.25,-.75):
    for y in (1.65,4.65):
        joinery.box((x,y,3.44),(.20,.18,.18),"wood")
for y in (1.55,4.8):
    roofs.box((-3.0,y,5.65),(6.5,.09,.08),"roof")
for x in [(-6.0+i*.24) for i in range(26)]:
    for y in (1.70,4.66):
        roofs.roof_tile((x,y,5.77),.22,.25)
for x in (-5.7,-3.0,-.3):
    roofs.tube([(x,3.10,7.40),(x,3.10,7.63),(x+.17,3.10,7.68)],
               (.07,.11,.03),"roof",9)

# Dedicated additional-visual lifecycle geometry. The original native body
# still owns its own stock selectors; these echo only the Vietnamese additions.
ruins.box((3,-3.55,.09),(5.35,4.20,.18),"stone")
for x,y in ((1.1,-3.1),(4.9,-3.1),(1.1,-1.85),(4.9,-1.85)):
    ruins.cylinder((x,y,.24),.28,.19,"stone",12)
    ruins.box((x+.24,y+.13,.34),(.42,.30,.23),"stone")
for x in (.8,5.2):
    ruins.box((x,-5.3,.28),(.52,.52,.56),"stone")
    ruins.cylinder((x,-5.3,.56),.17,.50,"wood",9)
for x,y in ((1.25,-5.3),(3.4,-5.0),(4.55,-5.45)):
    ruins.slab([(x-.38,y-.23),(x+.22,y-.29),
                (x+.43,y+.18),(x-.11,y+.34)],.25,.10,"roof")
damaged.box((3,-3.55,.09),(5.35,4.20,.18),"stone")
for x in (.8,5.2):
    damaged.box((x,-5.3,.34),(.52,.52,.35),"stone")
    damaged.cylinder((x,-5.3,.52),.18,1.93 if x<3 else 1.12,"wood",10)
damaged.box((2.2,-5.3,2.29),(2.96,.21,.16),"wood")
for x,y in ((1.1,-3.1),(4.9,-3.1),(1.1,-1.85),(4.9,-1.85)):
    damaged.cylinder((x,y,.27),.29,.22,"stone",12)
    damaged.box((x,y,.79),(.42,.23,.88 if x<3 else .52),"stone")

for part in parts:
    part.emit()
for obj in BASE.objects:
    if obj not in stock:
        obj.hide_set(True)
        obj.hide_render=True
for obj in stock:
    obj.hide_set(False)
    obj.hide_render=False
for obj in detail.objects:
    hidden=obj.name.endswith("0002") or obj.name.endswith("0003")
    obj.hide_set(hidden)
    obj.hide_render=hidden
SCENE["ccp070_university_stock_groups_preserved"]=len(stock)
SCENE["ccp070_university_overlay_status"]="master only; native stock material binding pending"
print({"collection":NAME,"overlay_parts":len(detail.objects),
       "stock_groups_preserved":len(stock),
       "overlay_triangles":sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in detail.objects)})
