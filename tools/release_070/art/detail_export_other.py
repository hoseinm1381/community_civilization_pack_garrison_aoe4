"""Export reviewed Foundry, Wonder, or University seven-part overlay by MCP.

Call export_detail(kind, xy_scale, z_scale, shift_x, shift_y, shift_z=0).
Shifts are model-local artwork fits. University shift is the verified inverse
pot-visual offset and applies to clones only; its stock body stays native.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import shutil
import bpy

ROOT=Path("E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison")
NAMES={"foundry":"CCP070_Trung_Foundries_Detailed_r3",
       "wonder":"CCP070_Kinh_Thien_Detailed_r4",
       "university":"CCP070_University_Detailed_Overlay_r6"}
ROOF_PROOFS={"foundry":("foundry-r2-roof-seated.json","CCP070_Trung_Foundries_Detailed_r2"),
             "wonder":("wonder-r3-roof-seated.json","CCP070_Kinh_Thien_Detailed_r3")}
ROOF_PROOF_DIR=Path("F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail")
TERRAIN_PROOFS={"foundry":"foundry-r3-terrain-base.json"}
STAGES=(0,20,0,80,20,20,20)
UNIVERSITY_SHIFT=(-2.338015973567963,3.7076730728149423,0.0)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def export_detail(kind,xy_scale,z_scale,shift_x,shift_y,shift_z=0.0):
    if kind not in NAMES:
        raise ValueError("Unknown detail asset")
    if not all(math.isfinite(v) for v in (xy_scale,z_scale,shift_x,shift_y,shift_z)):
        raise ValueError("Nonfinite model-local fit")
    if xy_scale<=0 or z_scale<=0:
        raise ValueError("Positive scales required")
    if kind=="university" and (abs(xy_scale-1.0)>1e-8 or abs(z_scale-1.0)>1e-8):
        raise ValueError("University overlay must retain the stock body scale")
    if kind=="wonder" and abs(shift_z)>1e-8:
        raise ValueError("Wonder podium grade is vertical zero; stamp tz is horizontal in Blender projection")
    if kind=="foundry" and abs(shift_z-0.23)>1e-8:
        raise ValueError("Foundry casting floors need exact +0.23 model-local Z clearance")
    if kind=="university" and (abs(shift_x-UNIVERSITY_SHIFT[0])>1e-8 or
                                abs(shift_y-UNIVERSITY_SHIFT[1])>1e-8 or
                                abs(shift_z)>1e-8):
        raise ValueError("University must use exact verified pot-visual inverse shift")
    collection=bpy.data.collections.get(NAMES[kind])
    if collection is None:
        raise RuntimeError("Reviewed detail collection missing")
    if kind=="university" and collection.name.endswith("_r1"):
        raise RuntimeError("University r1 has unsupported roof pans; use reviewed seated revision")
    repartition_file=ROOF_PROOF_DIR/'wonder-r4-repartition.json' if kind=='wonder' else None
    if repartition_file:
        repartition=json.loads(repartition_file.read_text())
        if repartition.get('revision')!=collection.name or not repartition.get('healthy_face_position_uv_multiset_exact') or max(repartition['after_per_part_corners'].values())>=60000:
            raise RuntimeError('Wonder native-corner-limit repartition proof missing')
    university_proof_file=ROOF_PROOF_DIR/'university-r6-independent-verify.json' if kind=='university' else None
    if university_proof_file:
        university_proof=json.loads(university_proof_file.read_text())
        if university_proof.get('status')!='passed' or university_proof.get('supported_roof_accents')!=94 or university_proof.get('failed_roof_accents'):
            raise RuntimeError('University final stock/UV/roof-contact proof missing or failed')
    if kind in ("foundry","wonder") and collection.name.endswith("_r1"):
        raise RuntimeError("Unseated r1 roof tiles are not exportable; use reviewed revision")
    proof_file=ROOF_PROOF_DIR/ROOF_PROOFS[kind][0] if kind in ROOF_PROOFS else None
    proof=None
    if proof_file:
        proof=json.loads(proof_file.read_text(encoding="utf-8"))
        if (proof.get("revision")!=ROOF_PROOFS[kind][1] or
            proof.get("unseated") or not proof.get("tiles_seated")):
            raise RuntimeError("Roof-contact proof does not qualify this source collection")
    terrain_file=ROOF_PROOF_DIR/TERRAIN_PROOFS[kind] if kind in TERRAIN_PROOFS else None
    terrain=None
    if terrain_file:
        terrain=json.loads(terrain_file.read_text(encoding="utf-8"))
        if (terrain.get("source")!=ROOF_PROOFS[kind][1] or
            terrain.get("revision")!=collection.name or
            terrain.get("world_recess_floor",-1)<=0 or
            abs(terrain.get("export_z_shift",-1)-shift_z)>1e-8):
            raise RuntimeError("Terrain-clearance proof does not qualify this source collection")
    target=ROOT/"art/exports/buildings_070"/(kind+'-r6' if kind=='university' else kind+'-r4' if kind=='wonder' else kind)
    if (target/"model.fbx").exists() or (target/"building.json").exists():
        raise FileExistsError("Existing export preserved; use new revision")
    parts={}
    for obj in collection.objects:
        for i in range(7):
            if obj.name.endswith("garrison_part_%04d"%i):
                parts[i]=obj
    if len(collection.objects)!=7 or set(parts)!=set(range(7)):
        raise RuntimeError("Exactly seven lifecycle parts required")
    if any(len(obj.data.loops)>=60000 for obj in parts.values()):
        raise RuntimeError('Per-mesh FBX corner count exceeds conservative native-import budget')
    tris={i:sum(len(p.vertices)-2 for p in obj.data.polygons)
          for i,obj in parts.items()}
    healthy=sum(tris[i] for i in (0,1,4,5,6))
    if healthy>=90000 or min(tris.values())==0:
        raise RuntimeError("Healthy triangle cap or empty selector part")
    if any(len(obj.data.materials)!=1 for obj in parts.values()):
        raise RuntimeError("Exactly one atlas material per part required")
    materials={obj.data.materials[0].name for obj in parts.values()}
    if len(materials)!=1 or any(not obj.data.uv_layers for obj in parts.values()):
        raise RuntimeError("Exactly one atlas material and UV layer required")
    clone_name="CCP070_"+kind.title()+"_Export_Clones_"+collection.name.rsplit("_",1)[-1]
    if bpy.data.collections.get(clone_name):
        raise RuntimeError("Export clones already present")
    archive=bpy.data.collections.new(clone_name)
    bpy.context.scene.collection.children.link(archive)
    bpy.ops.object.select_all(action="DESELECT")
    clones=[]
    per_part_bounds={}
    for i in range(7):
        canonical="garrison_part_%04d"%i
        owner=bpy.data.objects.get(canonical)
        if owner is not None:
            if owner.name in collection.objects:
                raise RuntimeError("Canonical export name belongs to source object")
            owner.name="CCP070_Archived_Export_Name_%04d_%s"%(i,kind)
            if bpy.data.objects.get(canonical) is not None:
                raise RuntimeError("Could not release canonical FBX object name")
        clone=parts[i].copy()
        clone.data=parts[i].data.copy()
        clone.name=canonical
        if clone.name!=canonical:
            raise RuntimeError("Blender suffixed an FBX part name")
        archive.objects.link(clone)
        clone.hide_set(False)
        clone.hide_render=False
        clone.location=(0,0,0)
        clone.rotation_euler=(0,0,0)
        clone.scale=(1,1,1)
        for v in clone.data.vertices:
            v.co=(v.co.x*xy_scale+shift_x,
                  v.co.y*xy_scale+shift_y,
                  v.co.z*z_scale+shift_z)
        for loop in clone.data.uv_layers.active.data:
            loop.uv.y=1-loop.uv.y
        verts=[v.co for v in clone.data.vertices]
        per_part_bounds["%04d"%i]={
            "min":[min(v[j] for v in verts) for j in range(3)],
            "max":[max(v[j] for v in verts) for j in range(3)]}
        clone.select_set(True)
        clones.append(clone)
    bpy.context.view_layer.objects.active=clones[0]
    target.mkdir(parents=True,exist_ok=True)
    result=bpy.ops.export_scene.fbx(filepath=str(target/"model.fbx"),
        use_selection=True,object_types={"MESH"},use_mesh_modifiers=False,
        add_leaf_bones=False,bake_anim=False,axis_forward="-Z",axis_up="Y",
        use_custom_props=False)
    if "FINISHED" not in result:
        raise RuntimeError("FBX export failed")
    raw=(target/"model.fbx").read_bytes()
    model_nodes=re.findall(rb"garrison_part_\d{4}(?:\.\d{3})?\x00\x01Model",raw)
    actual=[node.split(b"\x00",1)[0].decode("ascii") for node in model_nodes]
    expected=["garrison_part_%04d"%i for i in range(7)]
    if sorted(actual)!=expected:
        raise RuntimeError("FBX Model nodes violate exact seven-part contract: %r"%actual)
    for channel in ("albedo","normal","roughness","metalness"):
        shutil.copyfile(ROOT/"art/exports/buildings_070"/kind/"textures"/(kind+"_"+channel+"_2048.png"),
                        target/(channel+".png"))
    manifest={"schema":"garrison.building-source/v1","profile":"english-house",
              "parts":[{"name":"garrison_part_%04d"%i,
                        "first_stage":STAGES[i]} for i in range(7)],
              "material_name":next(iter(materials)),
              "textures":{channel:channel+".png" for channel in
                          ("albedo","normal","roughness","metalness")}}
    (target/"building.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    files=("model.fbx","building.json","albedo.png","normal.png",
           "roughness.png","metalness.png")
    receipt={"schema":"ccp-070-detail-export-receipt/v1",
             "kind":kind,"input_collection":collection.name,
             "fbx_model_nodes":actual,
             "healthy_triangles":healthy,"per_part_triangles":tris,
             "selector_parts":{"healthy":[0,1,4,5,6],"heavy_damage":[0,3],"ruins":[2]},
             "fit":{"xy_scale":xy_scale,"z_scale":z_scale,
                    "shift":[shift_x,shift_y,shift_z]},
             "per_part_export_bounds":per_part_bounds,
             "university_stock_body_preserved_outside_export":kind=="university",
             "university_final_proof":{"path":str(university_proof_file),"sha256":digest(university_proof_file)} if university_proof_file else None,
             "wonder_repartition_proof":{"path":str(repartition_file),"sha256":digest(repartition_file)} if repartition_file else None,
             "roof_seating_proof":{"path":str(proof_file),
                                   "sha256":digest(proof_file),
                                   "tiles_seated":proof["tiles_seated"],
                                   "unseated":len(proof["unseated"]),
                                   "applies_to":proof["revision"]} if proof_file else None,
             "terrain_clearance_proof":{"path":str(terrain_file),
                                         "sha256":digest(terrain_file),
                                         "recess_world_z":terrain["world_recess_floor"]} if terrain_file else None,
             "native_stamp_transform_baked":False,
             "files_sha256":{name:digest(target/name) for name in files}}
    (target/"source-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    for clone in clones:
        clone.select_set(False)
        clone.hide_set(True)
        clone.hide_render=True
    return receipt
