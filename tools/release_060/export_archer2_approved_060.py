"""Export the approved Archer II v3l outfit with its own native three LODs.

Run with the pinned v3l .blend open in a fresh background Blender process.
The approved high-detail body and garment pieces are joined on a copied rigged
mesh; exact Archer II donor far LODs receive corresponding tunic treatment.
No active resource, weapon, gameplay actor, or historical file is changed.
"""
from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART,EXPORT,OUT,RECIPES,guard,owned,read,sha,write
import ranged_roster_060 as roster
import pilot_author_blender as pilot
import representative_batch as review

SOURCE=ART/'archer/archer-base-v3l-owner-tunic.blend'
SOURCE_SHA='0092ebe4a428f12f3a0770d21cdde1a1758876ad16ecf3944ee2f432e5a6125c'
PARTS=('CCP060 · Archer II weighted body · base',
       'CCP060 · Archer v2 fitted upper trousers',
       'CCP060 · Archer v3 clean split tunic',
       'CCP060 · Archer v3 rear headcloth knot',
       'CCP060 · Bound hair cloth headwrap')


def stage():
    guard()
    recipe=read(RECIPES/'ranged-roster-060.json')
    entry=next(x for x in recipe['tiers'] if x['slug']=='archer2')
    manifest=Path(entry['decoded_manifest'])
    if (Path(bpy.data.filepath).resolve()!=SOURCE.resolve() or sha(SOURCE)!=SOURCE_SHA
        or sha(manifest)!=entry['decoded_manifest_sha256']):
        raise RuntimeError('Approved Archer II source or exact donor changed')
    target=owned(Path(entry['authoring_target']))
    export=owned(EXPORT/'ranged_roster/archer2/v1')
    evidence=owned(OUT/'qualification/ranged_roster/archer2/v1')
    for p in (target,export,evidence):
        if p.exists():raise FileExistsError(f'Preserve prior Archer II output: {p}')
    import addon_utils
    modules=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(modules)!=1:raise RuntimeError('One installed Garrison extension required')
    addon_utils.enable(modules[0],default_set=False,persistent=False)
    donor={n:next(o for o in bpy.data.objects if o.type=='MESH' and
                  o.name.endswith(f'lod{n}') and
                  'chi_ranged_bow_age02' in o.name) for n in (1,2,3)}
    rig=review.rig_of(donor[1])
    if len(rig.data.bones)!=48 or any(review.rig_of(o)!=rig for o in donor.values()):
        raise RuntimeError('Approved source lost its exact 48-bone donor rig')
    final=bpy.data.collections.new('CCP060_archer2_approved_final')
    stock=bpy.data.collections.new('CCP060_archer2_exact_stock')
    draft=bpy.data.collections.new('CCP060_archer2_empty_draft')
    for c in (final,stock,draft):bpy.context.scene.collection.children.link(c)
    copied=[]
    for name in PARTS:
        obj=bpy.data.objects[name]
        if obj.hide_render or review.rig_of(obj)!=rig:
            raise RuntimeError(f'Approved visible rigged outfit part changed: {name}')
        clone=obj.copy();clone.data=obj.data.copy();final.objects.link(clone)
        copied.append(clone)
        obj.hide_set(True);obj.hide_render=True
    bpy.ops.object.select_all(action='DESELECT')
    for obj in copied:obj.select_set(True)
    bpy.context.view_layer.objects.active=copied[0]
    bpy.ops.object.join()
    main=copied[0];main.name='CCP060_archer2_author_lod1'
    if len(main.data.materials)!=1 or review.rig_of(main)!=rig:
        raise RuntimeError('Approved joined body must have one native atlas/rig')
    expected_approved=[(893,1072),(70,112),(70,96),(8,12),(128,192)]
    observed=[(len(bpy.data.objects[n].data.vertices),
               sum(len(f.vertices)-2 for f in bpy.data.objects[n].data.polygons))
              for n in PARTS]
    if observed!=expected_approved:
        raise RuntimeError(f'Approved source component topology changed: {observed}')
    if (len(main.data.vertices),sum(len(f.vertices)-2 for f in main.data.polygons))!=(1169,1484):
        raise RuntimeError('Joined approved Archer II silhouette count changed')
    main.data.materials[0].name='lod1'
    if main.data.materials[0].name!='lod1':raise RuntimeError('Native lod1 material name occupied')
    owner_bounds,owner_audit=roster.owner_chart(donor[1].data.materials[0])
    far={};details={}
    for number in (2,3):
        obj=donor[number]
        material=obj.data.materials[0];material.name=f'CCP060_archer2_stock_lod{number}'
        clone=obj.copy();clone.data=obj.data.copy();clone.name=f'CCP060_archer2_author_lod{number}'
        final.objects.link(clone)
        clone.data.materials.clear()
        clone.data.materials.append(roster.preview_material(obj,number,'archer2'))
        details[number]=roster.remodel(obj,clone,'archer2',number,owner_bounds)
        clone.hide_set(True);clone.hide_render=True
        far[number]=clone
    for number,obj in donor.items():
        for c in tuple(obj.users_collection):c.objects.unlink(obj)
        stock.objects.link(obj)
        obj.hide_set(number>1);obj.hide_render=number>1
    final_lods={1:main,**far}
    atlas=roster.cloth_albedo_variant(donor,final_lods,'archer2',
                                      owned(export/'albedo.png'),include_all=True)
    pilot.set_comparison_layers(final,stock,draft)
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.scene['ccp060_approved_source_v3l_sha256']=SOURCE_SHA
    bpy.context.scene['ccp060_exact_stock_model']=entry['exact_native_body_model']
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    evidence.mkdir(parents=True)
    write(evidence/'authoring.json',{
        'schema':'ccp-060-archer2-approved-authoring/v1',
        'status':'approved_v3l_source_three_native_lod_authoring',
        'approved_source':str(SOURCE),'approved_source_sha256':SOURCE_SHA,
        'blend':str(target),'blend_sha256':sha(target),
        'exact_donor':str(manifest),'exact_donor_sha256':sha(manifest),
        'approved_lod1_components':dict(zip(PARTS,expected_approved)),
        'far_lod_remodel':details,'owner_chart':owner_audit,
        'albedo_variant':atlas,'native_weapon_unchanged':entry['primary_weapon_models']})
    review._review_folder_override=owned(evidence/'review')
    game=review.render_match('archer2','v1',donor[1],final)
    close=review.render_match('archer2','v1',donor[1],final,extra=True)
    module=importlib.import_module(modules[0]+'.unit_export')
    export_meshes=[]
    for number,obj in final_lods.items():
        clone=obj.copy();clone.data=obj.data.copy()
        clone.name='chi_ranged_bow_age02_lod'+str(number)
        bpy.context.scene.collection.objects.link(clone)
        for loop in clone.data.uv_layers.active.data:loop.uv.y=1-loop.uv.y
        clone.hide_render=True
        export_meshes.append(clone)
    module.export_unit_model(rig,export_meshes,export/'model.fbx',
                             module.skeleton_records(rig),three_lods=False)
    payload=(export/'model.fbx').read_bytes()
    skins=payload.count(b'DeformerS\x04\x00\x00\x00Skin')
    clusters=payload.count(b'DeformerS\x07\x00\x00\x00Cluster')
    if skins<3 or clusters<3:
        raise RuntimeError(f'Archer II FBX skin preflight failed: {skins=} {clusters=}')
    snapshot=roster.authored_snapshot(manifest,final_lods,export/'authored-snapshot.json')
    action=read(roster.ARCHER_CONTROL)
    if action.get('overrides') or action.get('attachments'):
        raise RuntimeError('Unexpected native Archer action overrides/attachments')
    action['material_name']='lod1';action['textures']=['albedo']
    (export/'action.json').write_text(json.dumps(action,indent=2)+'\n',encoding='utf-8')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in export.iterdir() if p.is_file()}
    write(evidence/'export.json',{
        'schema':'ccp-060-ranged-tier-export/v1',
        'status':'approved_v3l_three_lod_source_export_only',
        'slug':'archer2','source_blend':str(target),'source_blend_sha256':sha(target),
        'approved_source_sha256':SOURCE_SHA,'folder':str(export),'files':files,
        'fbx_sha256':sha(export/'model.fbx'),'albedo_sha256':sha(export/'albedo.png'),
        'action_sha256':sha(export/'action.json'),'authored_snapshot':snapshot,
        'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters,
        'mesh_names':[o.name for o in export_meshes],
        'material_names':[o.data.materials[0].name for o in export_meshes],
        'preexport_uv':'u unchanged; v := 1-v',
        'native_albedo_variant':atlas,
        'authoring_review':{'game':game,'close_owner':close},
        'native_cook':'not_run','native_weapon_attachments':'unchanged'})
    return {'blend':str(target),'export':str(export),'files':files,
            'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters}


def resume_snapshot():
    """Finish the owned v1 output after Blender wrote its valid FBX first."""
    guard()
    recipe=read(RECIPES/'ranged-roster-060.json')
    entry=next(x for x in recipe['tiers'] if x['slug']=='archer2')
    manifest=Path(entry['decoded_manifest'])
    target=owned(Path(entry['authoring_target']))
    export=owned(EXPORT/'ranged_roster/archer2/v1')
    evidence=owned(OUT/'qualification/ranged_roster/archer2/v1')
    if (Path(bpy.data.filepath).resolve()!=target.resolve() or
        sha(target)!=read(evidence/'authoring.json')['blend_sha256'] or
        (evidence/'export.json').exists() or
        (export/'authored-snapshot.json').exists() or
        (export/'action.json').exists()):
        raise RuntimeError('Only the owned incomplete Archer II v1 export may resume')
    final_lods={n:bpy.data.objects[f'CCP060_archer2_author_lod{n}'] for n in (1,2,3)}
    snapshot=roster.authored_snapshot(manifest,final_lods,export/'authored-snapshot.json')
    action=read(roster.ARCHER_CONTROL)
    if action.get('overrides') or action.get('attachments'):
        raise RuntimeError('Unexpected native Archer action overrides/attachments')
    action['material_name']='lod1';action['textures']=['albedo']
    (export/'action.json').write_text(json.dumps(action,indent=2)+'\n',encoding='utf-8')
    payload=(export/'model.fbx').read_bytes()
    skins=payload.count(b'DeformerS\x04\x00\x00\x00Skin')
    clusters=payload.count(b'DeformerS\x07\x00\x00\x00Cluster')
    if skins<3 or clusters<3:raise RuntimeError('Archer II source FBX has no real LOD skin')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in export.iterdir() if p.is_file()}
    reviews={p.stem:{'path':str(p),'sha256':sha(p)}
             for p in (evidence/'review').glob('*.png')}
    write(evidence/'export.json',{
        'schema':'ccp-060-ranged-tier-export/v1',
        'status':'approved_v3l_three_lod_source_export_only',
        'slug':'archer2','source_blend':str(target),'source_blend_sha256':sha(target),
        'approved_source_sha256':SOURCE_SHA,'folder':str(export),'files':files,
        'fbx_sha256':sha(export/'model.fbx'),'albedo_sha256':sha(export/'albedo.png'),
        'action_sha256':sha(export/'action.json'),'authored_snapshot':snapshot,
        'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters,
        'material_names':[o.data.materials[0].name for o in final_lods.values()],
        'preexport_uv':'u unchanged; v := 1-v',
        'native_albedo_variant':read(evidence/'authoring.json')['albedo_variant'],
        'authoring_review':reviews,'native_cook':'not_run',
        'native_weapon_attachments':'unchanged'})
    return {'blend':str(target),'export':str(export),'files':files,
            'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters}


def correct_snapshot():
    """Preserve v1 and pin Blender's actual quad triangulation as v2."""
    guard()
    entry=next(x for x in read(RECIPES/'ranged-roster-060.json')['tiers']
               if x['slug']=='archer2')
    manifest=Path(entry['decoded_manifest'])
    source_blend=owned(Path(entry['authoring_target']))
    prior=owned(EXPORT/'ranged_roster/archer2/v1')
    output=owned(EXPORT/'ranged_roster/archer2/v2')
    receipt=owned(OUT/'qualification/ranged_roster/archer2/v2/export.json')
    old=read(OUT/'qualification/ranged_roster/archer2/v1/export.json')
    if (Path(bpy.data.filepath).resolve()!=source_blend.resolve() or
        sha(source_blend)!=old['source_blend_sha256'] or
        output.exists() or receipt.exists() or
        any(sha(prior/name)!=old['files'][name]['sha256']
            for name in ('model.fbx','albedo.png','action.json'))):
        raise RuntimeError('Only pinned Archer II v1 can produce corrected v2 snapshot')
    output.mkdir(parents=True)
    for name in ('model.fbx','albedo.png','action.json'):
        shutil.copy2(prior/name,output/name)
    lods={n:bpy.data.objects[f'CCP060_archer2_author_lod{n}'] for n in (1,2,3)}
    snapshot=roster.authored_snapshot(manifest,lods,output/'authored-snapshot.json')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in output.iterdir() if p.is_file()}
    updated=dict(old)
    updated.update(status='approved_v3l_three_lod_source_export_corrected_corner_snapshot',
                   folder=str(output),files=files,authored_snapshot=snapshot,
                   source_receipt_v1=str(OUT/'qualification/ranged_roster/archer2/v1/export.json'),
                   source_receipt_v1_sha256=sha(OUT/'qualification/ranged_roster/archer2/v1/export.json'),
                   correction='Snapshot now uses Blender loop_triangles for approved garment quads; FBX, albedo and action are byte identical to v1.')
    write(receipt,updated)
    return {'folder':str(output),'receipt':str(receipt),
            'snapshot_sha256':snapshot['sha256'],
            'fbx_unchanged':sha(output/'model.fbx')==old['fbx_sha256']}


