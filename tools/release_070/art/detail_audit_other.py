"""Read-only selector, geometry, UV and bounds audit for detailed 0.7.0 art.

Call audit_detail('foundry'|'wonder'|'university') in the claimed Blender MCP.
"""
from pathlib import Path
import json
import math
import bpy

NAMES={"foundry":"CCP070_Trung_Foundries_Detailed_r3",
       "wonder":"CCP070_Kinh_Thien_Detailed_r4",
       "university":"CCP070_University_Detailed_Overlay_r6"}
OUT=Path("F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail")
SELECTORS={"healthy":[0,1,4,5,6],"heavy_damage":[0,3],"ruins":[2]}
STOCK_ENVELOPE={"min":[-6.5821,-6.9453,-.0001],
                "max":[7.5039,5.4063,8.5313]}

def audit_detail(kind):
    if kind not in NAMES:
        raise ValueError("Unknown detail kind")
    collection=bpy.data.collections.get(NAMES[kind])
    if collection is None:
        raise RuntimeError("Detail collection missing")
    parts={}
    for obj in collection.objects:
        for i in range(7):
            if obj.name.endswith("garrison_part_%04d"%i):
                parts[i]=obj
    if len(collection.objects)!=7 or set(parts)!=set(range(7)):
        raise RuntimeError("Exactly seven lifecycle parts required")
    result={"schema":"ccp-070-detail-audit/v1","kind":kind,
            "collection":collection.name,"selectors":SELECTORS,"parts":{}}
    for i,obj in parts.items():
        mesh=obj.data
        vertices=[v.co for v in mesh.vertices]
        world=[obj.matrix_world@v.co for v in mesh.vertices]
        uv=mesh.uv_layers.active
        loops=[item.uv for item in uv.data] if uv else []
        finite=all(math.isfinite(x) for v in vertices for x in v)
        finite=finite and all(math.isfinite(x) for v in loops for x in v)
        finite=finite and all(math.isfinite(x) for p in mesh.polygons for x in p.normal)
        result["parts"]["%04d"%i]={
            "triangles":sum(len(p.vertices)-2 for p in mesh.polygons),
            "faces":len(mesh.polygons),"vertices":len(vertices),
            "material":[m.name for m in mesh.materials],
            "finite":finite,"degenerate_faces":sum(p.area<=1e-10 for p in mesh.polygons),
            "uv_range":{"min":[min(v[j] for v in loops) for j in range(2)],
                        "max":[max(v[j] for v in loops) for j in range(2)]} if loops else None,
            "local_bounds":{"min":[min(v[j] for v in vertices) for j in range(3)],
                            "max":[max(v[j] for v in vertices) for j in range(3)]},
            "world_bounds":{"min":[min(v[j] for v in world) for j in range(3)],
                            "max":[max(v[j] for v in world) for j in range(3)]},
            "hidden_in_healthy_view":obj.hide_get()}
    result["healthy_triangles"]=sum(result["parts"]["%04d"%i]["triangles"]
                                    for i in SELECTORS["healthy"])
    result["all_finite"]=all(p["finite"] for p in result["parts"].values())
    result["all_faces_nonzero"]=all(p["degenerate_faces"]==0 for p in result["parts"].values())
    result["all_uv_inside_unit_square"]=all(p["uv_range"] is not None and
        min(p["uv_range"]["min"])>=0 and max(p["uv_range"]["max"])<=1
        for p in result["parts"].values())
    if kind=="university":
        base=bpy.data.collections.get("CCP070_University_Additions_Blockout")
        stock=[o for o in base.objects if o.get("stock_geometry_unchanged")]
        result["stock_groups_preserved"]=len(stock)==4 and all(
            o.get("stock_geometry_unchanged") for o in stock)
        healthy_local=[v.co for i in SELECTORS["healthy"]
                       for v in parts[i].data.vertices]
        result["healthy_overlay_inside_stock_xy"]=all(
            STOCK_ENVELOPE["min"][axis]-.01 <= v[axis] <=
            STOCK_ENVELOPE["max"][axis]+.01
            for v in healthy_local for axis in (0,1))
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/(kind+"-"+collection.name.rsplit("_",1)[-1]+"-audit.json")
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return {"audit":str(path),"healthy_triangles":result["healthy_triangles"],
            "all_finite":result["all_finite"],
            "all_faces_nonzero":result["all_faces_nonzero"],
            "all_uv_inside_unit_square":result["all_uv_inside_unit_square"],
            "stock_groups_preserved":result.get("stock_groups_preserved"),
            "healthy_overlay_inside_stock_xy":result.get("healthy_overlay_inside_stock_xy")}
