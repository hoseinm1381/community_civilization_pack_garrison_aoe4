"""Author remaining Vietnamese humanoid bodies from exact decoded stock donors.

One invocation owns one fresh background Blender process. This writes editable
source, three weighted LODs, native atlas, and review evidence. Native cook and
active binding integration are separate jobs.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import sys
from array import array
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, EXPORT, OUT, guard, owned, read, sha, write
import pilot_author_blender as donor
import representative_batch as review
import ranged_roster_060 as ranged

DATA = {
    "maa3": ("inventory/remaining-donors/run-004/decoded/014_mon_infantry_armor_age03/507fe368664a579364f5/decoded-static.json", "art/civilizations/mongols/humans/mon_infantry_armor_age03/mon_infantry_armor_age03.rgm", 3, (0.17, 0.32, 0.29)),
    "maa4": ("inventory/remaining-donors/run-004/decoded/014_mon_infantry_armor_age03/507fe368664a579364f5/decoded-static.json", "art/civilizations/mongols/humans/mon_infantry_armor_age03/mon_infantry_armor_age03.rgm", 4, (0.24, 0.25, 0.22)),
    "maa3_female": ("inventory/remaining-donors/run-004/decoded/015_mon_infantry_armor_female_age03/3038d2e494778b394c52/decoded-static.json", "art/civilizations/mongols/humans/mon_infantry_armor_female_age03/mon_infantry_armor_female_age03.rgm", 3, (0.18, 0.31, 0.30)),
    "maa4_female": ("inventory/remaining-donors/run-004/decoded/015_mon_infantry_armor_female_age03/3038d2e494778b394c52/decoded-static.json", "art/civilizations/mongols/humans/mon_infantry_armor_female_age03/mon_infantry_armor_female_age03.rgm", 4, (0.25, 0.25, 0.22)),
    "monk3": ("inventory/additional-official-models/monk3/3d026eebe8d003b4f8dd/decoded-static.json", "art/civilizations/chinese/humans/chi_infantry_monk_age03/chi_infantry_monk_age03.rgm", 3, (0.28, 0.30, 0.20)),
    "monk4": ("inventory/inherited-render-bodies-v2/run-003/decodes/chinese-monk-tier4-exact/b80ca264be282419047e/decoded-static.json", "art/civilizations/chinese/humans/chi_infantry_monk_age04/chi_infantry_monk_age04.rgm", 4, (0.34, 0.25, 0.16)),
    "repeater4": ("inventory/inherited-render-bodies-v2/run-003/decodes/chinese-repeater-crossbow-tier4-exact/ccea2d51d793824ed916/decoded-static.json", "art/civilizations/chinese/humans/chi_ranged_crossbow_age04/chi_ranged_crossbow_age04.rgm", 4, (0.13, 0.32, 0.30)),
}
REV = "v2"  # Monk III added after official reachability audit; earlier v1 outputs remain frozen.


def finish_geometry(obj, family, lod):
    """A fitted, split service coat over actual donor geometry and skin."""
    mesh = obj.data
    central = ranged.components(mesh)[0]
    zmax = max(mesh.vertices[i].co.z for i in central)
    zmin = min(mesh.vertices[i].co.z for i in central)
    if not zmin < 0.8 or not zmax > 1.50:
        raise RuntimeError(f"{family} LOD{lod} central body bounds {zmin:.3f}..{zmax:.3f}")
    moved = 0
    max_delta = 0.0
    for i in central:
        v = mesh.vertices[i]
        x, y, z = v.co
        if not (0.72 < z < 1.65 and abs(x) < 0.55):
            continue
        hem = max(0.0, 1.0 - abs(z - 0.94) / 0.42)
        chest = max(0.0, 1.0 - abs(z - 1.43) / 0.25)
        if family.startswith("monk"):
            delta = 0.052 * hem + 0.010 * chest
        elif family.startswith("maa"):
            delta = (0.040 if family == "maa4" else 0.052) * hem + 0.028 * chest
        else:
            delta = 0.030 * hem + 0.016 * chest
        if abs(x) > 0.035 and delta > 0.001:
            v.co.x += delta * (1 if x > 0 else -1)
            moved += 1
            max_delta = max(max_delta, delta)
        if y < -0.05:
            v.co.y -= 0.006 * hem
    if moved < 6 or max_delta < 0.018:
        raise RuntimeError(f"No visible coat redesign on {family} LOD{lod}: {moved=}, {max_delta=}")
    mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(mesh); bm.free(); mesh.update()
    if any(len(face.vertices) != 3 for face in mesh.polygons):
        raise RuntimeError("Nontriangle export geometry")
    return {"body_vertices_moved": moved, "max_fitted_coat_delta_m": max_delta,
            "stock_weights_uv": "retained", "triangles": len(mesh.polygons)}


def tint_atlas(objects, family, color, target):
    nodes = []
    for obj in objects.values():
        hits = [n for n in obj.data.materials[0].node_tree.nodes
                if n.type == "TEX_IMAGE" and n.image and "albedo" in n.name.lower()]
        if len(hits) != 1:
            raise RuntimeError(f"Expected one donor albedo for {obj.name}")
        nodes.append(hits[0])
    if len({(n.image.size[0], n.image.size[1], n.image.filepath) for n in nodes}) != 1:
        raise RuntimeError("LOD atlas mismatch")
    image = nodes[0].image.copy()
    image.name = f"CCP060_{family}_{REV}_albedo"
    w, h = image.size
    values = array("f", [0.0]) * (w*h*4)
    image.pixels.foreach_get(values)
    covered = set()
    for obj in objects.values():
        mesh = obj.data
        central = ranged.components(mesh)[0]
        uv = mesh.uv_layers.active.data
        for face in mesh.polygons:
            if not all(i in central for i in face.vertices):
                continue
            if not 0.73 < face.center.z < 1.60 or abs(face.center.x) > 0.52:
                continue
            pts = [tuple(uv[i].uv) for i in face.loop_indices]
            a,b,c = pts[:3]
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den) < 1e-10: continue
            for yy in range(max(0,int(min(a[1],b[1],c[1])*h)-1), min(h,int(max(a[1],b[1],c[1])*h)+2)):
                py=(yy+.5)/h
                for xx in range(max(0,int(min(a[0],b[0],c[0])*w)-1), min(w,int(max(a[0],b[0],c[0])*w)+2)):
                    px=(xx+.5)/w
                    u=((b[1]-c[1])*(px-c[0])+(c[0]-b[0])*(py-c[1]))/den
                    v=((c[1]-a[1])*(px-c[0])+(a[0]-c[0])*(py-c[1]))/den
                    if u>=-1e-5 and v>=-1e-5 and u+v<=1+1e-5:
                        covered.add(yy*w+xx)
    changed=0
    for pixel in covered:
        i=4*pixel
        r,g,b,a=values[i:i+4]
        if a<0.1 or max(r,g,b)-min(r,g,b)>0.24: continue
        lum=r*.26+g*.66+b*.08
        if not 0.13<lum<0.96: continue
        for j,t in enumerate(color):
            values[i+j]=min(1.0, values[i+j]*.23+t*lum*1.36)
        changed+=1
    if changed<100:
        raise RuntimeError(f"Too few neutral cloth pixels: {family} {changed}")
    image.pixels.foreach_set(values); image.update()
    target.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw=str(target); image.file_format="PNG"; image.save()
    for n in nodes: n.image=image
    return {"path": str(target), "sha256": sha(target), "cloth_pixels": changed}


def stage(family):
    guard()
    manifest_rel, model, age, color = DATA[family]
    manifest = OUT / manifest_rel
    manifest_hash = sha(manifest)
    decoded = read(manifest)
    groups = decoded["geometry"]["groups"]
    if len(groups)!=3 or {g["material"] for g in groups}!={"lod1","lod2","lod3"}:
        raise RuntimeError("Donor has no exact three LODs")
    target=owned(ART/"remaining_roster"/family/(family+"_"+REV+".blend"))
    export=owned(EXPORT/"remaining_roster"/family/REV)
    receipt=owned(OUT/"qualification"/"remaining_roster"/family/REV/"export.json")
    if target.exists() or export.exists() or receipt.exists():
        raise FileExistsError("Preserve existing art candidate")
    if bpy.data.filepath: raise RuntimeError("Use fresh Blender scene")
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    import addon_utils
    modules=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith("garrison")]
    if len(modules)!=1: raise RuntimeError("Garrison extension missing")
    addon_utils.enable(modules[0], default_set=False, persistent=False)
    _, imported=donor.import_donor(family, manifest, model)
    lods={n:donor.source_for_triangles(imported,next(g["triangle_count"] for g in groups if g["material"]==f"lod{n}")) for n in (1,2,3)}
    rig=review.rig_of(lods[1])
    if len(rig.data.bones)!=len(decoded["skeleton"]["bones"]) or any(review.rig_of(x)!=rig for x in lods.values()):
        raise RuntimeError("Donor rig mismatch")
    for n,obj in lods.items(): obj.data.materials[0].name=f"CCP060_{family}_stock_lod{n}"
    final=bpy.data.collections.new(f"CCP060_{family}_final")
    stock=bpy.data.collections.new(f"CCP060_{family}_stock")
    draft=bpy.data.collections.new(f"CCP060_{family}_draft_empty")
    for c in (final,stock,draft): bpy.context.scene.collection.children.link(c)
    clones={}; details={}
    for n,source in lods.items():
        clone=source.copy(); clone.data=source.data.copy(); clone.name=f"CCP060_{family}_author_lod{n}"
        final.objects.link(clone)
        mat=source.data.materials[0].copy(); mat.name=f"lod{n}"
        clone.data.materials.clear(); clone.data.materials.append(mat)
        details[n]=finish_geometry(clone,family,n); clones[n]=clone
        for c in tuple(source.users_collection): c.objects.unlink(source)
        stock.objects.link(source)
        if n>1:
            source.hide_set(True); source.hide_render=True
            clone.hide_set(True); clone.hide_render=True
    atlas=tint_atlas(clones,family,color,owned(export/"albedo.png"))
    donor.set_comparison_layers(final,stock,draft)
    bpy.context.scene["ccp060_exact_stock_model"]=model
    bpy.context.scene["ccp060_age_treatment"]=age
    bpy.context.scene["ccp060_native_equipment"]= "preserved in stock attachment owner"
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    for obj in clones.values():
        for n in obj.data.materials[0].node_tree.nodes:
            if n.type=="TEX_IMAGE" and n.image and "albedo" in n.name.lower():
                n.image.filepath_raw=str(export/"albedo.png")
    review._review_folder_override=owned(OUT/"qualification"/"remaining_roster"/family/REV/"review")
    game=review.render_match(family,REV,lods[1],final)
    close=review.render_match(family,REV,lods[1],final,extra=True)
    module=importlib.import_module(modules[0]+".unit_export")
    export.mkdir(parents=True,exist_ok=True)
    copies=[]
    for n,obj in clones.items():
        c=obj.copy(); c.data=obj.data.copy(); c.name=Path(model).stem+f"_lod{n}"
        bpy.context.scene.collection.objects.link(c)
        for loop in c.data.uv_layers.active.data: loop.uv.y=1-loop.uv.y
        copies.append(c)
    bones=module.skeleton_records(rig)
    module.export_unit_model(rig,copies,export/"model.fbx",bones,three_lods=False)
    snapshot=ranged.authored_snapshot(manifest,clones,export/"authored-snapshot.json")
    control=EXPORT/("archer-matched-control/action.json" if family=="repeater4" else "villager-geometry-route/male/stock-three-lod-control/action.json")
    action=read(control)
    if action.get("overrides") or action.get("attachments"):
        raise RuntimeError("Native actions/equipment must stay stock")
    action["bones"]=bones; action["material_name"]="lod1"; action["textures"]=["albedo"]
    (export/"action.json").write_text(json.dumps(action,indent=2)+"\n",encoding="utf-8")
    payload=(export/"model.fbx").read_bytes()
    skins=payload.count(b"DeformerS\x04\x00\x00\x00Skin")
    clusters=payload.count(b"DeformerS\x07\x00\x00\x00Cluster")
    if skins!=3 or clusters<3*len(decoded["skeleton"]["skin_palettes"][0]["bones"]):
        raise RuntimeError(f"Weighted LOD export incomplete: {skins=} {clusters=}")
    files={p.name:{"sha256":sha(p),"bytes":p.stat().st_size} for p in export.iterdir() if p.is_file()}
    write(receipt,{"schema":"ccp-060-remaining-humanoid-export/v1","status":"three_lod_source_export_only",
        "family":family,"age_treatment":age,"exact_native_body_model":model,"donor_manifest":str(manifest),
        "donor_manifest_sha256":manifest_hash,"blend":str(target),"blend_sha256":sha(target),
        "export":str(export),"files":files,"native_rig_bones":len(rig.data.bones),
        "native_skin_palette_bones":len(decoded["skeleton"]["skin_palettes"][0]["bones"]),
        "fbx_skin_nodes":skins,"fbx_cluster_nodes":clusters,"lod_remodel":details,
        "native_albedo_variant":atlas,"authored_snapshot":snapshot,
        "review":{"game":game,"close":close},"native_equipment":"unchanged",
        "native_cook":"not_run"})
    print(json.dumps({"family":family,"export":str(export),"receipt":str(receipt),"skins":skins,"clusters":clusters}))


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--family",choices=tuple(DATA),required=True)
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    stage(args.family)
