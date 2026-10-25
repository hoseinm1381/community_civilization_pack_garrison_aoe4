"""BACKGROUND Blender only; render explicit recipe and optional custom source.

Run after shared Blender slot is granted. Never saves a .blend or source changes.
Uses installed Garrison's existing decoded material projection, then reconstructs
only audited healthy faces from native manifest geometry. Material ambiguities
fail explicitly instead of silently using flat colours or an arbitrary texture.
"""
import argparse,hashlib,importlib.util,json,struct,sys
from pathlib import Path
import bpy
from mathutils import Vector,Quaternion

ROOT=Path(__file__).resolve().parents[3]
CFG=json.loads((ROOT/'workspace.json').read_text())
OUT=ROOT/'output/release_075/comparators'


def material_for(group,created):
 expected=group.get('preview_material') or group['material']
 # Garrison native projection retains the named material with Blender's normal
 # optional numeric suffix. Resolve only unique exact native names.
 def base(name):
  return name.rsplit('.',1)[0] if name.rsplit('.',1)[-1].isdigit() else name
 matches={m for o in created if o.type=='MESH' for m in o.data.materials if m and (base(m.name)==expected or (m.name.startswith('AoE IV · ') and m.name.split(' · ')[1]==expected))}
 if len(matches)!=1:
  raise RuntimeError(f'Native preview material mapping ambiguous: {expected}; candidates='+str(sorted({m.name for o in created if o.type=='MESH' for m in o.data.materials if m})))
 return next(iter(matches))


def face_selection(item,data,rc):
 metric=item['selector_metric'];groups=data['geometry']['groups']
 sets=metric.get('selector_sets',[])
 lower=set().union(*(set(s['members']) for s in sets if s['classification'] in ('unconditional','proven_healthy')))
 contract=data.get('structure_collection_contract')
 if not sets:
  return [list(g['triangles']) for g in groups]
 if contract is None:
  names={g['name'] for g in groups};allnames=set().union(*(set(s['members']) for s in sets))
  if names==allnames:return [list(g['triangles']) if g['name'] in lower else [] for g in groups]
  if metric['lower']==metric['raw']:return [list(g['triangles']) for g in groups]
  if metric['lower']==0:return [[] for _ in groups]
  raise RuntimeError('Cannot map proven face subset without guessing')
 model=rc.load(item['native_rgm']).roots[0];mscl=next(c for c in model.children if c.tag==b'MSCL')
 payload=mscl.children[0].payload;allnames=set().union(*(set(s['members']) for s in sets))
 offsets={n:payload.find(rc.lp_string(n)) for n in allnames}
 if any(x<2 for x in offsets.values()) or len(set(offsets.values()))!=len(allnames):raise RuntimeError('MSCL source ordering unresolved')
 ordered=sorted(allnames,key=offsets.get);result=[];gi=0
 for mapping,span in zip(contract['maps'],contract['geometry_group_spans']):
  inverse={bone:ordered[i] for i,bone in enumerate(mapping['source_to_local_bone']) if bone>=0}
  for group in groups[gi:gi+span]:
   faces=[];bones=group['collection_bone_indices']
   for tri in group['triangles']:
    b=[bones[i] for i in tri]
    if len(set(b))!=1 or b[0] not in inverse:raise RuntimeError('Mixed/unmapped collection triangle')
    if inverse[b[0]] in lower:faces.append(tri)
   result.append(faces)
  gi+=span
 if gi!=len(groups):raise RuntimeError('Unmapped group span')
 return result


def stamp_point(point,t):
 # Manifest B=(-native.x,-native.z,native.y). Apply native transform in its
 # native axes, then return to Blender. Quaternion serialization is x,y,z,w.
 native=Vector((-point[0],point[2],-point[1]))
 native=Vector([native[i]*t[7+i] for i in range(3)])
 native=Quaternion((t[3],t[0],t[1],t[2])).normalized()@native+Vector(t[4:7])
 return (-native.x,-native.z,native.y)


def configure_render(objects,folder,settings):
 s=bpy.context.scene
 for o in list(s.objects):
  if o.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
 pts=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
 if not pts:raise RuntimeError('No rendered vertices')
 lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
 center=(lo+hi)/2;size=max(hi-lo)
 s.render.engine='CYCLES';s.cycles.samples=settings['samples'];s.render.resolution_x,s.render.resolution_y=settings['resolution'];s.render.resolution_percentage=100
 if s.world is None:s.world=bpy.data.worlds.new('ReviewWorld')
 s.world.use_nodes=False;s.world.color=tuple(settings['world']);s.view_settings.view_transform=settings['view_transform']
 for vec,power in [((.8,-.8,1.6),70),((-.6,-.8,.65),40)]:
  light=bpy.data.lights.new('Review','AREA');obj=bpy.data.objects.new('Review',light);s.collection.objects.link(obj)
  obj.location=center+Vector(vec)*size;light.energy=size*size*power;light.size=size*1.2
 cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));s.collection.objects.link(cam);cam.data.type='ORTHO';s.camera=cam
 folder.mkdir(parents=True,exist_ok=True)
 for name,vec in settings['views'].items():
  cam.location=center+Vector(vec).normalized()*size*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  cam.data.ortho_scale=size*(2.1 if name=='gameplay' else 1.4);s.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
 return {'bounds_min':list(lo),'bounds_max':list(hi),'bounding_span':size,'apparent_scale_normalized':True}


