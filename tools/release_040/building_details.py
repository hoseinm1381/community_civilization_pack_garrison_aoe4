"""Private Vietnamese facade compounds for the four active building families.

Run only in the serialized, factory-startup Blender slot. The original remodeled
donor remains a separate native stamp; this script exports just the new geometry.
"""
import bpy
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/release_020"))
from model_ministry_farm_hideout_runner import box, mesh, hipped_tile_roof, join_stage, validate, export_building, write
sys.path.insert(0, r"C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com")
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material

assert bpy.app.background and not bpy.data.filepath
arg = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "all"
FAMILIES = ("blacksmith", "stable", "archery_range", "market")
jobs = [(f, a) for f in FAMILIES for a in (2, 3, 4) if arg == "all" or arg in (f, f"{f}:{a}")]
assert jobs, arg
BASE = ROOT / "art/authoring/buildings_040"
EXPORT = ROOT / "art/exports/buildings_040"
OUT = ROOT / "output/release_040/buildings/details"
DONORS = json.loads((ROOT / "art/recipes/release_040/buildings-donors.json").read_text(encoding="utf8"))["models"]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def atlas(family, source, target):
    """One deterministic weathered 4x2 atlas, matching the stock Garrison helper UVs."""
    import numpy as np
    palette = [(.40,.22,.15),(.27,.19,.13),(.44,.23,.15),(.49,.46,.38),
               (.36,.34,.27),(.17,.25,.23),(.24,.32,.17),(.50,.40,.25)]
    size=512; yy,xx=np.mgrid[0:size,0:size]
    rng=np.random.default_rng(400 + FAMILIES.index(family))
    grain=rng.normal(0,.026,(size,size))+np.sin(xx*.071)*.012+np.sin(yy*.047)*.012
    arr=np.ones((size,size,4),np.float32)
    rough=np.ones((size,size,4),np.float32);rough[:,:,:3]=.86
    for index,color in enumerate(palette):
        col,row=index%4,index//4
        sl=np.s_[row*256:(row+1)*256,col*128:(col+1)*128]
        u=xx[sl]-col*128;v=yy[sl]-row*256
        g=grain[sl].copy()
        if index==0:g+=np.where((v%18<2)|((u+12*((v//18)%2))%40<2),-.075,.01)
        if index==1:g+=np.sin(u*.24+np.sin(v*.035))*.025
        if index==2:g+=np.where((v%17<2)|((u+8*((v//17)%2))%14<2),-.065,.012)
        if index==7:g+=np.sin(u*.31)*.015
        for c in range(3):arr[sl+(c,)]=np.clip(color[c]+g,0,1)
    def save(label,data,noncolor=False):
        im=bpy.data.images.new(f"CCP040_{family}_{label}",width=size,height=size,alpha=True)
        im.pixels.foreach_set(data.ravel())
        if noncolor: im.colorspace_settings.name="Non-Color"
        im.filepath_raw=str(source/(label+".png"));im.file_format="PNG";im.save();im.pack()
        shutil.copy2(source/(label+".png"),target/(label+".png"))
        return im
    albedo=save("albedo",arr)
    save("roughness",rough,True)
    for label,color in (("normal",(.5,.5,1,1)),("metalness",(0,0,0,1))):
        image=bpy.data.images.new(f"CCP040_{family}_{label}",width=16,height=16,alpha=False)
        image.generated_color=color;image.colorspace_settings.name="Non-Color"
        image.filepath_raw=str(source/(label+".png"));image.file_format="PNG";image.save();image.pack()
        shutil.copy2(source/(label+".png"),target/(label+".png"))
    mat=bpy.data.materials.new(f"CCP040_{family}_atlas");mat.use_nodes=True
    mat.diffuse_color=(.43,.30,.20,1)
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get("Principled BSDF")
    bs.inputs["Specular IOR Level"].default_value=.06
    for label,socket in (("albedo","Base Color"),("roughness","Roughness"),("metalness","Metallic"),("normal","Normal")):
        im=albedo if label=="albedo" else bpy.data.images.load(str(source/(label+".png")),check_existing=True)
        if label!="albedo":im.colorspace_settings.name="Non-Color";im.pack()
        node=nodes.new("ShaderNodeTexImage");node.image=im
        if label=="normal":
            nm=nodes.new("ShaderNodeNormalMap");links.new(node.outputs["Color"],nm.inputs["Color"]);links.new(nm.outputs["Normal"],bs.inputs[socket])
        else:links.new(node.outputs["Color"],bs.inputs[socket])
    return mat

def build(family,age,mat):
    """Street-oriented, footprint-bounded regional details (front is -Y)."""
    foundation=[];upper=[];finish=[]
    contact={"model_translation":[0.0,0.0,0.0],"roof_post_contacts":[],"decorative_joints":[]}
    def add(obj,stage=40):
        (foundation if stage==0 else upper if stage==40 else finish).append(obj)
    def B(name,center,dims,tile="timber",stage=40):
        obj=box(name,center,dims,mat,tile)
        add(obj,stage)
        return obj
    def roof(name,center,w,d,eave,rise):
        obj=hipped_tile_roof(name,center,w,d,eave,rise,.14,mat)
        add(obj,40)
        return obj
    def frame(prefix,xs,front,ground,top,depth=.18):
        for i,x in enumerate(xs):B(f"{prefix} carved timber post {i}",(x,front,(ground+top)/2),(.17,depth,top-ground),"timber",0)
        B(f"{prefix} horizontal lintel",((xs[0]+xs[-1])/2,front,top-.05),(xs[-1]-xs[0]+.30,depth,.20),"timber")
    def roof_under_actual(roof_obj,x,y):
        # Ray intersection of the actual tessellated lower roof surface.
        hit,point,normal,face=roof_obj.ray_cast(Vector((x,y,-100)),Vector((0,0,1)))
        assert hit and normal.z<-.25,(roof_obj.name,x,y,normal,face)
        return float(point.z)
    def fitted_supports(prefix,xs,y,ground,post_top,roof_obj):
        for i,x in enumerate(xs):
            underside=roof_under_actual(roof_obj,x,y)
            start=post_top-.015;end=underside+.015
            assert end>start
            B(f"{prefix} fitted roof support {i}",(x,y,(start+end)/2),(.14,.14,end-start),"timber",40)
            contact["roof_post_contacts"].append({"post_index":i,"x":x,"y":y,
                "post_bottom_z":ground,"post_top_z":post_top,"lintel_top_z":post_top+.05,
                "roof_underside_z":underside,"support_bottom_z":start,"support_top_z":end,
                "post_support_overlap_m":post_top-start,
                "support_roof_overlap_m":end-underside})
    if family=="blacksmith":
        # A low, deep roadside forge canopy with its own hipped clay tile roof.
        # The native pair of chimney stacks remains visible behind it.
        y=-4.72;g=(-1.60 if age==4 else -1.44);top=1.89
        xs=[-3.56,-1.78,1.78,3.56]
        frame("forge verandah",xs,y,g,top)
        B("tiled canopy lower fascia",(0,-4.67,1.84),(7.24,.22,.25),"timber")
        canopy=roof("broad low Dai Viet forge roof",(0,-4.27),7.36,2.50,1.94,.66)
        fitted_supports("forge verandah",xs,y,g,top,canopy)
        for x in (-3.62,3.62):
            B("brick forge wing cheek",(x,-4.13,-.24),(.34,1.18,1.95),"brick",0)
        for x in (-2.80,-2.45,2.45,2.80):
            B("bamboo side ventilation lattice",(x,-4.85,.17),(.055,.09,1.90),"thatch",80)
        B("forge cross-brace left",(-2.67,-4.81,1.06),(1.85,.12,.08),"timber",80)
        B("forge cross-brace right",(2.67,-4.81,1.06),(1.85,.12,.08),"timber",80)
        B("aged roof ridge",(0,-4.27,2.64),(7.03,.10,.12),"tile",80)
    elif family=="stable":
        # A long open three-bay shelter; the passage stays open below the rail.
        y=-1.55;g=-1.50;top=1.68
        xs=[-3.12,-1.02,1.02,3.12]
        frame("three stall arcade",xs,y,g,top)
        # End before the donor's raised roof begins near Y=-1.35; otherwise
        # its stock tile surface cuts two pale triangles through our awning.
        canopy=roof("long low stable clay canopy",(0,-1.76),6.68,.64,1.77,.40)
        fitted_supports("three stall arcade",xs,y,g,top,canopy)
        for x in (-2.05,0,2.05):
            B("stall lintel name board",(x,-1.62,1.47),(1.53,.10,.18),"timber",80)
    elif family=="archery_range":
        # The watchtower is left clear; a low firing arcade and practice rack
        # establish the range without moving its native entry or balcony.
        y=-2.45;g=-1.20;top=1.39
        xs=[-1.92,-.64,.64,1.92,3.45]
        frame("firing arcade",xs,y,g,top)
        canopy=roof("archers clay shade",(.74,-2.53),5.85,1.45,1.44,.43)
        fitted_supports("firing arcade",xs,y,g,top,canopy)
        for x in (-1.73,-1.35,1.73,2.86):
            B("bamboo firing screen",(x,-2.51,.64),(.06,.08,1.56),"thatch",80)
        B("arrow rack crossbar",(2.30,-2.55,.68),(1.22,.10,.11),"timber",80)
        B("arrow rack lower bar",(2.30,-2.55,.00),(1.22,.10,.11),"timber",80)
    elif family=="market":
        # Restrained removable stall awning below the paired native roofline.
        y=-1.89;g=-1.64;top=1.22
        xs=[-4.52,-2.91,-1.28,.28,1.82,3.13]
        frame("merchant frontage",xs,y,g,top)
        canopy=roof("merchant clay eave",(-.66,-1.94),7.82,1.12,1.28,.29)
        fitted_supports("merchant frontage",xs,y,g,top,canopy)
        for left,right in zip(xs,xs[1:]):
            B("stall display shelf",((left+right)/2,-2.00,-.47),(right-left+.12,.43,.12),"timber",80)
        B("market woven fascia",(-.66,-1.96,1.10),(7.52,.08,.22),"thatch",80)
    # Audit every decorative joint before stage consolidation removes the
    # individual object boundaries. Box/box joints use exact AABB overlap.
    parts=foundation+upper+finish
    def matches(fragment):return [o for o in parts if fragment in o.name]
    def joint(a,b,label):
        av=[v.co for v in a.data.vertices];bv=[v.co for v in b.data.vertices]
        overlap=[min(max(v[i] for v in av),max(v[i] for v in bv))-
                 max(min(v[i] for v in av),min(v[i] for v in bv)) for i in range(3)]
        assert min(overlap)>.005,(family,age,label,a.name,b.name,overlap)
        contact["decorative_joints"].append({"name":label,"a":a.name,"b":b.name,
                                              "axis_overlap_m":overlap})
    posts=matches("carved timber post")
    lintel=matches("horizontal lintel")[0]
    supports=matches("fitted roof support")
    assert len(posts)==len(supports)==len(xs)
    for i,(post,support) in enumerate(zip(posts,supports)):
        joint(post,lintel,f"post {i} to lintel")
        joint(post,support,f"post {i} to fitted roof support")
        joint(lintel,support,f"lintel to roof support {i}")
    if family=="blacksmith":
        braces=matches("forge cross-brace")
        bamboo=matches("bamboo side ventilation lattice")
        assert len(braces)==2 and len(bamboo)==4
        for i,bar in enumerate(bamboo):
            side=0 if sum(v.co.x for v in bar.data.vertices)<0 else 1
            joint(bar,braces[side],f"bamboo screen {i} to brace")
        for i,brace in enumerate(braces):
            for post in posts:
                if (min(v.co.x for v in post.data.vertices)<0)==(i==0):
                    joint(brace,post,f"brace {i} to post {post.name}")
    elif family=="stable":
        for i,board in enumerate(matches("stall lintel name board")):joint(board,lintel,f"stall board {i} to lintel")
    elif family=="archery_range":
        screens=matches("bamboo firing screen")
        for i,bar in enumerate(screens):joint(bar,lintel,f"firing screen {i} to lintel")
        for rack in matches("arrow rack"):
            for bar in screens[2:]:joint(rack,bar,f"{rack.name} to bamboo")
    else:
        shelves=matches("stall display shelf")
        for i,shelf in enumerate(shelves):
            joint(shelf,posts[i],f"market shelf {i} left post")
            joint(shelf,posts[i+1],f"market shelf {i} right post")
        joint(matches("market woven fascia")[0],lintel,"market fascia to lintel")
    # The root remains exactly at principal-stamp origin. No global transforms.
    objects=[join_stage(foundation,f"vn_{family}_age{age:02}_detail_base",0),
            join_stage(upper,f"vn_{family}_age{age:02}_detail_structure",40),
            join_stage(finish,f"vn_{family}_age{age:02}_detail_furnish",80)]
    return objects,contact

def render_composite(family,age,detail,output):
    """Paired game/facade previews, donor plus private detail stamp."""
    donor_path=BASE/family/f"Vietnam_{family}_Age{age:02}.blend"
    assert donor_path.exists(),donor_path
    with bpy.data.libraries.load(str(donor_path),link=False) as (src,dst):
        dst.objects=list(src.objects)
    donor=[]
    for obj in dst.objects:
        if obj is not None and obj.type=="MESH":
            bpy.context.scene.collection.objects.link(obj);donor.append(obj)
    assert donor,donor_path
    # Workbench keeps this acceptance render quick; the FBX atlas is checked
    # separately and packed into the editable Blend.
    scene=bpy.context.scene;scene.render.engine="BLENDER_WORKBENCH"
    scene.display.shading.light="STUDIO";scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    scene.render.resolution_x=960;scene.render.resolution_y=780;scene.render.resolution_percentage=100
    coords=[v.co for o in donor+detail for v in o.data.vertices]
    lo=Vector([min(v[i] for v in coords) for i in range(3)])
    hi=Vector([max(v[i] for v in coords) for i in range(3)])
    center=(lo+hi)/2;span=(hi-lo).length
    for name,vec in (("game",(1,-1,.8)),("facade",(0,-1,.2))):
        cam=bpy.data.objects.new("Preview only",bpy.data.cameras.new("Preview only"))
        scene.collection.objects.link(cam);cam.location=center+Vector(vec).normalized()*span*2
        cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.data.type="ORTHO";cam.data.ortho_scale=span*1.35;scene.camera=cam
        scene.render.filepath=str(output/f"composite-{name}.png");bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam,do_unlink=True)
    scene.camera=None
    for obj in donor:bpy.data.objects.remove(obj,do_unlink=True)

rows=[]
for family,age in jobs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=BASE/family/f"details_age{age:02}"
    target=EXPORT/family/f"details_age{age:02}"
    output=OUT/family/f"age{age:02}"
    for path in (source,target,output):path.mkdir(parents=True,exist_ok=True)
    mat=atlas(family,source,target)
    objects,contact=build(family,age,mat)
    geometry=validate(objects)
    # Garrison's official preflight governs FBX suitability.
    preflight=require_valid(objects,bpy.context)
    assert preflight["ok"],preflight
    adopt_material(mat)
    bpy.ops.file.pack_all();blend=source/f"vn_{family}_details_age{age:02}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    manifest=export_building(objects,target)
    render_composite(family,age,objects,output)
    row={"family":family,"age":age,"private_model_stem":f"art/scenario/cc040/{family}_detail_age0{age}/model",
         "source_blend":str(blend),"source_blend_sha256":sha(blend),
         "export_dir":str(target),"manifest_sha256":sha(target/"building.json"),
         "fbx_sha256":sha(target/"model.fbx"),"textures":{n:sha(target/(n+".png")) for n in ("albedo","roughness","normal","metalness")},
         "geometry":geometry,"contact":contact,"profile":manifest["profile"],"stages":[p["first_stage"] for p in manifest["parts"]],
         "composite_game":str(output/"composite-game.png"),"composite_facade":str(output/"composite-facade.png")}
    write(output/"source.json",row);rows.append(row)
write(OUT/"details-validation.json",{"schema":"ccp.release040.building-details/v1","status":"authoring_export_only","models":rows})
print("CCP040 private building details",[(r["family"],r["age"],sum(g["triangles"] for g in r["geometry"])) for r in rows])
