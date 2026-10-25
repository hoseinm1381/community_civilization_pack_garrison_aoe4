"""Finish six 0.6.0 stock-rig representative silhouettes in separate blends.

Run in an exclusively leased Blender process, one pilot at a time:
  blender --background --python representative_batch.py -- --pilot spear2

This is authoring only. It preserves the pinned pilot input, stock rig, native
weapon attachments and animation, and writes into release_060/representatives.
The designs intentionally use broad stock-scale forms and donor UV/material data.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, EXPORT, OUT, guard, owned, read, sha, write

PILOTS = ("spear2", "male_villager1", "female_villager1", "horseman2",
          "elephant", "siege_mangonel3")
ANATOMY = {
    "spear2": "Native body, head and spear; broad chest armor and split knee tunic",
    "male_villager1": "Native body, head and tools; vented long work tunic",
    "female_villager1": "Native body, head and tools; indigo work cloth, calf wrap and waist tie",
    "horseman2": "Native horse, rider head and weapon; rider armor/tunic, saddle blanket and tack",
    "elephant": "Worker elephant; native animal without rider or goad, broad work drape and harness",
    "siege_mangonel3": "Native machine/crew; side timber rails, cross-braced frame and heavy beam cladding",
}
TINTS = {
    "deep_teal": ((.16,.33,.31), .84),
    "light_ochre": ((.56,.43,.27), .80),
    "indigo": ((.20,.27,.43), .82),
    "brown": ((.32,.22,.13), .73),
    "black_green": ((.13,.20,.16), .85),
}
_tint_cache = {}
_tint_context = None
_pipeline = False
_export_folder_override = None
_review_folder_override = None


def box(obj):
    points = [v.co for v in obj.data.vertices]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return low, high, high - low


def stock_material(source):
    mat = next((m for m in source.data.materials if m is not None), None)
    if mat is None or not source.data.uv_layers:
        raise RuntimeError("Donor material and UV required: " + source.name)
    return mat


def dyed_material(source, tint):
    """Copy only the donor albedo; retain the full native material node graph."""
    if _pipeline:
        return shared_atlas_material(source)
    if tint is None:
        return stock_material(source)
    pilot, revision = _tint_context
    key = (source.data.materials[0].name, tint)
    if key in _tint_cache:
        return _tint_cache[key]
    mat = stock_material(source).copy()
    mat.name = f"CCP060_{pilot}_{tint}_{revision}"
    albedo = next((n for n in mat.node_tree.nodes
                   if n.type == "TEX_IMAGE" and "albedo" in n.name.casefold()), None)
    if albedo is None or albedo.image is None:
        raise RuntimeError("Actual donor albedo node missing: " + source.name)
    original = albedo.image
    image = original.copy()
    image.name = mat.name + "_albedo"
    from array import array
    values = array('f', [0.0]) * (image.size[0]*image.size[1]*4)
    original.pixels.foreach_get(values)
    target, strength = TINTS[tint]
    for i in range(0, len(values), 4):
        lum = (values[i]*.26+values[i+1]*.66+values[i+2]*.08)
        if values[i+3] < .05:
            continue
        for ch in range(3):
            values[i+ch] = min(1.0, values[i+ch]*(1-strength) +
                               target[ch]*lum*strength*1.55)
    image.pixels.foreach_set(values)
    image.update()
    target_path = owned((_export_folder_override or EXPORT / "representatives" / pilot / revision) /
                        (tint+"_albedo.png"))
    target_path.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(target_path)
    image.file_format = "PNG"
    image.save()
    albedo.image = image
    _tint_cache[key] = mat
    return mat


def shared_atlas_material(source):
    """One albedo and one exact native material graph per donor mesh/LOD."""
    pilot, revision = _tint_context
    if pilot == "siege_mangonel3":
        return stock_material(source)
    donor = stock_material(source)
    key = (donor.name, "shared")
    if key in _tint_cache:
        return _tint_cache[key]
    mat = donor.copy()
    mat.name = f"CCP060_{pilot}_single_atlas_{revision}"
    node = next((n for n in mat.node_tree.nodes
                 if n.type == "TEX_IMAGE" and "albedo" in n.name.casefold()), None)
    if node is None or node.image is None:
        raise RuntimeError("No native albedo node")
    src = node.image
    image = src.copy()
    image.name = mat.name + "_albedo"
    from array import array
    w, h = image.size
    values = array('f', [0.0]) * (w*h*4)
    src.pixels.foreach_get(values)
    is_mount = pilot == "horseman2" and "horse_lod" in source.name
    if pilot == "spear2":
        color, rect = (.16,.33,.31), (0,.31,.76,1)
    elif pilot == "male_villager1":
        color, rect = (.56,.43,.27), (0,.34,1,1)
    elif pilot == "female_villager1":
        color, rect = (.20,.27,.43), (0,.32,1,1)
    elif pilot == "horseman2" and is_mount:
        color, rect = (.20,.27,.43), (0,.10,.44,.53)
    elif pilot == "horseman2":
        color, rect = (.16,.33,.31), (.28,.35,1,1)
    elif pilot == "elephant":
        color, rect = (.20,.27,.43), (.58,.40,1,1)
    else:
        raise RuntimeError(pilot)
    changed = 0
    for y in range(h):
        yt = 1-(y+.5)/h
        if not rect[1] <= yt <= rect[3]:
            continue
        for x in range(w):
            xt = (x+.5)/w
            if not rect[0] <= xt <= rect[2]:
                continue
            i = (y*w+x)*4
            r,g,b,a = values[i:i+4]
            if a < .1 or max(r,g,b)-min(r,g,b) > .17:
                continue
            lum = r*.26+g*.66+b*.08
            if not .16 <= lum <= .93:
                continue
            for ch in range(3):
                values[i+ch] = min(1.0,values[i+ch]*.22 + color[ch]*lum*1.18)
            changed += 1
    if changed < 100:
        raise RuntimeError(f"Atlas cloth selection too small: {pilot} {source.name} {changed}")
    image.pixels.foreach_set(values)
    image.update()
    target = owned((_export_folder_override or EXPORT / "representatives" / pilot / revision) /
                   ("single_atlas_"+str(len(_tint_cache))+".png"))
    target.parent.mkdir(parents=True,exist_ok=True)
    image.filepath_raw = str(target)
    image.file_format = "PNG"
    image.save()
    node.image = image
    _tint_cache[key] = mat
    return mat


def source_uv(source, role):
    """Choose an actual UV face from the donor's rigged structural surface."""
    uv = source.data.uv_layers.active.data
    mats = source.data.materials
    low, high, span = box(source)
    groups = {g.index:g.name.casefold() for g in source.vertex_groups}
    choices = []
    for face in source.data.polygons:
        if face.loop_total < 3:
            continue
        mat = mats[face.material_index] if face.material_index < len(mats) else None
        if mat is None:
            continue
        if role == "timber":
            # This donor's native material is one layered page, not a named
            # wood slot. Restrict UV choice to real weighted timber beams.
            material_score = sum(max((w.weight for w in source.data.vertices[i].groups
                                      if any(t in groups.get(w.group, "") for t in
                                             ("bone_crossbeam", "bone_top_beam",
                                              "bone_mangonel_base"))), default=0)
                                 for i in face.vertices)/len(face.vertices)
            spatial_score = 1-abs((face.center.z-low.z)/max(span.z,1e-6)-.40)
        else:
            raise ValueError(role)
        if material_score < .65:
            continue
        loops = list(face.loop_indices)[:3]
        coords = [tuple(uv[i].uv) for i in loops]
        area = abs((coords[1][0]-coords[0][0])*(coords[2][1]-coords[0][1])-
                   (coords[2][0]-coords[0][0])*(coords[1][1]-coords[0][1]))
        if area > 1e-7:
            choices.append((material_score+spatial_score*.1, face.index, mat, coords))
    if not choices:
        raise RuntimeError(f"No actual {role} donor material/UV face on {source.name}")
    _score, index, mat, coords = max(choices, key=lambda item:item[0])
    return index, mat, coords


