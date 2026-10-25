"""Independent exact face/UV readback of the importer-limit repartition."""
from pathlib import Path
from collections import Counter
import bpy,json
SOURCE='CCP070_Kinh_Thien_Detailed_r3';DEST='CCP070_Kinh_Thien_Detailed_r4'
a={int(o.name[-4:]):o for o in bpy.data.collections[SOURCE].objects};b={int(o.name[-4:]):o for o in bpy.data.collections[DEST].objects}
def counter(objects):
    c=Counter()
    for o in objects:
        m=o.data;uv=m.uv_layers.active.data
        for p in m.polygons:c[tuple(sorted(tuple(m.vertices[m.loops[i].vertex_index].co)+tuple(uv[i].uv) for i in p.loop_indices))]+=1
    return c
assert counter([a[4],a[5]])==counter([b[4],b[5]])
assert all(counter([a[i]])==counter([b[i]]) for i in (0,1,2,3,6))
assert {o.data.materials[0].name for o in b.values()}=={a[4].data.materials[0].name}
corners={i:len(o.data.loops) for i,o in b.items()};assert max(corners.values())<60000
moved=len(a[4].data.polygons)-len(b[4].data.polygons);assert moved==10140
for o in a.values():o.hide_set(True)
for i,o in b.items():o.hide_set(i in (2,3))
report={'schema':'ccp-070-wonder-exact-healthy-repartition/v1','source':SOURCE,'revision':DEST,'moved_closed_tile_pans':1014,'moved_faces':moved,'before_part4_corners':len(a[4].data.loops),'after_per_part_corners':corners,'healthy_face_position_uv_multiset_exact':True,'five_other_parts_exact':True,'part4_and_5_first_stage':20,'native_cook':False,'independent_readback':True}
path=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail/wonder-r4-repartition.json');assert not path.exists();path.write_text(json.dumps(report,indent=2));print(report)
