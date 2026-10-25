"""Render matched stock/pilot stills from an isolated pilot blend for art review."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, read, sha, write


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--surface", choices=("solid", "textured"), default="solid")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    guard()
    pilot = args.pilot
    source = read(OUT / "pilots" / pilot / "authoring.json")
    blend = Path(source["blend"])
    if sha(blend) != source["blend_sha256"]:
        raise RuntimeError("Pilot blend has changed since authoring receipt")
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene = bpy.context.scene
    body = [bpy.data.objects[item["source"]] for item in source["remix"]]
    if not body:
        raise RuntimeError("No simultaneously visible stock LOD1 mesh")
    def bounds(objects):
        vertices = [o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
        lo = Vector(tuple(min(p[i] for p in vertices) for i in range(3)))
        hi = Vector(tuple(max(p[i] for p in vertices) for i in range(3)))
        return (lo + hi) / 2, hi - lo
    center, size = bounds(body)
    camera_data = bpy.data.cameras.new("CCP060_Review_Ortho")
    camera = bpy.data.objects.new("CCP060_Review_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    direction = Vector((1.0, -1.65, .72)).normalized()
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    if args.surface == "solid":
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.studio_light = "paint.sl"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "BOTH"
        scene.display.shading.curvature_ridge_factor = 1.2
        scene.display.shading.curvature_valley_factor = 1.1
    else:
        scene.render.engine = "BLENDER_EEVEE"
        scene.world.use_nodes = True
        world_bg = scene.world.node_tree.nodes.get("Background")
        if world_bg:
            world_bg.inputs["Color"].default_value = (.6, .65, .65, 1)
            world_bg.inputs["Strength"].default_value = .8
        lamp_data = bpy.data.lights.new("CCP060_Review_Softbox", "AREA")
        lamp = bpy.data.objects.new("CCP060_Review_Softbox", lamp_data)
        scene.collection.objects.link(lamp)
        lamp_data.energy = 1700
        lamp_data.shape = "DISK"
        lamp_data.size = 5
        lamp.location = center + Vector((1.5, -3, 5))
        lamp.rotation_euler = (center - lamp.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.film_transparent = False
    scene.display.shading.background_type = "WORLD"
    scene.world.color = (.80, .82, .81)
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_mode = "RGBA"
    out = owned(OUT / "pilots" / pilot / "review")
    out.mkdir(parents=True, exist_ok=True)
    images = {}
    for distance, scale in (("close", max(size.x, size.y, size.z) * 1.26),
                            ("game", max(size.x, size.y, size.z) * 2.85)):
        camera.location = center + direction * max(4.0, scale * 2.2)
        camera_data.ortho_scale = max(1.1, scale)
        bpy.context.view_layer.update()
        from bpy_extras.object_utils import world_to_camera_view
        print("REVIEW_CAMERA", distance, "center", list(center), "size", list(size),
              "camera", list(camera.location), "projected", list(world_to_camera_view(scene, camera, center)),
              "body", [(o.name, o.hide_render, o.hide_viewport) for o in body])
        for layer in ("Exact stock donor", "Dai Viet pilot"):
            key = ("stock" if layer.startswith("Exact") else "dai_viet") + "_" + distance
            if args.surface == "textured":
                key += "_textured"
            path = out / (key + ".png")
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True, layer=layer)
            images[key] = {"path": str(path), "sha256": sha(path)}
    write(OUT / "pilots" / pilot / ("review.json" if args.surface == "solid" else "review-textured.json"), {
        "schema": "ccp-060-pilot-review/v1", "pilot": pilot,
        "blend": str(blend), "blend_sha256": sha(blend),
        "same_camera_framing": True, "render_engine": scene.render.engine,
        "surface_limit": ("Material display colours; inspect actual donor textures in blend"
                          if args.surface == "solid" else "EEVEE preview; game shader/cook still unqualified"),
        "pose": "stock donor rest pose; native animation not qualified", "images": images})
    print(json.dumps({"pilot": pilot, "images": images}))


if __name__ == "__main__":
    main()
