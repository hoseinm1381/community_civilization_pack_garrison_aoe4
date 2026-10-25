"""Render paired donor/remodel views from task-owned 0.4.0 blends.

Run only in the serialized background Blender slot. Does not save any blend.
These are authoring previews, not Content Editor or native game evidence.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/release_040/buildings"
models = json.loads((OUT / "model-validation.json").read_text())["models"]
requested = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
receipts = []


def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for model in models:
    family, age = model["family"], model["age"]
    if requested and family not in requested and str(age) not in requested and f"{family}:{age}" not in requested:
        continue
    lo = Vector(model["before_bounds"]["minimum"])
    hi = Vector(model["before_bounds"]["maximum"])
    center = (lo + hi) / 2
    span = (hi - lo).length
    for state, blend_key in (("before", "donor_blend"), ("after", "editable_blend")):
        blend = Path(model[blend_key])
        assert hash_file(blend) == model[blend_key + "_sha256"]
        bpy.ops.wm.open_mainfile(filepath=str(blend))
        scene = bpy.context.scene
        for material in bpy.data.materials:
            if not material.use_nodes:
                continue
            control = material.node_tree.nodes.get("GARRISON Material Controls")
            if control and control.inputs.get("Team Colour Strength"):
                control.inputs["Team Colour Strength"].default_value = 0
        ground_mat = bpy.data.materials.new("Preview earth")
        ground_mat.use_nodes = True
        ground_mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (.24, .23, .18, 1)
        bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.03))
        bpy.context.object.data.materials.append(ground_mat)
        bpy.context.object.name = "Preview only ground"
        sun = bpy.data.objects.new("Preview only sun", bpy.data.lights.new("Preview only sun", "SUN"))
        scene.collection.objects.link(sun)
        sun.rotation_euler = (.45, -.65, -.5)
        sun.data.energy = 3
        sun.data.angle = .15
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 12
        scene.cycles.use_denoising = True
        scene.render.resolution_x = 900
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100
        scene.view_settings.view_transform = "AgX"
        camera = bpy.data.objects.new("Preview only camera", bpy.data.cameras.new("Preview only camera"))
        scene.collection.objects.link(camera)
        camera.location = center + Vector((1, -1, .85)).normalized() * span * 2
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = span * 1.30
        scene.camera = camera
        destination = OUT / f"{model['name']}-{state}-textured-game.png"
        scene.render.filepath = str(destination)
        bpy.ops.render.render(write_still=True)
        receipts.append({"family": family, "age": age, "state": state,
                         "blend": str(blend), "blend_sha256": hash_file(blend),
                         "preview": str(destination), "preview_sha256": hash_file(destination),
                         "pair_same_framing": True, "offline_only": True})
        (OUT / "textured-preview-validation.json").write_text(json.dumps(receipts, indent=2), encoding="utf8")
        print("BUILDING_TEXTURED_PREVIEW", family, age, state, flush=True)
