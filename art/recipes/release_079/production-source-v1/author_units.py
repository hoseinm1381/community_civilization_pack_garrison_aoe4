"""Isolated editable 0.7.9 art, native rig contracts and skeletal LOD exports."""
import sys,re,math,importlib
from pathlib import Path
import bpy,bmesh
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from export_pilot import addon
from rig_contract import rig_text,fold_weights
from mesh_workshop import Workshop,make_atlas
from unit_recipes import human,buffalo,javelin

def weights(obj,contract,lod):
    names={g.index:g.name for g in obj.vertex_groups}
    samples=[{names[g.group]:g.weight for g in v.groups if g.weight>1e-8} for v in obj.data.vertices]
    obj.vertex_groups.clear()
    for i,ws in enumerate(samples):
        ws=fold_weights(ws,contract,lod);ws=dict(sorted(ws.items(),key=lambda p:p[1],reverse=True)[:4]);total=sum(ws.values())
        for n,w in ws.items():(obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n)).add([i],w/total,'REPLACE')

def main():
    guard()
    if not bpy.app.background:raise RuntimeError('Use isolated background Blender')
    family,revision=sys.argv[sys.argv.index('--')+1:]
    assert re.fullmatch('(buffalo|skirmisher[234]|javelin[234]|projectile[234])',family) and re.fullmatch('r[0-9]+',revision)
    art=ART/family/revision;exp=EXPORT/family/revision;out=OUT/'art'/family/revision
    if art.exists() or exp.exists():raise FileExistsError('Immutable art revision')
    for p in (art,exp,out):p.mkdir(parents=True)
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    for m in list(bpy.data.materials):bpy.data.materials.remove(m,do_unlink=True)
    rig=None;contract=None;refs=[]
    if family=='buffalo' or family.startswith('skirmisher'):
        row=read(OUT/'donors.json')[family];d=read(row['manifest']);d['manifest_path']=row['manifest']
        root=bpy.data.objects.new('Official reference - not exported',None);bpy.context.scene.collection.objects.link(root);root['garrison_logical_path']=row['logical_path']
        before=set(bpy.data.objects);addon('decode_projection')._apply_decoded_static(root,d,create_controls=False)
        refs=list(set(bpy.data.objects)-before);rig=next(o for o in refs if o.type=='ARMATURE')
        for obj in refs:
            if obj.type=='MESH':obj.hide_render=True;obj.hide_set(True)
        contract=read(OUT/'art'/family/'pilot-r1/export.json')['donor_contract']
        for m in bpy.data.materials:m.name='Reference_'+m.name
    material=make_atlas(exp);w=Workshop(rig,material)
    if family=='buffalo':buffalo(w)
    elif family.startswith('skirmisher'):human(w,int(family[-1]))
    else:javelin(w,int(family[-1]),family.startswith('projectile'))
    for obj in w.parts:
        assert all(math.isfinite(x) for v in obj.data.vertices for x in v.co)
        assert len(obj.data.uv_layers)>0
    count=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in w.parts)
    if family.startswith('skirmisher') and count>17500:
        for obj in w.parts:
            bpy.context.view_layer.objects.active=obj
            dec=obj.modifiers.new('Surface density budget','DECIMATE');dec.ratio=17500/count
            bpy.ops.object.modifier_apply(modifier=dec.name)
        count=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in w.parts)
    cap=20000 if family=='buffalo' else 24000 if family.startswith('skirmisher') else 3000
    assert count<=cap,(family,count,cap)
    components=[{'name':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'tile':o.get('079_tile')} for o in w.parts]
    bpy.ops.object.select_all(action='DESELECT');copies=[]
    for obj in w.parts:
        c=obj.copy();c.data=obj.data.copy();bpy.context.scene.collection.objects.link(c);c.hide_set(False);c.select_set(True);copies.append(c)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();body=bpy.context.object;body.name='body_lod1';lods=[body]
    if rig:weights(body,contract,1)
    for lod,ratio in ((2,.5),(3,.25)):
        obj=body.copy();obj.data=body.data.copy();obj.name='body_lod'+str(lod);bpy.context.scene.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj
        dec=obj.modifiers.new('Geometry LOD '+str(lod),'DECIMATE');dec.ratio=ratio;bpy.ops.object.modifier_apply(modifier=dec.name)
        if rig:weights(obj,contract,lod)
        obj.data.materials.clear();mat=material.copy();mat.name='lod'+str(lod);obj.data.materials.append(mat);lods.append(obj)
    for obj in w.parts:obj.hide_render=True;obj.hide_set(True)
    for obj in lods[1:]:obj.hide_render=True;obj.hide_set(True)
    if rig:
        rig.animation_data_clear();rig.data.pose_position='REST'
        addon('unit_export').export_unit_model(rig,lods,exp/'model.fbx',addon('unit_export').skeleton_records(rig),three_lods=False)
        (exp/'model.rig').write_text(rig_text(contract),encoding='utf-8')
    else:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in lods:
            obj.hide_set(False);obj.select_set(True)
            for uv in obj.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
        bpy.ops.export_scene.fbx(filepath=str(exp/'model.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
        for obj in lods:
            for uv in obj.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
        for obj in lods[1:]:obj.hide_set(True)
    bpy.context.preferences.filepaths.save_version=0
    for image in bpy.data.images:
        if image.name.startswith('079_'):image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(art/'model.blend'))
    result={'family':family,'revision':revision,'source':str(art/'model.blend'),'source_sha256':sha(art/'model.blend'),'export':str(exp),'files':{p.name:sha(p) for p in exp.iterdir() if p.is_file()},'lod_triangles':[sum(len(p.vertices)-2 for p in o.data.polygons) for o in lods],'donor_contract':contract,'components':components,'new_geometry':True,'new_texture_pixels':True,'texture_size':2048,'native_acceptance':False,'source_recipe_sha256':sha(Path(__file__).with_name('unit_recipes.py')),'workshop_sha256':sha(Path(__file__).with_name('mesh_workshop.py'))}
    write(out/'export.json',result);print('NEW_ART_EXPORTED',family,result['lod_triangles'])

if __name__=='__main__':main()
