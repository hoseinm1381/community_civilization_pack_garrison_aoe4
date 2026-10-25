"""Presentation-only renders; never save camera/light changes to the master."""
import bpy,sys,math
from mathutils import Vector
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from common import *
guard();family=sys.argv[sys.argv.index('--')+1];revision=sys.argv[sys.argv.index('--')+2]
source=ART/family/revision/('ministry.blend' if family=='ministry' else 'model.blend')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
if family=='buffalo':
    body=bpy.data.objects['body_lod1']
    for o in scene.objects:
        if o.type=='MESH':o.hide_render=o!=body
    body.hide_render=False;body.hide_set(False);objects=[body]
else:objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
scene.render.engine='CYCLES';scene.cycles.samples=8
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=900;scene.render.resolution_y=740;scene.render.resolution_percentage=100
scene.world.color=(.24,.24,.24);scene.view_settings.view_transform='AgX'
points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box];lo=Vector(tuple(min(v[k] for v in points) for k in range(3)));hi=Vector(tuple(max(v[k] for v in points) for k in range(3)));center=(lo+hi)*.5;size=max((v-center).length for v in points)
for name,pos,power in [('Key',(4,-5,6),1200),('Fill',(-4,-2,3),850),('Rim',(1,4,5),1100)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power*(size/2)**2;light.size=size*2;o=bpy.data.objects.new(name,light);scene.collection.objects.link(o);o.location=center+Vector(pos)*size/2;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('Presentation only');o=bpy.data.objects.new('Presentation only',cam);scene.collection.objects.link(o);scene.camera=o;cam.type='ORTHO';cam.ortho_scale=size*2.2
dest=OUT/'art'/family/revision/'views';dest.mkdir(parents=True,exist_ok=True)
def render(name,direction):
    o.location=center+Vector(direction).normalized()*size*5;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(dest/(name+'.png'));bpy.ops.render.render(write_still=True)
views=[('threequarter',(4,-6,2.7)),('front',(0,-1,0)),('back',(0,1,0)),('right',(1,0,0)),('left',(-1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]
for name,direction in views:
    if name!='threequarter':scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.55,.50,.43)
    render(name,direction)
if family=='buffalo':
    scene.render.engine='CYCLES'
    # Preview owner mask only; this is not a claim of native player-colour proof.
    mat=body.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');old=bs.inputs['Base Color'].links[0].from_socket
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images['081_pattern'];sep=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],sep.inputs['Color']);mix=nodes.new('ShaderNodeMixRGB');links.new(sep.outputs['Red'],mix.inputs[0]);links.new(old,mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color'])
    for name,color in [('owner-red',(.55,.025,.015,1)),('owner-blue',(.018,.09,.55,1))]:mix.inputs[2].default_value=color;render(name,(4,-6,2.7))
print('REVIEW_VIEWS_COMPLETE',family,revision)
