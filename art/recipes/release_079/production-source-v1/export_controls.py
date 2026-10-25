"""Export unchanged official live-body geometry/weights as neutral-material controls."""
import sys,importlib
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from rig_contract import rig_text
from export_pilot import addon

def main():
    guard();donors=read(OUT/'donors.json');selection={}
    revision=sys.argv[sys.argv.index('--')+1]
    if not __import__('re').fullmatch('control-r[0-9]+',revision):raise ValueError('Invalid revision')
    for family in ('buffalo','skirmisher2'):
        dest=EXPORT/family/revision;art=ART/family/revision
        if dest.exists() or art.exists():raise FileExistsError(dest)
        dest.mkdir(parents=True);art.mkdir(parents=True)
        # This script is restricted to the serialized isolated background process.
        if not bpy.app.background:raise RuntimeError('Controls require isolated background Blender')
        for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
        row=donors[family];data=read(row['manifest']);data['manifest_path']=row['manifest']
        root=bpy.data.objects.new('Official donor control',None);bpy.context.scene.collection.objects.link(root);root['garrison_logical_path']=row['logical_path']
        addon('decode_projection')._apply_decoded_static(root,data,create_controls=False)
        meshes=[o for o in bpy.data.objects if o.type=='MESH' and 'cow_resource' not in o.name]
        meshes.sort(key=lambda o:len(o.data.polygons),reverse=True)
        assert len(meshes)==3
        rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
        for obj in meshes:obj.data.materials.clear()
        for mat in list(bpy.data.materials):bpy.data.materials.remove(mat,do_unlink=True)
        triangles=[]
        for lod,obj in enumerate(meshes,1):
            obj.name='body_lod'+str(lod)
            triangles.append(sum(len(p.vertices)-2 for p in obj.data.polygons))
            material=bpy.data.materials.new('lod'+str(lod));obj.data.materials.clear();obj.data.materials.append(material)
        contract=read(OUT/'art'/family/'pilot-r1/export.json')['donor_contract']
        records=addon('unit_export').skeleton_records(rig)
        addon('unit_export').export_unit_model(rig,meshes,dest/'model.fbx',records,three_lods=False)
        (dest/'model.rig').write_text(rig_text(contract),encoding='utf-8')
        for name,color in {'albedo':(.4,.4,.4,1),'normal':(.5,.5,1,1),'roughness':(.8,.8,.8,1),'metalness':(0,0,0,1),'pattern':(0,0,0,1)}.items():
            im=bpy.data.images.new('control_'+name,width=8,height=8,alpha=True)
            if name!='albedo':im.colorspace_settings.name='Non-Color'
            im.pixels.foreach_set(list(color)*64);im.filepath_raw=str(dest/(name+'.png'));im.file_format='PNG';im.save()
        bpy.ops.wm.save_as_mainfile(filepath=str(art/'model.blend'))
        write(OUT/'art'/family/revision/'export.json',{'family':family,'revision':revision,'source':str(art/'model.blend'),'source_sha256':sha(art/'model.blend'),'export':str(dest),'files':{p.name:sha(p) for p in dest.iterdir() if p.is_file()},'lod_triangles':triangles,'donor_contract':contract,'native_acceptance':False,'purpose':'unchanged official live geometry and skin weights; neutral material for deformation control; buffalo resource carcass excluded'})
        selection[family]=revision
    write(RECIPES/'control-selection.json',selection);print('DONOR_CONTROLS_EXPORTED')
if __name__=='__main__':main()
