"""24-group exact-tug worker source with approved open-crate basket replacement.

Authoring/export only. All seven conditional cargo palettes/groups remain exact
stock; the three 2-bone basket LOD groups become the approved 96-triangle crate.
"""
from __future__ import annotations
import importlib
import json
import sys
from pathlib import Path
import bmesh
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART,EXPORT,OUT,guard,owned,read,sha,write
import pilot_author_blender as donor
import representative_batch as review

REV='v8-tug24-native-names'
LOGICAL='art/civilizations/sultanate_ha_tug/animals/tug_elephant_worker_age01/tug_elephant_worker_age01.rgm'


def main():
    guard()
    source_receipt=read(OUT/'representatives/elephant/v3/authoring.json')
    source_blend=Path(source_receipt['blend'])
    if sha(source_blend)!=source_receipt['blend_sha256']:
        raise RuntimeError('Approved riderless crate source changed')
    manifest=next((OUT/'qualification/nonhumanoid-route-preflight/worker-elephant-stock/decoded').rglob('decoded-static.json'))
    donor_manifest=read(manifest)
    groups=donor_manifest['geometry']['groups']
    palettes=donor_manifest['skeleton']['skin_palettes']
    if len(groups)!=24 or len(palettes)!=8 or len(donor_manifest['skeleton']['bones'])!=140:
        raise RuntimeError('Tug 24-group/8-palette/140-bone contract changed')
    basket_indices=(0,1,2)
    if [groups[i]['material'] for i in basket_indices]!=['baskets_lod1','baskets_lod2','baskets_lod3']:
        raise RuntimeError('Tug basket LOD slots changed')
    if [b['name'] for b in palettes[0]['bones']]!=['tsmg_root','chest_m']:
        raise RuntimeError('Basket two-bone palette changed')
    target=owned(ART/'remaining_roster/tug_worker'/f'tug_worker_{REV}.blend')
    export=owned(EXPORT/'remaining_roster/tug_worker'/REV)
    receipt=owned(OUT/'qualification/remaining_roster/tug_worker'/REV/'export.json')
    if target.exists() or export.exists() or receipt.exists():
        raise FileExistsError('Preserve existing tug candidate')
    if bpy.data.filepath:raise RuntimeError('Use disposable unsaved Blender process')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    import addon_utils
    mods=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(mods)!=1:raise RuntimeError('Garrison extension missing')
    addon_utils.enable(mods[0],default_set=False,persistent=False)
    _,imported=donor.import_donor('tug_worker',manifest,LOGICAL)
    meshes=[o for o in imported if o.type=='MESH' and len(o.data.polygons)>0]
    if len(meshes)!=24:raise RuntimeError(f'Expected 24 projection meshes: {len(meshes)}')
    native_bone_names={b['name'] for b in donor_manifest['skeleton']['bones']}
    rig=review.rig_of(meshes[0])
    if len(rig.data.bones)!=140 or any(review.rig_of(o)!=rig for o in meshes):
        raise RuntimeError('All tug groups must share exact 140-bone rig')
    # Resolve each decoded group using its real stem, material, vertices and
    # triangles. Duplicate conditional groups consume suffixes in name order.
    ordered=[]
    for index,group in enumerate(groups):
        hits=[o for o in meshes if o not in ordered and group['name'] in o.name
              and group['material'] in o.name and len(o.data.vertices)==group['vertex_count']
              and sum(len(p.vertices)-2 for p in o.data.polygons)==group['triangle_count']]
        if not hits:raise RuntimeError(f'Cannot identify native group {index}: {group["name"]}')
        ordered.append(sorted(hits,key=lambda o:o.name)[0])
    if len({o.name for o in ordered})!=24:raise RuntimeError('Group ordering reused an object')
    cargo_names=[p['name'] for p in source_receipt['parts'] if p['name'].startswith('CCP060_cargo_')]
    if len(cargo_names)!=8:raise RuntimeError('Approved crate has changed part count')
    with bpy.data.libraries.load(str(source_blend),link=False) as (src,dst):
        dst.objects=[name for name in cargo_names if name in src.objects]
    cargo_parts=[o for o in dst.objects if o is not None]
    if len(cargo_parts)!=8:raise RuntimeError('Could not load every approved crate part')
    atlas_source=EXPORT/'representatives/elephant/v3/single_atlas_0.png'
    if not atlas_source.exists():raise FileNotFoundError(atlas_source)
    export.mkdir(parents=True,exist_ok=False)
    cargo_atlas=export/'cargo_baskets_albedo.png'
    cargo_atlas.write_bytes(atlas_source.read_bytes())
    final=bpy.data.collections.new('CCP060_tug24_final_geometry')
    stock=bpy.data.collections.new('CCP060_tug24_stock_reference')
    for collection in (final,stock):bpy.context.scene.collection.children.link(collection)
    materials={};output=[];map_rows=[];native_name_ordinals={}
    for index,(source,group) in enumerate(zip(ordered,groups)):
        material_name=group['material']
        if material_name not in materials:
            material=source.data.materials[0].copy()
            material.name=material_name
            if material.name!=material_name:raise RuntimeError(f'Material collision {material_name}')
            if index in basket_indices:
                nodes=[n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and 'albedo' in n.name.lower()]
                if len(nodes)!=1:raise RuntimeError('Basket material has no unique native albedo: '+str([(n.name,n.image.name if n.image else None) for n in material.node_tree.nodes if n.type=='TEX_IMAGE']))
                image=bpy.data.images.load(str(cargo_atlas),check_existing=True)
                nodes[0].image=image
            materials[material_name]=material
        if index in basket_indices:
            pieces=[]
            for original in cargo_parts:
                part=original.copy();part.data=original.data.copy()
                final.objects.link(part)
                part.hide_set(False);part.hide_render=False
                for g in part.vertex_groups:
                    if g.name=='spine1_m':g.name='chest_m'
                if {g.name for g in part.vertex_groups}!={'chest_m'}:
                    raise RuntimeError('Cargo must use exact tug chest_m palette')
                part.parent=rig
                for modifier in part.modifiers:
                    if modifier.type=='ARMATURE':modifier.object=rig
                pieces.append(part)
            if bpy.context.object and bpy.context.object.mode!='OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            for obj in bpy.context.view_layer.objects:obj.select_set(False)
            for part in pieces:part.select_set(True)
            bpy.context.view_layer.objects.active=pieces[0]
            with bpy.context.temp_override(selected_objects=pieces,active_object=pieces[0],object=pieces[0]):
                bpy.ops.object.join()
            clone=pieces[0]
            native_name_ordinals[group['name']]=native_name_ordinals.get(group['name'],0)+1
            clone.name=f"{group['name']}_lod{native_name_ordinals[group['name']]}"
            bm=bmesh.new();bm.from_mesh(clone.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(clone.data);bm.free();clone.data.update()
            triangles=sum(len(p.vertices)-2 for p in clone.data.polygons)
            if triangles!=96:raise RuntimeError(f'Approved crate is {triangles}, expected 96 triangles')
            changed='approved_open_crate_96tri_chest_m'
        else:
            clone=source.copy();clone.data=source.data.copy();final.objects.link(clone)
            native_name_ordinals[group['name']]=native_name_ordinals.get(group['name'],0)+1
            clone.name=f"{group['name']}_lod{native_name_ordinals[group['name']]}"
            triangles=sum(len(p.vertices)-2 for p in clone.data.polygons)
            if triangles!=group['triangle_count']:raise RuntimeError(f'Native group {index} triangle drift')
            changed='stock_geometry_and_conditional_cargo_preserved'
        clone.parent=rig
        for modifier in clone.modifiers:
            if modifier.type=='ARMATURE':modifier.object=rig
        clone.data.materials.clear();clone.data.materials.append(materials[material_name])
        if not clone.data.uv_layers or {g.name for g in clone.vertex_groups}-native_bone_names:
            raise RuntimeError(f'Group {index} lost UV/native skin')
        if index in basket_indices and {g.name for g in clone.vertex_groups}!={'chest_m'}:
            raise RuntimeError('Joined basket skin palette changed')
        for c in tuple(source.users_collection):c.objects.unlink(source)
        stock.objects.link(source)
        source.hide_set(True);source.hide_render=True
        # Copies only: V inversion is an FBX source convention, saved in new
        # candidate; original imported stock reference retains native UVs.
        for uv in clone.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
        output.append(clone)
        map_rows.append({'group_index':index,'native_name':group['name'],
                         'material_name':material_name,'effect':group['effect'],
                         'original_triangles':group['triangle_count'],'export_triangles':triangles,
                         'mesh':clone.name,'treatment':changed,
                         'albedo_png':str(cargo_atlas) if index in basket_indices else None,
                         'texture_slot':'albedoTexture',
                         'native_unmodified_texture':index not in basket_indices})
    module=importlib.import_module(mods[0]+'.unit_export')
    records=module.skeleton_records(rig)
    if [b['name'] for b in records]!=[b['name'] for b in donor_manifest['skeleton']['bones']]:
        raise RuntimeError('Tug native bone sequence changed')
    module.export_unit_model(rig,output,export/'model.fbx',records,three_lods=False)
    payload=(export/'model.fbx').read_bytes()
    skins=payload.count(b'DeformerS\x04\x00\x00\x00Skin')
    clusters=payload.count(b'DeformerS\x07\x00\x00\x00Cluster')
    if skins!=24 or clusters<24:raise RuntimeError(f'FBX skin/group count {skins=} {clusters=}')
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.scene['ccp060_exact_worker_model']=LOGICAL
    bpy.context.scene['ccp060_cargo']='Approved v3 riderless open crate and three sticks; tug chest_m basket groups only'
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    write(export/'material-map.json',{'schema':'ccp-060-tug24-material-map/1',
        'exact_donor_manifest':str(manifest),'exact_donor_manifest_sha256':sha(manifest),
        'native_full_skeleton_bones':140,'native_skin_palettes':[
            {'name':p['name'],'bones':[b['name'] for b in p['bones']]} for p in palettes],
        'groups':map_rows})
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in export.iterdir() if p.is_file()}
    write(receipt,{'schema':'ccp-060-tug-worker-24group-cargo-export/1',
        'status':'24_group_source_export_only_native_cook_unqualified',
        'donor_manifest':str(manifest),'donor_manifest_sha256':sha(manifest),
        'approved_cargo_source':str(source_blend),'approved_cargo_source_sha256':sha(source_blend),
        'blend':str(target),'blend_sha256':sha(target),'folder':str(export),
        'files':files,'native_group_count':24,'native_palette_count':8,
        'export_group_order':map_rows,'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters,
        'native_cook':'not_run','conditional_cargo_groups':'all 21 non-basket groups retained exact stock geometry',
        'visual_review':source_receipt['review'],
        'limitation':'approved v3 cargo source is remapped from sul rig spine1_m to exact tug basket chest_m; in-game animation/contact unverified'})
    print(json.dumps({'receipt':str(receipt),'skins':skins,'clusters':clusters,
                      'changed_groups':list(basket_indices),'retained_groups':21}))


if __name__=='__main__':main()
