"""Re-import actual native readback, compare deformation, and render previews."""
import bpy,json,sys,math,subprocess
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text());sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
check_storage(ROOT,CFG)
OUT=ROOT/'output/release_082_animation/preview-v1';OUT.mkdir(parents=True,exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/release_082_animation/v2/buffalo-idle-walk.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['body_lod1'];scene=bpy.context.scene
sys.path.insert(0,str(Path(CFG['garrison_extension']).parent))
from garrison.unit_animation import import_clip_action
rig.animation_data.action=None
actions={}
for label,index in [('idle',10),('walk',3)]:
    payload=json.loads((ROOT/f'output/release_082_animation/encoded-v3/idle-walk-{index}-sampled.json').read_text())
    target,action=import_clip_action(rig,payload,fps=30,root_motion=False)
    action.name='082_Native_readback_'+label;actions[label]=action
errors={}
for label,native in actions.items():
    authored=bpy.data.actions['buffalo_082_'+label];points=[]
    for frame in [1,5,9,13,17,21,25,29,33] if label=='walk' else [1,38,75,112,149,186,223,260,297]:
        phase=(frame-1)/(128 if label=='walk' else 296)*(4 if label=='walk' else 2)
        source_frame=1+(phase%1)*(32 if label=='walk' else 120)
        rig.animation_data.action=authored;rig.animation_data.action_slot=authored.slots[0];scene.frame_set(int(source_frame),subframe=source_frame%1);bpy.context.view_layer.update()
        before={b.name:b.matrix.copy() for b in rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones}
        rig.animation_data.action=native;rig.animation_data.action_slot=native.slots[0];scene.frame_set(frame);bpy.context.view_layer.update()
        after=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        points.append(max((b.matrix.translation-before[b.name].translation).length for b in after.pose.bones))
    errors[label]=max(points)
    assert errors[label]<.003,(label,errors[label])
for o in scene.objects:
    if o.type=='MESH':o.hide_render=o!=body
body.hide_render=False;body.hide_set(False)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(.48,.40,.30);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.render.resolution_x=800;scene.render.resolution_y=600;scene.render.resolution_percentage=100
camera=bpy.data.cameras.new('082 Motion preview');obj=bpy.data.objects.new('082 Motion preview',camera);scene.collection.objects.link(obj);scene.camera=obj
center=Vector((0,0,.9));obj.location=center+Vector((4,-6,2.7));obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler();camera.type='ORTHO';camera.ortho_scale=4.8
scene.render.image_settings.file_format='PNG';scene.render.fps=30
encoder=Path(r'C:\Users\RS\AppData\Local\Programs\Python\Python313\Scripts\ffmpeg.exe');assert encoder.is_file()
for label,last,step in [('idle',297,4),('walk',129,2)]:
    frames=OUT/label;frames.mkdir()
    action=actions[label];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    for index,frame in enumerate(range(1,last+1,step)):
        scene.frame_set(frame);scene.render.filepath=str(frames/f'{index:04}.png');bpy.ops.render.render(write_still=True)
    proc=subprocess.run([str(encoder),'-hide_banner','-loglevel','error','-framerate',str(30/step),'-i',str(frames/'%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','22',str(OUT/(label+'.mp4'))],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    if label=='walk':
        obj.location=center+Vector((5.5,0,1.1));obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
        scene.frame_set(9);scene.render.filepath=str(OUT/'walk-side.png');bpy.ops.render.render(write_still=True)
(OUT/'proof.json').write_text(json.dumps({'source_to_native_maximum_bone_head_error':errors,'native_motion_reimported':True,'game_runtime':False},indent=2))
print('NATIVE_PREVIEWS_COMPLETE',errors)
