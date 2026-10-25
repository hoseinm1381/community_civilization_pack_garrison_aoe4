"""Second Garden draft: replace repetitive pots with bounded planted beds.

Source paths are immutable. Existing roofs, foundation and native-state meshes
are preserved. New vegetation is confined to previous ornamental locations.
"""
from pathlib import Path
import bpy,bmesh,json,math,random,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'art/authoring/release_075/garden/foliage-r1.blend'
TARGET=ROOT/'art/authoring/release_075/garden/planting-r2.blend'
OUT=ROOT/'output/release_075/art/garden/planting-r2'
assert bpy.app.background
if TARGET.exists() or OUT.exists():raise FileExistsError('Retain previous revision')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
col=bpy.data.collections['CCP075_Garden_Foliage_r1'];col.name='CCP075_Garden_Planting_r2'
parts={int(o.name[-4:]):o for o in col.objects if o.type=='MESH'}
def digest(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(v.uv) for v in o.data.uv_layers.active.data])).encode()).hexdigest()
before={i:digest(o) for i,o in parts.items()}
obj=parts[5];m=obj.data
parent=list(range(len(m.vertices)))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for e in m.edges:
 a,b=map(find,e.vertices);parent[a]=b
comps={}
for v in m.vertices:comps.setdefault(find(v.index),[]).append(v.index)
anchors=[(-6.8,8.8),(-8,6.7),(-8,1.7),(-9.5,-5.8),(-6.9,-8.6),(.6,-9),(3.6,-8.8),(6,-8.7),(8.9,-6.5),(8.3,-2.5),(5.3,-1.4)]
remove=[];removed=[]
for ids in comps.values():
 pts=[m.vertices[i].co for i in ids];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);c=(lo+hi)/2
 near=any(abs(c.x-x)<.49 and abs(c.y-y)<.32 for x,y in anchors)
 if near and .14<lo.z<.30 and hi.z<.86 and len(ids) in (8,14):
  remove+=ids;removed.append({'bounds':[list(lo),list(hi)],'vertices':len(ids)})
assert len(removed)==55,(len(removed),'Expected eleven beds and44 bare stalks')
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(m);bm.free()
ns={};exec((ROOT/'tools/release_070/art/detail_core.py').read_text(),ns)
b=ns['Batch']('bounded_planting',col,obj.data.materials[0],obj.location)
rng=random.Random(750752);contacts=[];leaf_count=0
def leaf(a,d,length,width):
 global leaf_count
 a=Vector(a);d=Vector(d).normalized();side=d.cross(Vector((0,0,1))).normalized();n=d.cross(side).normalized();mid=a+d*length*.48
 b.add([a,mid+side*width*.5,a+d*length,mid-side*width*.5,mid+n*.025,mid-n*.012],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],'foliage');leaf_count+=1
# Six composed groups replace eleven identical boxes. Stay within ornamental
# margins; no new object occupies the east service route or bridge approach.
for index in (0,2,3,5,8,9):
 x,y=anchors[index];rx,ry=(.60,.34) if index%2 else (.44,.48)
 outline=[(x+rx*math.cos(a*math.tau/9),y+ry*math.sin(a*math.tau/9)) for a in range(9)]
 b.slab(outline,.065,.08,'clay')
 for k in range(7):
  angle=k*2.399963;cx=x+math.cos(angle)*rx*.60;cy=y+math.sin(angle)*ry*.55
  for j in range(7):
   az=j*math.tau/7+k*.44
   leaf((cx,cy,.055),(math.cos(az),math.sin(az),.5+rng.random()*.6),rng.uniform(.23,.40),.11)
 contacts.append({'bed':index,'soil_top':.065,'leaf_base':.055,'intentional_overlap':.010,'bounds':[x-rx,y-ry,x+rx,y+ry]})
new=b.emit()
for o in bpy.context.selected_objects:o.select_set(False)
obj.hide_set(False);new.hide_set(False);obj.select_set(True);new.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
after={i:digest(o) for i,o in parts.items()};assert all(before[i]==after[i] for i in parts if i!=5)
for i,o in parts.items():o.hide_render=i in (2,3);o.hide_set(i in (2,3));o.data.calc_loop_triangles()
OUT.mkdir(parents=True);bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
receipt={'status':'source_draft_review_required','source':str(SOURCE),'output':str(TARGET),'removed_repeated_objects':len(removed),'new_composed_beds':6,'new_leaves':leaf_count,'contacts':contacts,'unchanged_parts':[i for i in parts if before[i]==after[i]],'before_mesh_hashes':before,'after_mesh_hashes':after,'healthy_triangles':sum(len(parts[i].data.loop_triangles) for i in (0,1,4,5,6)),'remaining':['Material scale and colour study pending','Final complete-compound comparator and owner flag pending']}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
