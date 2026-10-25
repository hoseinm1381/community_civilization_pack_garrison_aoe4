"""Texture/ground review for saved donor and edited building blends.

Run in factory-startup Blender only with the shared background Blender token.
Only the task-owned after blends are updated with packed private preview albedos.
Presentation ground/cameras/lights are removed from editable files before saving.
"""
import bpy
import hashlib
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/release_020/barracks_tc"
materials = json.loads((OUT / "materials-ready.json").read_text())
handoff = json.loads((OUT / "source-handoff.json").read_text())
requested = list(map(int, sys.argv[sys.argv.index("--") + 1:])) if "--" in sys.argv else [1, 4]
proof = []

for family in ("barracks", "town_center"):
    author = ROOT / f"art/authoring/buildings_020/{family}"
    for age in requested:
        model = next(r for r in handoff["models"] if r["family"] == family and r["age"] == age)
        texture_rows = next(r for r in materials["models"] if r["family"] == family and r["age"] == age)["roof_materials"]
        texture_by_name = {r["material_name"]: r for r in texture_rows}
        center = Vector([(a + b) / 2 for a, b in zip(model["donor_bounds"]["minimum"], model["donor_bounds"]["maximum"])])
        lo, hi = Vector(model["donor_bounds"]["minimum"]), Vector(model["donor_bounds"]["maximum"])
        span = (hi - lo).length
        for state in ("before", "after"):
            blend = Path(model["donor_blend"] if state == "before" else model["editable_blend"])
            bpy.ops.wm.open_mainfile(filepath=str(blend))
            scene = bpy.context.scene
            if state == "after":
                for obj in [o for o in scene.objects if o.type == "MESH"]:
                    row = texture_by_name.get(obj.get("garrison_material_slot"))
                    if not row:
                        continue
                    for mat in obj.data.materials:
                        if not mat or not mat.use_nodes:
                            continue
                        node = mat.node_tree.nodes.get("Essence · " + row["slot"])
                        if node is not None:
                            img = bpy.data.images.load(row["image"], check_existing=True)
                            img.colorspace_settings.name = "sRGB"
                            node.image = img
                bpy.ops.file.pack_all()
                bpy.ops.wm.save_as_mainfile(filepath=str(blend))
            # Disable decoded team's fixed preview tint only in this presentation.
            for mat in bpy.data.materials:
                if not mat.use_nodes:
                    continue
                control = mat.node_tree.nodes.get("GARRISON Material Controls")
                if control and control.inputs.get("Team Colour Strength"):
                    control.inputs["Team Colour Strength"].default_value = 0
            groundmat = bpy.data.materials.new("Presentation ground")
            groundmat.use_nodes = True
            groundmat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (.24, .23, .19, 1)
            bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.03))
            ground = bpy.context.object
            ground.name = "Presentation ground"
            ground.data.materials.append(groundmat)
            world = scene.world or bpy.data.worlds.new("Presentation world")
            scene.world = world
            world.use_nodes = True
            world.node_tree.nodes.get("Background").inputs[0].default_value = (.30, .35, .39, 1)
            world.node_tree.nodes.get("Background").inputs[1].default_value = .7
            sun = bpy.data.objects.new("Presentation sun", bpy.data.lights.new("Presentation sun", "SUN"))
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
            for view, vector in (("game", (1, -1, .85)), ("facade", (0, -1, .32))):
                cam = bpy.data.objects.new("Presentation camera", bpy.data.cameras.new("Presentation camera"))
                scene.collection.objects.link(cam)
                cam.location = center + Vector(vector).normalized() * span * 2
                cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
                cam.data.type = "ORTHO"
                cam.data.ortho_scale = span * 1.30
                scene.camera = cam
                dest = OUT / f"{model['name']}-{state}-textured-{view}.png"
                scene.render.filepath = str(dest)
                bpy.ops.render.render(write_still=True)
                bpy.data.objects.remove(cam, do_unlink=True)
            proof.append({"family": family, "age": age, "state": state, "source": str(blend),
                          "source_sha256": hashlib.sha256(blend.read_bytes()).hexdigest(),
                          "ground_z": -.03, "span_m": span, "pair_same_framing": True,
                          "offline_render_only": True})
            (OUT / "textured-preview-validation.json").write_text(json.dumps(proof, indent=2), encoding="utf8")
        print("TEXTURED_REVIEW_READY", family, age, flush=True)
