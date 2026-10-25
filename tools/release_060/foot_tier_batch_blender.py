"""Author exact-donor Vietnamese foot tiers after an exclusive Blender lease.

This stage creates separate editable blends and stock-distance visual receipts.
It does not change gameplay bindings, weapons, rig actions, or active source.
Run one --model index per fresh Blender process so native material caches stay
independent and outputs are deterministic. The archer family is opt-in while
its approved representative artist owns it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, EXPORT, OUT, RECIPES, guard, owned, read, sha, write
import pilot_author_blender as pilot
import representative_batch as design


def stage(model_index: int, include_archer: bool) -> None:
    guard()
    recipe = read(RECIPES / "representative-foot-tier-batch.json")
    entry = recipe["models"][model_index]
    path = entry["model_path"]
    slug = Path(path).stem
    if "chi_ranged_bow" in slug and not include_archer:
        raise RuntimeError("Archer tier artist ownership remains separate")
    manifest = Path(entry["manifest"])
    if sha(manifest) != entry["manifest_sha256"]:
        raise RuntimeError("Pinned stock donor manifest changed: " + path)
    if bpy.data.filepath:
        raise RuntimeError("Refusing to overwrite an open .blend")
    target = owned(ART / "representatives" / "foot_tiers" / slug / (slug + "_v1.blend"))
    report = owned(OUT / "representatives" / "foot_tiers" / slug / "v1" / "authoring.json")
    if target.exists() or report.exists():
        raise FileExistsError("Preserve existing tier authoring: " + str(target))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    import addon_utils
    modules = [m.__name__ for m in addon_utils.modules()
               if m.__name__.endswith("garrison")]
    if len(modules) != 1:
        raise RuntimeError("Expected one installed Garrison extension")
    addon_utils.enable(modules[0], default_set=False, persistent=False)
    _, imported = pilot.import_donor("foot_" + slug, manifest, path)
    lod1 = pilot.source_for_triangles(imported, entry["stock_lod1_triangles"])
    rig = design.rig_of(lod1)
    if len(rig.data.bones) != 48:
        raise RuntimeError("Exact donor rig changed")
    finish = bpy.data.collections.new("CCP060_" + slug + "_final_geometry")
    stock = bpy.data.collections.new("CCP060_" + slug + "_stock_geometry")
    draft = bpy.data.collections.new("CCP060_" + slug + "_empty_draft")
    for c in (finish, stock, draft):
        bpy.context.scene.collection.children.link(c)
    design._tint_context = ("spear2", "v1")
    design._pipeline = True
    design._export_folder_override = owned(EXPORT / "representatives" /
                                            "foot_tiers" / slug / "v1")
    design._review_folder_override = owned(OUT / "representatives" /
                                            "foot_tiers" / slug / "v1" / "review")
    sources = [obj for obj in imported if obj.type == "MESH" and
               any("lod" + str(i) in obj.name.casefold() for i in (1,2,3))]
    if len(sources) != 3 or lod1 not in sources:
        raise RuntimeError(f"Expected three exact stock LOD meshes: {[o.name for o in sources]}")
    clones = []
    for source in sources:
        clone = source.copy()
        clone.data = source.data.copy()
        clone.name = "CCP060_DaiViet_" + slug + "_" + source.name[-4:]
        finish.objects.link(clone)
        clone.data.materials.clear()
        clone.data.materials.append(design.shared_atlas_material(source))
        for collection in tuple(source.users_collection):
            collection.objects.unlink(source)
        stock.objects.link(source)
        if source != lod1:
            source.hide_set(True)
            source.hide_render = True
            clone.hide_set(True)
            clone.hide_render = True
        clones.append({"source":source.name,"remix":clone.name,
                       "triangles":len(source.data.polygons),
                       "uv_preserved":bool(clone.data.uv_layers),
                       "weights_preserved":bool(clone.vertex_groups)})
    parts = []
    is_spear = "chi_infantry_light" in slug
    older = entry["age"] >= 3
    if is_spear:
        # The approved Age II spearman silhouette carries forward, with each
        # actual age donor retaining its own helmet, armor and body proportions.
        parts.append(design.donor_layer(lod1,finish,"split_knee_tunic",
                       ("pelvis","spine"),(.12,.65),expand=.055,
                       flare=.17 if older else .22,tint="deep_teal"))
        parts.append(design.donor_layer(lod1,finish,"broad_chest_armor",
                       ("ribcage","spine"),(.43,.85),expand=.065 if older else .095,
                       tint="deep_teal"))
        # Native LOD2/LOD3 retain the readable hem rather than switching to
        # an unaltered stock silhouette at normal match distance. Keep their
        # own exact donor weights/UV and hide them only in this LOD1 preview.
        for level in (2,3):
            source = next(s for s in sources if "lod"+str(level) in s.name.casefold())
            part = design.donor_layer(source,finish,f"split_knee_tunic_lod{level}",
                      ("pelvis","spine"),(.12,.65),expand=.050,
                      flare=.13,tint="deep_teal")
            obj = bpy.data.objects[part["name"]]
            obj.hide_set(True)
            obj.hide_render = True
            part["native_lod"] = level
            part["authoring_visibility"] = "hidden with corresponding stock LOD"
            parts.append(part)
    else:
        parts.append(design.donor_layer(lod1,finish,"long_service_tunic",
                       ("pelvis","spine"),(.16,.66),expand=.058,
                       flare=.13 if older else .18,tint="deep_teal"))
        parts.append(design.donor_layer(lod1,finish,"shoulder_chest_cloth",
                       ("ribcage","spine"),(.43,.81),expand=.060,
                       tint="deep_teal"))
    pilot.set_comparison_layers(finish,stock,draft)
    bpy.context.scene["ccp060_exact_stock_model"] = path
    bpy.context.scene["ccp060_native_animation_rule"] = "preserve stock 48-bone rig and clips"
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    game = design.render_match("foot_"+slug,"v1",lod1,finish)
    close = design.render_match("foot_"+slug,"v1",lod1,finish,extra=True)
    write(report,{"schema":"ccp-060-foot-tier-authoring/v1",
                  "model":path,"consumers":entry["consuming_families"],
                  "donor_manifest":str(manifest),"donor_manifest_sha256":sha(manifest),
                  "blend":str(target),"blend_sha256":sha(target),
                  "native_bone_count":len(rig.data.bones),"lods":clones,
                  "parts":parts,"stock_lod1_triangles":len(lod1.data.polygons),
                  "game_review":game,"close_and_owner_review":close,
                  "status":"authoring preview only; native geometry export/cook/in-game pending"})
    print(json.dumps({"model":slug,"blend":str(target),
                      "blend_sha256":sha(target),"parts":len(parts)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=int, required=True)
    parser.add_argument("--include-archer", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    stage(args.model,args.include_archer)
