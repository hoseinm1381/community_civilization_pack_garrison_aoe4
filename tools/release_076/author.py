"""Deterministic new meshes on untouched official skeletons. Isolated Blender only."""
import sys,math,json,importlib
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from inspect_rigs import load,addon
TAU=math.tau
PARTS=[];RIG=None;MAT=None
def mesh(name,verts,faces,uvs,weights):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
 obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj)
 obj.data.materials.append(MAT);uv=data.uv_layers.new(name='UVMap')
 for p in data.polygons:
  p.use_smooth=True
  for li in p.loop_indices:uv.data[li].uv=uvs[data.loops[li].vertex_index]
 if RIG:
  for i,ws in enumerate(weights):
   for bone,w in ws.items():
    g=obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone);g.add([i],w,'REPLACE')
  mod=obj.modifiers.new('Native skin','ARMATURE');mod.object=RIG;obj.parent=RIG
 bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(data);bm.free()
 PARTS.append(obj);return obj
def tileuv(tile,u,v):return ((tile%4+.06+.88*u)/4,(tile//4+.06+.88*v)/4)
def tube(name,rings,tile,bones,sides=12,axis='z'):
 # Ring is (center_xyz,radius_a,radius_b). Every bend uses connected edge loops.
 verts=[];faces=[];uvs=[];weights=[]
 for k,(c,ra,rb) in enumerate(rings):
  c=Vector(c)
  if axis=='z':a,b=Vector((1,0,0)),Vector((0,1,0))
  elif axis=='y':a,b=Vector((1,0,0)),Vector((0,0,1))
  else:
   lo=Vector(rings[max(0,k-1)][0]);hi=Vector(rings[min(len(rings)-1,k+1)][0]);t=(hi-lo).normalized()
   a=t.cross(Vector((0,1,0)))
   if a.length<.01:a=t.cross(Vector((1,0,0)))
   a.normalize();b=t.cross(a).normalized()
  ws=bones[k] if isinstance(bones,list) else {bones:1} if bones else {}
  for i in range(sides):
   angle=TAU*i/sides;verts.append(c+a*math.cos(angle)*ra+b*math.sin(angle)*rb);uvs.append(tileuv(tile,i/sides,k/(len(rings)-1)));weights.append(ws)
  if k:
   for i in range(sides):j=(i+1)%sides;faces.append(((k-1)*sides+i,(k-1)*sides+j,k*sides+j,k*sides+i))
 faces.extend([tuple(reversed(range(sides))),tuple((len(rings)-1)*sides+i for i in range(sides))])
 return mesh(name,verts,faces,uvs,weights)
def ellipsoid(name,c,scale,tile,bone,sides=12,steps=6):
 rings=[]
 for i in range(steps+1):
  t=math.pi*(.015+.97*i/steps);rings.append(((c[0],c[1],c[2]-scale[2]*math.cos(t)),max(.001,scale[0]*math.sin(t)),max(.001,scale[1]*math.sin(t))))
 return tube(name,rings,tile,bone,sides)
def bonepos(name):return RIG.data.bones[name].head_local.copy()
def link(name,points,radii,tile,bones,sides=10):return tube(name,[(p,r,r*.85) for p,r in zip(points,radii)],tile,bones,sides,'path')
def buffalo(detail=True):
 # Stock-compatible 1.65m shoulder height; 2.7m trunk/head length. Barrel, low neck, broad forehead.
 tube('Barrel',[( (0,y,z),rx,rz) for y,z,rx,rz in [(1.12,1.27,.24,.29),(.92,1.29,.46,.46),(.5,1.27,.56,.51),(.05,1.26,.59,.49),(-.42,1.25,.51,.47),(-.72,1.19,.33,.38)]],0,[{'root_m':1},{'root_m':1},{'spine1_m':.65,'root_m':.35},{'chest_m':.65,'spine1_m':.35},{'chest_m':1},{'neck_m':.5,'chest_m':.5}],16,'y')
 tube('Neck',[( (0,y,z),rx,rz) for y,z,rx,rz in [(-.52,1.18,.36,.37),(-.85,1.17,.33,.34),(-1.1,1.2,.27,.29),(-1.3,1.15,.26,.27),(-1.59,.94,.21,.18),(-1.76,.86,.20,.13)]],0,[{'chest_m':1},{'neck_m':1},{'neck1_m':1},{'head_m':1},{'head_m':1},{'head_m':1}],12,'y')
 if detail:
  ellipsoid('Rounded haunch',(0,.91,1.25),(.43,.38,.43),0,'root_m',12,7)
  ellipsoid('Shoulder muscle',(0,-.48,1.22),(.46,.43,.43),0,'chest_m',12,7)
 for side,sgn in [('l',1),('r',-1)]:
  for prefix,start in [('front','frontrump_'),('back','backhip_')]:
   names=([start+side,'fronthip_'+side,'frontknee_'+side,'frontankle_'+side,'fronttoes_'+side] if prefix=='front' else [start+side,'backknee_'+side,'backankle_'+side,'backtoes3_'+side])
   pts=[bonepos(n) for n in names];rs=[.19,.13,.09,.07,.08] if prefix=='front' else [.23,.14,.08,.085]
   link(prefix+side,pts,rs,0,[{n:1} for n in names])
   foot=pts[-1]
   for split in [-1,1]:ellipsoid(prefix+side+' hoof '+str(split),(foot.x+split*.045,foot.y-.025,.075),(.043,.115,.07),2,names[-1],8,3)
  head=bonepos('head_m')
  link('Horn '+side,[(sgn*.20,-1.24,1.48),(sgn*.39,-1.19,1.49),(sgn*.62,-1.03,1.52),(sgn*.80,-.84,1.61),(sgn*.86,-.65,1.77),(sgn*.81,-.52,1.88)],[.09,.08,.065,.048,.026,.002],1,'head_m',8)
  ellipsoid('Ear '+side,(sgn*.32,-1.19,1.39),(.23,.10,.05),0,'ear_'+side,10,3)
  if detail:
   ellipsoid('Eye '+side,(sgn*.238,-1.38,1.19),(.023,.026,.022),3,'head_m',8,4)
   ellipsoid('Nostril '+side,(sgn*.12,-1.755,.91),(.04,.018,.022),3,'head_m',8,3)
 names=['tail'+str(i)+'_m' for i in range(5)]
 link('Tail',[bonepos(n) for n in names],[.035,.028,.024,.02,.013],0,[{n:1} for n in names],7)
 ellipsoid('Tail tuft',bonepos(names[-1]),(.035,.065,.08),3,names[-1],8,4)
def human(age,detail=True):
 # New body surfaces. The native A-pose and bone positions are compatibility anchors.
 torso=[((0,0,z),x,y) for z,x,y in [(.86,.20,.13),(.98,.17,.12),(1.12,.17,.12),(1.30,.225,.135),(1.46,.245,.13),(1.54,.215,.115)]]
 tube('Cross collar tunic',torso,4,[{'metarig_pelvis':1},{'metarig_pelvis':.7,'metarig_spine1':.3},{'metarig_spine1':.5,'metarig_spine2':.5},{'metarig_ribcage':1},{'metarig_ribcage':1},{'metarig_ribcage':1}],12)
 tube('Neck',[((0,0,1.48),.074,.075),((0,0,1.68),.073,.075)],6,'metarig_neck2',10)
 tube('Head',[((0,-.005,z),x,y) for z,x,y in [(1.65,.055,.06),(1.68,.078,.085),(1.73,.10,.097),(1.80,.108,.10),(1.88,.10,.09),(1.93,.065,.07)]],6,'metarig_head',12)
 ellipsoid('Nose',(0,-.103,1.77),(.026,.038,.045),6,'metarig_head',8,4)
 for side,sgn in [('l',1),('r',-1)]:
  hip=bonepos('metarig_'+side+'leg1');knee=bonepos('metarig_'+side+'leg2');ankle=bonepos('metarig_'+side+'legankle')
  link('Trousers '+side,[hip,hip.lerp(knee,.5),knee,knee.lerp(ankle,.65),ankle],[.115,.11,.09,.065,.055],5,[{'metarig_'+side+'leg1':1},{'metarig_'+side+'leg1':1},{'metarig_'+side+'leg1':.4,'metarig_'+side+'leg2':.6},{'metarig_'+side+'leg2':1},{'metarig_'+side+'legankle':1}],10)
  ellipsoid('Sandal '+side,(ankle.x,-.065,.055),(.07,.15,.045),7,'metarig_'+side+'legankle',10,3)
  names=['metarig_'+side+n for n in ['armupper1','armupper2','armlower1','armlower2','armpalm']];pts=[bonepos(n) for n in names]
  link('Sleeve '+side,pts[:3],[.105,.10,.077],4,[{n:1} for n in names[:3]],10)
  link('Forearm '+side,pts[2:],[.076,.06,.044],6,[{n:1} for n in names[2:]],10)
  palm=pts[-1];direction=(palm-pts[-2]).normalized()
  link('Hand '+side,[palm,palm+direction*.07,palm+direction*.12],[.055,.052,.036],6,names[-1],8)
  if detail:
   for finger in ['thumb','index','middle']:
    ns=['metarig_'+side+'arm'+finger+str(i) for i in (1,2,3)]
    link('Finger '+side+finger,[bonepos(n) for n in ns],[.018,.015,.011],6,[{n:1} for n in ns],6)
   ellipsoid('Eye '+side,(sgn*.044,-.096,1.807),(.016,.009,.009),3,'metarig_head',8,3)
   ellipsoid('Ear '+side,(sgn*.105,-.005,1.786),(.024,.035,.05),6,'metarig_head',8,4)
   link('Eyebrow '+side,[(sgn*.025,-.105,1.826),(sgn*.066,-.092,1.825)],[.007,.006],3,'metarig_head',5)
 # Fitted rattan chest, sleeve clearance and belt are surface-derived from the torso dimensions.
 tube('Rattan vest',[((0,0,z),x,y) for z,x,y in [(1.13,.185,.133),(1.28,.24,.151),(1.44,.258,.148)]],8,'metarig_ribcage',12)
 tube('Waist sash',[((0,0,.98),.185,.135),((0,0,1.055),.185,.135)],9,'metarig_pelvis',12)
 if age==2:
  tube('Head wrap',[((0,0,1.85),.115,.105),((0,0,1.89),.118,.107),((0,0,1.94),.105,.095),((0,0,1.98),.01,.01)],5,'metarig_head',12)
 else:
  tube('Conical helmet',[((0,0,1.88),.22,.19),((0,0,1.93),.24,.20),((0,0,2.015),.15,.13),((0,0,2.13),.012,.012)],8 if age==3 else 10,'metarig_head',16)
 if age>=3 and detail:
  for side,sgn in [('l',1),('r',-1)]:
   ellipsoid('Shoulder '+side,(sgn*.255,.005,1.475),(.12,.14,.065),8 if age==3 else 10,'metarig_'+side+'armupper1',10,4)
 if age==4:
  tube('Elite skirt plates',[((0,0,.80),.24,.155),((0,0,.97),.205,.14)],10,'metarig_pelvis',12)
  tube('Helmet rim',[((0,0,1.90),.242,.203),((0,0,1.93),.242,.203)],11,'metarig_head',16)
 if detail:
  # Diagonal front collar follows fitted chest, no floating straps.
  link('Collar binding',[(.10,-.12,1.51),(.035,-.155,1.40),(-.08,-.16,1.28)],[.014,.014,.014],9,'metarig_ribcage',6)
  link('Mouth',[(-.034,-.091,1.707),(0,-.103,1.703),(.034,-.091,1.707)],[.004,.004,.004],9,'metarig_head',5)
  for obj in PARTS:
   if obj.name.startswith(('Head','Nose','Eye','Ear','Mouth','Conical','Helmet')):
    for vertex in obj.data.vertices:vertex.co.z-=.055
def unify_buffalo():
 from mathutils.kdtree import KDTree
 names=('Barrel','Neck','Rounded haunch','Shoulder muscle','frontl','frontr','backl','backr')
 sources=[o for o in PARTS if o.name in names];samples=[]
 for o in sources:
  for v in o.data.vertices:samples.append((v.co.copy(),{o.vertex_groups[g.group].name:g.weight for g in v.groups}))
 kd=KDTree(len(samples))
 for i,(p,w) in enumerate(samples):kd.insert(p,i)
 kd.balance();bpy.ops.object.select_all(action='DESELECT')
 for o in sources:o.select_set(True);PARTS.remove(o)
 bpy.context.view_layer.objects.active=sources[0];bpy.ops.object.join();o=bpy.context.object;o.name='Continuous buffalo hide'
 o.modifiers.clear();o.data.remesh_voxel_size=.043;bpy.ops.object.voxel_remesh()
 smooth=o.modifiers.new('Anatomical junctions','SMOOTH');smooth.factor=1.25;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
 count=sum(len(p.vertices)-2 for p in o.data.polygons);dec=o.modifiers.new('Game topology','DECIMATE');dec.ratio=min(1,1850/count);bpy.ops.object.modifier_apply(modifier=dec.name)
 o.vertex_groups.clear()
 for v in o.data.vertices:
  ws={}
  for co,i,d in kd.find_n(v.co,4):
   for n,w in samples[i][1].items():ws[n]=ws.get(n,0)+w/(d+.01)**2
  ws=dict(sorted(ws.items(),key=lambda it:it[1],reverse=True)[:4]);total=sum(ws.values())
  for n,w in ws.items():(o.vertex_groups.get(n) or o.vertex_groups.new(name=n)).add([v.index],w/total,'REPLACE')
 uv=o.data.uv_layers.new(name='UVMap') if not o.data.uv_layers else o.data.uv_layers.active
 for p in o.data.polygons:
  p.use_smooth=True
  for li in p.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=tileuv(0,(v.y+1.8)/3.2,v.z/1.8)
 mod=o.modifiers.new('Native skin','ARMATURE');mod.object=RIG;o.parent=RIG;PARTS.append(o)
def weapon(age,projectile=False):
 tube('Shaft',[((0,0,z),r,r) for z,r in [(-.80,.014),(-.70,.021),(1.81,.021),(1.91,.016)]],12,None,8)
 tube('Grip',[((0,0,-.12),.025,.025),((0,0,.16),.025,.025)],9,None,8)
 tube('Socket',[((0,0,1.74),.029,.029),((0,0,1.94),.029,.029)],10,None,8)
 width={2:.055,3:.065,4:.075}[age]
 tube('Forged leaf blade',[((0,0,z),x,y) for z,x,y in [(1.88,.024,.012),(2.00,width,.012),(2.17,width*.65,.009),(2.33,.001,.001)]],10 if age<4 else 11,None,4)
 if age>=3:tube('Collar',[((0,0,1.78),.038,.038),((0,0,1.84),.038,.038)],11,None,8)
 if projectile:
  # Native projectile is forward +Y, distinct from held +Z. Preserve its measured length/origin.
  for o in PARTS:
   for v in o.data.vertices:v.co=Vector((v.co.x,v.co.z*.545+.085,-v.co.y))
def atlas(folder):
 # Authored deterministic textile/rattan/hide atlas. No stock pixels copied.
 import numpy as np
 colors=[(68,73,75),(106,103,91),(38,35,31),(15,14,12),(184,181,155),(45,61,64),(159,111,76),(56,39,27),(136,100,47),(112,45,29),(95,108,111),(164,133,58),(107,77,40),(80,80,80),(80,80,80),(80,80,80)]
 size=512;a=np.zeros((size,size,4),dtype=np.float32);pattern=np.zeros_like(a);normal=np.zeros_like(a);rough=np.zeros_like(a);metal=np.zeros_like(a)
 yy,xx=np.mgrid[0:128,0:128];noise=np.random.default_rng(76).normal(0,.002,(128,128))
 for t,c in enumerate(colors):
  y=(t//4)*128;x=(t%4)*128;grain=noise.copy()
  if t in (4,5,9):grain+=.004*((xx%4==0)+(yy%4==0))
  if t==8:grain+=.022*np.sin(xx*.55)*np.sign(np.sin(yy*.4))
  if t in (1,12):grain+=.006*np.sin(yy*.32)
  a[y:y+128,x:x+128,:3]=np.clip((np.array(c)/255)**2.2+grain[:,:,None],0,1)
  pattern[y:y+128,x:x+128,0]=1 if t==4 else 0
  rough[y:y+128,x:x+128,:3]=.78 if t not in (10,11) else .38
  metal[y:y+128,x:x+128,:3]=.75 if t in (10,11) else 0
 normal[:,:,:3]=(.5,.5,1)
 for name,pixels in [('albedo',a),('pattern',pattern),('normal',normal),('roughness',rough),('metalness',metal)]:
  pixels[:,:,3]=1;im=bpy.data.images.new('076_'+name,width=size,height=size,alpha=True)
  if name!='albedo':im.colorspace_settings.name='Non-Color'
  im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(folder/(name+'.png'));im.file_format='PNG';im.save()
 mat=bpy.data.materials.new('lod1');mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.get('076_albedo');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.75
 return mat
def review(folder,objs):
 # Presentation cameras only after geometry assembly; solid-shaded source remains editable.
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
 scene.render.resolution_x=1000;scene.render.resolution_y=850;scene.render.resolution_percentage=100
 scene.world.color=(.25,.25,.25)
 bound=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];center=sum(bound,Vector())/len(bound);size=max((v-center).length for v in bound)
 for name,loc,power,scale in [('Key',(4,-5,7),1100,5),('Fill',(-4,-1,4),850,4),('Rim',(2,4,5),1200,3)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=scale;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Review');o=bpy.data.objects.new('Review',d);scene.collection.objects.link(o);scene.camera=o;d.type='ORTHO';d.ortho_scale=size*2.5
 for name,direction in [('threequarter',(4,-6,3)),('front',(0,-7,0)),('side',(7,0,0)),('back',(0,7,0)),('left',(-7,0,0)),('top',(0,0,7)),('bottom',(0,0,-7))]:
  o.location=center+Vector(direction).normalized()*size*5;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
def main():
 global RIG,MAT
 guard();family,revision=sys.argv[sys.argv.index('--')+1:][:2];detail=revision!='r1'
 art=ART/family/revision;exp=EXPORT/family/revision;out=OUT/'art'/family/revision
 if art.exists() or exp.exists():raise FileExistsError('Immutable revision already exists')
 for p in (art,exp,out):p.mkdir(parents=True,exist_ok=False)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 donor='buffalo' if family=='buffalo' else 'skirmisher2' if family.startswith('skirmisher') else None
 refs=[]
 if donor:
  RIG,refs=load(donor)
  for o in refs:
   if o.type=='MESH':o.hide_render=True;o.hide_set(True)
 MAT=atlas(exp)
 if family=='buffalo':
  buffalo(detail)
  if revision not in ('r1','r2'):unify_buffalo()
 elif family.startswith('skirmisher'):human(int(family[-1]),detail)
 else:weapon(int(family[-1]),family.startswith('projectile'))
 triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in PARTS)
 budget=3544 if family=='buffalo' else 4264 if family.startswith('skirmisher') else 416
 if triangles>budget:raise ValueError(('Budget exceeded',triangles,budget))
 write(out/'anatomy.json',{'family':family,'revision':revision,'parts':[o.name for o in PARTS],'triangles':triangles,'budget':budget,'donor':donor,'new_geometry':True,'source_only':True})
 review(out,PARTS)
 # Source preserves component-level editability; exports are joined private copies.
 for o in bpy.context.selected_objects:o.select_set(False)
 copies=[]
 for obj in PARTS:
  c=obj.copy();c.data=obj.data.copy();bpy.context.scene.collection.objects.link(c);c.select_set(True);copies.append(c)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();body=bpy.context.object;body.name='body_lod1'
 lods=[body]
 for level,ratio in [(2,.55),(3,.25)]:
  c=body.copy();c.data=body.data.copy();c.name='body_lod'+str(level);bpy.context.scene.collection.objects.link(c);bpy.context.view_layer.objects.active=c
  m=c.modifiers.new('Simplification','DECIMATE');m.ratio=ratio;bpy.ops.object.modifier_apply(modifier=m.name)
  c.data.materials.clear();material=MAT.copy();material.name='lod'+str(level);c.data.materials.append(material);lods.append(c)
 for obj in PARTS:obj.hide_render=True;obj.hide_set(True)
 if RIG:
  records=addon('unit_export').skeleton_records(RIG)
  addon('unit_export').export_unit_model(RIG,lods,exp/'model.fbx',records,three_lods=False)
  names=[r['name'] for r in records]
  (exp/'model.rig').write_text('[HAVOK SKELETON DEFINITION FILE]\n\n[BONES START]\n'+'\n'.join(names)+'\n[END]\n\n[PARTITION START]\nfullbody_lod3 '+names[0]+' '+names[-1]+'\n[END]\n')
 else:
  bpy.ops.object.select_all(action='DESELECT')
  for o in lods:o.select_set(True)
  for o in lods:
   for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
  bpy.ops.export_scene.fbx(filepath=str(exp/'model.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
  for o in lods:
   for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
 if family=='buffalo':
  RIG.animation_data_create();act=bpy.data.actions.new('076_Supervise_SOURCE_ONLY');RIG.animation_data.action=act
  for name,amplitude in [('head_m',.045),('neck1_m',.018),('ear_l',.10),('ear_r',-.08),('tail2_m',.13),('spine1_m',.009)]:
   b=RIG.pose.bones[name];b.rotation_mode='XYZ'
   for frame in (1,31,61,91,121):b.rotation_euler[1]=amplitude*math.sin((frame-1)/120*TAU);b.keyframe_insert('rotation_euler',frame=frame)
  bpy.context.scene.frame_end=121;bpy.context.scene.frame_set(1)
  write(out/'animation-status.json',{'action':act.name,'frames':[1,121],'fps':30,'root_motion':False,'status':'editable_source_only_native_bovine_clip_export_not_supported_by_installed_contract','integration_enabled':False})
 for o in lods[1:]:o.hide_render=True;o.hide_set(True)
 bpy.ops.wm.save_as_mainfile(filepath=str(art/'model.blend'))
 write(out/'export.json',{'family':family,'revision':revision,'source':str(art/'model.blend'),'source_sha256':sha(art/'model.blend'),'export':str(exp),'files':{p.name:sha(p) for p in exp.iterdir() if p.is_file()},'lod_triangles':[sum(len(p.vertices)-2 for p in o.data.polygons) for o in lods],'rig_bones':len(RIG.data.bones) if RIG else 0,'native_acceptance':False})
 print('076_EXPORT_COMPLETE',family,revision,triangles)
if __name__=='__main__':main()
