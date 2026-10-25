"""Illustrative rice-farm assembly comparison from exact native edge positions.

The central rice terrain/crop renderer is a deliberately identical procedural
proxy in every view: its actual native strips, splats and resource animator are
unchanged and are not reproduced by this offline scene. Do not call this game
rendering or claim a fixed mesh-percentage change from it.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from model_ministry_farm_hideout_runner import box,mesh,write

ROOT=Path(__file__).resolve().parents[2]
FARM=ROOT/"art/authoring/buildings_020/farm/farm.blend"
GRAPH=ROOT/"output/release_020/inventory/native-graph.json"
OUT=ROOT/"output/release_020/ministry_farm_hideout/farm/context"
OUT.mkdir(parents=True,exist_ok=True)
native=json.loads(GRAPH.read_text(encoding="utf-8"))
edges={k:native["stamps"]["farm_rice_"+k]["visuals"] for k in ("back","front","left","right")}
placements=[]
for side, entries in edges.items():
    for entry in entries:
        if "sagebush_row" not in entry["model"]:continue
        t=entry["transform"]
        placements.append({"side":side,"source_model":entry["model"],
                           "native_visual_id":entry["id"],"xy":[t[4],t[6]],
                           "angle_degrees":90 if side in ("left","right") else 0})
assert len(placements)==5

bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(FARM),link=False) as (a,b):
    b.objects=[n for n in a.objects if n.startswith("Farm_")]
assert len(b.objects)==2
farm_parts=b.objects

def simple_material(label,color):
    m=bpy.data.materials.new(label)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(*color,1)
    m.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.9
    return m

soil=simple_material("Context soil",(.32,.27,.18))
water=simple_material("Context shallow water",(.21,.31,.28))
rice=simple_material("Context rice proxy",(.33,.42,.15))
sage=simple_material("Context native sagebush proxy",(.35,.39,.21))

def link_copy(obj,prefix,position,rotation):
    clone=obj.copy();clone.data=obj.data.copy()
    clone.name=prefix+"_"+obj.name
    bpy.context.scene.collection.objects.link(clone)
    clone.location=position
    clone.rotation_euler.z=rotation
    return clone

def scene_tile(cx,cy,after,clear_shared=None):
    made=[]
    made.append(box(f"Soil_proxy_{cx}_{cy}",(cx,cy,-.08),(11.6,11.6,.16),soil,"earth"))
    made.append(box(f"Central_native_strip_proxy_{cx}_{cy}",(cx,cy,.015),(10.5,10.5,.03),water,"water"))
    # Identical central proxy in before/after; it represents unchanged native
    # terrain strips and crop animation, not their exact renderer geometry.
    for i in range(9):
        y=cy-4.4+i*1.1
        for j in range(11):
            x=cx-4.7+j*.94
            made.append(box(f"Rice_proxy_{cx}_{i}_{j}",(x,y,.19),(.055,.055,.34),rice,"rice"))
    for item in placements:
        if item["side"]==clear_shared:continue
        x,y=item["xy"]
        pos=(cx+x,cy+y,0)
        if after:
            for part in farm_parts:
                made.append(link_copy(part,f"Edge_{cx}_{item['side']}_{item['native_visual_id']}",pos,
                                      math.radians(item["angle_degrees"])))
        else:
            # Old sagebush visual shown as a clearly labeled proxy cluster.
            for i in range(4):
                dx=(i-1.5)*.45
                if item["angle_degrees"]: ox,oy=0,dx
                else: ox,oy=dx,0
                made.append(box(f"Sagebush_proxy_{cx}_{item['native_visual_id']}_{i}",
                    (pos[0]+ox,pos[1]+oy,.24),(.32,.31,.40),sage,"rice"))
    return made

def render(label,tiles,scale,focus):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    objects=[]
    for cx,cy,after,clear in tiles:objects.extend(scene_tile(cx,cy,after,clear))
    scene=bpy.context.scene
    scene.render.engine="CYCLES";scene.cycles.samples=10
    scene.render.resolution_x=1000;scene.render.resolution_y=780
    scene.render.resolution_percentage=100
    scene.view_settings.view_transform="AgX"
    if scene.world is None:scene.world=bpy.data.worlds.new("Context world")
    scene.world.color=(.40,.40,.40)
    light_data=bpy.data.lights.new("Context key","AREA")
    light=bpy.data.objects.new("Context key",light_data)
    scene.collection.objects.link(light)
    light.location=(focus[0]+8,focus[1]-7,16);light_data.energy=5000;light_data.size=13
    cam=bpy.data.objects.new("Context camera",bpy.data.cameras.new("Context camera"))
    scene.collection.objects.link(cam)
    center=Vector((focus[0],focus[1],.15))
    cam.location=center+Vector((1,-1,.95)).normalized()*scale*2
    cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
    scene.camera=cam;scene.render.filepath=str(OUT/(label+".png"))
    bpy.ops.render.render(write_still=True)
    print("FARM_CONTEXT",label,flush=True)

render("isolated-before",[(0,0,False,None)],20,(0,0))
render("isolated-after",[(0,0,True,None)],20,(0,0))
render("adjacent-after",[(0,0,True,"right"),(12,0,True,"left")],32,(6,0))
write(OUT/"context.json",{"schema":"ccp.020-farm-context/v1",
    "status":"illustrative offline composition, not a native game render",
    "native_graph_source":str(GRAPH),"native_positions":placements,
    "unchanged_native_central":"art/stamps/resources/farm_rice_a and art/environment/nat_economy/farm/farm_rice/farm_rice_a resource_animator",
    "central_visual_policy":"same procedural central proxy in every image; exact engine strips/splats and harvest animation are not simulated",
    "before_edges":"native sagebush row proxies at exact visual transforms",
    "after_edges":"authored paddy modules at same transforms",
    "adjacency":"shared right/left edge modules omitted to illustrate existing clearable outskirts behavior",
    "coverage_percent":"qualitative target; no measured mesh or fixed dense-layout percentage"})
