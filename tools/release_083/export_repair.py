"""Preserve selected geometry and fix FBX's collision-suffixed material names."""
from pathlib import Path
import sys,shutil,importlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy
sys.path.append(str(ROOT/'tools/release_079'));from rig_contract import rig_text
guard();selection=read(RECIPES/'selection.json');result={}
for family,oldrev in selection.items():
    prior=read(OUT/'art'/family/oldrev/'export.json');bpy.ops.wm.open_mainfile(filepath=prior['source'])
    revision='r12';a=ART/family/revision;e=EXPORT/family/revision;o=OUT/'art'/family/revision
    for p in (a,e,o):p.mkdir(parents=True,exist_ok=False)
    meshes=[bpy.data.objects['body_lod'+str(i)] for i in [1,2,3]];selected={obj.data.materials[0] for obj in meshes}
    for mat in bpy.data.materials:
        if mat not in selected:mat.name='Reference_'+mat.name
    for i,obj in enumerate(meshes,1):obj.data.materials[0].name='lod'+str(i)
    assert [obj.data.materials[0].name for obj in meshes]==['lod1','lod2','lod3']
    for p in Path(prior['export']).glob('*.png'):shutil.copyfile(p,e/p.name)
    for image in bpy.data.images:
        if image.name.startswith('083_'):image.filepath=str(e/(image.name[4:]+'.png'))
    if family.startswith('skirmisher'):
        rig=next(mod.object for mod in meshes[0].modifiers if mod.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST'
        addon=importlib.import_module(next(k for k in bpy.context.preferences.addons.keys() if k.endswith('.garrison'))+'.unit_export')
        addon.export_unit_model(rig,meshes,e/'model.fbx',addon.skeleton_records(rig),three_lods=False)
        (e/'model.rig').write_text(rig_text(prior['donor_contract']))
    else:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in meshes:
            obj.hide_set(False);obj.select_set(True)
            for uv in obj.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
        bpy.ops.export_scene.fbx(filepath=str(e/'model.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
        for obj in meshes:
            for uv in obj.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(a/'model.blend'))
    prior.update(revision=revision,source=str(a/'model.blend'),source_sha256=sha(a/'model.blend'),export=str(e),files={p.name:sha(p) for p in e.iterdir() if p.is_file()},geometry_from_revision=oldrev,repair='canonical material names matching native model.material')
    write(o/'export.json',prior);result[family]=revision;print('083_EXPORT_REPAIRED',family,flush=True)
write(RECIPES/'selection-pre-material-repair.json',selection);write(RECIPES/'selection.json',result)
