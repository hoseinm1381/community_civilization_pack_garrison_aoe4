"""Seat every University roof accent, preserving r3 and the exact stock body.

The earlier pan-only pass missed ridge caps and long decorative battens.
Run through the sole claimed Blender MCP instance, never background Blender.
"""
from pathlib import Path
import bpy, bmesh, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
SOURCE='CCP070_University_Detailed_Overlay_r3'
DEST='CCP070_University_Detailed_Overlay_r4'
assert not bpy.data.collections.get(DEST)
base=bpy.data.collections['CCP070_University_Additions_Blockout']
origin=Vector((15,-15,0))
trees=[(o.name,BVHTree.FromPolygons([o.matrix_world@v.co-origin for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])) for o in base.objects if o.type=='MESH' and ('roof' in o.name.lower() or o.get('stock_geometry_unchanged'))]
c=bpy.data.collections.new(DEST);bpy.context.scene.collection.children.link(c)
parts={}
for o in bpy.data.collections[SOURCE].objects:
    n=o.copy();n.data=o.data.copy();n.name=DEST+'_garrison_part_'+o.name[-4:];c.objects.link(n);parts[int(o.name[-4:])]=n
m=parts[4].data;parent=list(range(len(m.vertices)))
def find(a):
    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
    return a
for e in m.edges:
    a,b=map(find,e.vertices);parent[b]=a
groups={}
for i in range(len(parent)):groups.setdefault(find(i),[]).append(i)
changed=[];removed=[];drop=[]
for root,ids in groups.items():
    # The single 18-vertex gateway roof is the supporting body itself.
    if root==0 and len(ids)==18:continue
    coords=[m.vertices[i].co.copy() for i in ids];z=min(v.z for v in coords)
    candidates=[]
    for name,tree in trees:
        hits=[tree.ray_cast(Vector((v.x,v.y,40)),Vector((0,0,-1)),100)[0] for v in coords]
        if all(h is not None for h in hits):
            candidates.append((abs(z-sum(h.z for h in hits)/len(hits)),name,hits))
    if not candidates:
        removed.append({'root':root,'vertices':len(ids),'reason':'No complete stock/gateway roof support'});drop.extend(ids);continue
    _,name,hits=min(candidates,key=lambda x:x[0])
    for i,v,h in zip(ids,coords,hits):m.vertices[i].co.z=h.z+.004+v.z-z
    changed.append({'root':root,'vertices':len(ids),'support':name,'contact':.004})
if drop:
    bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in drop],context='VERTS');bm.to_mesh(m);bm.free()
m.update()
for o in bpy.data.collections[SOURCE].objects:o.hide_set(True)
for i,o in parts.items():o.hide_set(i in (2,3))
result={'schema':'ccp-070-university-all-roof-accents/v1','source':SOURCE,'revision':DEST,'seated_components':changed,'removed_components':removed,'removed_vertices':len(drop),'stock_body_modified':False,'native_proof':False}
(OUT/'university-r4-all-accents-seated.json').write_text(json.dumps(result,indent=2))
print({'revision':DEST,'seated':len(changed),'removed':removed})
