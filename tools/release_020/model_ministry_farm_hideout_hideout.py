"""Native-topology Hideout default/stone visual remodelling.

Runs only in a dedicated factory-startup Blender process after the shared token.
Keeps donor GEOB groups, indices, UVs, material slots, fragment identity and
construction/damage pieces. Integration owns RGM bounds and private binding.
"""
import bpy
import copy
import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[2]
EXT=Path(os.environ["APPDATA"])/"Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0,str(EXT))
spec=importlib.util.spec_from_file_location("garrison_shared",str(EXT/"garrison_shared.cp313-win_amd64.pyd"))
shared=importlib.util.module_from_spec(spec);sys.modules["garrison_shared"]=shared;spec.loader.exec_module(shared)
from garrison_shared import relic_chunky as rc
sys.path.insert(0,str(EXT.parent))
import garrison
sys.modules["garrison.garrison_shared"]=shared
garrison.register()
from garrison.decode_projection import _apply_decoded_static

sha=lambda data:hashlib.sha256(data).hexdigest()
AUTHOR=ROOT/"art/authoring/buildings_020/hideout"
DONOR=Path("F:/aoe_4_temp/Community_civilization_pack_garrison_temp/stock-cache/release_020/hideout")
EXPORT=ROOT/"art/exports/buildings_020/hideout"
OUT=ROOT/"output/release_020/ministry_farm_hideout/hideout"
RECIPE=ROOT/"art/recipes/release_020/hideout-source.json"
for p in (EXPORT,OUT,RECIPE.parent):p.mkdir(parents=True,exist_ok=True)


def smooth(v,a,b):
    t=max(0,min(1,(v-a)/(b-a)))
    return t*t*(3-2*t)


def remodel(pos,stone):
    x,y,z=pos
    if z<=0: return Vector((x,y,z))
    # Compress the old enclosed middle into a narrower sheltered core while
    # retaining its upper lookout near the native weapon-origin height. The
    # private timber screen sits outside this middle core in the combined view.
    # Every native fragment uses this same continuous map so contacts remain.
    knee=3.6 if not stone else 5.0
    top=8.19 if not stone else 12.49
    middle=smooth(z,1.4 if not stone else 3.3,2.8 if not stone else 4.5)
    middle*=1-smooth(z,4.4 if not stone else 7.0,5.5 if not stone else 8.2)
    roof=smooth(z,5.1 if not stone else 8.1,top)
    foot=smooth(z,0,.4)*(1-smooth(z,1.6 if not stone else 2.5,2.8 if not stone else 4.0))
    xx=x*(1+(.10 if not stone else .06)*foot-(.16 if not stone else .12)*middle+(.05 if not stone else .035)*roof)
    yy=y*(1+(.08 if not stone else .05)*foot-(.13 if not stone else .10)*middle+(.045 if not stone else .03)*roof)
    # Moderate height reduction avoids a detached projectile/weapon origin.
    zz=z-(.16 if not stone else .23)*smooth(z,2.0 if not stone else 3.4,knee)
    zz-=(z-knee)*(.045 if not stone else .055)*smooth(z,knee,top)
    zz-=(.25 if not stone else .34)*smooth(z,6.5 if not stone else 10.0,top)
    return Vector((xx,yy,zz))


def jacobian(pos,stone):
    epsilon=.0001
    cols=[]
    for i in range(3):
        a=list(pos);b=list(pos);a[i]+=epsilon;b[i]-=epsilon
        cols.append((remodel(a,stone)-remodel(b,stone))/(2*epsilon))
    return Matrix(cols).transposed()


def bounds(groups):
    points=[p for g in groups for p in g["positions"]]
    low=[min(p[i] for p in points) for i in range(3)]
    high=[max(p[i] for p in points) for i in range(3)]
    return {"min":low,"max":high,"dimensions":[b-a for a,b in zip(low,high)]}


