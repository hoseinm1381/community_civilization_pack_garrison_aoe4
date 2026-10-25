"""Author and bake a planted four-beat cattle gait on the unchanged 45 bones."""
import bpy,math,json,sys,importlib.util
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
check_storage(ROOT,CFG)
OUT=ROOT/'output/release_082_animation/source-v2';ART=ROOT/'art/authoring/release_082_animation/v2'
OUT.mkdir(parents=True,exist_ok=False);ART.mkdir(parents=True,exist_ok=False)
source=ROOT/'art/authoring/release_081/buffalo/r6/model.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
rig.data.pose_position='POSE';scene.render.fps=30
original_bind={b.name:[list(r) for r in b.matrix_local] for b in rig.data.bones}
assert len(original_bind)==45
sys.path.insert(0,str(ROOT/'tools/release_081'))
spec=importlib.util.spec_from_file_location('source081',ROOT/'tools/release_081/animation_source.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
idle=old.set_cycle('buffalo_082_idle',rig,old.IDLE_FRAMES,old.idle_angles)['action']
idle.use_fake_user=True
# Native walk is four 32-frame cycles with 7.42006588 units reference travel.
period=32;stride=7.420065879821777/4;duty=.55
rig.animation_data_clear();rig.animation_data_create()
walk_setup=bpy.data.actions.new('buffalo_082_walk_IK');rig.animation_data.action=walk_setup
targets=[];leg_records=[]
for front,side,offset in [(False,'l',0.),(True,'l',.25),(False,'r',.5),(True,'r',.75)]:
    ankle=('frontankle_' if front else 'backankle_')+side
    foot=('fronttoes_' if front else 'backtoes3_')+side
    pb=rig.pose.bones[ankle]
    obj=bpy.data.objects.new('082_IK_'+ankle,None);scene.collection.objects.link(obj)
    obj.rotation_mode='QUATERNION';obj.rotation_quaternion=pb.bone.matrix_local.to_quaternion()
    origin=pb.bone.tail_local.copy()
    obj.location=origin
    constraint=pb.constraints.new('IK');constraint.name='082_Planted_hoof';constraint.target=obj
    constraint.chain_count=4 if front else 3;constraint.use_stretch=False;constraint.iterations=200
    constraint.use_rotation=True;constraint.weight=1.;constraint.orient_weight=1.
    targets.append(obj)
    leg_records.append({'ankle':ankle,'foot':foot,'offset':offset,'origin':list(origin),'target':obj})
for frame in range(1,period+2):
    scene.frame_set(frame)
    for bone in rig.pose.bones:
        bone.rotation_mode='QUATERNION';bone.matrix_basis=Matrix.Identity(4)
    phase=(frame-1)/period
    root=rig.pose.bones['root_m']
    # Cosmetic body settling. No horizontal root-bone travel or object travel.
    root.location=root.bone.matrix_local.to_3x3().inverted()@Vector((0,0,-.18+.010*math.sin(phase*4*math.pi)))
    root.keyframe_insert('location',frame=frame)
    for name,angle in [('neck_m',.018*math.sin(phase*4*math.pi)),('neck1_m',-.028*math.sin(phase*4*math.pi)),('head_m',-.035*math.sin(phase*4*math.pi))]:
        old.set_world_axis_angle(rig.pose.bones[name],Vector((1,0,0)),angle)
        rig.pose.bones[name].keyframe_insert('rotation_quaternion',frame=frame)
    for i in range(1,5):
        bone=rig.pose.bones[f'tail{i}_m'];old.set_world_axis_angle(bone,Vector((0,0,1)),.045*math.sin(phase*2*math.pi-i*.2));bone.keyframe_insert('rotation_quaternion',frame=frame)
    for leg in leg_records:
        p=(phase+leg['offset'])%1.;origin=Vector(leg['origin']);target=leg['target']
        reach=stride*duty
        if p<duty:
            y=(p/duty-.5)*reach;lift=0.
        else:
            t=(p-duty)/(1-duty);smooth=t*t*(3-2*t)
            y=(.5-smooth)*reach;lift=.16*math.sin(math.pi*t)**1.3
        target.location=origin+Vector((0,y,lift))
        target.keyframe_insert('location',frame=frame)
    bpy.context.view_layer.update()
# Bake the evaluated IK into ordinary native-bone keyframes.
poses=[];contacts=[]
for frame in range(1,period+2):
    scene.frame_set(frame);bpy.context.view_layer.update()
    evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    poses.append({b.name:b.matrix.copy() for b in evaluated.pose.bones})
    row={'frame':frame,'legs':{}}
    for leg in leg_records:
        pb=evaluated.pose.bones[leg['ankle']]
        actual=pb.matrix@Vector((0,pb.length,0));target=leg['target'].location.copy()
        row['legs'][leg['ankle']]={'target':list(target),'actual':list(actual),'error':(actual-target).length,'stance':((frame-1)/period+leg['offset'])%1.<duty}
    contacts.append(row)
for bone in rig.pose.bones:
    for c in list(bone.constraints):bone.constraints.remove(c)
for target in targets:bpy.data.objects.remove(target,do_unlink=True)
rig.animation_data_clear();rig.animation_data_create()
walk=bpy.data.actions.new('buffalo_082_walk');rig.animation_data.action=walk;walk.use_fake_user=True
for frame,matrices in enumerate(poses,1):
    scene.frame_set(frame)
    for bone in rig.pose.bones:
        parent=bone.parent
        bone.matrix_basis=bone.bone.convert_local_to_pose(matrices[bone.name],bone.bone.matrix_local,
            parent_matrix=matrices[parent.name] if parent else Matrix.Identity(4),
            parent_matrix_local=parent.bone.matrix_local if parent else Matrix.Identity(4),invert=True)
        for key in ('location','rotation_quaternion','scale'):bone.keyframe_insert(key,frame=frame,group=bone.name)
for action in (idle,walk):
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(action.slots[0])
            if bag:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
assert original_bind=={b.name:[list(r) for r in b.matrix_local] for b in rig.data.bones}
# Export evaluated parent-local game-space samples, in the native RHKA order.
projection=Matrix(((-1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
axes=Matrix(((0,1,0,0),(1,0,0,0),(0,0,1,0),(0,0,0,1)))
records=json.loads(rig['garrison_skeleton_records']);names=[r['name'] for r in records]
samples={}
for action,last in [(idle,121),(walk,33)]:
    rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];rows=[]
    for frame in range(1,last+1):
        scene.frame_set(frame);bpy.context.view_layer.update()
        evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        glob={name:projection.inverted()@evaluated.pose.bones[name].matrix@axes.inverted() for name in names}
        row=[]
        for r in records:
            local=glob[r['parent_name']].inverted()@glob[r['name']] if r['parent_name'] else glob[r['name']]
            t,q,s=local.decompose();q.normalize()
            if q.w<0:q.negate()
            assert max(abs(x-1) for x in s)<1e-4,(r['name'],list(s))
            row += [*t,0,q.x,q.y,q.z,q.w,1,1,1,0]
        rows.append(row)
    samples[action.name]={'fps':30,'names':names,'parents':[r['parent_name'] for r in records],'rows':rows,'duration':(last-1)/30}
rig.animation_data.action=idle;rig.animation_data.action_slot=idle.slots[0];scene.frame_set(1);scene.frame_start=1;scene.frame_end=121
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'buffalo-idle-walk.blend'))
(OUT/'samples.json').write_text(json.dumps(samples))
proof={'source':str(source),'blend':str(ART/'buffalo-idle-walk.blend'),'bones':45,'rest_binds_exact':True,'stride':stride,'cycle_frames':period,'stance_fraction':duty,'contacts':contacts,'maximum_ik_target_error':max(v['error'] for r in contacts for v in r['legs'].values())}
(OUT/'proof.json').write_text(json.dumps(proof,indent=2))
print('BUFFALO_082_AUTHORED',proof['maximum_ik_target_error'])
