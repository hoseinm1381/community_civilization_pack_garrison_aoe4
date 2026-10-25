"""Supported human idle encoder control. Never used as buffalo or cooked."""
import bpy, json, math, sys, shutil
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
check_storage(ROOT,CFG)
BASE=ROOT/'output/release_081_animation'
manifest=json.loads(next((BASE/'human-encoder-control').rglob('prototype.json')).read_text())
DEST=BASE/'human-control-source'
DEST.mkdir(exist_ok=False)
records=manifest['skeleton']['bones']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
arm=bpy.data.armatures.new('HumanControl48');rig=bpy.data.objects.new('HumanControl48',arm)
bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
projection=Matrix(((-1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
axes=Matrix(((0,1,0,0),(1,0,0,0),(0,0,1,0),(0,0,0,1)))
for row in records:
    t=row['global_reference_transform'];q=t['quaternion_xyzw']
    bone=arm.edit_bones.new(row['name']);bone.matrix=projection@Matrix.LocRotScale(Vector(t['translation_xyz']),Quaternion((q[3],*q[:3])),Vector(t['scale_xyz']))@axes
    bone.length=.1
for row in records:
    if row['parent_name']:arm.edit_bones[row['name']].parent=arm.edit_bones[row['parent_name']]
bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('control')
meshes=[]
for lod in range(1,4):
    bpy.ops.mesh.primitive_cube_add(size=.1,location=(0,0,1))
    mesh=bpy.context.object;mesh.name='control_lod'+str(lod);mesh.data.materials.append(mat)
    group=mesh.vertex_groups.new(name='metarig_pelvis');group.add(range(len(mesh.data.vertices)),1,'REPLACE')
    modifier=mesh.modifiers.new('Rig','ARMATURE');modifier.object=rig;mesh.parent=rig;meshes.append(mesh)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for mesh in meshes:mesh.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(DEST/'model.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False)
rows=[]
neck=next((r['index'] for r in records if 'neck' in r['name'].lower()),2)
for frame in range(31):
    components=[]
    for row in records:
        t=row['local_reference_transform'];q=t['quaternion_xyzw'];q=Quaternion((q[3],*q[:3]))
        if row['index']==neck:q=q@Quaternion((0,0,1),.1*math.sin(2*math.pi*frame/30))
        q.normalize()
        components.extend([*t['translation_xyz'],0,q.x,q.y,q.z,q.w,1,1,1,0])
    rows.append({'time_seconds':frame/30,'components':components})
sample={'schema':'garrison.unit-action-samples/v1','profile':'prototype-clips-v1','bones':records,'samples':rows,'loop':True,'timing':'repeat_idle_cycle'}
document={'schema':'garrison.unit-prototype-build/v1','profile':'prototype-clips-v1','prototype':manifest['prototype']['key'],'fingerprint':manifest['fingerprint'],'bones':records,'attachments':[],
          'overrides':[{'clip':'navigation\\idle_calm_basic_01','samples':sample}],'textures':['albedo'],'material_name':'control'}
(DEST/'action.json').write_text(json.dumps(document))
shutil.copyfile(ROOT/'art/exports/release_081/buffalo/r6/albedo.png',DEST/'albedo.png')
bpy.ops.wm.save_as_mainfile(filepath=str(DEST/'human-control.blend'))
print('HUMAN_CONTROL_SOURCE_READY',str(DEST))
