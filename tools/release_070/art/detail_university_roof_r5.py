"""Remove visually intrusive stock-roof accents; retain scholarly gateway roof.

The native roof silhouette is better preserved without isolated replacement
tile strips and finials. The approved court, gate and steles stay intact.
"""
from pathlib import Path
import bpy,bmesh,json
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
SOURCE='CCP070_University_Detailed_Overlay_r4';DEST='CCP070_University_Detailed_Overlay_r5'
assert not bpy.data.collections.get(DEST)
c=bpy.data.collections.new(DEST);bpy.context.scene.collection.children.link(c)
parts={}
for o in bpy.data.collections[SOURCE].objects:
    n=o.copy();n.data=o.data.copy();n.name=DEST+'_garrison_part_'+o.name[-4:];c.objects.link(n);parts[int(o.name[-4:])]=n
m=parts[4].data;parent=list(range(len(m.vertices)))
def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for e in m.edges:
    a,b=map(find,e.vertices);parent[b]=a
groups={}
for i in range(len(parent)):groups.setdefault(find(i),[]).append(i)
drop=[i for ids in groups.values() if sum(m.vertices[j].co.y for j in ids)/len(ids)>0 for i in ids]
before=(len(m.vertices),len(m.polygons))
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in drop],context='VERTS');bm.to_mesh(m);bm.free();m.update()
for o in bpy.data.collections[SOURCE].objects:o.hide_set(True)
for i,o in parts.items():o.hide_set(i in (2,3))
result={'source':SOURCE,'revision':DEST,'removed_stock_roof_accent_vertices':len(drop),'before':before,'after':[len(m.vertices),len(m.polygons)],'reason':'Preserve recognizable native roof; isolated tile strips and finials read poorly in close review','main_stock_body_unchanged':True}
(OUT/'university-r5-visual-refinement.json').write_text(json.dumps(result,indent=2));print(result)
