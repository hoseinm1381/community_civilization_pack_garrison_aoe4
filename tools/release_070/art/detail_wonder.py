"""Detailed Kinh Thiên-inspired Wonder master in the approved blockout scene.

The surviving 57:41.5 podium ratio and three stair aisles are documented; the
lost timber hall, tiered roof, ornament, and dragon treatment are interpretive.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT=Path("E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison")
exec((ROOT/"tools/release_070/art/detail_core.py").read_text(encoding="utf-8"),globals())
SCENE=bpy.data.scenes.get("CCP070_Architecture_Blockouts")
BASE=bpy.data.collections.get("CCP070_Kinh_Thien_Wonder_Blockout")
NAME="CCP070_Kinh_Thien_Detailed_r1"
OFFSET=Vector((-15,-15,0))
ATLAS=ROOT/"art/exports/buildings_070/wonder/textures"
if SCENE is None or BASE is None or len(BASE.objects)<25:
    raise RuntimeError("Approved Wonder blockout is unavailable")
if bpy.data.collections.get(NAME):
    raise RuntimeError("Wonder detail revision exists")
for channel in ("albedo","normal","roughness","metalness"):
    if not (ATLAS/("wonder_"+channel+"_2048.png")).is_file():
        raise RuntimeError("Generate Wonder PBR sources first")
bpy.context.window.scene=SCENE
detail=bpy.data.collections.new(NAME)
SCENE.collection.children.link(detail)
mat=atlas_material("CCP070_Kinh_Thien_PBR_r1",ATLAS,"wonder")
parts=[Batch("garrison_part_%04d"%i,detail,mat,OFFSET) for i in range(7)]
foundation,structure,ruins,damaged,roof,ornament,galleries=parts

for obj in BASE.objects:
    if obj.type!="MESH":
        continue
    key=obj.data.materials[0].name.lower() if obj.data.materials else "stone"
    cat=next((c for c in CATEGORIES if key.endswith(c)),"stone")
    n=obj.name.lower()
    dest=(roof if "roof" in n else
          foundation if any(v in n for v in ("podium","stair","path")) else
          galleries if "gallery" in n or "gate" in n else structure)
    vertices=[tuple(obj.matrix_world@v.co-OFFSET) for v in obj.data.vertices]
    dest.add(vertices,[tuple(p.vertices) for p in obj.data.polygons],cat)

# Repeated stone course and corner pilaster geometry traces the podium.
for z in (.16,.40,.64,.88,1.12):
    foundation.box((0,-7.62,z),(21.08,.12,.045),"stone")
    foundation.box((0,7.62,z),(21.08,.12,.045),"stone")
    for x in (-10.48,10.48):
        foundation.box((x,0,z),(.12,15.25,.045),"stone")
for x in (-10.35,-8.1,-5.85,5.85,8.1,10.35):
    foundation.box((x,-7.73,.7),(.16,.16,1.12),"stone")
for y in (-7.45,-5.0,-2.5,0,2.5,5.0,7.45):
    for x in (-10.40,10.40):
        foundation.box((x,y,.64),(.16,.16,1.12),"stone")

# Three dragon stair aisles. Each balustrade's serpent is a continuous
# tapering S-profile tube seated on a carved parapet, with jaw/crest and
# segmented scales. This is authored motif geometry, not final archaeology.
for center in (-5.4,0,5.4):
    for side in (-1,1):
        x=center+side*1.59
        foundation.box((x,-9.05,.42),(.20,3.20,.84),"stone")
        pts=[]
        radii=[]
        for j in range(17):
            t=j/16
            y=-10.54+2.76*t
            z=.22+1.05*t+.12*math.sin(2.5*math.pi*t)
            pts.append((x+side*(.09*math.sin(3*math.pi*t)),y,z))
            radii.append(.115-.055*t)
        ornament.tube(pts,radii,"stone",10)
        for j in range(1,16):
            t=j/16
            xj=x+side*(.09*math.sin(3*math.pi*t))
            yj=-10.54+2.76*t
            zj=.22+1.05*t+.12*math.sin(2.5*math.pi*t)
            ornament.box((xj+side*.09,yj,zj+.09),(.10,.09,.12),"stone")
        ornament.tube([(x,-7.86,1.30),(x+side*.12,-7.68,1.42),
                       (x+side*.21,-7.49,1.36)],(.13,.16,.08),"stone",10)
        ornament.box((x+side*.19,-7.44,1.30),(.33,.20,.07),"stone")
    # Carved stone nosing is visible on all ten steps.
    for j in range(10):
        y=-10.50+j*.30
        z=.12*(j+1)
        foundation.box((center,y-.13,z-.025),(3.04,.06,.055),"stone")

# Hall colonnades sit on dressed plinths; the southern veranda stays open.
for y in (-1.20,5.60):
    for x in (-6.0,-3.0,0,3.0,6.0):
        structure.box((x,y,1.32),(.53,.53,.24),"stone")
        structure.cylinder((x,y,1.43),.20,3.48,"wood",14)
        structure.box((x,y,4.86),(.58,.58,.20),"wood")
        structure.box((x,y,4.76),(1.1,.20,.19),"wood")
    structure.box((0,y,4.72),(12.4,.27,.27),"wood")
for x in (-6,-3,0,3,6):
    structure.box((x,2.2,4.68),(.20,6.8,.20),"wood")
    for y in (-1.2,5.6):
        direction=1 if y<2 else -1
        structure.tube([(x,y,3.78),(x+direction*.55,y+direction*.40,4.62)],
                       (.09,.075),"wood",8)
for x in (-4.5,-1.5,1.5,4.5):
    for z in (2.55,3.55):
        structure.box((x,5.65,z),(2.55,.13,.12),"wood")
    for k in range(7):
        structure.box((x-1.15+k*.38,5.65,3.03),(.075,.13,1.02),"wood")
# Heavy lintel, raised upper-chamber arcade, and gold-toned metal edge plates.
for y in (.0,4.4):
    for x in (-4.45,-2.20,0,2.20,4.45):
        structure.box((x,y,5.48),(.38,.38,.17),"stone")
        structure.cylinder((x,y,5.56),.13,1.34,"wood",12)
    structure.box((0,y,6.95),(9.1,.23,.18),"wood")
for y in (.0,4.4):
    ornament.box((0,y,6.98),(9.2,.07,.055),"metal")
for x in (-4.45,4.45):
    ornament.box((x,2.2,6.98),(.07,4.6,.055),"metal")

# Two roof tiers: explicit individual fired-clay pans are laid on both sides
# of each ridge. The swept eaves of the approved four-hip surfaces remain.
def tiled_tier(cx,cy,width,depth,eave,rise,nx,ny):
    for i in range(nx):
        x=cx-width*.49+(i+.5)*width*.98/nx
        for sign in (-1,1):
            for j in range(ny):
                y=cy+sign*(.25+(j+.5)*(depth*.48-.25)/ny)
                t=min(1,abs(y-cy)/(depth*.52))
                z=eave+rise*(1-t*t)+.09*t*t
                roof.roof_tile((x,y,z),width*.92/nx,depth*.43/ny)
    # Filled ridge cylinder rows give a legible fired-clay crest.
    for i in range(nx+2):
        x=cx-width*.48+i*width*.96/(nx+1)
        roof.cylinder((x,cy,eave+rise-.07),.105,.20,"roof",9)
tiled_tier(0,2.2,12.9,7.15,4.88,1.48,39,11)
tiled_tier(0,2.2,10.55,5.6,6.88,1.28,33,9)
for x in (-8.2,8.2):
    tiled_tier(x,2.0,3.5,7.15,3.78,.87,11,10)
tiled_tier(0,-5.55,5.2,1.9,3.72,.72,17,4)

# Ridge dragon pair face a central sun disc. S-curved necks, open jaws,
# ascending whiskers, scale nodes, and curled tails create readable silhouettes.
sun_x,sun_y,sun_z=0,2.2,8.45
ornament.cylinder((sun_x,sun_y,sun_z-.34),.34,.68,"metal",16)
for a in range(12):
    angle=a*2*math.pi/12
    x=.49*math.cos(angle)
    z=sun_z+.49*math.sin(angle)
    ornament.tube([(0,2.2,sun_z),(x,2.2,z)],(.055,.025),"metal",7)
for side in (-1,1):
    points=[]
    radii=[]
    for j in range(15):
        t=j/14
        x=side*(4.7-3.9*t)
        y=2.2+.10*math.sin(4*math.pi*t)
        z=8.0+.23*math.sin(3*math.pi*t)+.13*t
        points.append((x,y,z))
        radii.append(.12+.065*t)
    ornament.tube(points,radii,"metal",10)
    head=side*.8
    ornament.tube([(head,2.2,8.18),(head-side*.17,2.2,8.43),
                   (head-side*.27,2.2,8.38)],(.18,.17,.095),"metal",10)
    ornament.box((head-side*.34,2.2,8.28),(.29,.25,.07),"metal")
    ornament.tube([(head-side*.26,2.2,8.40),
                   (head-side*.36,2.2,8.65)],(.055,.012),"metal",7)
    for j in range(2,14,2):
        t=j/14
        x=side*(4.7-3.9*t)
        z=8.0+.23*math.sin(3*math.pi*t)+.13*t
        ornament.box((x,2.2,z+.12),(.13,.12,.18),"metal")
    # Upturned corner brackets continue the timber vocabulary at four hips.
    for y in (-1.25,5.65):
        ornament.tube([(side*6.10,y,4.93),(side*6.48,y,5.06),
                       (side*6.68,y,5.28)],(.11,.09,.035),"wood",8)

# Lower galleries receive real balustrades, screen panels and coherent thresholds.
for x in (-8.2,8.2):
    for y in (-1.5,0,2,4,5.5):
        galleries.cylinder((x,y,1.25),.12,2.17,"wood",10)
        galleries.box((x,y,1.26),(.44,.44,.13),"stone")
    for sx in (-1.35,1.35):
        for z in (1.82,2.37):
            galleries.box((x+sx,2, z),(.09,6.35,.10),"wood")
        for y in (-.8,.4,1.6,2.8,4,5.2):
            galleries.box((x+sx,y,2.06),(.08,.08,.62),"wood")
for x in (-2.3,-1.15,1.15,2.3):
    galleries.box((x,-5.55,2.78),(.14,1.65,1.11),"wood")

# Lifecycle-only masters echo the hall and documented podium rather than
# assigning healthy roof or galleries to ruin/damage selectors.
ruins.box((0,0,.60),(21,15.3,1.20),"stone")
for x in (-6,-3,0,3,6):
    ruins.cylinder((x,5.6,1.20),.19,.42+(x%3)*.20,"wood",9)
for x,y in ((-4,1.2),(2.5,3.2),(7.4,-2.4),(-8.0,3.0)):
    ruins.slab([(x-.55,y-.30),(x+.25,y-.42),
                (x+.68,y+.18),(x-.13,y+.55)],1.36,.11,"roof")
for x in (-5.4,0,5.4):
    for i in range(10):
        z=.12*(i+1)
        ruins.box((x,-10.5+.3*i,z*.5),(3,.3,z),"stone")
damaged.box((0,0,.60),(21,15.3,1.20),"stone")
for x in (-6,-3,0,3,6):
    for y in (-1.2,5.6):
        damaged.cylinder((x,y,1.2),.20,3.3 if (x+y)%3 else 1.5,"wood",10)
damaged.box((0,5.6,4.62),(12.2,.22,.20),"wood")
for x in (-8.2,8.2):
    damaged.box((x,2,2.28),(3.1,6.8,2.16),"plaster")
for x in (-5.4,0,5.4):
    for i in range(10):
        z=.12*(i+1)
        damaged.box((x,-10.5+.3*i,z*.5),(3,.3,z),"stone")

for part in parts:
    part.emit()
for obj in BASE.objects:
    obj.hide_set(True)
    obj.hide_render=True
for obj in detail.objects:
    hidden=obj.name.endswith("0002") or obj.name.endswith("0003")
    obj.hide_set(hidden)
    obj.hide_render=hidden
SCENE["ccp070_wonder_detail_revision"]="r1"
SCENE["ccp070_wonder_hall_reconstruction"]="interpretive; surviving podium and stairs are evidenced"
print({"collection":NAME,"parts":len(detail.objects),
       "triangles":sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in detail.objects)})