def triangulated_export():
    """Make FBX triangles explicit after the v1 native quad-diagonal mismatch."""
    import bmesh
    guard()
    entry=next(x for x in read(RECIPES/'ranged-roster-060.json')['tiers']
               if x['slug']=='archer2')
    manifest=Path(entry['decoded_manifest'])
    prior_blend=owned(Path(entry['authoring_target']))
    prior=read(OUT/'qualification/ranged_roster/archer2/v1/export.json')
    if Path(bpy.data.filepath).resolve()!=prior_blend.resolve() or sha(prior_blend)!=prior['source_blend_sha256']:
        raise RuntimeError('Open exact approved-derived v1 Archer II blend')
    target=owned(prior_blend.with_name('archer2_v3.blend'))
    export=owned(EXPORT/'ranged_roster/archer2/v3')
    receipt=owned(OUT/'qualification/ranged_roster/archer2/v3/export.json')
    if any(p.exists() for p in (target,export,receipt)):
        raise FileExistsError('Preserve existing Archer II v3')
    lods={n:bpy.data.objects[f'CCP060_archer2_author_lod{n}'] for n in (1,2,3)}
    tri_counts={}
    for number,obj in lods.items():
        before=len(obj.data.vertices)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        if before!=len(obj.data.vertices) or any(len(f.vertices)!=3 for f in obj.data.polygons):
            raise RuntimeError(f'Explicit LOD{number} triangulation changed vertex count')
        tri_counts[number]=len(obj.data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    import addon_utils
    modules=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(modules)!=1:raise RuntimeError('Installed Garrison extension unavailable')
    addon_utils.enable(modules[0],default_set=False,persistent=False)
    module=importlib.import_module(modules[0]+'.unit_export')
    rig=review.rig_of(lods[1])
    export.mkdir(parents=True)
    copied=[]
    for number,obj in lods.items():
        clone=obj.copy();clone.data=obj.data.copy()
        clone.name='chi_ranged_bow_age02_lod'+str(number)
        bpy.context.scene.collection.objects.link(clone)
        for loop in clone.data.uv_layers.active.data:loop.uv.y=1-loop.uv.y
        copied.append(clone)
    module.export_unit_model(rig,copied,export/'model.fbx',
                             module.skeleton_records(rig),three_lods=False)
    for name in ('albedo.png','action.json'):
        shutil.copy2(EXPORT/'ranged_roster/archer2/v1'/name,export/name)
    snapshot=roster.authored_snapshot(manifest,lods,export/'authored-snapshot.json')
    payload=(export/'model.fbx').read_bytes()
    skins=payload.count(b'DeformerS\x04\x00\x00\x00Skin')
    clusters=payload.count(b'DeformerS\x07\x00\x00\x00Cluster')
    if skins<3 or clusters<3:raise RuntimeError('Triangulated FBX lacks weighted LODs')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in export.iterdir() if p.is_file()}
    write(receipt,{
        'schema':'ccp-060-ranged-tier-export/v1',
        'status':'approved_v3l_explicit_triangulated_source_export_only',
        'slug':'archer2','source_blend':str(target),'source_blend_sha256':sha(target),
        'approved_source_sha256':SOURCE_SHA,'folder':str(export),'files':files,
        'fbx_sha256':sha(export/'model.fbx'),'albedo_sha256':sha(export/'albedo.png'),
        'action_sha256':sha(export/'action.json'),'authored_snapshot':snapshot,
        'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters,
        'explicit_triangle_counts':tri_counts,
        'preexport_uv':'u unchanged; v := 1-v',
        'source_v1_blend_sha256':prior['source_blend_sha256'],
        'native_cook':'not_run','native_weapon_attachments':'unchanged',
        'correction':'LOD surfaces explicitly triangulated before FBX export to remove Blender FBX quad-diagonal ambiguity.'})
    return {'blend':str(target),'export':str(export),'fbx_sha256':sha(export/'model.fbx'),
            'snapshot_sha256':snapshot['sha256'],'triangles':tri_counts}


if __name__=='__main__':
    print(json.dumps(triangulated_export() if '--triangulated-export' in sys.argv else
                     correct_snapshot() if '--correct-snapshot' in sys.argv else
                     resume_snapshot() if '--resume-snapshot' in sys.argv else stage(),indent=2))
