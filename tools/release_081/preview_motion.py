"""Encode source-only Blender motion previews; no native animation export."""
import bpy,sys,subprocess,shutil
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from common import *
guard();bpy.ops.wm.open_mainfile(filepath=str(ART/'animation/buffalo-trial.blend'))
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');body=bpy.data.objects['body_lod1']
for o in scene.objects:
    if o.type=='MESH':o.hide_render=o!=body
rig.data.pose_position='POSE';body.hide_render=False;body.hide_set(False)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.48,.40,.30);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
cam=bpy.data.cameras.new('Source motion preview');obj=bpy.data.objects.new('Source motion preview',cam);scene.collection.objects.link(obj);scene.camera=obj
center=Vector((0,0,.95));obj.location=center+Vector((4,-6,2.7));obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.ortho_scale=4.6
scene.render.image_settings.file_format='PNG';scene.render.fps=30
dest=OUT/'art/animation';dest.mkdir(parents=True,exist_ok=True)
for name,last in [('buffalo_idle_source_trial',121),('buffalo_walk_source_trial',25)]:
    rig.animation_data.action=bpy.data.actions[name];frames=dest/name;frames.mkdir(exist_ok=True)
    step=2 if last==121 else 1
    for i,frame in enumerate(range(1,last+1,step)):
        scene.frame_set(frame);scene.render.filepath=str(frames/f'{i:04}.png');bpy.ops.render.render(write_still=True)
    encoder=shutil.which('ffmpeg');assert encoder,'Installed FFmpeg is required for source preview encoding'
    result=subprocess.run([encoder,'-hide_banner','-loglevel','error','-framerate',str(30//step),'-i',str(frames/'%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','23',str(dest/(name+'.mp4'))],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr)
print('SOURCE_MOTION_PREVIEWS_COMPLETE')
