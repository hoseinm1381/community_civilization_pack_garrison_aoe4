"""Export real six-group mangonel skin and both UVs from temporary copies."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/release_060"))
from common import ART, EXPORT, OUT, guard, owned, read, sha, write  # noqa: E402

SOURCE = ART / "nonhumanoid-stock-rig/siege_mangonel3/six-group-control.blend"
PRIOR = OUT / "qualification/nonhumanoid-route-preflight/siege_mangonel3/source-export.json"
CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
DEST = EXPORT / "nonhumanoid-stock-rig/siege_mangonel3/two-uv-skin-control"
RECEIPT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-skin-export.json"


def main():
    guard()
    for path in (DEST, RECEIPT): owned(path)
    if DEST.exists() or RECEIPT.exists(): raise FileExistsError("Preserve prior skinned two-UV export")
    prior, contract = read(PRIOR), read(CONTRACT)
    if (Path(bpy.data.filepath).resolve() != SOURCE.resolve() or
            sha(SOURCE) != prior["saved_blend_sha256"] or
            sha(CONTRACT) != prior["contract_sha256"]):
        raise RuntimeError("Open unchanged pinned six-group Mangonel blend")
    donor_path = Path(contract["donors"]["siege_mangonel3"]["donor_manifest"])
    if sha(donor_path) != contract["donors"]["siege_mangonel3"]["donor_manifest_sha256"]:
        raise RuntimeError("Native donor manifest drift")
    donor = read(donor_path)
    collection = bpy.data.collections.get("CCP060_siege_mangonel3_StockRig_SixGroup_Control")
    if collection is None: raise RuntimeError("Six-group source collection missing")
    objects = list(collection.objects)
    names = prior["export_mesh_names"]
    if len(objects) != 6 or sorted(o.name for o in objects) != sorted(names):
        raise RuntimeError("Native six-group source identity changed")
    objects = [next(o for o in objects if o.name == name) for name in names]
    rig_set = {obj.parent for obj in objects if obj.parent and obj.parent.type == "ARMATURE"}
    if len(rig_set) != 1: raise RuntimeError("Single real donor armature absent")
    rig = rig_set.pop()
    if [b.name for b in rig.data.bones] != [b["name"] for b in donor["skeleton"]["bones"]]:
        raise RuntimeError("Full 14-bone donor skeleton changed")
    native = {b.name for b in rig.data.bones}
    preflight = []
    for source, group in zip(objects, donor["geometry"]["groups"]):
        modifiers = [m for m in source.modifiers if m.type == "ARMATURE" and m.object == rig and m.show_viewport]
        weighted = sum(bool(v.groups) for v in source.data.vertices)
        if (len(modifiers) != 1 or weighted != len(source.data.vertices) or
                not source.vertex_groups or
                {v.name for v in source.vertex_groups} - native or
                set(u.name for u in source.data.uv_layers) != {"UVMap", "UV2"} or
                len(source.data.vertices) != group["vertex_count"] or
                sum(len(poly.vertices)-2 for poly in source.data.polygons) != group["triangle_count"]):
            raise RuntimeError(f"Actual skinned two-UV source preflight failed: {source.name}")
        preflight.append({"mesh": source.name, "vertices": len(source.data.vertices),
                          "triangles": group["triangle_count"], "vertex_group_count": len(source.vertex_groups),
                          "weighted_vertex_count": weighted, "active_armature_modifiers_to_exact_rig": 1,
                          "uv_layers": [u.name for u in source.data.uv_layers]})
    selected_before = [obj for obj in bpy.context.selected_objects]
    active_before = bpy.context.view_layer.objects.active
    temp = bpy.data.collections.new("CCP060_Mangonel_TwoUV_Skin_Export_Temporary")
    bpy.context.scene.collection.children.link(temp)
    made = []
    try:
        for source in objects:
            old_name = source.name
            source.name = old_name + "__held_for_export"
            clone = source.copy()
            clone.data = source.data.copy()
            temp.objects.link(clone)
            clone.name = old_name
            clone.data.name = old_name + "_two_uv_skin_export"
            clone.parent = rig
            clone.matrix_world = source.matrix_world.copy()
            for item in clone.data.uv_layers["UV2"].data:
                item.uv.y = 1.0 - item.uv.y
            made.append((source, old_name, clone))
        bpy.ops.object.select_all(action="DESELECT")
        for obj in [rig, *(row[2] for row in made)]: obj.select_set(True)
        bpy.context.view_layer.objects.active = rig
        DEST.mkdir(parents=True)
        fbx = DEST / "model.fbx"
        result = bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True,
                                          object_types={"ARMATURE", "MESH"},
                                          use_mesh_modifiers=True, use_custom_props=True,
                                          add_leaf_bones=False, bake_anim=False,
                                          path_mode="AUTO", use_tspace=False)
        if "FINISHED" not in result or not fbx.is_file():
            raise RuntimeError("Native skinned two-UV FBX export failed")
    finally:
        for source, old_name, clone in reversed(made):
            mesh_data = clone.data
            bpy.data.objects.remove(clone, do_unlink=True)
            bpy.data.meshes.remove(mesh_data)
            source.name = old_name
        bpy.data.collections.remove(temp)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in selected_before:
            if obj.name in bpy.data.objects: obj.select_set(True)
        if active_before and active_before.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = active_before
    if sorted(obj.name for obj in collection.objects) != sorted(names):
        raise RuntimeError("Temporary export cleanup changed original mesh names")
    record = {"schema": "ccp-060-mangonel-six-group-two-uv-skinned-fbx/v1",
              "status": "source_export_only_native_cook_unproved", "source_blend": str(SOURCE),
              "source_blend_sha256": sha(SOURCE), "prior_export_sha256": sha(PRIOR),
              "donor_manifest_sha256": sha(donor_path), "stock_bones": 14,
              "six_group_lod_triangles": [g["triangle_count"] for g in donor["geometry"]["groups"]],
              "actual_source_skin_uv_preflight": preflight,
              "uv_layers": [{"mesh": p["mesh"], "uv_layers": p["uv_layers"]} for p in preflight],
              "blender_fbx_use_mesh_modifiers": True, "blender_fbx_use_custom_props": True,
              "exported_fbx": str(fbx), "exported_fbx_sha256": sha(fbx),
              "temporary_copies_removed_original_scene_not_saved": True,
              "no_unit_prototype_or_action": True}
    write(RECEIPT, record)
    return {"status": record["status"], "fbx": str(fbx), "receipt": str(RECEIPT)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
