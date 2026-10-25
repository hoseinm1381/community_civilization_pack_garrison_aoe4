"""Independently compare seated tile revisions with their source and roofs.

Run verify_roof_revision(source, revision, base, offset, slug) in Blender MCP.
This reads source/target data and writes a compact numerical receipt only.
"""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT=Path("F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail")

def verify_roof_revision(source_name,revision_name,base_name,offset,slug):
    source=bpy.data.collections[source_name]
    revised=bpy.data.collections[revision_name]
    base=bpy.data.collections[base_name]
    center=Vector(offset)
    src={int(o.name[-4:]):o for o in source.objects}
    dst={int(o.name[-4:]):o for o in revised.objects}
    if set(src)!=set(range(7)) or set(dst)!=set(range(7)):
        raise RuntimeError("Both revisions need all seven parts")
    topology=[]
    for i in range(7):
        a,b=src[i].data,dst[i].data
        same=(len(a.vertices)==len(b.vertices) and
              len(a.polygons)==len(b.polygons) and
              len(a.loops)==len(b.loops) and
              len(a.uv_layers)==len(b.uv_layers))
        if same:
            same=all(tuple(a.uv_layers[0].data[j].uv)==tuple(b.uv_layers[0].data[j].uv)
                     for j in range(len(a.loops)))
        topology.append({"part":i,"same_vertex_face_loop_uv":same,
                         "source_vertices":len(a.vertices),
                         "revised_vertices":len(b.vertices),
                         "source_faces":len(a.polygons),
                         "revised_faces":len(b.polygons)})
    trees={o.name:BVHTree.FromPolygons(
        [o.matrix_world@v.co-center for v in o.data.vertices],
        [list(p.vertices) for p in o.data.polygons])
        for o in base.objects if o.type=="MESH" and
        ("roof" in o.name.lower() or o.get("stock_geometry_unchanged"))}
    mesh=dst[4].data
    parent=list(range(len(mesh.vertices)))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]
            a=parent[a]
        return a
    for edge in mesh.edges:
        a,b=map(find,edge.vertices)
        parent[b]=a
    groups={}
    for index in range(len(parent)):
        groups.setdefault(find(index),[]).append(index)
    group_faces={}
    for face in mesh.polygons:
        group_faces.setdefault(find(face.vertices[0]),[]).append(face)
    seat=json.loads((OUT/(slug+"-roof-seated.json")).read_text(encoding="utf-8"))
    supports={row["component"]:row["support"] for row in seat["per_pan_support"]}
    failures=[]
    min_contact=[]
    for root,indices in groups.items():
        faces=group_faces.get(root,[])
        if len(indices)!=12 or len(faces)!=10 or any(len(f.vertices)!=4 for f in faces):
            continue
        name=supports.get(root)
        if name not in trees:
            failures.append({"component":root,"reason":"missing proof support"})
            continue
        gaps=[]
        for i in indices:
            v=mesh.vertices[i].co
            hit=trees[name].ray_cast(Vector((v.x,v.y,40)),Vector((0,0,-1)),100)[0]
            if hit is None:
                failures.append({"component":root,"reason":"vertex misses support"})
                gaps=[]
                break
            gaps.append(v.z-hit.z)
        if gaps:
            low=min(gaps)
            min_contact.append(low)
            if not (.0035<=low<=.0045) or min(gaps)<0 or max(gaps)>.12:
                failures.append({"component":root,"reason":"bad contact profile",
                                 "min_gap":low,"max_gap":max(gaps)})
    result={"schema":"ccp-070-roof-revision-independent-verify/v1",
            "source":source_name,"revision":revision_name,"base":base_name,
            "parts":topology,"all_topology_uv_unchanged":all(x["same_vertex_face_loop_uv"] for x in topology),
            "tile_components":len(min_contact),"expected_tiles":seat["tiles_seated"],
            "contact_min":min(min_contact) if min_contact else None,
            "contact_max":max(min_contact) if min_contact else None,
            "failed_components":failures,
            "status":"passed" if not failures and len(min_contact)==seat["tiles_seated"]
                      and all(x["same_vertex_face_loop_uv"] for x in topology) else "failed"}
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/(slug+"-roof-independent-verify.json")
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return {"status":result["status"],"path":str(path),
            "tile_components":result["tile_components"],
            "expected_tiles":result["expected_tiles"],
            "contact_min":result["contact_min"],
            "contact_max":result["contact_max"],
            "failed_component_count":len(failures),
            "all_topology_uv_unchanged":result["all_topology_uv_unchanged"]}
