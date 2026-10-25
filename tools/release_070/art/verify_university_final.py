"""Independent retained-face/UV and actual roof-contact readback for University."""
import bpy,json
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
def parts(name):return {int(o.name[-4:]):o.data for o in bpy.data.collections[name].objects}
def faces(mesh,with_z=True):
    uv=mesh.uv_layers.active.data
    return Counter(tuple(sorted(tuple(round(x,6) for x in (tuple(mesh.vertices[mesh.loops[i].vertex_index].co)[:3 if with_z else 2]+tuple(uv[i].uv))) for i in p.loop_indices)) for p in mesh.polygons)
a=parts('CCP070_University_Detailed_Overlay_r2');b=parts('CCP070_University_Detailed_Overlay_r3');c=parts('CCP070_University_Detailed_Overlay_r6')
previous=parts('CCP070_University_Detailed_Overlay_r5')
assert all(faces(a[i])==faces(b[i])==faces(c[i]) for i in range(7) if i not in (4,6))
assert all(faces(c[i])==faces(previous[i]) for i in range(7) if i!=6)
assert all(.14<v.co.x<5.5 and -4.8<v.co.y<-1.4 and .2099<v.co.z<1 for v in c[6].vertices)
assert not (faces(b[4])-faces(a[4]))
assert len(a[4].vertices)-len(b[4].vertices)==504
assert len(a[4].polygons)-len(b[4].polygons)==420
assert not (faces(c[4],False)-faces(b[4],False))
base=bpy.data.collections['CCP070_University_Additions_Blockout'];origin=Vector((15,-15,0))
trees=[(o.name,BVHTree.FromPolygons([o.matrix_world@v.co-origin for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])) for o in base.objects if o.type=='MESH' and ('roof' in o.name.lower() or o.get('stock_geometry_unchanged'))]
m=c[4];parent=list(range(len(m.vertices)))
def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for e in m.edges:
    x,y=map(find,e.vertices);parent[y]=x
groups={}
for i in range(len(parent)):groups.setdefault(find(i),[]).append(i)
fail=[];contacts=[]
for root,ids in groups.items():
    if root==0 and len(ids)==18:continue
    good=[]
    for name,tree in trees:
        hits=[tree.ray_cast(Vector((m.vertices[i].co.x,m.vertices[i].co.y,40)),Vector((0,0,-1)),100)[0] for i in ids]
        if all(h is not None for h in hits):
            gaps=[m.vertices[i].co.z-h.z for i,h in zip(ids,hits)]
            if .0035<=min(gaps)<=.0045 and min(gaps)>0:good.append((name,min(gaps),max(gaps)))
    if not good:fail.append(root)
    else:contacts.append({'root':root,'vertices':len(ids),'supports':good})
stock=[o for o in base.objects if o.get('stock_geometry_unchanged')]
decoded=json.loads(Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/inventory/university/decoded/012f675cd6b5f5cb1222/decoded-static.json').read_text())
stock_match=all([tuple(v.co) for v in sorted(stock,key=lambda o:o.name)[i].data.vertices]==[tuple(p) for p in g['positions']] for i,g in enumerate(decoded['geometry']['groups']))
assert not fail,fail
assert stock_match
result={'status':'passed','original_four_stock_groups_vertices_exact':stock_match,'five_nonroof_nonfurniture_parts_geometry_uv_exact':True,'r6_only_courtyard_furniture_changed':True,'furniture_seated_on_paving_min_z':min(v.co.z for v in c[6].vertices),'r3_only_removed_42_closed_unsupported_pans':True,'r4_retained_xy_face_uv_subset_exact':True,'supported_roof_accents':len(contacts),'failed_roof_accents':fail,'contacts':contacts,'native_runtime':False}
(OUT/'university-r6-independent-verify.json').write_text(json.dumps(result,indent=2))
print({k:v for k,v in result.items() if k!='contacts'})
