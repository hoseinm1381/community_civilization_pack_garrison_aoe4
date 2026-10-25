"""Presentation renders of completed geometry, leaving editable source unchanged."""
import sys,math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
family,revision=sys.argv[sys.argv.index('--')+1:];guard()
bpy.ops.wm.open_mainfile(filepath=str(ART/family/revision/'model.blend'))
body=bpy.data.objects['body_lod1']
for o in bpy.data.objects:
    if o.type=='MESH':o.hide_render=o!=body
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.22,.22,.22);scene.view_settings.view_transform='AgX'
bounds=[body.matrix_world@Vector(c) for c in body.bound_box];center=sum(bounds,Vector())/8;size=max((v-center).length for v in bounds)
for name,pos,power in [('Key',(4,-5,6),1000),('Fill',(-4,-2,3),850),('Rim',(1,4,5),1200)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.size=4;o=bpy.data.objects.new(name,light);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('Review only');obj=bpy.data.objects.new('Review only',cam);scene.collection.objects.link(obj);scene.camera=obj;cam.type='ORTHO';cam.ortho_scale=size*2.25
dest=OUT/'art'/family/revision/'views';dest.mkdir(parents=True,exist_ok=True)
for name,direction in [('threequarter',(4,-6,2.7)),('front',(0,-1,0)),('back',(0,1,0)),('right',(1,0,0)),('left',(-1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:
    obj.location=center+Vector(direction).normalized()*size*5;obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(dest/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SOURCE_VIEWS_RENDERED',family)
