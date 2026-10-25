"""Final-archive monastery geometry envelope; no native material claim."""
import bpy,ast,json,struct,hashlib
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/building_style_audit_077'
tree=ast.parse((ROOT/'tools/render_building_style_audit_077.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='rc'],type_ignores=[]),'readonly-chunky','exec'))
import numpy as np
records=[]
for age in (3,4):
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
 base=ROOT/f'output/asset_audit_077/readback/art/scenario/cccastle/monastery_age{age:02}/model.rrgeom'
 detail=ROOT/f'output/asset_audit_077/readback/art/scenario/cccastle/monastery_detail_age{age:02}/model.rrgeom'
 materials=[]
 for name,color in [('main',(.42,.35,.26,1)),('roof',(.30,.35,.37,1)),('detail',(.40,.20,.12,1))]:
  m=bpy.data.materials.new(name);m.diffuse_color=color;materials.append(m)
 tris=0;objects=[]
 for file in (base,detail):
  chunks=[c for c in rc.walk(rc.load(file).roots) if c.tag==b'GEOB'];assert len(chunks)%2==0
  for gi in range(len(chunks)//2):
   v,i=chunks[gi*2:gi*2+2];n,_,stride,_=struct.unpack_from('<4I',v.payload);count,_,width,_=struct.unpack_from('<4I',i.payload)
   assert stride in (20,24) and width==2
   raw=np.ndarray((n,4),dtype='<f2',buffer=v.payload,offset=16,strides=(stride,2))
   points=np.stack((-raw[:,0],-raw[:,2],raw[:,1]),axis=1).astype(float)
   faces=np.frombuffer(i.payload,dtype='<u2',offset=16,count=count).astype(int).reshape((-1,3))
   faces=faces[np.array([len(set(t))==3 for t in faces])]
   mesh=bpy.data.meshes.new('Final native envelope');mesh.from_pydata(points.tolist(),[],faces.tolist());mesh.update()
   ob=bpy.data.objects.new('Native body '+str(gi) if file==base else 'Native details',mesh);s.collection.objects.link(ob);mesh.materials.append(materials[(gi%2) if file==base else 2]);objects.append(ob);tris+=len(faces)
 pts=[o.matrix_world@v.co for o in objects for v in o.data.vertices];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);c=(lo+hi)/2;size=max(hi-lo)
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.render.resolution_x=800;s.render.resolution_y=640;s.render.resolution_percentage=100
 cam=bpy.data.objects.new('Audit camera',bpy.data.cameras.new('Audit camera'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.ortho_scale=size*1.5;s.camera=cam
 folder=OUT/'native-monastery'/str(age);folder.mkdir(parents=True,exist_ok=True)
 for name,vec in [('iso',(1,-1,.9)),('back',(-1,1,.9))]:
  cam.location=c+Vector(vec).normalized()*size*2;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 records.append(dict(age=age,body_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),detail_sha256=hashlib.sha256(detail.read_bytes()).hexdigest(),all_state_triangles=tris,scope='Exact final 077 geometry envelope; unfiltered lifecycle states; local body/detail coordinates only; native stamp transforms, stock props and native materials not simulated. Artificial diagnostic colours.'))
(OUT/'native-monastery/receipt.json').write_text(json.dumps(records,indent=2))
print('FINAL_MONASTERY_ENVELOPE_DONE',len(records))
