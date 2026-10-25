"""Export a reviewed Garden detail revision through the claimed Blender MCP.

Call export_garden(xy_scale, z_scale, y_shift, z_shift) after preview approval.
The four alignment values are explicit so footprint and stock model size are
never conflated. The native stamp transform is retained by integration; this
export applies only a model-local artwork fit and never bakes the stamp.
"""
from pathlib import Path
import hashlib
import json
import shutil
import bpy
from mathutils import Vector

ROOT = Path("E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison")
COLLECTION = "CCP070_Imperial_Garden_Detailed_r2"
TARGET = ROOT / "art/exports/buildings_070/garden"
SOURCE_MAPS = TARGET / "textures"
STAGES = (0, 20, 0, 80, 20, 20, 20)
STOCK_X = (-5.4922, 5.4922)
STOCK_Y = (-6.8164, 4.9141)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_garden(xy_scale, z_scale, y_shift, z_shift=0.0):
    if not (0 < xy_scale < 1 and 0 < z_scale < 3):
        raise ValueError("Explicit positive model-local scales are required")
    if (TARGET / "model.fbx").exists() or (TARGET / "building.json").exists():
        raise FileExistsError("Retain existing Garden export; use a revision dir")
    source = bpy.data.collections.get(COLLECTION)
    if source is None:
        raise RuntimeError("Reviewed Garden detail collection not found")
    parts = {}
    for obj in source.objects:
        for index in range(7):
            if obj.name.endswith("garrison_part_%04d" % index):
                parts[index] = obj
    if set(parts) != set(range(7)):
        raise RuntimeError("Garden requires exactly seven detail source parts")
    if len(source.objects) != 7:
        raise RuntimeError("Unexpected Garden detail object count")
    per_part_triangles = {i: sum(len(poly.vertices)-2 for poly in part.data.polygons)
                          for i, part in parts.items()}
    healthy_triangles = sum(per_part_triangles[i] for i in (0, 1, 4, 5, 6))
    if healthy_triangles >= 90000:
        raise RuntimeError("Garden healthy-geometry interim triangle cap exceeded")
    if any(count == 0 for count in per_part_triangles.values()):
        raise RuntimeError("Garden lifecycle part is empty")
    if any(len(part.data.uv_layers) == 0 or len(part.data.materials) != 1
           for part in parts.values()):
        raise RuntimeError("Missing UV or single-atlas material")
    if len({part.data.materials[0].name for part in parts.values()}) != 1:
        raise RuntimeError("Garden parts do not share the same atlas material")

    all_points = [Vector((v.co.x*xy_scale, v.co.y*xy_scale+y_shift,
                          v.co.z*z_scale+z_shift))
                  for part in parts.values() for v in part.data.vertices]
    mins = [min(p[i] for p in all_points) for i in range(3)]
    maxs = [max(p[i] for p in all_points) for i in range(3)]
    if mins[0] < STOCK_X[0]-.05 or maxs[0] > STOCK_X[1]+.05:
        raise RuntimeError("Garden model-local X exceeds official stock envelope")
    if mins[1] < STOCK_Y[0]-.05 or maxs[1] > STOCK_Y[1]+.05:
        raise RuntimeError("Garden model-local Y exceeds official stock envelope")

    # Clones are retained in a hidden owned collection to avoid the installed
    # MCP's removed-RNA reporting bug. No earlier revision is deleted.
    archive_name = "CCP070_Garden_Export_Clones_r2"
    if bpy.data.collections.get(archive_name):
        raise RuntimeError("Garden export clones already exist")
    archive = bpy.data.collections.new(archive_name)
    bpy.context.scene.collection.children.link(archive)
    bpy.ops.object.select_all(action="DESELECT")
    clones = []
    for index in range(7):
        original = parts[index]
        clone = original.copy()
        clone.data = original.data.copy()
        clone.name = "garrison_part_%04d" % index
        archive.objects.link(clone)
        clone.hide_set(False)
        clone.hide_render = False
        clone.location = (0, 0, 0)
        clone.rotation_euler = (0, 0, 0)
        clone.scale = (1, 1, 1)
        for vertex in clone.data.vertices:
            vertex.co = (vertex.co.x*xy_scale,
                         vertex.co.y*xy_scale+y_shift,
                         vertex.co.z*z_scale+z_shift)
        # The established 0.2.0/0.6.1 FBX route flips UV V on clones only.
        for loop in clone.data.uv_layers.active.data:
            loop.uv.y = 1.0-loop.uv.y
        clone.select_set(True)
        clones.append(clone)
    bpy.context.view_layer.objects.active = clones[0]
    TARGET.mkdir(parents=True, exist_ok=True)
    result = bpy.ops.export_scene.fbx(
        filepath=str(TARGET / "model.fbx"), use_selection=True,
        object_types={"MESH"}, use_mesh_modifiers=False,
        add_leaf_bones=False, bake_anim=False,
        axis_forward="-Z", axis_up="Y", use_custom_props=False)
    if "FINISHED" not in result:
        raise RuntimeError("Blender FBX export did not finish")

    for channel in ("albedo", "normal", "roughness", "metalness"):
        source_map = SOURCE_MAPS / ("garden_" + channel + "_2048.png")
        shutil.copyfile(source_map, TARGET / (channel + ".png"))
    manifest = {
        "schema": "garrison.building-source/v1",
        "profile": "english-house",
        "parts": [{"name": "garrison_part_%04d" % i,
                   "first_stage": STAGES[i]} for i in range(7)],
        "material_name": clones[0].data.materials[0].name,
        "textures": {name: name+".png" for name in
                     ("albedo", "normal", "roughness", "metalness")},
    }
    (TARGET / "building.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    receipt = {
        "schema": "ccp-070-garden-export-receipt/v1",
        "input_collection": COLLECTION,
        "healthy_triangle_count": healthy_triangles,
        "per_part_triangle_count": per_part_triangles,
        "selector_parts": {"healthy": [0, 1, 4, 5, 6],
                           "heavy_damage": [0, 3], "ruins": [2]},
        "model_local_fit": {"xy_scale": xy_scale, "z_scale": z_scale,
                            "y_shift": y_shift, "z_shift": z_shift},
        "model_local_bounds": {"min": mins, "max": maxs},
        "native_stamp_transform_baked": False,
        "files_sha256": {path.name: digest(path) for path in TARGET.iterdir()
                         if path.is_file() and path.name in
                         ("model.fbx", "building.json", "albedo.png",
                          "normal.png", "roughness.png", "metalness.png")},
    }
    (TARGET / "source-receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    for clone in clones:
        clone.select_set(False)
        clone.hide_set(True)
        clone.hide_render = True
    return receipt
