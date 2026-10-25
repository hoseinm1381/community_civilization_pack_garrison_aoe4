"""Background-only source inspection and renders; never saves Blender sources."""
import bpy,bmesh,json,hashlib,sys,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/building_style_audit_077'
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,CFG['garrison_extension'])
from types import SimpleNamespace
# Read-only Chunky v4 walker; the installed compiled Python wrapper does not
# expose its submodules in this background interpreter. No binary writes.
class rc:
 @staticmethod
 def read_lp_string(data,at):
  n=struct.unpack_from('<I',data,at)[0];at+=4
  return data[at:at+n].decode('utf-8'),at+n
 @staticmethod
 def lp_string(s):
  b=s.encode('utf-8');return struct.pack('<I',len(b))+b
 @staticmethod
 def load(path):
  raw=Path(path).read_bytes();assert raw[:16]==b'Relic Chunky\r\n\x1a\x00'
  assert struct.unpack_from('<I',raw,16)[0]==4
  def parse(start,end):
   out=[];at=start
   while at<end:
    kind,tag,version,size,n=struct.unpack_from('<4s4sIII',raw,at);assert kind in (b'FOLD',b'DATA')
    data=at+20+n;stop=data+size;assert stop<=end
    out.append(SimpleNamespace(tag=tag,payload=raw[data:stop],children=parse(data,stop) if kind==b'FOLD' else []));at=stop
   assert at==end;return out
  return SimpleNamespace(roots=parse(24,len(raw)))
 @staticmethod
 def walk(chunks):
  for c in chunks:
   yield c
   yield from rc.walk(c.children)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lp_set(payload):
 name,at=rc.read_lp_string(payload,0);n=struct.unpack_from('<I',payload,at)[0];at+=4;names=[]
 for _ in range(n):s,at=rc.read_lp_string(payload,at);names.append(s)
 return names
def states(payload):
 n=struct.unpack_from('<I',payload)[0];at=4;result=[]
 for _ in range(n):
  op,flag,one=struct.unpack_from('<IBI',payload,at);at+=9
  k,at=rc.read_lp_string(payload,at);v,at=rc.read_lp_string(payload,at);result.append((op,flag,one,k,v))
 return result
def filter_healthy(job):
 if not job.get('donor_manifest'):return dict(status='source-visible-meshes-only; native state not reconstructed')
 d=json.loads(Path(job['donor_manifest']).read_text());ct=d.get('structure_collection_contract')
 if not ct:return dict(status='no collection contract; source-visible meshes')
 chunks=list(rc.walk(rc.load(ct['source']['path']).roots))
 sets=[lp_set(c.payload) for c in chunks if c.tag==b'MSD ' and len(c.payload)>4]
 cond=[states(c.payload) for c in chunks if c.tag==b'CNBP']
 healthy=set();allnames=set()
 for i,names in enumerate(sets):
  allnames.update(names)
  c=cond[i] if i<len(cond) else []
  if not c or (2,0,1,'life_cycle_state','healthy') in c:healthy.update(names)
 if not healthy:return dict(status='healthy predicate unresolved; source envelope only')
 mscl=next(c for c in chunks if c.tag==b'MSCL');payload=mscl.children[0].payload
 offsets={n:payload.find(rc.lp_string(n)) for n in allnames}
 assert all(v>=2 for v in offsets.values())
 ordered=sorted(allnames,key=offsets.get);gi=0;kept=0;removed=0
 objs={int(o['garrison_mesh_index']):o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('garrison_mesh_index') is not None}
 for mapping,span in zip(ct['maps'],ct['geometry_group_spans']):
  inv={bone:ordered[i] for i,bone in enumerate(mapping['source_to_local_bone']) if bone>=0}
  for g in d['geometry']['groups'][gi:gi+span]:
   obj=objs.get(gi)
   if obj is None:raise RuntimeError('No mesh for collection group '+str(gi))
   assert len(obj.data.polygons)==len(g['triangles'])
   mask=[];bones=g['collection_bone_indices']
   for t in g['triangles']:
    b=[bones[i] for i in t];assert len(set(b))==1
    mask.append(inv[b[0]] in healthy)
   bm=bmesh.new();bm.from_mesh(obj.data);bm.faces.ensure_lookup_table()
   erase=[bm.faces[i] for i,v in enumerate(mask) if not v]
   removed+=len(erase);kept+=sum(mask)
   bmesh.ops.delete(bm,geom=erase,context='FACES');bm.to_mesh(obj.data);bm.free();obj.data.update();gi+=1
 return dict(status='native healthy/unconditional selector subset',kept_triangles=kept,excluded_triangles=removed,conditional_visibility_not_simulated=True)

