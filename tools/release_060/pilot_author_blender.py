"""Build a reviewable 0.6.0 pilot .blend from exact weighted stock donor geometry.

Run only in an isolated Blender 5.2 process after the shared Blender slot is
granted: blender --background --python this_file -- --pilot ID
This script does not export/cook or touch active tuning. Native clips are never
fabricated. Garments and equipment are surface-derived from weighted stock LOD1.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Euler, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, read, sha, write

PILOT_GEOMETRY = {
    "spear2": [1236],
    "male_villager1": [1188],
    "female_villager1": [1312],
    "horseman2": [1656, 1204],
    "elephant": [3349, 1272],
    "siege_mangonel3": [4449, 384],
}

# Each layer is copied from actual weighted donor triangles. An axis and bone
# region selects the contact surface; offset and taper alter silhouette while
# preserving topology, vertex groups, UVs, armature and stock component origin.
LAYERS = {
    "spear2": [
        (1236, "split_tunic", ("spine", "pelvis"), (0.05, .64), .025, .025, "worn_cloth"),
        (1236, "rattan_chest", ("ribcage", "spine2"), (.44, .94), .050, .07, "rattan"),
        (1236, "chest_cross_tie", ("ribcage", "spine2"), (.40, .93), .058, .04, "dark_cloth"),
        (1236, "close_head_wrap", ("head",), (.64, 1.0), .028, .015, "dark_cloth"),
    ],
    "male_villager1": [
        (1188, "work_tunic", ("spine", "ribcage", "pelvis"), (.12, .85), .028, .025, "worn_cloth"),
        (1188, "rolled_sleeves", ("armupper", "armlower"), (.25, .72), .019, .01, "light_cloth"),
        (1188, "cloth_headband", ("head",), (.83, 1.0), .021, .0, "dark_cloth"),
    ],
    "female_villager1": [
        (1312, "wrapped_work_tunic", ("spine", "ribcage", "pelvis"), (.12, .87), .031, .035, "light_cloth"),
        (1312, "lower_work_wrap", ("pelvis", "cloth"), (.0, .53), .034, .05, "worn_cloth"),
        (1312, "cloth_headband", ("head",), (.82, 1.0), .021, .0, "dark_cloth"),
    ],
    "horseman2": [
        (1204, "rider_split_tunic", ("metarig_spine", "metarig_pelvis"), (.12, .78), .030, .035, "worn_cloth"),
        (1204, "rider_rattan_chest", ("metarig_ribcage",), (.39, .96), .047, .045, "rattan"),
        (1204, "rider_cross_tie", ("metarig_ribcage",), (.39, .96), .057, .02, "dark_cloth"),
        (1204, "rider_close_wrap", ("metarig_head",), (.67, 1.0), .025, .0, "dark_cloth"),
        (1656, "horse_saddle_cloth", ("gaia_c_spine",), (.13, .88), .031, .015, "dark_cloth"),
    ],
    "elephant": [
        (3349, "elephant_saddle_cloth", ("spine1_m", "chest_m", "cloth"), (.28, .93), .047, .02, "dark_cloth"),
        (3349, "cane_harness_panel", ("frontcloth", "midcloth", "rearcloth"), (.13, .88), .068, .02, "rattan"),
        (1272, "mahout_work_tunic", ("metarig_spine", "metarig_ribcage"), (.18, .9), .028, .02, "worn_cloth"),
        (1272, "mahout_close_wrap", ("metarig_head",), (.68, 1.0), .022, .0, "light_cloth"),
    ],
    "siege_mangonel3": [
        (4449, "weathered_beam_cladding", ("bone_mangonel_base", "bone_crossbeam", "bone_top_beam"), (.0, 1.0), .027, .012, "dark_wood"),
        (4449, "iron_braces", ("bone_brace", "bone_crank_base"), (.12, .93), .042, .01, "dark_iron"),
    ],
}

PALETTE = {
    "worn_cloth": (.28, .20, .12, 1),
    "light_cloth": (.52, .43, .29, 1),
    "dark_cloth": (.14, .20, .18, 1),
    "rattan": (.39, .30, .16, 1),
    "dark_wood": (.20, .14, .09, 1),
    "dark_iron": (.105, .11, .11, 1),
}

DYE = {
    "spear2": ((.30, .42, .36, 1), (.22, .28, .37, 1)),
    "male_villager1": ((.42, .48, .32, 1), (.38, .32, .22, 1)),
    "female_villager1": ((.39, .44, .34, 1), (.22, .34, .37, 1)),
    "horseman2": ((.24, .38, .37, 1), (.30, .30, .41, 1)),
    "elephant": ((.29, .40, .35, 1), (.45, .34, .22, 1)),
    "siege_mangonel3": ((.30, .26, .18, 1), (.20, .24, .23, 1)),
}


def donor_dye_material(donor: bpy.types.Material, pilot: str, source_name: str) -> bpy.types.Material:
    mat = donor.copy()
    mat.name = "CCP060_DaiViet_" + pilot + "_" + source_name[:22]
    if not mat.use_nodes:
        raise RuntimeError("Exact donor material has no shader nodes")
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        raise RuntimeError("Exact donor material has no Principled BSDF")
    original = bsdf.inputs["Base Color"].links[0] if bsdf.inputs["Base Color"].is_linked else None
    socket = original.from_socket if original else None
    if original:
        links.remove(original)
    if socket is None:
        base = nodes.new("ShaderNodeRGB")
        base.outputs[0].default_value = bsdf.inputs["Base Color"].default_value[:]
        socket = base.outputs[0]
    for idx, color in enumerate(DYE[pilot]):
        attr = nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "CCP060_dye_" + str(idx)
        strength = nodes.new("ShaderNodeMath")
        strength.operation = "MULTIPLY"
        strength.inputs[1].default_value = .78 if idx == 0 else .65
        links.new(attr.outputs["Fac"], strength.inputs[0])
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        links.new(strength.outputs[0], mix.inputs[0])
        links.new(socket, mix.inputs[1])
        mix.inputs[2].default_value = color
        socket = mix.outputs[0]
    links.new(socket, bsdf.inputs["Base Color"])
    mat.diffuse_color = DYE[pilot][0]
    return mat


def make_donor_remix(source: bpy.types.Object, pilot: str,
                     collection: bpy.types.Collection,
                     stock_only: bpy.types.Collection) -> dict:
    clone = source.copy()
    clone.data = source.data.copy()
    clone.name = "CCP060_DaiViet_native_mesh_" + source.name
    collection.objects.link(clone)
    for old in tuple(source.users_collection):
        old.objects.unlink(source)
    stock_only.objects.link(source)
    zmin = min(v.co.z for v in clone.data.vertices)
    zmax = max(v.co.z for v in clone.data.vertices)
    span = max(zmax - zmin, 1e-6)
    masks = [clone.data.attributes.new("CCP060_dye_" + str(i), "FLOAT", "POINT")
             for i in range(2)]
    groups = {g.index: g.name.casefold() for g in clone.vertex_groups}
    is_machine = pilot == "siege_mangonel3"
    is_mount = pilot in {"horseman2", "elephant"} and len(clone.data.polygons) in {1656, 3349}
    for v in clone.data.vertices:
        z = (v.co.z - zmin) / span
        influences = {groups.get(g.group, ""): g.weight for g in v.groups}
        if is_machine:
            body_score = 1.0 if .18 < z < .88 else .25
            trim_score = 1.0 if z > .68 else .0
        elif is_mount:
            body_score = max((w for name, w in influences.items()
                              if any(token in name for token in ("spine", "chest", "cloth"))), default=0.0)
            trim_score = max((w for name, w in influences.items()
                              if "cloth" in name or "saddle" in name), default=0.0)
        else:
            # The donor has one atlas/material for skin and clothing, while
            # torso vertex weights also taper into arms. Use a broad anatomical
            # body window so actual fabric receives a legible dye without
            # colouring face or hands.
            x = abs(v.co.x)
            body_score = (max(0.0, min(1.0, (z - .29) * 11)) *
                          max(0.0, min(1.0, (.89 - z) * 15)) *
                          max(0.0, min(1.0, (.61 - x) * 8)))
            trim_score = (max(0.0, min(1.0, (z - .12) * 11)) *
                          max(0.0, min(1.0, (.49 - z) * 12)) *
                          max(0.0, min(1.0, (.46 - x) * 7)))
        masks[0].data[v.index].value = max(0.0, min(1.0, body_score))
        masks[1].data[v.index].value = max(0.0, min(1.0, trim_score))
    for i, donor in enumerate(source.data.materials):
        if donor:
            clone.data.materials[i] = donor_dye_material(donor, pilot, source.name)
    return {"source": source.name, "remix": clone.name,
            "triangles": len(clone.data.polygons), "weights_preserved": bool(clone.vertex_groups),
            "uv_preserved": bool(clone.data.uv_layers), "stock_material": [m.name for m in source.data.materials if m],
            "mask": "anatomical cloth/trim windows; donor texture and normal retained",
            "mask_mean": [sum(item.value for item in attr.data) / len(attr.data) for attr in masks]}


def material(name: str, source: bpy.types.Object) -> bpy.types.Material:
    donor = next((slot.material for slot in source.material_slots if slot.material), None)
    if donor is None:
        raise RuntimeError(f"Decoded stock mesh has no donor material: {source.name}")
    key = "CCP060_" + name + "_on_" + donor.name
    old = bpy.data.materials.get(key)
    if old:
        return old
    mat = donor.copy()
    mat.name = key
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        raise RuntimeError(f"Donor material lacks Principled surface: {donor.name}")
    old_color = bsdf.inputs["Base Color"].default_value[:]
    original_link = bsdf.inputs["Base Color"].links[0] if bsdf.inputs["Base Color"].is_linked else None
    source_socket = original_link.from_socket if original_link else None
    if original_link:
        links.remove(original_link)
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "CCP060 donor detail plus local cloth colour"
    mix.blend_type = "MIX"
    if source_socket:
        links.new(source_socket, mix.inputs[1])
    else:
        mix.inputs[1].default_value = old_color
    mix.inputs[2].default_value = PALETTE[name]
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 25 if name != "dark_wood" else 17
    noise.inputs["Detail"].default_value = 2.2
    remap = nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value = .22
    remap.inputs["From Max"].default_value = .78
    remap.inputs["To Min"].default_value = .30 if name != "rattan" else .40
    remap.inputs["To Max"].default_value = .58 if name != "rattan" else .67
    links.new(noise.outputs["Fac"], remap.inputs["Value"])
    links.new(remap.outputs["Result"], mix.inputs[0])
    if name in {"rattan", "dark_wood"}:
        weave = nodes.new("ShaderNodeTexWave")
        weave.wave_type = "BANDS"
        weave.bands_direction = "X"
        weave.inputs["Scale"].default_value = 22 if name == "rattan" else 11
        weave.inputs["Distortion"].default_value = .14
        bands = nodes.new("ShaderNodeMixRGB")
        bands.blend_type = "MULTIPLY"
        bands.inputs[0].default_value = .16 if name == "rattan" else .09
        links.new(mix.outputs[0], bands.inputs[1])
        links.new(weave.outputs["Color"], bands.inputs[2])
        links.new(bands.outputs[0], bsdf.inputs["Base Color"])
    else:
        links.new(mix.outputs[0], bsdf.inputs["Base Color"])
    # Preserve donor normal/bump and all original images. The new roughness
    # variation is bounded and matte, ready for a later atlas bake.
    rough = nodes.new("ShaderNodeMapRange")
    rough.inputs["From Min"].default_value = .2
    rough.inputs["From Max"].default_value = .8
    rough.inputs["To Min"].default_value = .44 if name == "dark_iron" else .73
    rough.inputs["To Max"].default_value = .61 if name == "dark_iron" else .88
    links.new(noise.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    if name == "dark_iron":
        bsdf.inputs["Metallic"].default_value = .66
    mat.diffuse_color = PALETTE[name]
    return mat


def import_donor(pilot: str, manifest: Path, logical_path: str,
                 role: str = "body", require_armature: bool = True
                 ) -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["manifest_path"] = str(manifest)
    collection = bpy.data.collections.new("CCP060_" + pilot + "_" + role + "_stock_reference")
    bpy.context.scene.collection.children.link(collection)
    root = bpy.data.objects.new("CCP060_" + pilot + "_" + role + "_import_root", None)
    collection.objects.link(root)
    root["garrison_logical_path"] = logical_path
    projection = next((module for name, module in sys.modules.items()
                       if name.endswith("garrison.decode_projection")), None)
    if projection is None:
        raise RuntimeError("Installed Garrison decode_projection is not loaded in this Blender instance")
    before = set(bpy.data.objects)
    projection._apply_decoded_static(root, data, create_controls=True)
    created = sorted(set(bpy.data.objects) - before, key=lambda obj: obj.name)
    if require_armature and not any(o.type == "ARMATURE" for o in created):
        raise RuntimeError("Garrison projection did not create donor armature")
    if not any(o.type == "MESH" for o in created):
        raise RuntimeError("Garrison projection did not create stock geometry")
    # Garrison consumes its placeholder root and creates an AoE4 hierarchy.
    # Keep the generated top-level root for socket parenting.
    generated_root = next((o for o in created if o.type == "EMPTY" and o.parent is None), None)
    if generated_root is None:
        raise RuntimeError("Garrison projection did not return a top-level stock root")
    return generated_root, created


def add_equipment(pilot: str, armature: bpy.types.Object) -> list[dict]:
    equipment = read(OUT / "pilots/pilot-equipment.json")["pilots"][pilot]
    placements = []
    bones = {b.name.casefold(): b.name for b in armature.data.bones}
    for name, item in equipment.items():
        manifest = Path(item["manifest"])
        if sha(manifest) != item["manifest_sha256"]:
            raise RuntimeError(f"Stock equipment decode changed: {name}")
        role = Path(name).stem
        root, objects = import_donor(pilot, manifest,
                                     item["stock_model"]["logical_path"], role,
                                     require_armature=False)
        if role == "res_rice_carry":
            # Work cargo is a separate stock reference; a carried load and an
            # active tool are not assumed to display simultaneously.
            for obj in objects:
                if obj.type == "MESH":
                    obj.hide_set(True)
                    obj.hide_render = True
            placements.append({"equipment": name, "status": "stock_reference_hidden_alternate_task"})
            continue
        socket = bones.get("metarig_rarmpalmsocket")
        if socket is None:
            placements.append({"equipment": name, "status": "socket_missing_reference_only"})
            continue
        root.parent = armature
        root.parent_type = "BONE"
        root.parent_bone = socket
        bpy.context.view_layer.update()
        # Blender bone parenting normally seats at the bone tail. The native
        # attachment marker is the socket bone frame, so place the stock
        # weapon grip at that full rest-pose matrix and measure the result.
        expected = armature.matrix_world @ armature.pose.bones[socket].matrix
        root.matrix_world = expected
        bpy.context.view_layer.update()
        actual = root.matrix_world.copy()
        gap = (actual.translation - expected.translation).length
        angle = math.degrees(actual.to_quaternion().rotation_difference(
            expected.to_quaternion()).angle)
        if gap > .001 or angle > 1.0:
            raise RuntimeError(f"Native socket placement mismatch: {name}, "
                               f"{gap:.5f} m, {angle:.3f} deg")
        placements.append({"equipment": name, "status": "stock_model_at_native_right_palm_socket",
                           "socket": socket,
                           "socket_matrix_translation_error_m": gap,
                           "socket_matrix_rotation_error_deg": angle,
                           "limit": "rest-pose grip orientation and action clearance require visual/native review"})
        weapon_meshes = [obj for obj in objects if obj.type == "MESH"]
        highest = [obj for obj in weapon_meshes if "lod1" in obj.name.casefold()]
        if highest:
            for obj in weapon_meshes:
                if obj not in highest:
                    obj.hide_set(True)
                    obj.hide_render = True
    return placements


def source_for_triangles(objects: list[bpy.types.Object], triangles: int) -> bpy.types.Object:
    hits = [o for o in objects if o.type == "MESH" and len(o.data.polygons) == triangles]
    if len(hits) != 1:
        raise RuntimeError(f"Expected one exact stock mesh with {triangles} triangles; got {[o.name for o in hits]}")
    return hits[0]


def score_by_vertex(obj: bpy.types.Object, tokens: tuple[str, ...]) -> list[float]:
    names = {g.index: g.name.lower() for g in obj.vertex_groups}
    result = []
    for v in obj.data.vertices:
        result.append(sum(m.weight for m in v.groups
                          if any(t in names.get(m.group, "") for t in tokens)))
    return result


def make_weighted_layer(source: bpy.types.Object, name: str,
                        tokens: tuple[str, ...], band: tuple[float, float],
                        offset: float, taper: float, color: str,
                        collection: bpy.types.Collection) -> dict:
    scores = score_by_vertex(source, tokens)
    mesh = source.data
    candidates = [f for f in mesh.polygons
                  if sum(scores[i] for i in f.vertices) / len(f.vertices) > .20]
    if not candidates:
        return {"name": name, "status": "no_weighted_faces", "tokens": tokens}
    low = min(f.center.z for f in candidates)
    high = max(f.center.z for f in candidates)
    extent = max(high - low, 1e-6)
    min_x = min(f.center.x for f in candidates)
    max_x = max(f.center.x for f in candidates)
    width = max(max_x - min_x, 1e-6)
    selected = {f.index for f in candidates
                if band[0] <= (f.center.z - low) / extent <= band[1]}
    if "cross_tie" in name:
        selected = {f.index for f in candidates if f.index in selected and
                    abs((f.center.x - min_x) / width -
                        (f.center.z - low) / extent) < .14}
    if len(selected) < 5:
        return {"name": name, "status": "insufficient_faces", "faces": len(selected)}
    layer = source.copy()
    layer.data = source.data.copy()
    layer.name = "CCP060_" + name
    collection.objects.link(layer)
    layer.hide_set(False)
    layer.hide_render = False
    styled_material = material(color, source)
    layer.data.materials.clear()
    layer.data.materials.append(styled_material)
    bm = bmesh.new()
    bm.from_mesh(layer.data)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    bmesh.ops.delete(bm, geom=[face for face in bm.faces if face.index not in selected],
                     context="FACES")
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    center_x = sum(v.co.x for v in bm.verts) / len(bm.verts)
    for v in bm.verts:
        # Fitted donor surface expansion plus a mild shaped garment flare.
        rel = (v.co.z - low) / extent
        flare = taper * max(0.0, .62 - rel)
        v.co += v.normal * offset
        v.co.x += (v.co.x - center_x) * flare
    bm.to_mesh(layer.data)
    bm.free()
    for face in layer.data.polygons:
        face.material_index = 0
    layer.data.update()
    return {"name": name, "status": "donor_surface_remodel", "source": source.name,
            "faces": len(layer.data.polygons), "vertices": len(layer.data.vertices),
            "tokens": tokens, "band": band, "offset_m": offset,
            "taper": taper, "material": styled_material.name,
            "donor_material": next((slot.material.name for slot in source.material_slots
                                    if slot.material), None)}


def set_review_view(objects: set[bpy.types.Object]) -> None:
    points = [obj.matrix_world @ vertex.co for obj in objects
              for vertex in obj.data.vertices]
    if not points:
        return
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (lo + hi) / 2
    extent = max((hi - lo).length, .5)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            view = area.spaces.active
            view.shading.type = "SOLID"
            view.shading.color_type = "MATERIAL"
            view.overlay.show_extras = False
            view.region_3d.view_location = center
            view.region_3d.view_distance = extent * 1.3
            view.region_3d.view_rotation = Euler((math.radians(67), 0,
                                                  math.radians(-35)), "XYZ").to_quaternion()


def set_comparison_layers(remodel: bpy.types.Collection,
                          stock_only: bpy.types.Collection,
                          draft: bpy.types.Collection) -> None:
    scene = bpy.context.scene
    bpy.context.view_layer.name = "Dai Viet pilot"
    donor = scene.view_layers.new("Exact stock donor")
    def find(layer_collection, collection):
        if layer_collection.collection == collection:
            return layer_collection
        for child in layer_collection.children:
            found = find(child, collection)
            if found:
                return found
        return None
    for view, collection in ((donor, remodel), (donor, draft),
                             (bpy.context.view_layer, stock_only),
                             (bpy.context.view_layer, draft)):
        target = find(view.layer_collection, collection)
        if target is None:
            raise RuntimeError(f"Could not isolate {collection.name} in {view.name}")
        target.exclude = True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", required=True, choices=PILOT_GEOMETRY)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    pilot = args.pilot
    guard()
    decodes = read(OUT / "pilots/pilot-decodes.json")
    record = decodes["pilots"][pilot]
    manifest = Path(record["manifest"])
    if sha(manifest) != record["manifest_sha256"]:
        raise RuntimeError("Exact donor decode changed since qualification")
    # Run in a fresh background Blender process with user extensions available.
    # Factory startup removes Garrison's extension repository from discovery.
    if bpy.data.filepath:
        raise RuntimeError(f"Refusing to overwrite an open Blender file: {bpy.data.filepath}")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Enabling the installed extension gives this instance its native weighted
    # projection; absence is a hard stop rather than an unweighted substitute.
    import addon_utils
    modules = [m.__name__ for m in addon_utils.modules()
               if m.__name__.endswith("garrison")]
    if len(modules) != 1:
        raise RuntimeError(f"Expected one installed Garrison extension: {modules}")
    addon_utils.enable(modules[0], default_set=False, persistent=False)
    _body_root, imported = import_donor(pilot, manifest,
                                        record["stock_model"]["logical_path"])
    visible = {source_for_triangles(imported, n) for n in PILOT_GEOMETRY[pilot]}
    rigs = {modifier.object for source in visible for modifier in source.modifiers
            if modifier.type == "ARMATURE" and modifier.object is not None}
    if len(rigs) != 1:
        raise RuntimeError(f"Highest-detail parts do not share one native donor rig: {rigs}")
    armature = rigs.pop()
    for obj in imported:
        if obj.type == "MESH" and obj not in visible:
            obj.hide_set(True)
            obj.hide_render = True
    garment = bpy.data.collections.new("CCP060_" + pilot + "_remodel")
    stock_only = bpy.data.collections.new("CCP060_" + pilot + "_exact_stock_mesh")
    draft = bpy.data.collections.new("CCP060_" + pilot + "_skinned_geometry_draft")
    for collection in (garment, stock_only, draft):
        bpy.context.scene.collection.children.link(collection)
    remixes = [make_donor_remix(source, pilot, garment, stock_only)
               for source in sorted(visible, key=lambda obj: obj.name)]
    layers = []
    for count, name, tokens, band, offset, taper, color in LAYERS[pilot]:
        source = source_for_triangles(imported, count)
        layers.append(make_weighted_layer(source, name, tokens, band,
                                          offset, taper, color, draft))
    equipment = add_equipment(pilot, armature)
    if not any(layer["status"] == "donor_surface_remodel" for layer in layers):
        raise RuntimeError("No donor-derived remodel layer succeeded")
    source_triangles = sum(len(o.data.polygons) for o in visible)
    # No stock Actions are fabricated. Rest pose is a static authoring preview.
    bpy.context.scene["ccp060_pilot"] = pilot
    bpy.context.scene["ccp060_evidence"] = "weighted donor geometry; rest pose; native motion unqualified"
    set_review_view(visible)
    set_comparison_layers(garment, stock_only, draft)
    blend = owned(ART / "pilots" / pilot / (pilot + "_review.blend"))
    blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = {"schema": "ccp-060-pilot-authoring/v1", "pilot": pilot,
              "donor_manifest": str(manifest), "donor_manifest_sha256": sha(manifest),
              "stock_model": record["stock_model"],
              "blend": str(blend), "blend_sha256": sha(blend),
              "highest_lod_base_triangles": source_triangles,
              "all_lod_inventory_triangles": sum(g["triangles"] for g in record["groups"]),
              "remix": remixes, "skinned_geometry_draft": layers,
              "draft_status": "preserved but hidden in both review layers; unsupported native unit model cook",
              "comparison_view_layers": ["Exact stock donor", "Dai Viet pilot"],
              "equipment": equipment,
              "motion": "untouched stock rig, no authored/replaced clips; native motion pending",
              "export_cook_native": "not run"}
    write(OUT / "pilots" / pilot / "authoring.json", report)
    print(json.dumps({"pilot": pilot, "blend": str(blend),
                      "base_triangles": source_triangles,
                      "layers": [(x["name"], x["status"]) for x in layers]}))


if __name__ == "__main__":
    main()