def rig_of(source):
    rigs = {m.object for m in source.modifiers if m.type == "ARMATURE" and m.object}
    if len(rigs) != 1:
        raise RuntimeError("Expected donor rig on " + source.name)
    return rigs.pop()


def group_name(source, tokens):
    names = [g.name for g in source.vertex_groups]
    for token in tokens:
        found = [name for name in names if token in name.casefold()]
        if found:
            return found[0]
    raise RuntimeError(f"No rig anchor {tokens} on {source.name}")


def donor_layer(source, collection, label, bones, band, side=None,
                expand=.035, flare=.0, z_shift=0.0, tint=None):
    """Cut an actual weighted donor surface, keeping all native UVs and weights."""
    low, high, span = box(source)
    groups = {g.index: g.name.casefold() for g in source.vertex_groups}
    mesh = source.data
    def score(face):
        return sum(max((w.weight for w in mesh.vertices[i].groups
                        if any(t in groups.get(w.group, "") for t in bones)),
                       default=0.0) for i in face.vertices) / len(face.vertices)
    selected = set()
    for face in mesh.polygons:
        z = (face.center.z - low.z) / max(span.z, 1e-6)
        if score(face) < .20 or not (band[0] <= z <= band[1]):
            continue
        if side == "left" and face.center.x > (low.x + high.x) * .5:
            continue
        if side == "right" and face.center.x < (low.x + high.x) * .5:
            continue
        selected.add(face.index)
    if len(selected) < 5:
        raise RuntimeError(f"{label}: only {len(selected)} donor faces")
    part = source.copy()
    part.data = source.data.copy()
    part.name = "CCP060_finish_" + label
    collection.objects.link(part)
    part.hide_set(False)
    part.hide_render = False
    part.data.materials.clear()
    part.data.materials.append(dyed_material(source, tint))
    bm = bmesh.new()
    bm.from_mesh(part.data)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in selected],
                     context="FACES")
    bm.normal_update()
    center_x = (low.x + high.x) * .5
    for v in bm.verts:
        rel = (v.co.z - low.z) / max(span.z, 1e-6)
        outward = expand * (1.0 + flare * max(0.0, .65-rel))
        v.co += v.normal * outward
        v.co.x += (v.co.x-center_x) * flare * max(0.0, .65-rel)
        v.co.z += z_shift
    bm.to_mesh(part.data)
    bm.free()
    part.data.update()
    if _pipeline and tint in ("black_green","brown"):
        # For the new cap/armor only, sample the donor's existing dark hair or
        # leather UV block. All geometry still uses the one body atlas.
        head_regions = {"spear2":(.08,.02,.58,.16),
                        "male_villager1":(.01,.02,.20,.26),
                        "female_villager1":(.01,.02,.20,.25),
                        "horseman2":(.32,.02,.75,.22)}
        region = (head_regions[_tint_context[0]] if tint == "black_green" else
                  (.02,.02,.68,.28))
        layer_uv = part.data.uv_layers.active.data
        xs = [p.co.x for p in part.data.vertices]
        zs = [p.co.z for p in part.data.vertices]
        dx = max(max(xs)-min(xs),1e-6)
        dz = max(max(zs)-min(zs),1e-6)
        for loop in part.data.loops:
            v = part.data.vertices[loop.vertex_index].co
            u = region[0]+(v.x-min(xs))/dx*(region[2]-region[0])
            top = region[1]+(v.z-min(zs))/dz*(region[3]-region[1])
            layer_uv[loop.index].uv = (u,1-top)
    return {"name": part.name, "donor": source.name, "faces": len(part.data.polygons),
            "uv": bool(part.data.uv_layers), "weights": bool(part.vertex_groups),
            "band": band, "anchor_tokens": bones, "albedo_tint":tint}


