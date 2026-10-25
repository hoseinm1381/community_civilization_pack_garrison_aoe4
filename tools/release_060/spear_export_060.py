"""Export approved Spear I-IV three-LOD authoring as native geometry sources.

Open each pinned foot-tier v1 .blend with Blender -b, then pass --age 1..4.
Join the already approved weighted overlays into their corresponding donor LOD,
keep one native material/atlas per LOD, and explicitly triangulate before FBX.
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART,EXPORT,OUT,RECIPES,guard,owned,read,sha,write
import ranged_roster_060 as roster
import representative_batch as review


def stage(age):
    guard()
    recipe=read(RECIPES/'representative-foot-tier-batch.json')
    entries=[x for x in recipe['models'] if x['age']==age and
             'chi_infantry_light_age' in x['model_path']]
    if len(entries)!=1:raise RuntimeError(f'Expected one actual Spear Age {age} donor')
    entry=entries[0];slug=Path(entry['model_path']).stem
    manifest=Path(entry['manifest'])
    if sha(manifest)!=entry['manifest_sha256']:
        raise RuntimeError('Pinned Spear donor changed')
    original=owned(ART/'representatives/foot_tiers'/slug/(slug+'_v1.blend'))
    evidence_v1=read(OUT/'representatives/foot_tiers'/slug/'v1/authoring.json')
    if (Path(bpy.data.filepath).resolve()!=original.resolve() or
        sha(original)!=evidence_v1['blend_sha256']):
        raise RuntimeError('Open the exact approved foot-tier v1 blend')
    target=owned(ART/'spear_roster'/slug/(slug+'_v3.blend'))
    export=owned(EXPORT/'spear_roster'/slug/'v3')
    receipt=owned(OUT/'qualification/spear_roster'/slug/'v3/export.json')
    if any(p.exists() for p in (target,export,receipt)):
        raise FileExistsError(f'Preserve earlier Spear {slug} output')
    import addon_utils
    modules=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(modules)!=1:raise RuntimeError('Installed Garrison extension unavailable')
    addon_utils.enable(modules[0],default_set=False,persistent=False)
    if bpy.context.object and bpy.context.object.mode!='OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE' and
             o.name==slug+' · Armature')
    if len(rig.data.bones)!=48:raise RuntimeError('Expected native Spear 48-bone rig')
    collection=bpy.data.collections[slug.replace('chi_','CCP060_chi_')+'_final_geometry']
    original_finish=list(o for o in collection.objects if o.type=='MESH')
    overlays={1:['CCP060_finish_split_knee_tunic','CCP060_finish_broad_chest_armor'],
              2:['CCP060_finish_split_knee_tunic_lod2'],
              3:['CCP060_finish_split_knee_tunic_lod3']}
    produced={};piece_counts={}
    for number in (1,2,3):
        body=bpy.data.objects[f'CCP060_DaiViet_{slug}_lod{number}']
        parts=[body]+[bpy.data.objects[name] for name in overlays[number]]
        if any(review.rig_of(obj)!=rig for obj in parts):
            raise RuntimeError(f'LOD{number} approved part has another rig')
        material=body.data.materials[0].copy();material.name=f'lod{number}'
        if material.name!=f'lod{number}':raise RuntimeError('Exact native material name occupied')
        clones=[]
        for source in parts:
            clone=source.copy();clone.data=source.data.copy();collection.objects.link(clone)
            clone.hide_set(False);clone.hide_render=False
            clone.data.materials.clear();clone.data.materials.append(material)
            clones.append(clone)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in clones:obj.select_set(True)
        bpy.context.view_layer.objects.active=clones[0]
        bpy.ops.object.join()
        merged=clones[0];merged.name=f'CCP060_{slug}_author_lod{number}'
        bm=bmesh.new();bm.from_mesh(merged.data)
        bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
        bm.to_mesh(merged.data);bm.free();merged.data.update()
        if any(len(f.vertices)!=3 for f in merged.data.polygons):
            raise RuntimeError('Joined Spear LOD not fully triangulated')
        merged.hide_set(number>1);merged.hide_render=number>1
        produced[number]=merged
        piece_counts[number]=[{'name':p.name,'vertices':len(p.data.vertices),
                               'triangles':sum(len(f.vertices)-2 for f in p.data.polygons)}
                              for p in parts]
    for obj in original_finish:obj.hide_set(True);obj.hide_render=True
    # The original v1 material already points to a saved private albedo PNG.
    # All three LOD images are byte-identical; keep one copy for native source.
    source_images=[EXPORT/'representatives/foot_tiers'/slug/'v1'/f'single_atlas_{n}.png'
                   for n in (0,1,2)]
    if len({sha(p) for p in source_images})!=1:
        raise RuntimeError('Approved LODs have different albedo atlases')
    export.mkdir(parents=True)
    shutil.copy2(source_images[0],export/'albedo.png')
    for obj in produced.values():
        albedo=[n for n in obj.data.materials[0].node_tree.nodes
                if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.name.casefold()]
        if len(albedo)!=1:raise RuntimeError('One native albedo per Spear LOD required')
        albedo[0].image.filepath_raw=str(export/'albedo.png')
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    review._review_folder_override=owned(OUT/'qualification/spear_roster'/slug/'v3/review')
    stock=bpy.data.objects[f'{slug} · {slug} · lod1']
    game=review.render_match(slug,'v3',stock,collection)
    close=review.render_match(slug,'v3',stock,collection,extra=True)
    module=importlib.import_module(modules[0]+'.unit_export')
    export_meshes=[]
    for number,obj in produced.items():
        clone=obj.copy();clone.data=obj.data.copy()
        clone.name=slug+'_lod'+str(number)
        bpy.context.scene.collection.objects.link(clone)
        for loop in clone.data.uv_layers.active.data:loop.uv.y=1-loop.uv.y
        export_meshes.append(clone)
    module.export_unit_model(rig,export_meshes,export/'model.fbx',
                             module.skeleton_records(rig),three_lods=False)
    snapshot=roster.authored_snapshot(manifest,produced,export/'authored-snapshot.json')
    action=read(roster.ARCHER_CONTROL)
    if action.get('overrides') or action.get('attachments'):
        raise RuntimeError('No Spear action/attachment replacement allowed')
    action['material_name']='lod1';action['textures']=['albedo']
    (export/'action.json').write_text(json.dumps(action,indent=2)+'\n',encoding='utf-8')
    payload=(export/'model.fbx').read_bytes()
    skins=payload.count(b'DeformerS\x04\x00\x00\x00Skin')
    clusters=payload.count(b'DeformerS\x07\x00\x00\x00Cluster')
    if skins<3 or clusters<3:raise RuntimeError('Spear FBX lacks real LOD skin')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in export.iterdir() if p.is_file()}
    write(receipt,{'schema':'ccp-060-spear-tier-export/v1',
                   'status':'three_lod_source_export_only','slug':slug,'age':age,
                   'model':entry['model_path'],'source_blend':str(target),
                   'source_blend_sha256':sha(target),
                   'approved_v1_blend':str(original),'approved_v1_blend_sha256':sha(original),
                   'exact_donor_manifest':str(manifest),'exact_donor_manifest_sha256':sha(manifest),
                   'folder':str(export),'files':files,
                   'fbx_sha256':sha(export/'model.fbx'),
                   'albedo_sha256':sha(export/'albedo.png'),
                   'action_sha256':sha(export/'action.json'),
                   'authored_snapshot':snapshot,'fbx_skin_nodes':skins,
                   'fbx_cluster_nodes':clusters,'approved_piece_counts':piece_counts,
                   'review':{'game':game,'close_owner':close},
                   'preexport_uv':'u unchanged; v := 1-v',
                   'native_cook':'not_run','native_weapons_attachments':'unchanged',
                   'consuming_families':entry['consuming_families']})
    return {'slug':slug,'blend':str(target),'folder':str(export),
            'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters,'files':files}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--age',type=int,required=True,choices=(1,2,3,4))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    print(json.dumps(stage(args.age),indent=2))
