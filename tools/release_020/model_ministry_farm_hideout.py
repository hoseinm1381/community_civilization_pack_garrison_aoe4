"""Build editable 0.2.0 Ministry or visual-only farm edge in owned paths.

Usage (dedicated Blender process): blender -b --factory-startup --python this_file -- ministry|farm|shelter_default|shelter_stone
Neither recipe edits gameplay, native stamps, the central rice resource animator, or 0.1.0.
"""
import bpy
import hashlib
import math
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_ministry_farm_hideout_runner import (box, export_building, faceted_vessel,
    gable, hipped_tile_roof, join_stage, mesh, render_views, sha, validate, write)

ROOT = Path(__file__).resolve().parents[2]
name = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "ministry"
assert name in ("ministry", "farm", "shelter_default", "shelter_stone")
family=ROOT/"art/authoring/buildings_020"
export_family=ROOT/"art/exports/buildings_020"
source = family/"hideout"/name if name.startswith("shelter_") else family/name
target = export_family/"hideout"/name if name.startswith("shelter_") else export_family/name
out = ROOT / "output/release_020/ministry_farm_hideout" / name
for path in (source, target, out): path.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def atlas():
    """Shared, native-friendly 512 square atlas; all source maps retained and packed."""
    import numpy as np
    colors = [(0.40,.245,.175),(.275,.175,.105),(.38,.145,.105),(.63,.59,.47),
              (.33,.255,.155),(.22,.32,.29),(.29,.39,.17),(.46,.31,.15)]
    rng = np.random.default_rng(20842 if name == "ministry" else 20843)
    yy, xx = np.mgrid[0:512,0:512]
    noise = rng.normal(0,.018,(512,512))
    grain = np.sin(xx*.19+np.sin(yy*.025))* .012
    rgba = np.ones((512,512,4), dtype=np.float32)
    for i, color in enumerate(colors):
        col,row=i%4,i//4
        sl=np.s_[row*256:(row+1)*256,col*128:(col+1)*128]
        tile_noise=noise[sl]+grain[sl]
        lx=xx[sl]-col*128;ly=yy[sl]-row*256
        if i==0:
            brick_row=ly//18
            mortar=(ly%18<2)|((lx+18*(brick_row%2))%36<2)
            tile_noise += np.where(mortar,-.09,.012)+np.sin(lx*.13)*.012
        if i==2:
            tile_row=ly//11
            channel=((lx+4*(tile_row%2)+.6*np.sin(ly*.09))%9<1.2)
            overlap=(ly%11<1.2)
            tile_noise += np.where(channel,-.07,.015)+np.where(overlap,-.033,0)
            tile_noise += np.sin(lx*.40+ly*.055)*.009
        if i==1: tile_noise += np.sin(xx[sl]*.40+np.sin(yy[sl]*.03))*.02
        if i==5: tile_noise += np.sin(xx[sl]*.07+yy[sl]*.08)*.02
        for channel in range(3): rgba[sl+(channel,)] = np.clip(color[channel]+tile_noise,0,1)
    image=bpy.data.images.new("CCP_020_shared_albedo",width=512,height=512,alpha=True)
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw=str(source/"albedo.png");image.file_format="PNG";image.save();image.pack()
    for tex, color in (("normal",(.5,.5,1,1)),("roughness",(.82,.82,.82,1)),("metalness",(0,0,0,1))):
        img=bpy.data.images.new("CCP_020_"+tex,width=16,height=16,alpha=False)
        img.generated_color=color;img.colorspace_settings.name="Non-Color"
        img.filepath_raw=str(source/(tex+".png"));img.file_format="PNG";img.save();img.pack()
    material=bpy.data.materials.new("ccp_020_neutral_atlas")
    material.use_nodes=True
    shader=material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value=.85
    tex=material.node_tree.nodes.new("ShaderNodeTexImage");tex.image=image
    material.node_tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])
    for tex in ("albedo","normal","roughness","metalness"):
        shutil.copy2(source/(tex+".png"),target/(tex+".png"))
    return material


MAT=atlas()
base=[];superstructure=[];contacts=[]
def add(part, phase=20):
    (base if phase==0 else superstructure).append(part)
    return part