def timber(source, collection, label, a, b, width, depth, anchor_tokens, role="timber"):
    """A stock-textured eight-corner beam weighted to the donor's nearest anchor."""
    a, b = Vector(a), Vector(b)
    direction = (b-a).normalized()
    up = Vector((0, 0, 1))
    side = direction.cross(up)
    if side.length < .01:
        side = direction.cross(Vector((0, 1, 0)))
    side.normalize()
    vertical = side.cross(direction).normalized()
    corners = []
    for center in (a, b):
        for sx, sy in ((-1,-1), (1,-1), (1,1), (-1,1)):
            corners.append(center + side * sx * width/2 + vertical * sy * depth/2)
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5),
             (2,3,7,6), (3,0,4,7)]
    mesh = bpy.data.meshes.new("CCP060_finish_" + label)
    mesh.from_pydata(corners, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    uv_face, mat, tri_uv = source_uv(source, role)
    mesh.materials.append(mat)
    uv = mesh.uv_layers.new(name="UVMap")
    for face in mesh.polygons:
        for j, loop in enumerate(face.loop_indices):
            uv.data[loop].uv = tri_uv[j % 3]
    anchor = group_name(source, anchor_tokens)
    obj.vertex_groups.new(name=anchor).add(list(range(8)), 1.0, "REPLACE")
    mod = obj.modifiers.new("Exact stock rig", "ARMATURE")
    mod.object = rig_of(source)
    return {"name": obj.name, "donor_material": mat.name,
            "donor_uv_face":uv_face, "donor_uv_role":role,
            "rig_anchor": anchor, "length": (b-a).length,
            "seat": [list(a), list(b)], "triangles": len(faces)*2}


def worker_cargo_box(source, collection, label, center, size):
    """Low-poly crate timber, UV'd to the stock elephant atlas's plank patch.

    This stock donor atlas includes a broad brown wooden plank panel at
    top-left (image x .01-.14, top y .10-.22). The crate uses the exact body
    material and native atlas; no new shader or unrelated prop material.
    """
    cx,cy,cz = center
    sx,sy,sz = (v*.5 for v in size)
    vertices = [(cx+x*sx,cy+y*sy,cz+z*sz)
                for z in (-1,1) for y in (-1,1) for x in (-1,1)]
    faces = ((0,1,3,2),(4,6,7,5),(0,4,5,1),
             (1,5,7,3),(3,7,6,2),(2,6,4,0))
    mesh = bpy.data.meshes.new("CCP060_cargo_"+label)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    mesh.materials.append(dyed_material(source, "brown"))
    uv = mesh.uv_layers.new(name="UVMap")
    for face in mesh.polygons:
        for j, loop in enumerate(face.loop_indices):
            # Actual stock planks, with enough UV extent to retain wood grain.
            u = .012 + (.122 if j in (1,2) else 0)
            v = .895 - (.114 if j in (2,3) else 0)
            uv.data[loop].uv = (u,v)
    anchor = group_name(source,("spine1_m",))
    obj.vertex_groups.new(name=anchor).add(list(range(8)),1.0,"REPLACE")
    mod = obj.modifiers.new("Native worker elephant spine", "ARMATURE")
    mod.object = rig_of(source)
    return {"name":obj.name,"kind":"wooden cargo", "donor":source.name,
            "native_uv_region":[.012,.105,.134,.219], "anchor":anchor,
            "triangles":12,"bounds_center":list(center),"size":list(size)}


def team_preview(color):
    touched = 0
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nodes = mat.node_tree.nodes
        controls = nodes.get("GARRISON Material Controls")
        if controls and "Team Colour" in controls.inputs and "Team Colour Strength" in controls.inputs:
            controls.inputs["Team Colour"].default_value = color
            controls.inputs["Team Colour Strength"].default_value = 1.0
            touched += 1
        else:
            fallback = nodes.get("GARRISON Team Colour Preview")
            strength = nodes.get("GARRISON Team Colour Preview Strength")
            if fallback and strength:
                fallback.outputs[0].default_value = color
                strength.outputs[0].default_value = 1.0
                touched += 1
    return touched


def render_match(pilot, revision, source, final_collection, extra=False):
    """Native scale preview: the subject occupies about a tenth of frame height."""
    scene = bpy.context.scene
    def locate(layer, collection):
        if layer.collection == collection:
            return layer
        for child in layer.children:
            found = locate(child, collection)
            if found:
                return found
        return None
    donor_layer_view = scene.view_layers.get("Exact stock donor")
    finish_layer_view = scene.view_layers.get("Dai Viet pilot")
    if donor_layer_view is None or finish_layer_view is None:
        raise RuntimeError("Pilot comparison layers absent")
    locate(donor_layer_view.layer_collection, final_collection).exclude = True
    camera_data = bpy.data.cameras.new("CCP060_review_only_camera")
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    corners = [source.matrix_world @ Vector(corner) for corner in source.bound_box]
    low = Vector(tuple(min(p[i] for p in corners) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    center = (low+high)*.5
    dimensions = high-low
    direction = Vector((1.0, -1.0, 1.3)).normalized()
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(dimensions.x, dimensions.y, dimensions.z) * 8.7
    camera.location = center + direction * max(12.0, camera_data.ortho_scale*1.5)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.use_nodes = True
    world_bg = scene.world.node_tree.nodes.get("Background")
    if world_bg:
        world_bg.inputs["Color"].default_value = (.65,.67,.66,1)
        world_bg.inputs["Strength"].default_value = .8
    lamp_data = bpy.data.lights.new("CCP060_review_only_light", "AREA")
    lamp = bpy.data.objects.new(lamp_data.name, lamp_data)
    scene.collection.objects.link(lamp)
    lamp.location = center + Vector((2,-3,5))
    lamp.rotation_euler = (center-lamp.location).to_track_quat("-Z", "Y").to_euler()
    lamp_data.energy = 1500
    lamp_data.size = 5
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    low_screen = world_to_camera_view(scene, camera, Vector((center.x, center.y, low.z)))
    high_screen = world_to_camera_view(scene, camera, Vector((center.x, center.y, high.z)))
    px = abs(high_screen.y-low_screen.y)*960
    review_dir = owned(_review_folder_override or
                       OUT / "representatives" / pilot / revision / "review")
    review_dir.mkdir(parents=True, exist_ok=True)
    images = {}
    if extra:
        camera_data.ortho_scale = max(dimensions.x, dimensions.y, dimensions.z) * 1.55
        camera.location = center + direction * max(12.0, camera_data.ortho_scale*1.5)
        frames = (("Exact stock donor","stock_close"),
                  ("Dai Viet pilot","finish_close"))
    else:
        frames = (("Exact stock donor","stock_game"),
                  ("Dai Viet pilot","finish_game"))
    for layer_name, key in frames:
        path = owned(review_dir / (key+".png"))
        if path.exists():
            raise FileExistsError(path)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, layer=layer_name)
        images[key] = {"path":str(path), "sha256":sha(path)}
    if extra:
        camera_data.ortho_scale = max(dimensions.x, dimensions.y, dimensions.z) * 8.7
        camera.location = center + direction * max(12.0, camera_data.ortho_scale*1.5)
        for key, color in (("finish_red_game", (1,.06,.04,1)),
                           ("finish_blue_game", (.04,.21,1,1))):
            count = team_preview(color)
            if count == 0:
                raise RuntimeError("Native team-color preview controls missing")
            path = owned(review_dir / (key+".png"))
            if path.exists():
                raise FileExistsError(path)
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True, layer="Dai Viet pilot")
            images[key] = {"path":str(path),"sha256":sha(path),"control_materials":count}
    return {"camera_elevation_deg":math.degrees(math.asin(direction.z)),
            "native_resolution":[960,960], "projected_vertical_span_px":px,
            "orthographic_scale":camera_data.ortho_scale, "images":images,
            "matched_camera":True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", required=True, choices=PILOTS)
    parser.add_argument("--revision", default="v1", choices=("v1","v2","v3","v4","v5","v6","v7"))
    parser.add_argument("--pipeline", action="store_true", help="Use one donor albedo/material per LOD")
    parser.add_argument("--inspect", action="store_true", help="Read donor geometry without writing")
    parser.add_argument("--review-only", action="store_true", help="Add close and red/blue previews")
    parser.add_argument("--audit-legacy", action="store_true", help="Inspect legacy pilot draft visibility")
    parser.add_argument("--inspect-cargo", action="store_true", help="Measure elephant work-drape contact")
    parser.add_argument("--cargo", action="store_true", help="Add riderless wooden worker cargo")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    guard()
    pilot = args.pilot
    revision = args.revision
    global _tint_context, _pipeline
    _tint_context = (pilot, revision)
    _pipeline = args.pipeline
    receipt = read(OUT / "pilots" / pilot / "authoring.json")
    base = Path(receipt["blend"])
    if sha(base) != receipt["blend_sha256"]:
        raise RuntimeError("Pinned donor blend changed")
    pose_receipt = None
    if pilot in ("horseman2", "elephant"):
        pose_receipt = read(OUT / "pilots" / pilot / "pose.json")
        posed = Path(pose_receipt["blend"])
        if sha(posed) != pose_receipt["blend_sha256"]:
            raise RuntimeError("Pinned native idle review blend changed")
        base = posed
    if args.inspect:
        bpy.ops.wm.open_mainfile(filepath=str(base))
        inventory = []
        for item in receipt["remix"]:
            source = bpy.data.objects[item["source"]]
            low, high, span = box(source)
            inventory.append({"name":source.name, "triangles":len(source.data.polygons),
                              "bounds":[list(low),list(high)],
                              "materials":[m.name if m else None for m in source.data.materials],
                              "material_images":[{"name":n.name,"image":n.image.name if n.image else None}
                                  for m in source.data.materials if m and m.use_nodes
                                  for n in m.node_tree.nodes if n.type == "TEX_IMAGE"],
                              "groups":[g.name for g in source.vertex_groups],
                              "uv":bool(source.data.uv_layers)})
        print(json.dumps({"pilot":pilot,"donors":inventory},indent=2))
        return
    target = owned(ART / "representatives" / pilot / (pilot + "_finish_"+revision+".blend"))
    report = owned(OUT / "representatives" / pilot / revision / "authoring.json")
    if args.inspect_cargo:
        if pilot != "elephant":
            raise ValueError("Cargo inspection requires worker elephant")
        bpy.ops.wm.open_mainfile(filepath=str(target))
        animal = max((bpy.data.objects[item["remix"]] for item in receipt["remix"]),
                     key=lambda o:len(o.data.polygons))
        low, high, span = box(animal)
        x0,y0,z0 = (low+high)*.5
        samples=[]
        for face in animal.data.polygons:
            p=face.center
            if (abs(p.x-x0)<span.x*.26 and abs(p.y-y0)<span.y*.22
                    and face.normal.z>.25 and p.z>low.z+span.z*.65):
                samples.append([p.x,p.y,p.z,face.normal.z])
        samples.sort(key=lambda p:p[2])
        bins=[]
        for by in range(6):
            center_y=low.y+span.y*(by+.5)/6
            band=[p for p in samples if abs(p[1]-center_y)<span.y/12]
            bins.append({"y":center_y,"count":len(band),
                         "z25":sorted(p[2] for p in band)[len(band)//4] if band else None,
                         "z75":sorted(p[2] for p in band)[len(band)*3//4] if band else None})
        print(json.dumps({"bounds":[list(low),list(high)],"top_patch_count":len(samples),
                          "longitudinal_bins":bins,
                          "top_patch_min":samples[0] if samples else None,
                          "top_patch_median":samples[len(samples)//2] if samples else None,
                          "top_patch_max":samples[-1] if samples else None,
                          "bone_names":[g.name for g in animal.vertex_groups if
                                        any(t in g.name.casefold() for t in ("spine","cloth"))]},indent=2))
        return
    if args.audit_legacy:
        bpy.ops.wm.open_mainfile(filepath=str(target))
        draft = bpy.data.collections["CCP060_"+pilot+"_skinned_geometry_draft"]
        data = {"pilot":pilot,"draft_objects":[{"name":o.name,"hidden_render":o.hide_render,
                "triangles":len(o.data.polygons)} for o in draft.objects if o.type == "MESH"],
                "views":{v.name:next((c.exclude for c in v.layer_collection.children
                                     if c.collection == draft),None)
                         for v in bpy.context.scene.view_layers}}
        print(json.dumps(data,indent=2))
        return
    if args.review_only:
        done = read(report)
        if sha(target) != done["blend_sha256"]:
            raise RuntimeError("Representative blend changed before extra visual review")
        bpy.ops.wm.open_mainfile(filepath=str(target))
        source = max((bpy.data.objects[item["source"]] for item in receipt["remix"]),
                     key=lambda o:len(o.data.polygons))
        collection = bpy.data.collections["CCP060_"+pilot+"_final_geometry"]
        visual = render_match(pilot,revision,source,collection,extra=True)
        write(OUT / "representatives" / pilot / revision / "close-and-owner-review.json",
              {"schema":"ccp-060-representative-review/v1","pilot":pilot,
               "blend":str(target),"blend_sha256":sha(target),
               "boundary":"Blender preview, not native match or cook",**visual})
        print(json.dumps({"pilot":pilot,"visual_review":list(visual["images"]) }))
        return
    if target.exists() or report.exists():
        raise FileExistsError("Representative output exists; preserve it before iteration")
    bpy.ops.wm.open_mainfile(filepath=str(base))
    collection = bpy.data.collections.new("CCP060_" + pilot + "_final_geometry")
    bpy.context.scene.collection.children.link(collection)
    sources = [bpy.data.objects[item["source"]] for item in receipt["remix"]]
    if _pipeline:
        for item in receipt["remix"]:
            source = bpy.data.objects[item["source"]]
            remix = bpy.data.objects[item["remix"]]
            remix.data.materials.clear()
            remix.data.materials.append(shared_atlas_material(source))
    by_size = sorted(sources, key=lambda x: len(x.data.polygons), reverse=True)
    body = by_size[0]
    low, high, span = box(body)
    x0, y0, z0 = (low+high)*.5
    parts = []
    add = lambda *x, **k: parts.append(donor_layer(body, collection, *x, **k))
    beam = lambda *x, **k: parts.append(timber(body, collection, *x, **k))
    if pilot == "spear2":
        add("split_knee_tunic", ("pelvis", "spine"), (.12,.65), expand=.060, flare=.22, tint="deep_teal")
        add("wide_rattan_chest", ("ribcage", "spine"), (.43,.85), expand=.095, tint="light_ochre")
    elif pilot == "male_villager1":
        add("vented_work_tunic", ("spine", "ribcage", "pelvis"), (.17,.57), expand=.060, flare=.20, tint="light_ochre")
    elif pilot == "female_villager1":
        add("calf_wrap", ("cloth", "pelvis"), (.12,.53), expand=.077, flare=.23, tint="indigo")
        add("tied_waist", ("pelvis", "spine"), (.38,.49), expand=.065, tint="brown")
    elif pilot == "horseman2":
        rider = min(sources, key=lambda x: len(x.data.polygons))
        parts.append(donor_layer(rider, collection, "rider_split_tunic",
                                 ("spine", "pelvis"), (.20,.74), expand=.055, flare=.14, tint="deep_teal"))
        parts.append(donor_layer(rider, collection, "rider_chest_armor",
                                 ("ribcage",), (.45,.87), expand=.073, tint="brown"))
        add("broad_horse_blanket", ("spine", "saddle", "cloth"), (.40,.85), expand=.078, flare=.16, tint="indigo")
        add("horse_tack", ("chest", "spine"), (.31,.72), expand=.043, tint="brown")
    elif pilot == "elephant":
        rider = min(sources, key=lambda x: len(x.data.polygons))
        rider_remix = bpy.data.objects[next(item["remix"] for item in receipt["remix"]
                                            if item["source"] == rider.name)]
        rider_remix.hide_set(True)
        rider_remix.hide_render = True
        # The inherited combat donor contains a mahout and palm-socket goad.
        # This actual Vietnamese family is the Worker Elephant: remove both
        # from the new representative while leaving the pinned donor intact.
        for obj in bpy.data.objects:
            if obj.type == "MESH" and "sul_spear_goad" in obj.name.casefold():
                obj.hide_set(True)
                obj.hide_render = True
        add("broad_saddle_cloth", ("spine", "chest", "cloth"), (.47,.89), expand=.10, flare=.10, tint="indigo")
        add("cane_side_harness", ("frontcloth", "midcloth", "rearcloth"), (.31,.76), expand=.094, tint="brown")
        if args.cargo:
            # Riderless WORK elephant. Sit the crate on the native rear back
            # drape: measured central donor top ~3.34-3.48 at y -0.5..0.4.
            # The shallow timber floor deliberately enters that drape by
            # ~0.04 so it stays seated through the sampled idle pose.
            cargo = lambda *a: parts.append(worker_cargo_box(body,collection,*a))
            y = -.12
            z = 3.44
            cargo("crate_floor",(0,y,z),(.96,1.18,.08))
            for side,x in (("left",-.46),("right",.46)):
                cargo("crate_side_"+side,(x,y,z+.19),(.055,1.18,.32))
            for end,ey in (("front",y-.56),("rear",y+.56)):
                cargo("crate_end_"+end,(0,ey,z+.19),(.96,.055,.32))
            for i,x in enumerate((-.28,0,.28)):
                cargo("cargo_stick_"+str(i+1),(x,y,z+.405),(.065,1.37,.065))
    else:
        add("heavy_side_cladding", ("bone_mangonel_base", "bone_crossbeam"),
            (.18,.78), expand=.066, tint="brown")
        add("throwing_beam_shell", ("bone_top_beam", "bone_arm"),
            (.42,.95), expand=.055, tint="brown")
        z = low.z + span.z*.38
        for side, x in (("left", low.x+span.x*.13), ("right", high.x-span.x*.13)):
            beam(side+"_diagonal_brace", (x,low.y+span.y*.16,z),
                 (x,high.y-span.y*.16,z+span.z*.28),span.x*.055,span.z*.065,
                 ("bone_mangonel_base", "bone_crossbeam"))
        beam("front_crossbar", (low.x+span.x*.13,low.y+span.y*.17,z),
             (high.x-span.x*.13,low.y+span.y*.17,z),span.y*.06,span.z*.06,
             ("bone_mangonel_base", "bone_crossbeam"))
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene["ccp060_representative"] = pilot
    bpy.context.scene["ccp060_design_anatomy"] = ANATOMY[pilot]
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    review = render_match(pilot, revision, body, collection)
    write(report, {"schema":"ccp-060-representative-authoring/v1", "pilot":pilot,
                   "anatomy": ANATOMY[pilot], "base":str(base),
                   "base_sha256":sha(base),
                   "native_idle_clip":pose_receipt["clip_name"] if pose_receipt else None,
                   "blend":str(target),
                   "blend_sha256":sha(target), "parts":parts,
                   "review":review,
                   "rig_and_animation":"stock rig; no clip or weapon modification",
                   "material":("one copied native albedo/material graph per donor mesh; owner pattern and skin LUT unchanged"
                               if _pipeline else "per-part albedo preview only; native one-atlas route unqualified"),
                   "gates":"authoring only; visual, export, cook, readback and native match pending"})
    print(json.dumps({"pilot":pilot,"blend":str(target),"parts":len(parts)}))


if __name__ == "__main__":
    main()
