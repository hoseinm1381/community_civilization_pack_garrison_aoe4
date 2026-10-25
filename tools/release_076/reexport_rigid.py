"""Immutable rigid export correction: native cook expects V-flipped FBX UVs."""
import sys,shutil
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
guard()
selection=read(RECIPES/'selection.json')
for family in ('javelin2','javelin3','javelin4','projectile2','projectile3','projectile4'):
 old=selection[family];new='r3'
 dst=ART/family/new;exp=EXPORT/family/new;out=OUT/'art'/family/new
 if dst.exists() or exp.exists():raise ValueError('Revision already exists')
 dst.mkdir(parents=True);shutil.copytree(EXPORT/family/old,exp);shutil.copytree(OUT/'art'/family/old,out)
 bpy.ops.wm.open_mainfile(filepath=str(ART/family/old/'model.blend'))
 lods=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('body_lod')]
 bpy.ops.object.select_all(action='DESELECT')
 for o in lods:
  o.hide_set(False);o.select_set(True)
  for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
 bpy.ops.export_scene.fbx(filepath=str(exp/'model.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
 for o in lods:
  for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
  if o.name!='body_lod1':o.hide_set(True)
 bpy.ops.wm.save_as_mainfile(filepath=str(dst/'model.blend'))
 receipt=read(out/'export.json');receipt.update(revision=new,source=str(dst/'model.blend'),source_sha256=sha(dst/'model.blend'),export=str(exp),files={p.name:sha(p) for p in exp.iterdir() if p.is_file()},correction='V-flipped native FBX export; editable source UVs unchanged')
 write(out/'export.json',receipt)
 anatomy=read(out/'anatomy.json');anatomy['revision']=new;write(out/'anatomy.json',anatomy)
 selection[family]=new
write(RECIPES/'selection.json',selection)