def beam(name, a, b, thickness, tile="timber", phase=20):
    # Rectangular horizontal or vertical member: the endpoints meet actual
    # module planes, then the box overlaps those faces by half its thickness.
    p=[(a[i]+b[i])/2 for i in range(3)]
    d=[abs(a[i]-b[i])+thickness for i in range(3)]
    return add(box(name,p,d,MAT,tile),phase)


def ministry():
    # Ratios: main roof width/depth 6.25/5.25, eave/ridge height 3.2/4.45.
    # Its 7.8 by 7.8 visual envelope stays inside the existing 8x8 placement.
    # The arrangement is interpretation, not a reconstruction of Kinh Thien.
    plinth_top=.26
    add(box("Brick_raised_civic_plinth",(0,.65,plinth_top/2),(6.15,5.85,plinth_top),MAT,"brick"),0)
    add(box("Packed_yard_base",(-2.65,-2.60,.055),(2.25,2.35,.11),MAT,"earth"),0)
    add(box("Storage_brick_threshold",(2.62,-2.18,.10),(2.25,2.45,.20),MAT,"brick"),0)
    # Hall wall and open south-facing veranda. Front openings remain readable.
    wall_bottom=plinth_top-.025
    wall_top=3.02
    wall_center=(wall_bottom+wall_top)/2
    wall_height=wall_top-wall_bottom
    column_height=2.70
    column_bottom=plinth_top-.04
    column_center=column_bottom+column_height/2
    add(box("Hall_back_plaster",(0,3.35,wall_center),(5.45,.20,wall_height),MAT,"plaster"))
    for side in (-1,1):
        for index,(ya,yb) in enumerate(((-.75,-.10),(.50,1.80),(2.40,3.45))):
            add(box(f"Hall_side_wall_{side}_{index}",(side*2.65,(ya+yb)/2,wall_center),
                    (.18,yb-ya,wall_height),MAT,"plaster"))
        for index,(ya,yb) in enumerate(((-.10,.50),(1.80,2.40))):
            add(box(f"Hall_vent_lower_{side}_{index}",(side*2.65,(ya+yb)/2,(wall_bottom+1.56)/2),
                    (.18,yb-ya,1.56-wall_bottom),MAT,"plaster"))
            add(box(f"Hall_vent_header_{side}_{index}",(side*2.65,(ya+yb)/2,(2.07+wall_top)/2),
                    (.18,yb-ya,wall_top-2.07),MAT,"plaster"))
            # Recessed dark bed and three timber louvers inside a real wall gap.
            inset_x=side*2.56
            add(box(f"Hall_vent_bed_{side}_{index}",(inset_x,(ya+yb)/2,1.815),
                    (.035,yb-ya-.08,.44),MAT,"timber"))
            for slat,z in enumerate((1.66,1.82,1.98)):
                add(box(f"Hall_vent_louver_{side}_{index}_{slat}",(side*2.68,(ya+yb)/2,z),
                        (.055,yb-ya-.08,.055),MAT,"timber"))
        for y in (-.72,1.16,3.18):
            add(box(f"Hall_timber_pilaster_{side}_{y:+.2f}",(side*2.76,y,column_center),
                    (.14,.15,2.70),MAT,"timber"))
    # Recessed office door between framed, screened bays. The wall is assembled
    # around the opening; the leaf is set behind its front plane.
    for side in (-1,1):
        add(box("Office_bay_wall_"+str(side),(side*1.71,-.94,.69),(1.87,.18,.91),MAT,"plaster"))
        for x in (side*1.03,side*1.67,side*2.31):
            add(box(f"Office_screen_post_{x:+.2f}",(x,-.94,1.93),(.10,.13,1.60),MAT,"timber"))
        for z in (1.24,2.12,2.68):
            add(box(f"Office_screen_lath_{side}_{z:.2f}",(side*1.70,-.94,z),(1.87,.13,.09),MAT,"timber"))
    add(box("Office_door_upper_lintel",(0,-.94,2.68),(1.52,.21,.17),MAT,"timber"))
    add(box("Office_recessed_door_leaf",(0,-.77,1.43),(1.25,.075,2.12),MAT,"timber"))
    add(box("Office_door_threshold",(0,-1.03,.29),(1.47,.39,.13),MAT,"brick"))
    for x in (-2.64,-.88,.88,2.64):
        add(box(f"Veranda_column_{x:+.2f}",(x,-1.68,column_center),(.19,.19,column_height),MAT,"timber"))
        contacts.append({"interface":"veranda column to plinth", "column_x":x,
                         "column_bottom":column_bottom,"plinth_top":plinth_top,
                         "signed_gap":column_bottom-plinth_top})
    for x in (-2.65,2.65):
        add(box(f"Hall_back_column_{x:+.2f}",(x,3.28,column_center),(.19,.19,column_height),MAT,"timber"))
    add(box("Veranda_front_lintel",(0,-1.68,3.03),(5.5,.24,.22),MAT,"timber"))
    add(box("Back_lintel",(0,3.28,3.03),(5.5,.24,.22),MAT,"timber"))
    # Broad, gently hipped fired-clay roof with lifted eaves. Closed roof ends
    # avoid the black triangular void of the generic gable blockout.
    add(hipped_tile_roof("Main_broad_tile_roof",(0,.80),6.30,5.40,3.10,1.35,.20,MAT))
    # Eight-sided earthen ridge cap is a real faceted section, not a box strip.
    ridge_verts=[]
    for x in (-2.72,2.72):
        for i in range(8):
            a=math.tau*i/8
            ridge_verts.append((x,.80+math.cos(a)*.115,4.45+math.sin(a)*.115))
    ridge_faces=[tuple(reversed(range(8))),tuple(range(8,16))]
    ridge_faces += [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    add(mesh("Faceted_tile_ridge",ridge_verts,ridge_faces,MAT,"tile"))
    for y,label in ((-1.83,"front"),(3.43,"rear")):
        add(box("Roof_fascia_"+label,(0,y,3.075),(6.1,.14,.16),MAT,"timber"))
        for x in (-2.64,-1.76,-.88,0,.88,1.76,2.64):
            add(box(f"Under_eave_bracket_{label}_{x:+.2f}",(x,y,2.96),(.15,.41,.16),MAT,"timber"))
    for z in (.075,.185):
        for y in (-2.27,3.58):
            add(box(f"Plinth_course_y_{y:.2f}_{z:.2f}",(0,y,z),(6.13,.065,.045),MAT,"brick"),0)
        for x in (-3.10,3.10):
            add(box(f"Plinth_course_x_{x:.2f}_{z:.2f}",(x,.65,z),(.06,5.86,.045),MAT,"brick"),0)
    # Attached storage wing: lower shed-sized roof, timber-framed and vented.
    wing_bottom=.17
    wing_top=2.40
    wing_center=(wing_bottom+wing_top)/2
    wing_height=wing_top-wing_bottom
    add(box("Wing_back_wall",(2.67,-1.02,wing_center),(2.12,.15,wing_height),MAT,"plaster"))
    for side in (-1,1):
        add(box("Wing_side_wall_"+str(side),(2.67+side*1.0,-2.18,wing_center),(.13,2.36,wing_height),MAT,"plaster"))
        add(box("Wing_front_jamb_"+str(side),(2.67+side*.76,-3.35,wing_center),(.55,.14,wing_height),MAT,"plaster"))
    add(box("Wing_front_door_header",(2.67,-3.35,2.21),(.98,.14,.30),MAT,"plaster"))
    add(gable("Wing_tile_roof",(2.65,-2.18),2.55,2.75,2.43,.65,.12,MAT,"tile"))
    add(box("Wing_recessed_door",(2.67,-3.20,1.04),(.78,.055,1.72),MAT,"timber"))
    for x in (1.72,3.58):
        add(box(f"Wing_post_{x:.2f}",(x,-3.27,1.24),(.12,.12,2.12),MAT,"timber"))
    for height in (1.70,1.90,2.10):
        add(box(f"Wing_vent_lath_{height:.2f}",(2.65,-3.42,height),(1.04,.055,.055),MAT,"timber"))
    # Small elephant-handling yard as practical utility: paired hitch rails,
    # open gate, trough and shade screen, with no elephant/animation prop.
    for x in (-3.61,-1.72):
        for y in (-3.67,-1.57):
            add(box(f"Yard_post_{x:.2f}_{y:.2f}",(x,y,.68),(.14,.14,1.30),MAT,"timber"))
    for y in (-3.67,-1.57):
        beam(f"Yard_long_rail_{y:.2f}",(-3.61,y,.90),(-1.72,y,.90),.11)
    beam("Yard_west_rail",(-3.61,-3.67,.90),(-3.61,-1.57,.90),.11)
    add(box("Stone_water_trough",(-2.55,-2.42,.22),(1.05,.40,.28),MAT,"brick"))
    add(box("Trough_water",(-2.55,-2.42,.36),(.89,.28,.025),MAT,"water"))
    add(box("Veranda_ledger_counter",(-1.82,-1.16,.82),(1.05,.42,.14),MAT,"timber"))
    for x in (-2.23,-1.40):
        add(box(f"Counter_leg_{x:.2f}",(x,-1.16,.50),(.11,.36,.53),MAT,"timber"))
    for index,(x,y,scale) in enumerate(((3.41,-2.77,1),(3.22,-1.76,.78))):
        profile=[(0,.18*scale),(.06*scale,.25*scale),(.31*scale,.29*scale),
                 (.48*scale,.20*scale),(.52*scale,.15*scale)]
        add(faceted_vessel(f"Storage_grain_jar_{index}",(x,y,.20),profile,MAT,"thatch",10))
    for label,gap in (("veranda column/lintel",column_bottom+column_height-(3.03-.11)),
                      ("hall wall/plinth",wall_bottom-plinth_top),
                      ("wing wall/threshold",wing_bottom-.20),
                      ("wing wall/roof",(2.43-.12)-wing_top),
                      ("yard posts/earth",(.68-1.30/2)-.11),
                      ("water trough/earth",(.22-.28/2)-.11)):
        contacts.append({"interface":label,"signed_gap":gap})
    assert max(abs(v.co.x) for o in base+superstructure for v in o.data.vertices)<4.01
    assert max(abs(v.co.y) for o in base+superstructure for v in o.data.vertices)<4.01
    assert all(c["signed_gap"]<=1e-6 for c in contacts),contacts
    return {"design":"Scratch practical civic hall; brick platform, timber veranda, tiled roof, storage wing, small handling yard",
            "ground_footprint":"existing 8x8 source placement; no gameplay collision authored",
            "historical_evidence":"Timber and brick/tile vocabulary is regional archaeological inspiration; arrangement and Ministry form are invention",
            "source":"https://hoangthanhthanglong.vn/en/kinh-thien-palace-the-heart-of-the-imperial-citadel-of-thang-long/"}


def farm():
    # Private visual edge supplement only. Individual outskirts clear on adjacency.
    # Never include central crop rows as harvest/resource-animation replacement.
    add(box("Paddy_edge_earth_contact",(0,0,.045),(2.80,.88,.09),MAT,"earth"),0)
    add(box("Shallow_visual_water",(0,.01,.102),(2.53,.43,.025),MAT,"water"),0)
    for side in (-1,1):
        # Closed sloped earth bank, not a vertical wall or concrete trough.
        section=[(side*.18,.09),(side*.25,.205),(side*.40,.235),(side*.48,.07)]
        vertices=[(x,y,z) for x in (-1.39,1.39) for y,z in section]
        faces=[tuple(reversed(range(4))),tuple(range(4,8))]
        faces += [(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
        add(mesh("Sloped_paddy_bund_"+str(side),vertices,faces,MAT,"earth"))
    for x in (-1.17,-.57,.03,.63,1.23):
        for y in (-.08,.10):
            # Small closed paired leaf wedges to read as irrigated rice, not a
            # dense replacement for the functional central crop animator.
            verts=[(x-.025,y-.018,.115),(x+.025,y-.018,.115),(x+.023,y+.018,.115),
                   (x-.023,y+.018,.115),(x-.012,y,.37),(x+.012,y,.37)]
            faces=[(3,2,1,0),(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
            add(mesh(f"Rice_edge_pair_{x:+.2f}_{y:+.2f}",verts,faces,MAT,"rice"))
    assert all(-.001<=v.co.z<.5 for obj in base+superstructure for v in obj.data.vertices)
    return {"design":"2.8m low embankment, shallow visual water and sparse edge rice",
            "target":"Private additions to four native rice-farm clearable outskirts; center rice resource animator and central terrain stamp unchanged",
            "bounds_policy":"segment <0.5m high and no authored collision, harvest or terrain change",
            "qualitative_change":"Original central rice remains visible; boundary appearance varies with adjacent farms"}


def shelter(stone):
    # Additive visual-only structure in each official outpost's local coordinates.
    # Keep the front central ladder/access corridor open and native lookout roof
    # in place near the weapon origin. Stone version is a larger screened apron.
    half_x=1.60 if not stone else 2.28
    back_y=1.53 if not stone else 2.15
    front_y=-1.53 if not stone else -2.15
    floor_z=.03 if not stone else .06
    top_z=2.35 if not stone else 3.25
    post_width=.14 if not stone else .18
    center_y=(front_y+back_y)/2
    for x in (-half_x,half_x):
        for y in (front_y,back_y):
            add(box(f"Shelter_corner_post_{x:+.2f}_{y:+.2f}",
                    (x,y,(floor_z+top_z)/2),(post_width,post_width,top_z-floor_z),MAT,"timber"))
    # Continuous low screen wall: one prototype bay pattern, repeated along
    # measured side spans. The solid lower panel seats in the same post plane.
    for side in (-1,1):
        x=side*half_x
        add(box(f"Side_earth_footing_{side}",(x,center_y,.13),
                (.19,back_y-front_y,.22),MAT,"earth"),0)
        add(box(f"Side_screen_sill_{side}",(x,center_y,.63),
                (.13,back_y-front_y,.15),MAT,"timber"))
        add(box(f"Side_screen_header_{side}",(x,center_y,top_z-.30),
                (.16,back_y-front_y,.17),MAT,"timber"))
        for i in range(9):
            y=front_y+(back_y-front_y)*(i+.5)/9
            add(box(f"Side_vertical_screen_{side}_{i:02}",(x,y,(.69+top_z-.32)/2),
                    (.075,.07,top_z-1.01),MAT,"timber"))
    add(box("Rear_screen_earth_footing",(0,back_y,.13),(half_x*2,.19,.22),MAT,"earth"),0)
    add(box("Rear_screen_sill",(0,back_y,.63),(half_x*2,.14,.15),MAT,"timber"))
    add(box("Rear_screen_header",(0,back_y,top_z-.30),(half_x*2,.15,.17),MAT,"timber"))
    for i in range(10):
        x=-half_x+(half_x*2)*(i+.5)/10
        add(box(f"Rear_vertical_screen_{i:02}",(x,back_y,(.69+top_z-.32)/2),
                (.07,.075,top_z-1.01),MAT,"timber"))
    # Front leaves a central opening wide enough to keep the existing ladder
    # and lower access readable. Its side panels screen the shelter, not combat.
    gap=.78 if not stone else 1.00
    for side in (-1,1):
        width=half_x-gap
        x=side*(gap+width/2)
        add(box(f"Front_lower_panel_{side}",(x,front_y,.60),(width,.12,.87),MAT,"timber"))
        add(box(f"Front_screen_header_{side}",(x,front_y,top_z-.30),
                (width,.13,.17),MAT,"timber"))
        for i in range(3 if not stone else 5):
            px=side*(gap+width*(i+.5)/(3 if not stone else 5))
            add(box(f"Front_screen_slat_{side}_{i}",(px,front_y,(1.06+top_z-.35)/2),
                    (.07,.07,top_z-1.41),MAT,"timber"))
    # A restrained small canopy over lower screens. Existing stock lookout
    # remains the top silhouette and its weapon marker is never translated.
    canopy_depth=(back_y-front_y)+.36
    canopy_rise=.38 if not stone else .45
    add(gable("Low_screen_canopy",(0,center_y),half_x*2+.37,canopy_depth,
              top_z-.03,canopy_rise,.12,MAT,"thatch"))
    add(box("Canopy_front_fascia",(0,front_y-.16,top_z-.04),
            (half_x*2+.34,.13,.16),MAT,"timber"))
    lift=0.0
    for obj in base+superstructure:
        for vertex in obj.data.vertices:vertex.co.z+=lift
        obj.data.update()
    assert all(abs(v.co.x)<(1.9 if not stone else 2.6) for o in base+superstructure for v in o.data.vertices)
    assert all(v.co.z<(2.75 if not stone else 3.75) for o in base+superstructure for v in o.data.vertices)
    assert min(v.co.z for o in base+superstructure for v in o.data.vertices)>=0
    return {"design":"Visual-only timber screened shelter below retained native lookout",
            "variant":"stone" if stone else "default",
            "local_height_interval":[0,lift+top_z+canopy_rise],
            "native_contract":"Native model, original weapon origin, layout_outpost and stamp gameplay remain integration-owned",
            "visual_binding":"Second private VisualStampBlueprint only after two-visual native compilation is qualified",
            "source":"Official Chinese outpost geometry defines scale; timber vernacular shelter is interpretation"}


notes = ministry() if name == "ministry" else farm() if name == "farm" else shelter(name=="shelter_stone")
if name=="ministry":
    # Garrison converts Blender Y to negative native Z. The unchanged native
    # principal stamp rotates 180 degrees about Y and then adds Z=1.881305.
    # Shifting source Y by -1.812 gives native-local Z +1.812 and centers the
    # final building at world Z approximately zero without moving markers.
    for part in base+superstructure:
        for vertex in part.data.vertices:vertex.co.y-=1.812
        part.data.update()
    notes["geometry_only_blender_y_shift_m"]=-1.812
    notes["expected_native_local_z_shift_m"]=1.812
    notes["principal_stamp_transform_unchanged"]={"translation_z_m":1.881305,"rotation_y_degrees":180}
objects=[join_stage(base,name.title()+"_00_foundation",0),
         join_stage(superstructure,name.title()+"_20_superstructure",20)]
for obj in objects: obj["garrison_building_profile"]="english-house"
collection=bpy.data.collections.new("CCP_020_"+name)
bpy.context.scene.collection.children.link(collection)
for key,val in {"garrison_asset_container":True,"garrison_asset_id":"cc020_"+name,
                "garrison_namespace":"community_civilization_pack",
                "garrison_display_name":"CCP 0.2.0 "+name.title(),
                "garrison_qualified_id":"community_civilization_pack:cc020_"+name,
                "garrison_archetype":"building","garrison_building_profile":"english-house",
                "garrison_building_integration":"script"}.items():collection[key]=val
for obj in objects:
    collection.objects.link(obj)
    for existing in tuple(obj.users_collection):
        if existing != collection: existing.objects.unlink(obj)

geometry=validate(objects)
sys.path.insert(0, r"C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com")
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material
garrison_check=require_valid(objects,bpy.context)
adopt_material(MAT)
manifest=export_building(objects,target)
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version=0
blend=source/(name+".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
render_views(objects,out)
report={"schema":"ccp.020-ministry-farm-art/v1","asset":name,"status":"authored",
        "source_blend":str(blend),"source_sha256":sha(blend),"export_directory":str(target),
        "export_files":{p.name:sha(p) for p in target.iterdir() if p.is_file()},
        "geometry":geometry,"garrison_preflight":garrison_check,"contact_checks":contacts,
        "construction_stages":[0,20],"notes":notes,"native_cook":"not run",
        "native_match":"not run"}
write(out/"validation.json",report)
write(ROOT/"art/recipes/release_020"/(name+"-source.json"),
      {"schema":"ccp.020-art-recipe/v1","generator":str(Path(__file__).resolve()),
       "asset":name,"source":str(blend),"export":str(target),"design":notes,
       "source_sha256":report["source_sha256"],"export_files":report["export_files"]})
print("CCP_020_ART_READY",name,flush=True)
