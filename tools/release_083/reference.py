import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy,importlib,math
from mathutils import Vector
guard()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/release_079/skirmisher2/r3/model.blend'))
key=next(k for k in bpy.context.preferences.addons.keys() if k.endswith('.garrison'))
manifest=next((OUT/'references/chinese-archer').glob('*/decoded-static.json'));data=read(manifest);data['manifest_path']=str(manifest)
parent=bpy.data.objects.new('Chinese archer reference',None);bpy.context.scene.collection.objects.link(parent)
parent['garrison_logical_path']=data['request']['logical_path']
before=set(bpy.data.objects);importlib.import_module(key+'.decode_projection')._apply_decoded_static(parent,data,create_controls=False)
added=set(bpy.data.objects)-before
objects=[o for o in added if o.type=='MESH' and o.get('garrison_lod_level')==1]
assert len(objects)==1;body=objects[0]
for o in bpy.context.scene.objects:
    if o.type=='MESH':o.hide_render=o!=body
body.hide_set(False)
info={'meshes':[(o.name,len(o.data.vertices)) for o in objects],'materials':[],'body_triangles':sum(len(p.vertices)-2 for p in body.data.polygons)}
for m in body.data.materials:
    info['materials'].append({'name':m.name,'images':[{'node':n.name,'label':n.label,'image':n.image.name,'file':n.image.filepath} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='TEXTURE';scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
vs=[body.matrix_world@v.co for v in body.data.vertices];lo=Vector([min(p[i] for p in vs) for i in range(3)]);hi=Vector([max(p[i] for p in vs) for i in range(3)]);center=(lo+hi)/2
cam=bpy.data.objects.new('Reference camera',bpy.data.cameras.new('Reference camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.3;cam.location=center+Vector((2,-5,1));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.filepath=str(OUT/'references/chinese-archer.png');bpy.ops.render.render(write_still=True)
write(OUT/'references/chinese-archer-info.json',info)
print('REF_INFO',info)