def preview(prefix, center, span):
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True
    scene.render.resolution_x=1000;scene.render.resolution_y=850
    scene.render.resolution_percentage=100
    for name, vec in (("iso",(1,-1,.8)),("front",(0,-1,.14)),("back",(0,1,.14)),
                      ("left",(-1,0,.14)),("right",(1,0,.14)),("top",(0,0,1)),("bottom",(0,0,-1))):
        camera=bpy.data.objects.new("Presentation only",bpy.data.cameras.new("Presentation only"))
        scene.collection.objects.link(camera)
        camera.location=Vector(center)+Vector(vec).normalized()*span*2
        camera.rotation_euler=(Vector(center)-camera.location).to_track_quat("-Z","Y").to_euler()
        camera.data.type="ORTHO";camera.data.ortho_scale=span*1.4
        scene.camera=camera;scene.render.filepath=str(OUT/f"{prefix}-{name}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(camera,do_unlink=True)
    scene.camera=None


report={"schema":"ccp.020-hideout-native-remodel/v1","status":"running",
        "method":"Continuous stock GEOB deformation; original groups, indices, UV selectors, masks, parts and reference assets retained",
        "limitations":"Native owner graph, weapon markers, stamp placement, damage and construction require integration readback and match testing",
        "models":[]}
for variant in ("default","stone"):
    stone=variant=="stone"
    donor=next((DONOR/variant).rglob("decoded-static.json"))
    old=json.loads(donor.read_text(encoding="utf-8"));new=copy.deepcopy(old)
    original_raw=Path(old["geometry"]["source"]["path"]).read_bytes()
    doc=rc.parse(original_raw)
    chunks=[c for c in rc.walk(doc.roots) if c.tag==b"GEOB"]
    assert len(chunks)==len(new["geometry"]["groups"])*2
    changes={};groups=[]
    for gi,(group,chunk) in enumerate(zip(new["geometry"]["groups"],chunks[::2])):
        data=bytearray(chunk.payload)
        count,_,stride,_=struct.unpack_from("<4I",data)
        assert stride==24 and count==len(group["positions"])
        touched=0;maxerr=0
        for vi,p in enumerate(group["positions"]):
            offset=16+vi*stride
            packed=struct.unpack_from("<4e",data,offset)
            assert tuple(p)==(-packed[0],-packed[2],packed[1])
            v=remodel(p,stone)
            J=jacobian(p,stone)
            assert J.determinant()>.15,(variant,gi,vi,J.determinant())
            data[offset:offset+8]=struct.pack("<4e",-v.x,v.z,-v.y,packed[3])
            q=struct.unpack_from("<4e",data,offset)
            group["positions"][vi]=[-q[0],-q[2],q[1]]
            maxerr=max(maxerr,(Vector(group["positions"][vi])-v).length)
            normal=(J.inverted().transposed()@Vector(group["normals"][vi])).normalized()
            raw_tangent=struct.unpack_from("<3b",data,offset+12)
            tangent=J@Vector((-raw_tangent[0]/127,-raw_tangent[2]/127,raw_tangent[1]/127))
            tangent=(tangent-normal*tangent.dot(normal)).normalized()
            for delta,value in ((8,normal),(12,tangent)):
                data[offset+delta:offset+delta+3]=struct.pack("<3b",*(max(-127,min(127,round(component*127))) for component in (-value.x,value.z,-value.y)))
            n=struct.unpack_from("<3b",data,offset+8)
            group["normals"][vi]=list(Vector((-n[0]/127,-n[2]/127,n[1]/127)).normalized())
            assert bytes(data[offset+16:offset+24])==chunk.payload[offset+16:offset+24]
            if bytes(data[offset:offset+16])!=chunk.payload[offset:offset+16]:touched+=1
        changes[chunk.offset]=bytes(data)
        groups.append({"group":gi,"material":group["preview_material"],"vertices":count,
                       "changed_vertices":touched,"index_sha256":sha(chunks[2*gi+1].payload),
                       "uv_and_selector_bytes_preserved":True,"max_half_float_error_m":maxerr})
    encoded=rc.rebuild(doc,lambda c:changes.get(c.offset))
    assert len(encoded)==len(original_raw)
    target=EXPORT/("cc020_hideout_"+variant+".rrgeom")
    target.write_bytes(encoded)
    projection=AUTHOR/variant/("cc020_hideout_"+variant+"-projection.json")
    projection.write_text(json.dumps(new),encoding="utf-8")
    repeats={};sharedcount=0;maxgap=0
    for oldg,newg in zip(old["geometry"]["groups"],new["geometry"]["groups"]):
        for before,after in zip(oldg["positions"],newg["positions"]):
            key=tuple(before)
            if key in repeats:
                sharedcount+=1
                maxgap=max(maxgap,(Vector(after)-Vector(repeats[key])).length)
            else:repeats[key]=after
    assert maxgap==0
    bpy.ops.wm.read_factory_settings(use_empty=True)
    proxy=bpy.data.objects.new("Native Chinese outpost "+variant,None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"]=str(donor)
    proxy["garrison_logical_path"]=old["request"]["logical_path"]
    proxy["garrison_display_name"]="Chinese outpost "+variant
    root=_apply_decoded_static(proxy,old,create_controls=False)
    bb=bounds(old["geometry"]["groups"])
    center=[(a+b)/2 for a,b in zip(bb["min"],bb["max"])]
    span=max(bb["dimensions"])*1.08
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    before_blend=AUTHOR/variant/("chinese_outpost_"+variant+"_donor.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(before_blend))
    preview(variant+"-before",center,span)
    for obj in [o for o in bpy.context.scene.objects if o.type=="MESH"]:
        gi=obj.get("garrison_mesh_index")
        if gi is None:continue
        group=new["geometry"]["groups"][gi]
        assert len(obj.data.vertices)==len(group["positions"])
        for vertex,co in zip(obj.data.vertices,group["positions"]):vertex.co=co
        obj.data.normals_split_custom_set_from_vertices(group["normals"])
        obj.data.update()
        obj["ccp_native_geometry"]=str(target)
        obj["ccp_remodel"]="broader screened-shelter base, visually lower lookout; native topology preserved"
    root.name="Vietnam_Hideout_"+variant
    preview(variant+"-after",center,span)
    bpy.ops.file.pack_all()
    blend=AUTHOR/variant/("Vietnam_Hideout_"+variant+".blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    row={"variant":variant,"donor_manifest":str(donor),"donor_blend":str(before_blend),
         "editable_blend":str(blend),"editable_blend_sha256":sha(blend.read_bytes()),
         "geometry_export":str(target),"geometry_sha256":sha(encoded),
         "donor_geometry_sha256":sha(original_raw),"before_bounds":bb,
         "after_bounds":bounds(new["geometry"]["groups"]),"groups":groups,
         "contact_checks":{"repeat_vertices":sharedcount,"max_gap_m":maxgap,"below_ground_unchanged":True},
         "native_owner_marks":"Preserve existing layout_outpost, origin, top weapon marker and native stamp graph; never bake owner colour into texture"}
    report["models"].append(row)
    (OUT/"validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("CCP_020_HIDEOUT_READY",variant,flush=True)
report["status"]="authored"
(OUT/"validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
RECIPE.write_text(json.dumps({"schema":"ccp.020-hideout-recipe/v1",
    "generator":str(Path(__file__).resolve()),"models":[{k:v for k,v in row.items() if k!="groups"} for row in report["models"]],
    "design_note":"Visible remodeling of native Chinese outpost proportions; low shelter/readable lookout, stock source and topology retained; qualitative target only"},indent=2),encoding="utf-8")
