"""Read-only numerical Garden detail audit for the claimed Blender MCP scene."""
from pathlib import Path
import json
import math
import bpy

ROOT=Path("E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison")
OUT=Path("F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail")
NAME="CCP070_Imperial_Garden_Detailed_r2"
collection=bpy.data.collections.get(NAME)
if collection is None:
    raise RuntimeError("Garden r2 detail missing")
parts={}
for obj in collection.objects:
    for i in range(7):
        if obj.name.endswith("garrison_part_%04d"%i):
            parts[i]=obj
if set(parts)!=set(range(7)) or len(collection.objects)!=7:
    raise RuntimeError("Garden detail does not have exactly seven lifecycle parts")

report={"schema":"ccp-070-garden-detail-audit/v1",
        "collection":NAME,"parts":{},"selectors":{"healthy":[0,1,4,5,6],
          "heavy_damage":[0,3],"ruins":[2]},
        "designed_contacts":{"bridge_to_pavilion_y":2.7,
                             "pond_to_bridge_north_y":.2,
                             "yard_exit_y":[4.0,10.0]}}
for i,obj in parts.items():
    mesh=obj.data
    local=[v.co for v in mesh.vertices]
    world=[obj.matrix_world@v.co for v in mesh.vertices]
    uv=mesh.uv_layers.active
    uvs=[l.uv for l in uv.data] if uv else []
    degenerate=sum(p.area<=1e-10 for p in mesh.polygons)
    finite=all(math.isfinite(x) for v in local for x in v)
    finite=finite and all(math.isfinite(x) for v in uvs for x in v)
    finite=finite and all(math.isfinite(x) for p in mesh.polygons for x in p.normal)
    report["parts"]["%04d"%i]={
        "triangles":sum(len(p.vertices)-2 for p in mesh.polygons),
        "faces":len(mesh.polygons),"vertices":len(mesh.vertices),
        "material":[m.name for m in mesh.materials],
        "uv_layers":[layer.name for layer in mesh.uv_layers],
        "uv_min":[min(v[j] for v in uvs) for j in range(2)] if uvs else None,
        "uv_max":[max(v[j] for v in uvs) for j in range(2)] if uvs else None,
        "finite":finite,"degenerate_faces":degenerate,
        "local_bounds":{"min":[min(v[j] for v in local) for j in range(3)],
                        "max":[max(v[j] for v in local) for j in range(3)]},
        "world_bounds":{"min":[min(v[j] for v in world) for j in range(3)],
                        "max":[max(v[j] for v in world) for j in range(3)]},
        "hidden_in_healthy_view":obj.hide_get(),
    }
report["healthy_triangles"]=sum(report["parts"]["%04d"%i]["triangles"]
                                for i in report["selectors"]["healthy"])
report["all_finite"]=all(p["finite"] for p in report["parts"].values())
report["all_uv_inside_unit_square"]=all(p["uv_min"] is not None and
        min(p["uv_min"])>=0 and max(p["uv_max"])<=1
        for p in report["parts"].values())
report["all_faces_nonzero"]=all(p["degenerate_faces"]==0
        for p in report["parts"].values())
OUT.mkdir(parents=True,exist_ok=True)
dest=OUT/"garden-r2-audit.json"
dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print({"audit":str(dest),"healthy_triangles":report["healthy_triangles"],
       "all_finite":report["all_finite"],
       "all_uv_inside_unit_square":report["all_uv_inside_unit_square"],
       "all_faces_nonzero":report["all_faces_nonzero"]})
