"""PREPARED ONLY: direct six-group stock-rig FBX export, no prototype.

Run only in a claimed Blender instance with the exact pilot review .blend open.
This is an export experiment, not an installed Build Unit admission or native cook.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/release_060"))
from common import ART, EXPORT, OUT, guard, owned, read, sha, write  # noqa: E402
from export_archer_matched_control import addon_module  # noqa: E402

CONTRACT = OUT / "qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json"
PILOTS = {"horseman2", "elephant", "siege_mangonel3"}


def main(pilot: str) -> dict:
    guard()
    if pilot not in PILOTS:
        raise ValueError(f"Expected one of {sorted(PILOTS)}")
    contract = read(CONTRACT)
    if contract["status"] != "three_donors_pinned_generic_export_possible_manual_native_source_unproved":
        raise RuntimeError("Nonhumanoid source preflight changed")
    row = contract["donors"][pilot]
    source_blend = Path(row["pilot_blend"])
    if Path(bpy.data.filepath).resolve() != source_blend.resolve() or sha(source_blend) != row["pilot_blend_sha256"]:
        raise RuntimeError("Open only the pinned pilot review blend")
    donor_path = Path(row["donor_manifest"])
    if sha(donor_path) != row["donor_manifest_sha256"]:
        raise RuntimeError("Pinned native donor manifest changed")
    donor = read(donor_path)
    source_collection = bpy.data.collections.get(f"CCP060_{pilot}_body_stock_reference")
    highest_collection = bpy.data.collections.get(f"CCP060_{pilot}_exact_stock_mesh")
    if source_collection is None or highest_collection is None:
        raise RuntimeError("Pinned original Garrison body projection or exact high LOD missing")
    # Pilot authoring moved the two highest-detail originals into the exact
    # stock review collection; the lower four remain in the body projection.
    pool = [obj for obj in set(source_collection.all_objects) | set(highest_collection.all_objects)
            if obj.type == "MESH" and sum(len(poly.vertices) - 2 for poly in obj.data.polygons) > 0]
    expected = row["geometry_groups_in_native_order"]
    if len(expected) != 6 or len(pool) != 6:
        raise RuntimeError(f"Expected exactly six original donor meshes; found {len(pool)}")
    selected = []
    for index, group in enumerate(expected):
        matches = [obj for obj in pool
                   if len(obj.data.vertices) == group["vertices"]
                   and sum(len(poly.vertices) - 2 for poly in obj.data.polygons) == group["triangles"]]
        if len(matches) != 1 or matches[0] in selected:
            raise RuntimeError(f"Cannot uniquely identify native group {index}: {matches}")
        obj = matches[0]
        if len(obj.data.materials) != 1 or not obj.data.uv_layers:
            raise RuntimeError(f"{obj.name} does not have one stock material and UV")
        selected.append(obj)
    rigs = {modifier.object for mesh in selected for modifier in mesh.modifiers
            if modifier.type == "ARMATURE" and modifier.object is not None}
    if len(rigs) != 1:
        raise RuntimeError("All six native groups must share exactly one original rig")
    rig = rigs.pop()
    native_names = [b["name"] for b in donor["skeleton"]["bones"]]
    unit_export = addon_module("unit_export")
    records = unit_export.skeleton_records(rig)
    if [r["name"] for r in records] != native_names or len(records) != row["full_skeleton_bones"]:
        raise RuntimeError("Garrison stock skeleton records differ from native model")
    folder = owned(EXPORT / "nonhumanoid-stock-rig" / pilot / "six-group-control")
    saved = owned(ART / "nonhumanoid-stock-rig" / pilot / "six-group-control.blend")
    receipt = owned(OUT / "qualification/nonhumanoid-route-preflight" / pilot / "source-export.json")
    collection_name = f"CCP060_{pilot}_StockRig_SixGroup_Control"
    if any(path.exists() for path in (folder, saved, receipt)) or bpy.data.collections.get(collection_name):
        raise FileExistsError("Preserve existing stock-rig source candidate")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    materials = {}
    copies = []
    uv_rows = []
    for index, (source, group) in enumerate(zip(selected, expected)):
        unknown = {g.name for g in source.vertex_groups} - set(native_names)
        if unknown:
            raise RuntimeError(f"Native group {index} has unmapped weights: {sorted(unknown)}")
        clone = source.copy()
        clone.data = source.data.copy()
        collection.objects.link(clone)
        # The mangonel has two three-LOD groups with one shared `page`
        # material. Native group identity depends on these exact mesh stems.
        if pilot == "siege_mangonel3":
            clone.name = f"{group['name']}_lod{index % 3 + 1}"
        elif pilot == "horseman2":
            clone.name = f"{group['name']}_lod{index % 3 + 1}"
        else:
            # This donor's animal and rider share one mesh stem. Keep both
            # real groups distinct while retaining their actual LOD suffix.
            clone.name = f"{group['name']}_{group['material']}"
        clone.data.name = clone.name + "_mesh"
        clone.hide_viewport = False
        clone.hide_render = False
        clone.parent = rig
        clone.matrix_world = source.matrix_world.copy()
        for modifier in clone.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = rig
        material_name = group["material"]
        material = materials.get(material_name)
        if material is None:
            material = source.data.materials[0].copy()
            material.name = material_name
            if material.name != material_name:
                raise RuntimeError(f"Native material-name collision: {material_name}")
            materials[material_name] = material
        clone.data.materials.clear()
        clone.data.materials.append(material)
        old_uv = source.data.uv_layers.active.data
        new_uv = clone.data.uv_layers.active.data
        if len(old_uv) != len(new_uv) or len(new_uv) != len(clone.data.loops):
            raise RuntimeError(f"Native group {index} UV corner count changed")
        for before, after in zip(old_uv, new_uv):
            after.uv.x, after.uv.y = before.uv.x, 1.0 - before.uv.y
        uv_rows.append({"group_index": index, "corners": len(new_uv),
                        "preexport_v_inversion": True})
        copies.append(clone)
    folder.mkdir(parents=True)
    unit_export.export_unit_model(rig, copies, folder / "model.fbx", records, three_lods=False)
    fbx_bytes = (folder / "model.fbx").read_bytes()
    skin_nodes = fbx_bytes.count(b"DeformerS\x04\x00\x00\x00Skin")
    cluster_nodes = fbx_bytes.count(b"DeformerS\x07\x00\x00\x00Cluster")
    if skin_nodes < 6 or cluster_nodes < 6:
        raise RuntimeError(f"FBX lacks six actual skin bindings: {skin_nodes=} {cluster_nodes=}")
    saved.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(saved))
    write(receipt, {"schema": "ccp-060-direct-stock-rig-six-group-export/v1",
                    "status": "raw_stock_rig_fbx_export_only_native_cook_unproved",
                    "pilot": pilot, "contract_sha256": sha(CONTRACT),
                    "donor_manifest_sha256": sha(donor_path),
                    "source_blend": str(source_blend), "source_blend_sha256": row["pilot_blend_sha256"],
                    "saved_blend": str(saved), "saved_blend_sha256": sha(saved),
                    "stock_skeleton_bones": len(records),
                    "stock_palette_bone_counts": [p["bone_count"] for p in donor["skeleton"]["skin_palettes"]],
                    "native_group_material_order": [(g["name"], g["material"], g["effect"])
                                                    for g in expected],
                    "source_mesh_names": [obj.name for obj in selected],
                    "export_mesh_names": [obj.name for obj in copies],
                    "source_lod_triangles": [g["triangles"] for g in expected],
                    "uv_preexport": uv_rows, "exported_fbx": str(folder / "model.fbx"),
                    "fbx_skin_nodes": skin_nodes, "fbx_cluster_nodes": cluster_nodes,
                    "exported_fbx_sha256": sha(folder / "model.fbx"),
                    "garrison_prototype_or_action_used": False,
                    "original_animation_owner_to_be_preserved": True,
                    "next_gate": "donor-specific editable .rig and neutral material source qualification, then fresh manual native geometry cook/readback; no normal Build Unit admission"})
    return {"status": "raw_stock_rig_fbx_export_only_native_cook_unproved",
            "fbx": str(folder / "model.fbx"), "receipt": str(receipt)}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PILOTS:
        raise SystemExit("Run main(pilot) only in a claimed Blender session")
    print(json.dumps(main(sys.argv[1]), indent=2))
