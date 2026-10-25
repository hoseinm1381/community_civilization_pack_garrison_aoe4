"""Author exact-donor mounted Dai Viet remixes with per-material albedo maps.

Native multi-group geometry cook is unqualified: retain editable skinned visual
details and separately saved native-material atlas mappings for integration.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART,EXPORT,OUT,guard,owned,read,sha,write
import pilot_author_blender as donor
import representative_batch as review

ROOT=OUT/'inventory/remaining-donors/run-004/decoded'
TARGETS={
    'armor3':'001_chi_horse_combined_armor_age03',
    'armor4':'002_chi_horse_combined_armor_age04',
    'light3':'003_chi_horse_combined_light_age03',
    'light4':'004_chi_horse_combined_light_age04',
    'scout1':'005_chi_horse_combined_scout_age01',
    'scout2':'006_chi_horse_combined_scout_age02',
    'scout3':'007_chi_horse_combined_scout_age03',
    'scout4':'008_chi_horse_combined_scout_age04',
    'scout_female1':'009_chi_horse_combined_scout_female_age01',
    'scout_female2':'010_chi_horse_combined_scout_female_age02',
    'scout_female3':'011_chi_horse_combined_scout_female_age03',
    'scout_female4':'012_chi_horse_combined_scout_female_age04',
    'trade4':'inherited-exact-trade',
    'trade2':'additional-official-models/trade2',
    'trade3':'additional-official-models/trade3',
}
REV='v1'


def main(key):
    guard()
    revision='v2' if key=='trade4' else REV
    source_root=(OUT/'inventory/inherited-render-bodies-v2/run-003/decodes/chinese-trade-cart-tier4-exact'
                 if key=='trade4' else OUT/'inventory'/TARGETS[key]
                 if key in ('trade2','trade3') else ROOT/TARGETS[key])
    manifest=next(source_root.rglob('decoded-static.json'))
    decoded=read(manifest)
    model=decoded['request']['logical_path']
    groups=decoded['geometry']['groups']
    if len(decoded['skeleton']['bones'])!=127 or len(groups) not in (6,7,12):
        raise RuntimeError(f'Mounted donor rig/group contract changed: {key}')
    target=owned(ART/'remaining_roster/mounted'/key/(key+'_'+revision+'.blend'))
    export=owned(EXPORT/'remaining_roster/mounted'/key/revision)
    receipt=owned(OUT/'qualification/remaining_roster/mounted'/key/revision/'authoring.json')
    if target.exists() or export.exists() or receipt.exists():
        raise FileExistsError('Preserve existing mounted candidate')
    if bpy.data.filepath:raise RuntimeError('Start with unsaved Blender scene')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    import addon_utils
    mods=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(mods)!=1:raise RuntimeError('Garrison extension missing')
    addon_utils.enable(mods[0],default_set=False,persistent=False)
    _,imported=donor.import_donor(key,manifest,model)
    sources=[o for o in imported if o.type=='MESH' and len(o.data.polygons)>0]
    if len(sources)!=len(groups):raise RuntimeError('Imported group count mismatch')
    horse=max((o for o in sources if 'horse_lod1' in o.name),key=lambda o:len(o.data.polygons))
    rider=max((o for o in sources if 'rider_lod1' in o.name),key=lambda o:len(o.data.polygons))
    rig=review.rig_of(horse)
    if len(rig.data.bones)!=127 or review.rig_of(rider)!=rig:
        raise RuntimeError('Mounted stock rig mismatch')
    final=bpy.data.collections.new('CCP060_'+key+'_final')
    stock=bpy.data.collections.new('CCP060_'+key+'_stock')
    draft=bpy.data.collections.new('CCP060_'+key+'_draft_empty')
    for c in (final,stock,draft):bpy.context.scene.collection.children.link(c)
    review._tint_context=('horseman2',revision)
    review._pipeline=True
    review._tint_cache.clear()
    review._export_folder_override=export
    review._review_folder_override=owned(OUT/'qualification/remaining_roster/mounted'/key/revision/'review')
    material_rows=[];remixes=[]
    for source in sources:
        clone=source.copy();clone.data=source.data.copy()
        clone.name='CCP060_'+key+'_remix_'+str(len(remixes))
        final.objects.link(clone)
        role=('horse' if 'horse_lod' in source.name else
              'rider' if 'rider_' in source.name else 'trade_goods')
        if role=='trade_goods':
            mat=source.data.materials[0].copy()
            node=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.name.lower()),None)
            if node is None:raise RuntimeError(f'No exact trade goods albedo {source.name}')
            original=node.image
            image=original.copy();image.name='CCP060_trade4_stock_'+str(len(material_rows))
            path=owned(export/('stock_goods_albedo_'+str(len(material_rows))+'.png'))
            path.parent.mkdir(parents=True,exist_ok=True)
            try:
                image.filepath_raw=str(path);image.file_format='PNG';image.save()
                node.image=image
            except RuntimeError as error:
                if 'does not have any image data' not in str(error):raise
                bpy.data.images.remove(image)
                path=None
        else:
            mat=review.shared_atlas_material(source)
        clone.data.materials.clear();clone.data.materials.append(mat)
        node=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.name.lower()),None)
        if node is None:raise RuntimeError(f'No native albedo on {source.name}')
        imported_name=source.data.materials[0].name
        bits=imported_name.split(' · ')
        native_material=bits[1] if len(bits)>=3 and bits[0]=='AoE IV' else imported_name
        material_rows.append({'native_material':native_material,
                              'projection_material':imported_name,
                              'native_group':source.name,'role':role,
                              'albedo_png':(str(Path(node.image.filepath).resolve()) if role!='trade_goods' or path is not None else None),
                              'texture_slot':'albedoTexture',
                              'visual_source':('native stock goods retained' if role=='trade_goods'
                                               else 'native atlas selective cloth/tack tint')})
        for c in tuple(source.users_collection):c.objects.unlink(source)
        stock.objects.link(source)
        if 'lod1' not in source.name:
            source.hide_set(True);source.hide_render=True
            clone.hide_set(True);clone.hide_render=True
        remixes.append(clone)
    parts=[]
    parts.append(review.donor_layer(rider,final,'rider_split_service_coat',
                   ('spine','pelvis'),(.18,.74),expand=.055,flare=.13,tint='deep_teal'))
    parts.append(review.donor_layer(rider,final,'rider_chest_armor',
                   ('ribcage','spine'),(.45,.84),expand=.060,tint='brown'))
    parts.append(review.donor_layer(horse,final,'woven_saddle_blanket',
                   ('spine','saddle','cloth'),(.39,.86),expand=.065,flare=.12,tint='indigo'))
    parts.append(review.donor_layer(horse,final,'leather_chest_tack',
                   ('chest','spine'),(.28,.73),expand=.040,tint='brown'))
    if any(p.get('status') for p in parts):
        raise RuntimeError(f'Mounted design part failed: {parts}')
    donor.set_comparison_layers(final,stock,draft)
    bpy.context.scene['ccp060_exact_stock_model']=model
    bpy.context.scene['ccp060_native_animation']='preserve stock 127-bone mounted rig/actions/equipment'
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    game=review.render_match(key,revision,horse,final)
    close=review.render_match(key,revision,horse,final,extra=True)
    # Exact native material names are extracted from the decoded manifest;
    # Blender preview names are recorded alongside them, never substituted.
    spec={'schema':'ccp-060-mounted-material-map/1','exact_native_model':model,
          'donor_manifest':str(manifest),'donor_manifest_sha256':sha(manifest),
          'native_group_count':len(groups),'native_skeleton_bones':127,
          'groups':material_rows,
          'geometry_route':'editable skinned source only; native multi-group FBX/cook unqualified',
          'stock_weapon_and_mount_motion':'unchanged'}
    write(export/'material-map.json',spec)
    atlas_files=sorted({row['albedo_png'] for row in material_rows if row['albedo_png']})
    if any(not Path(p).exists() for p in atlas_files):raise RuntimeError('Mounted atlas missing')
    write(receipt,{'schema':'ccp-060-mounted-exact-donor-authoring/1',
        'status':'blend_albedos_and_reviews_only_native_geometry_export_unqualified',
        'key':key,'logical_model':model,'donor_manifest':str(manifest),
        'donor_manifest_sha256':sha(manifest),'blend':str(target),
        'blend_sha256':sha(target),'material_map':str(export/'material-map.json'),
        'material_map_sha256':sha(export/'material-map.json'),
        'albedos':[{'path':p,'sha256':sha(Path(p))} for p in atlas_files],
        'parts':parts,'review':{'game':game,'close':close},
        'native_cook':'not_run'})
    print(json.dumps({'key':key,'receipt':str(receipt),'atlas_count':len(atlas_files),'parts':len(parts)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--key',choices=tuple(TARGETS),required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.key)