def main():
 if not bpy.app.background:raise RuntimeError('Use a task-owned background Blender process only')
 ap=argparse.ArgumentParser();ap.add_argument('--recipe',required=True);ap.add_argument('--custom');ap.add_argument('--label',default='reference-pilot');ap.add_argument('--clay',action='store_true')
 args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);recipe=json.loads(Path(args.recipe).read_text())
 folder=OUT/'renders'/args.label
 if folder.exists():raise FileExistsError('Preserve prior render attempt; choose new --label')
 bpy.ops.wm.read_factory_settings(use_empty=True)
 ext=Path(CFG['garrison_extension']);sys.path.insert(0,str(ext))
 from garrison_shared import relic_chunky as rc
 shared=sys.modules['garrison_shared'];sys.path.insert(0,str(ext.parent));import garrison
 sys.modules['garrison.garrison_shared']=shared;garrison.register()
 from garrison.decode_projection import _apply_decoded_static
 rendered=[];proof=[]
 for index,item in enumerate(recipe['included']):
  # Blender's bundled Python may not open a >260-character logical extraction
  # path. The existing short-key native extraction is identical by SHA-256.
  short=(OUT/'official/decoded-rgm'/(hashlib.sha256(item['model'].encode()).hexdigest()[:16]+'.rgm')).resolve()
  if short.exists() and hashlib.sha256(short.read_bytes()).hexdigest()==item['native_rgm_sha256']:
   item['native_rgm']=str(short)
  manifest=Path(item['manifest']);raw=manifest.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=item['manifest_sha256']:raise RuntimeError('Manifest drift')
  if hashlib.sha256(Path(item['native_rgm']).read_bytes()).hexdigest()!=item['native_rgm_sha256']:raise RuntimeError('RGM drift')
  data=json.loads(raw);data['manifest_path']=str(manifest)
  before=set(bpy.data.objects);root=bpy.data.objects.new('StockMaterialProjection',None);bpy.context.scene.collection.objects.link(root)
  _apply_decoded_static(root,data,create_controls=False)
  created=list(set(bpy.data.objects)-before)
  for obj in created:obj.hide_render=True
  selected=face_selection(item,data,rc);count=0
  for gi,(group,faces) in enumerate(zip(data['geometry']['groups'],selected)):
   if not faces:continue
   material=material_for(group,created)
   # Compact unused vertices so cameras fit only the actually rendered subset.
   ids=sorted({i for tri in faces for i in tri});remap={old:new for new,old in enumerate(ids)}
   verts=[stamp_point(group['positions'][i],item['transform']) for i in ids]
   mesh=bpy.data.meshes.new(f'StaticReference_{index}_{gi}');mesh.from_pydata(verts,[],[[remap[i] for i in tri] for tri in faces]);mesh.update()
   for name,uvs in group['uv_layers'].items():
    layer=mesh.uv_layers.new(name=name)
    for loop in mesh.loops:layer.data[loop.index].uv=uvs[ids[loop.vertex_index]]
   mesh.materials.append(material);obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(obj);rendered.append(obj);count+=len(faces)
  if count!=item['render_triangle_target']:raise RuntimeError(f'Face-count preservation failed: {count} != {item["render_triangle_target"]}')
  proof.append({'stamp':item['stamp'],'object_id':item['object_id'],'model':item['model'],'triangles':count,'transform':item['transform']})
 if args.clay:
  clay=bpy.data.materials.new('Presentation-only neutral geometry');clay.use_nodes=True
  bsdf=clay.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.38,.34,.29,1);bsdf.inputs['Metallic'].default_value=0;bsdf.inputs['Roughness'].default_value=.8
  for obj in rendered:obj.data.materials.clear();obj.data.materials.append(clay)
 reference_capture=configure_render(rendered,folder/'reference',recipe['render_settings'])
 capture={'reference':recipe['reference'],'scope':recipe['scope'],'material_scope':recipe['material_scope'],
          'native':False,'rendered_instances':proof,'excluded_instances':recipe['excluded'],'reference_capture':reference_capture}
 if args.clay:capture['material_scope']='Presentation-only neutral clay. Native materials deliberately not represented; shape and structure comparison only.'
 if args.custom:
  custom=Path(args.custom).resolve();capture['custom_source']=str(custom);capture['custom_source_sha256']=hashlib.sha256(custom.read_bytes()).hexdigest()
  bpy.ops.wm.open_mainfile(filepath=str(custom))
  objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
  capture['custom_capture']=configure_render(objects,folder/'custom',recipe['render_settings'])
  if hashlib.sha256(custom.read_bytes()).hexdigest()!=capture['custom_source_sha256']:raise RuntimeError('Custom source changed')
 (folder/'capture.json').write_text(json.dumps(capture,indent=2)+'\n')
 print(json.dumps({'status':'offline_partial_reference_rendered','folder':str(folder),'native':False}))


if __name__=='__main__':main()
