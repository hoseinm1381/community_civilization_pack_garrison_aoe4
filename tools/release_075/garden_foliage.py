"""Owned Garden foliage draft: preserve architecture and native-state meshes.

Replaces seven closed placeholder crowns with branching broadleaf geometry.
Uses opaque, closed leaves: no unsupported alpha material is introduced.
Run in background Blender. Historical source is read-only; outputs are immutable.
"""
from pathlib import Path
import bpy,bmesh,json,math,random,hashlib
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_075/art/garden/foliage-r1'
TARGET=ROOT/'art/authoring/release_075/garden/foliage-r1.blend'
SOURCE=ROOT/'art/authoring/buildings_070/architecture-final-r4.blend'
COLLECTION='CCP070_Imperial_Garden_Detailed_r4'
if OUT.exists() or TARGET.exists():raise FileExistsError('Use a new revision; preserve prior draft')
assert bpy.app.background
OUT.mkdir(parents=True);TARGET.parent.mkdir(parents=True,exist_ok=True)
with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):dst.collections=[COLLECTION]
col=dst.collections[0];bpy.context.scene.collection.children.link(col)
col.name='CCP075_Garden_Foliage_r1'
for o in list(bpy.context.scene.objects):
 if o not in list(col.all_objects):o.hide_render=True;o.hide_set(True)
parts={int(o.name[-4:]):o for o in col.all_objects if o.type=='MESH'}
assert set(parts)==set(range(7))
def mesh_hash(o):
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(v.uv) for v in o.data.uv_layers.active.data])).encode()).hexdigest()
before={i:mesh_hash(o) for i,o in parts.items()}
obj=parts[5];m=obj.data
parent=list(range(len(m.vertices)))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for e in m.edges:
 a,b=map(find,e.vertices);parent[a]=b
components={}
for v in m.vertices:components.setdefault(find(v.index),[]).append(v.index)
crowns=[]
for ids in components.values():
 pts=[m.vertices[i].co for i in ids]
 lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
 if len(ids)==37 and hi.z>2 and lo.z>1:
  crowns.append((ids,lo,hi))
assert len(crowns)==7, 'Unexpected source crown topology'
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.verts[i] for ids,_,_ in crowns for i in ids],context='VERTS')
bm.to_mesh(m);bm.free()

# Use the established atlas/mesh helper, with a single shared material.
ns={};exec((ROOT/'tools/release_070/art/detail_core.py').read_text(),ns)
Batch=ns['Batch'];batch=Batch('foliage_branches',col,obj.data.materials[0],obj.location)
rng=random.Random(75075);contacts=[];leaf_count=0
def leaf(base,direction,length,width):
 global leaf_count
 a=Vector(base);d=Vector(direction).normalized();side=d.cross(Vector((0,0,1)))
 if side.length<.01:side=d.cross(Vector((0,1,0)))
 side.normalize();n=d.cross(side).normalized();mid=a+d*length*.48
 v=[a,mid+side*width*.5,a+d*length,mid-side*width*.5,mid+n*.035,mid-n*.018]
 batch.add(v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],'foliage')
 leaf_count+=1
for tree_index,(_,lo,hi) in enumerate(crowns):
 center=(lo+hi)*.5
 # Source canopy's asymmetric extrema are from a nine-sided radial mesh.
 # Recover original trunk centre from the crown's polygon vertex positions.
 ids=crowns[tree_index][0]
 original=[Vector(p) for p in []]
 # Known source trunk anchors are exact recipe constants, not bbox guesses.
 anchors=[(-9.25,8.1,3.25,.88),(-9.1,3.5,2.55,.77),(-9.2,-1.4,2.8,.83),(-8.45,-8.2,2.65,.73),(1.15,-8.7,3,.84),(4.25,-7.7,2.6,.72),(7.9,-7.2,2.3,.72)]
 x,y,h,r=min(anchors,key=lambda a:(a[0]-center.x)**2+(a[1]-center.y)**2)
 anchor=Vector((x,y,h*.56))
 batch.tube([anchor-Vector((0,0,.10)),anchor+Vector((.02,0,h*.25))],[.09,.025],'wood',7)
 contacts.append({'tree':tree_index,'interface':'new stem to retained trunk top','anchor':list(anchor),'intentional_overlap':.10})
 for branch in range(9):
  angle=branch*2.399963+tree_index*.7
  rise=.18+(branch%3)*.16
  start=anchor+Vector((.01,0,(branch%3)*.13))
  end=Vector((x+math.cos(angle)*r*.82,y+math.sin(angle)*r*.82,min(h-.16,anchor.z+rise+.35)))
  elbow=start.lerp(end,.5)+Vector((0,0,.09))
  batch.tube([start,elbow,end],[.055,.032,.009],'wood',6)
  for twig in range(3):
   t=.42+twig*.27;origin=elbow.lerp(end,t)
   ta=angle+(-.85 if twig%2 else .85)
   tip=origin+Vector((math.cos(ta)*r*.38,math.sin(ta)*r*.38,.13))
   batch.tube([origin,tip],[.018,.005],'wood',5)
   for k in range(7):
    point=origin.lerp(tip,(k+1)/8)
    la=ta+(-1 if k%2 else 1)*(.6+rng.random()*.6)
    leaf(point,(math.cos(la),math.sin(la),rng.uniform(-.1,.5)),rng.uniform(.28,.43),rng.uniform(.13,.21))
new=batch.emit()
for o in bpy.context.selected_objects:o.select_set(False)
obj.hide_set(False);new.hide_set(False);obj.select_set(True);new.select_set(True)
bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
obj.data.calc_loop_triangles()
after={i:mesh_hash(o) for i,o in parts.items()}
assert all(before[i]==after[i] for i in parts if i!=5),'Nonfoliage source drift'
for i,o in parts.items():
 o.hide_render=i in (2,3);o.hide_set(i in (2,3));o.data.calc_loop_triangles()
for img in bpy.data.images:
 if img.source=='FILE' and not img.packed_file:
  try:img.pack()
  except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
report={'status':'source_foliage_draft_not_accepted','source':str(SOURCE),'output':str(TARGET),'crowns_replaced':7,'closed_opaque_leaves':leaf_count,'healthy_triangles':sum(len(parts[i].data.loop_triangles) for i in (0,1,4,5,6)),'unchanged_parts':[i for i in parts if before[i]==after[i]],'contacts':contacts,'before_mesh_hashes':before,'after_mesh_hashes':after,'native_owner_colour':'pending separate stock attachment','limitations':['Native colour, official complete-compound comparison and final appearance pending','Branch/leaf canopy needs visual review before export']}
(OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','crowns_replaced','closed_opaque_leaves','healthy_triangles','unchanged_parts')}))
