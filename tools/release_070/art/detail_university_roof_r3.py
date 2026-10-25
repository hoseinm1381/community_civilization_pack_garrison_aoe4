"""Bounded University overlay roof repair: remove 42 unsupported tile pans.

Run only in the claimed live Blender MCP scene. The exact four stock University
mesh groups remain untouched in their approved blockout collection. This makes
a new seven-part overlay revision from r2; it never edits or deletes r1/r2.
"""
from pathlib import Path
import json
import bpy
import bmesh

OUT=Path("F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail")
SOURCE="CCP070_University_Detailed_Overlay_r2"
DEST="CCP070_University_Detailed_Overlay_r3"
BASE="CCP070_University_Additions_Blockout"
PROOF=OUT/"university-r2-roof-seated.json"
if bpy.data.collections.get(DEST):
    raise RuntimeError("University r3 already exists; preserve revision")
source=bpy.data.collections.get(SOURCE)
base=bpy.data.collections.get(BASE)
if source is None or base is None:
    raise RuntimeError("University r2 or exact stock base missing")
stock=[o for o in base.objects if o.get("stock_geometry_unchanged")]
if len(stock)!=4:
    raise RuntimeError("Four exact stock mesh groups must remain")
proof=json.loads(PROOF.read_text(encoding="utf-8"))
if proof.get("revision")!=SOURCE or proof.get("tiles_seated")!=124:
    raise RuntimeError("Expected 124 seated pans in source r2")
unsupported={row["component"] for row in proof.get("unseated",[])}
if len(unsupported)!=42 or len(proof.get("unseated",[]))!=42:
    raise RuntimeError("Expected exactly 42 unsupported tile components")
if any(row.get("reason")!="No roof supports complete pan" for row in proof["unseated"]):
    raise RuntimeError("Unexpected unsupported-pan reason")
parts={int(o.name[-4:]):o for o in source.objects}
if set(parts)!=set(range(7)) or len(source.objects)!=7:
    raise RuntimeError("University r2 must contain seven exact parts")
roof=parts[4].data
parent=list(range(len(roof.vertices)))
def find(index):
    while parent[index]!=index:
        parent[index]=parent[parent[index]]
        index=parent[index]
    return index
for edge in roof.edges:
    a,b=map(find,edge.vertices)
    parent[b]=a
components={}
for index in range(len(parent)):
    components.setdefault(find(index),[]).append(index)
faces_by_root={}
for face in roof.polygons:
    faces_by_root.setdefault(find(face.vertices[0]),[]).append(face)
for root in unsupported:
    verts=components.get(root,[])
    faces=faces_by_root.get(root,[])
    if len(verts)!=12 or len(faces)!=10 or any(len(face.vertices)!=4 for face in faces):
        raise RuntimeError("Unsupported component is not a closed 12-vertex tile pan")
supported={row["component"] for row in proof.get("per_pan_support",[])}
if len(supported)!=124 or supported & unsupported:
    raise RuntimeError("Seated/unsupported component sets overlap or are incomplete")
def centroid_key(vertices,indices):
    return tuple(round(sum(vertices[i].co[axis] for i in indices)/len(indices),6)
                 for axis in range(3))
source_support={centroid_key(roof.vertices,components[row["component"]]):row["support"]
                for row in proof["per_pan_support"]}
if len(source_support)!=124:
    raise RuntimeError("Supported pan centroids are not unique")
drop={vertex for root in unsupported for vertex in components[root]}
if len(drop)!=42*12:
    raise RuntimeError("Unsupported tile vertex groups overlap")

dest=bpy.data.collections.new(DEST)
bpy.context.scene.collection.children.link(dest)
clones={}
for i in range(7):
    obj=parts[i].copy()
    obj.data=parts[i].data.copy()
    obj.name=DEST+"_garrison_part_%04d"%i
    dest.objects.link(obj)
    clones[i]=obj

mesh=clones[4].data
original_vertices=len(mesh.vertices)
original_faces=len(mesh.polygons)
original_loops=len(mesh.loops)
bm=bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
to_delete=[bm.verts[i] for i in sorted(drop)]
bmesh.ops.delete(bm,geom=to_delete,context="VERTS")
bm.to_mesh(mesh)
bm.free()
mesh.update()
if len(mesh.vertices)!=original_vertices-42*12:
    raise RuntimeError("Unexpected vertex loss during tile removal")
if len(mesh.polygons)!=original_faces-42*10:
    raise RuntimeError("Unexpected face loss during tile removal")
if len(mesh.loops)!=original_loops-42*40:
    raise RuntimeError("Unexpected UV loop loss during tile removal")
if not mesh.uv_layers or not mesh.color_attributes:
    raise RuntimeError("UV or viewport material color was lost")
new_parent=list(range(len(mesh.vertices)))
def new_find(index):
    while new_parent[index]!=index:
        new_parent[index]=new_parent[new_parent[index]]
        index=new_parent[index]
    return index
for edge in mesh.edges:
    a,b=map(new_find,edge.vertices)
    new_parent[b]=a
new_components={}
for index in range(len(new_parent)):
    new_components.setdefault(new_find(index),[]).append(index)
new_faces={}
for face in mesh.polygons:
    new_faces.setdefault(new_find(face.vertices[0]),[]).append(face)
new_support=[]
for root,indices in new_components.items():
    faces=new_faces.get(root,[])
    if len(indices)!=12 or len(faces)!=10 or any(len(face.vertices)!=4 for face in faces):
        continue
    key=centroid_key(mesh.vertices,indices)
    name=source_support.get(key)
    if name is None:
        raise RuntimeError("A remaining tile lacks a seated support proof")
    new_support.append({"component":root,"support":name,
                        "bottom_contact_offset":.004})
if len(new_support)!=124:
    raise RuntimeError("Unexpected seated pan count after removal")

for obj in source.objects:
    obj.hide_set(True)
    obj.hide_render=True
for i,obj in clones.items():
    hidden=i in (2,3)
    obj.hide_set(hidden)
    obj.hide_render=hidden
for obj in stock:
    obj.hide_set(False)
    obj.hide_render=False

result={
    "schema":"ccp-070-university-supported-roof-source/v1",
    "source":SOURCE,"revision":DEST,
    "tiles_seated":124,
    "unsupported_removed":42,
    "removed_reason":"No original stock or gate roof supports all vertices of these pans",
    "unseated":[],
    "per_pan_support":new_support,
    "roof_part_before":{"vertices":original_vertices,"faces":original_faces,"loops":original_loops},
    "roof_part_after":{"vertices":len(mesh.vertices),"faces":len(mesh.polygons),
                       "loops":len(mesh.loops)},
    "original_stock_groups_preserved":len(stock),
    "healthy_parts":[0,1,4,5,6],"heavy_damage_parts":[0,3],"ruins_parts":[2],
    "native_cook":False,"native_render":False,
}
OUT.mkdir(parents=True,exist_ok=True)
path=OUT/"university-r3-roof-seated.json"
path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print({"revision":DEST,"removed_unsupported_pans":42,
       "retained_seated_pans":124,"roof_vertices":len(mesh.vertices),
       "stock_groups_preserved":len(stock),"proof":str(path)})