assert bpy.app.background
jobs=json.loads((OUT/'jobs.json').read_text());records=[]
supplement='--supplement' in sys.argv
if supplement:jobs=[j for j in jobs if j['family'] in ('house','hideout')]
for job in jobs:
 dest=OUT/('supplement' if supplement else 'renders')/job['id'];dest.mkdir(parents=True,exist_ok=True)
 source=Path(job['source']);assert sha(source)==job['source_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
 try:state=filter_healthy(job)
 except Exception as e:state=dict(status='filter failed; preview envelope only',error=str(e))
 for extra in job.get('extras',[]):
  with bpy.data.libraries.load(extra,link=False) as (src,dst):dst.objects=list(src.objects) if supplement else [n for n in src.objects if n.startswith('vn_')]
  for obj in dst.objects:
   if obj and obj.type=='MESH':s.collection.objects.link(obj)
 if job.get('collection'):
  cols=[bpy.data.collections[job['collection']]]
  if job['family']=='university':cols.append(bpy.data.collections['CCP070_University_Additions_Blockout'])
  allowed={o for c in cols for o in c.all_objects}
  for o in s.objects:
   if o.type=='MESH':o.hide_render=o not in allowed or (o in cols[0].all_objects.values() and o.name.endswith(('0002','0003')))
 objs=[o for o in s.objects if o.type=='MESH' and not o.hide_render and len(o.data.polygons)]
 # Collection visibility in saved sources can suppress otherwise visible parts.
 for col in bpy.data.collections:col.hide_render=False
 for o in objs:o.hide_render=False
 pts=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
 lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
 if supplement:lo.z=max(0,lo.z)
 center=(lo+hi)/2;size=max(hi-lo)
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE':textures.append(dict(name=im.name,path=bpy.path.abspath(im.filepath),packed=bool(im.packed_file),exists=Path(bpy.path.abspath(im.filepath)).exists(),size=list(im.size)))
 for o in list(s.objects):
  if o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
 for mat in bpy.data.materials:
  if mat.use_nodes:
   control=mat.node_tree.nodes.get('GARRISON Material Controls')
   if control and control.inputs.get('Team Colour Strength'):control.inputs['Team Colour Strength'].default_value=0
 s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True
 s.render.resolution_x=800;s.render.resolution_y=640;s.render.resolution_percentage=100
 if s.world is None:s.world=bpy.data.worlds.new('Audit World')
 s.world.use_nodes=False;s.world.color=(.28,.28,.28);s.view_settings.view_transform='AgX'
 for vec,power in [((.8,-.8,1.6),65),((-.6,-.8,.65),35)]:
  d=bpy.data.lights.new('Audit','AREA');o=bpy.data.objects.new('Audit',d);s.collection.objects.link(o);o.location=center+Vector(vec)*size;d.energy=size*size*power;d.size=size
 cam=bpy.data.objects.new('Audit camera',bpy.data.cameras.new('Audit camera'));s.collection.objects.link(cam);cam.data.type='ORTHO';s.camera=cam
 if supplement:
  ground=bpy.data.materials.new('Audit terrain proxy');ground.use_nodes=True;ground.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.12,.135,.075,1)
  bpy.ops.mesh.primitive_plane_add(size=size*8,location=(center.x,center.y,-.02));bpy.context.object.data.materials.append(ground)
 record={**job,'state_scope':state,'bounds_min':list(lo),'bounds_max':list(hi),'mesh_count':len(objs),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objs),'material_slots':sum(len(o.data.materials) for o in objs),'textures':textures,'objects':[dict(name=o.name,triangles=sum(len(p.vertices)-2 for p in o.data.polygons)) for o in objs]}
 for name,vec in [('iso',(1,-1,.9)),('back',(-1,1,.9))]:
  cam.location=center+Vector(vec).normalized()*size*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size*1.5
  s.render.filepath=str(dest/(name+'.png'));bpy.ops.render.render(write_still=True)
 assert sha(source)==job['source_sha256']
 (dest/'metrics.json').write_text(json.dumps(record,indent=2),encoding='utf-8');records.append(record)
 (OUT/('supplement-metrics.json' if supplement else 'render-metrics.json')).write_text(json.dumps(records,indent=2),encoding='utf-8')
 print('AUDIT_RENDER_DONE',job['id'],record['triangles'],state['status'],flush=True)
print('AUDIT_ALL_RENDERS_DONE',len(records),flush=True)
