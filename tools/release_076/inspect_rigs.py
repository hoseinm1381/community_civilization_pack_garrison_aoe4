import sys,importlib,json
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def addon(name):
 key=next(k for k in bpy.context.preferences.addons.keys() if k.endswith('.garrison'))
 return importlib.import_module(key+'.'+name)
def load(name):
 row=read(OUT/'donors.json')[name];data=read(row['manifest']);data['manifest_path']=row['manifest']
 root=bpy.data.objects.new('reference_'+name,None);bpy.context.scene.collection.objects.link(root);root['garrison_logical_path']=row['logical_path']
 before=set(bpy.data.objects);addon('decode_projection')._apply_decoded_static(root,data,create_controls=False)
 objs=list(set(bpy.data.objects)-before)
 return next((o for o in objs if o.type=='ARMATURE'),None),objs
if __name__=='__main__':
 result={}
 for name in ['buffalo','skirmisher2']:
  rig,objs=load(name)
  result[name]={'rig':rig.name,'matrix':[list(r) for r in rig.matrix_world], 'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones},'meshes':[{'name':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'matrix':[list(r) for r in o.matrix_world]} for o in objs if o.type=='MESH']}
 write(OUT/'rig-inspection.json',result)
 print('INSPECTION_SAVED')
