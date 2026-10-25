"""Direct six-group FBX control retaining both actual stock UV layers.

Run only with the saved six-group control blend open and an exclusive Blender
lease. This is authoring output, not a cook or native geometry qualification.
"""
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
DEST = EXPORT / "nonhumanoid-stock-rig/siege_mangonel3/two-uv-control"
RECEIPT = OUT / "qualification/nonhumanoid-route-preflight/mangonel/two-uv-export.json"


def main(use_mesh_modifiers: bool = False, use_custom_props: bool = False):
    guard()
    for p in (DEST, RECEIPT): owned(p)
    if DEST.exists() or RECEIPT.exists(): raise FileExistsError("Preserve prior two-UV export")
    prior, contract = read(PRIOR), read(CONTRACT)
    if (Path(bpy.data.filepath).resolve() != SOURCE.resolve() or
            sha(SOURCE) != prior["saved_blend_sha256"] or
            sha(CONTRACT) != prior["contract_sha256"]):
        raise RuntimeError("Open unchanged saved mangonel six-group control")
    donor = read(Path(contract["donors"]["siege_mangonel3"]["donor_manifest"]))
    collection = bpy.data.collections.get("CCP060_siege_mangonel3_StockRig_SixGroup_Control")
    if collection is None: raise RuntimeError("Six-group control collection missing")
    meshes = list(collection.objects)
    expected = prior["export_mesh_names"]
    if sorted(o.name for o in meshes) != sorted(expected) or len(meshes) != 6:
        raise RuntimeError("Exact six native control meshes changed")
    meshes = [next(o for o in meshes if o.name == name) for name in expected]
    rig_set = {m.parent for m in meshes if m.parent and m.parent.type == "ARMATURE"}
    if len(rig_set) != 1: raise RuntimeError("Exact shared mangonel rig missing")
    rig = rig_set.pop()
    if [b.name for b in rig.data.bones] != [b["name"] for b in donor["skeleton"]["bones"]]:
        raise RuntimeError("Native donor bone order drift")
    uv_rows = []
    uv2_original = {}
    for i, mesh in enumerate(meshes):
        layers = mesh.data.uv_layers
        if set(layer.name for layer in layers) != {"UVMap", "UV2"}:
            raise RuntimeError(f"{mesh.name} lacks exact two native UV sets")
        group = donor["geometry"]["groups"][i]
        if (len(mesh.data.vertices) != group["vertex_count"] or
                sum(len(p.vertices)-2 for p in mesh.data.polygons) != group["triangle_count"] or
                len(layers["UV2"].data) != len(mesh.data.loops)):
            raise RuntimeError(f"{mesh.name} topology changed")
        # The existing control pre-flipped UVMap for the installed exporter's
        # V inversion. The untouched native UV2 needs the same pre-flip here.
        uv2_original[mesh.name] = [loop.uv.y for loop in layers["UV2"].data]
        for loop in layers["UV2"].data:
            loop.uv.y = 1.0 - loop.uv.y
        uv_rows.append({"mesh": mesh.name, "uv_layers": [layer.name for layer in layers],
                        "corners_per_layer": [len(layer.data) for layer in layers],
                        "uv2_preexport_v_inversion": True})
    bpy.ops.object.select_all(action="DESELECT")
    for obj in [rig, *meshes]: obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    DEST.mkdir(parents=True)
    fbx = DEST / "model.fbx"
    try:
        result = bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True,
                                          object_types={"ARMATURE", "MESH"},
                                          use_mesh_modifiers=use_mesh_modifiers, add_leaf_bones=False,
                                          bake_anim=False, path_mode="AUTO",
                                          use_tspace=False, use_custom_props=use_custom_props)
    finally:
        for mesh in meshes:
            for loop, value in zip(mesh.data.uv_layers["UV2"].data, uv2_original[mesh.name]):
                loop.uv.y = value
    if "FINISHED" not in result or not fbx.is_file():
        raise RuntimeError("Blender FBX exporter did not produce source")
    record = {"schema": "ccp-060-mangonel-two-stock-uv-fbx-control/v1",
              "status": "source_export_only_native_cook_unproved", "source_blend": str(SOURCE),
              "source_blend_sha256": sha(SOURCE), "prior_export_sha256": sha(PRIOR),
              "donor_manifest_sha256": sha(Path(contract["donors"]["siege_mangonel3"]["donor_manifest"])),
              "stock_bones": 14, "six_group_lod_triangles": [g["triangle_count"] for g in donor["geometry"]["groups"]],
              "uv_layers": uv_rows, "exported_fbx": str(fbx), "exported_fbx_sha256": sha(fbx),
              "blender_fbx_use_mesh_modifiers": use_mesh_modifiers,
              "blender_fbx_use_custom_props": use_custom_props,
              "saved_scene_changed": False, "no_unit_prototype_or_action": True,
              "next_gate": "fresh isolated 14-bone partition native cook; require six groups/two palettes and both direct UV layers versus stock"}
    write(RECEIPT, record)
    return {"status": record["status"], "fbx": str(fbx), "receipt": str(RECEIPT)}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
