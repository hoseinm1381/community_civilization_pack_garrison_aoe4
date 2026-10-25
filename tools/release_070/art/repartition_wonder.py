"""Repartition identical healthy roof faces below native FBX corner limits.

Move whole closed tile-pan components from part4 to part5. Both have first
stage20 and identical healthy selector activation. No visible face, UV, material,
position, damage/ruin part or native animation owner changes.
"""
from pathlib import Path
from collections import Counter
import bpy,json
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
SOURCE='CCP070_Kinh_Thien_Detailed_r3';DEST='CCP070_Kinh_Thien_Detailed_r4'
assert not bpy.data.collections.get(DEST)
source={int(o.name[-4:]):o for o in bpy.data.collections[SOURCE].objects}
c=bpy.data.collections.new(DEST);bpy.context.scene.collection.children.link(c)
dest={}
for i,o in source.items():
    n=o.copy();n.data=o.data.copy();n.name=DEST+'_garrison_part_%04d'%i;c.objects.link(n);dest[i]=n
m=source[4].data;parent=list(range(len(m.vertices)))
def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for e in m.edges:
    a,b=map(find,e.vertices);parent[b]=a
components={}
for p in m.polygons:components.setdefault(find(p.vertices[0]),[]).append(p.index)
movable=[ids for ids in components.values() if len(ids)==10 and len({i for f in ids for i in m.polygons[f].vertices})==12 and all(len(m.polygons[f].vertices)==4 for f in ids)]
assert len(movable)==2028
move={i for ids in movable[::2] for i in ids};keep=[p.index for p in m.polygons if p.index not in move]
def rebuild(name,inputs,material):
    vertices=[];faces=[];uvs=[];colors=[];smooth=[];mapping={}
    for index,(mesh,ids) in enumerate(inputs):
        uv=mesh.uv_layers.active.data;col=mesh.color_attributes.active_color
        for pi in ids:
            p=mesh.polygons[pi];face=[];fuv=[];fcol=[]
            for li in p.loop_indices:
                vi=mesh.loops[li].vertex_index;key=(index,vi)
                if key not in mapping:mapping[key]=len(vertices);vertices.append(tuple(mesh.vertices[vi].co))
                face.append(mapping[key]);fuv.append(tuple(uv[li].uv));fcol.append(tuple(col.data[li].color))
            faces.append(face);uvs.append(fuv);colors.append(fcol);smooth.append(p.use_smooth)
    out=bpy.data.meshes.new(name);out.from_pydata(vertices,[],faces);out.update();out.materials.append(material)
    uv=out.uv_layers.new(name='UVMap');col=out.color_attributes.new(name='CCP070_Color',type='BYTE_COLOR',domain='CORNER')
    for p,fu,fc,sm in zip(out.polygons,uvs,colors,smooth):
        p.use_smooth=sm
        for li,u,color in zip(p.loop_indices,fu,fc):uv.data[li].uv=u;col.data[li].color=color
    return out
mat=source[4].data.materials[0]
dest[4].data=rebuild(DEST+'_roof_mesh',[(m,keep)],mat)
dest[5].data=rebuild(DEST+'_ornament_mesh',[(source[5].data,[p.index for p in source[5].data.polygons]),(m,sorted(move))],mat)
def face_counter(objects):
    result=Counter()
    for o in objects:
        me=o.data;uv=me.uv_layers.active.data
        for p in me.polygons:
            result[tuple(sorted(tuple(me.vertices[me.loops[i].vertex_index].co)+tuple(uv[i].uv) for i in p.loop_indices))]+=1
    return result
assert face_counter([source[4],source[5]])==face_counter([dest[4],dest[5]])
assert all(face_counter([source[i]])==face_counter([dest[i]]) for i in (0,1,2,3,6))
corners={i:len(o.data.loops) for i,o in dest.items()};assert max(corners.values())<60000,corners
for o in source.values():o.hide_set(True)
for i,o in dest.items():o.hide_set(i in (2,3))
report={'schema':'ccp-070-wonder-exact-healthy-repartition/v1','source':SOURCE,'revision':DEST,'moved_closed_tile_pans':len(movable[::2]),'moved_faces':len(move),'before_part4_corners':len(m.loops),'after_per_part_corners':corners,'healthy_face_position_uv_multiset_exact':True,'five_other_parts_exact':True,'part4_and_5_first_stage':20,'native_cook':False}
(OUT/'wonder-r4-repartition.json').write_text(json.dumps(report,indent=2));print(report)
