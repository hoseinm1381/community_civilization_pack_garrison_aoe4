"""Private Northern Dai Viet architectural compounds for five Castle buildings.

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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import guarded
sys.path.insert(0, str(ROOT / "tools/release_020"))
from model_ministry_farm_hideout_runner import box, mesh, hipped_tile_roof, join_stage, validate, export_building, write
from building_design import build as build_castle
sys.path.insert(0, r"C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com")
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material

assert bpy.app.background and not bpy.data.filepath
guarded()
arg = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "all"
FAMILIES = ("monastery", "siege_workshop", "keep")
jobs = [(f, a) for f, a in (("monastery", 3), ("monastery", 4),
        ("siege_workshop", 3), ("siege_workshop", 4), ("keep", 3))
        if arg == "all" or arg in (f, f"{f}:{a}")]
assert jobs, arg
BASE = ROOT / "art/authoring/castle_next/buildings"
EXPORT = ROOT / "art/exports/castle_next/buildings"
OUT = ROOT / "output/castle_next/buildings/details"
DONOR_MANIFEST = ROOT / "output/castle_next/donors/donor-manifest.json"
DONORS = json.loads(DONOR_MANIFEST.read_text(encoding="utf8"))["donors"]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def atlas(family, source, target):
    """One deterministic weathered 4x2 atlas, matching the stock Garrison helper UVs."""
    import numpy as np
    palette = [(.40,.22,.15),(.27,.19,.13),(.44,.23,.15),(.49,.46,.38),
               (.36,.34,.27),(.17,.25,.23),(.24,.32,.17),(.50,.40,.25)]
    size=1024; cell_w=size//4; cell_h=size//2
    yy,xx=np.mgrid[0:size,0:size]
    rng=np.random.default_rng(400 + FAMILIES.index(family))
    grain=rng.normal(0,.026,(size,size))+np.sin(xx*.071)*.012+np.sin(yy*.047)*.012
    arr=np.ones((size,size,4),np.float32)
    rough=np.ones((size,size,4),np.float32);rough[:,:,:3]=.86
    for index,color in enumerate(palette):
        col,row=index%4,index//4
        sl=np.s_[row*cell_h:(row+1)*cell_h,col*cell_w:(col+1)*cell_w]
        u=xx[sl]-col*cell_w;v=yy[sl]-row*cell_h
        g=grain[sl].copy()
        if index==0:g+=np.where((v%15<2)|((u+8*((v//15)%2))%16<2),-.075,.01)
        if index==1:g+=np.sin(u*.24+np.sin(v*.035))*.025
        if index==2:g+=np.where((v%17<2)|((u+8*((v//17)%2))%14<2),-.065,.012)
        if index==7:g+=np.sin(u*.31)*.015
        for c in range(3):arr[sl+(c,)]=np.clip(color[c]+g,0,1)
    def save(label,data,noncolor=False):
        im=bpy.data.images.new(f"CCP_CASTLE_{family}_{label}",width=size,height=size,alpha=True)
        im.pixels.foreach_set(data.ravel())
        if noncolor: im.colorspace_settings.name="Non-Color"
        im.filepath_raw=str(source/(label+".png"));im.file_format="PNG";im.save();im.pack()
        shutil.copy2(source/(label+".png"),target/(label+".png"))
        return im
    albedo=save("albedo",arr)
    save("roughness",rough,True)
    for label,color in (("normal",(.5,.5,1,1)),("metalness",(0,0,0,1))):
        image=bpy.data.images.new(f"CCP_CASTLE_{family}_{label}",width=16,height=16,alpha=False)
        image.generated_color=color;image.colorspace_settings.name="Non-Color"
        image.filepath_raw=str(source/(label+".png"));image.file_format="PNG";image.save();image.pack()
        shutil.copy2(source/(label+".png"),target/(label+".png"))
    mat=bpy.data.materials.new(f"CCP_CASTLE_{family}_atlas");mat.use_nodes=True
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

def render_composite(family,age,detail,output):
    """Paired game/facade previews, donor plus private detail stamp."""
    donor_path=BASE/family/f"age{age:02}"/f"Vietnam_{family}_Age{age:02}.blend"
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
    source=BASE/family/f"age{age:02}"/"details"
    target=EXPORT/family/f"age{age:02}"/"details"
    output=OUT/family/f"age{age:02}"
    for path in (source,target,output):path.mkdir(parents=True,exist_ok=True)
    mat=atlas(family,source,target)
    donor=next(r for r in DONORS.values() if r['name']==f'{family}{age:02}')
    objects,contacts=build_castle(family,age,mat,donor)
    geometry=validate(objects)
    # Garrison's official preflight governs FBX suitability.
    preflight=require_valid(objects,bpy.context)
    assert preflight["ok"],preflight
    adopt_material(mat)
    bpy.ops.file.pack_all();blend=source/f"vn_{family}_details_age{age:02}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    manifest=export_building(objects,target)
    row={"family":family,"age":age,"private_model_stem":f"art/scenario/cccastle/{family}_detail_age0{age}/model",
         "source_blend":str(blend),"source_blend_sha256":sha(blend),
         "export_dir":str(target),"manifest_sha256":sha(target/"building.json"),
         "fbx_sha256":sha(target/"model.fbx"),"textures":{n:sha(target/(n+".png")) for n in ("albedo","roughness","normal","metalness")},
         "geometry":geometry,"contact_checks":contacts,"profile":manifest["profile"],"stages":[p["first_stage"] for p in manifest["parts"]],
         "composite_game":str(OUT.parent/"previews"/f"{family}{age:02}"/"composite"/"iso-solid.png"),
         "composite_facade":str(OUT.parent/"previews"/f"{family}{age:02}"/"composite"/"front-solid.png")}
    write(output/"source.json",row);rows.append(row)
write(OUT/"details-validation.json",{"schema":"ccp.castle-next.building-details/v1","status":"authoring_export_only","models":rows})
print("CCP_CASTLE private building details",[(r["family"],r["age"],sum(g["triangles"] for g in r["geometry"])) for r in rows])
