"""Render actual native-decoded highest LOD, without saving or touching source."""
import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from inspect_rigs import addon
from author import review
guard();label,family=sys.argv[sys.argv.index('--')+1:]
p=Path(read(OUT/'cooks'/label/'decoded-proof.json')[family]['manifest']);data=read(p);data['manifest_path']=str(p)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
root=bpy.data.objects.new('Cooked model',None);bpy.context.scene.collection.objects.link(root);root['garrison_logical_path']=data['resources']['model']['logical_path']
addon('decode_projection')._apply_decoded_static(root,data,create_controls=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH'];body=max(meshes,key=lambda o:len(o.data.polygons))
for o in meshes:o.hide_render=o!=body
dest=OUT/'cooks'/label/'review'/family;dest.mkdir(parents=True,exist_ok=True);review(dest,[body])
print('COOKED_PREVIEW_COMPLETE',family)
