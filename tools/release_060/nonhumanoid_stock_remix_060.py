"""Compatible per-material remixes for exact combat elephant and siege donors.

Ram, springald and trebuchet English bodies are donor candidates only: their
generic active animation roots are unresolved and must not be presented as
confirmed runtime bindings.
"""
from __future__ import annotations
import argparse,json,sys
from array import array
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART,EXPORT,OUT,guard,owned,read,sha,write
import pilot_author_blender as donor
import representative_batch as review

ROOT=OUT/'inventory'
DATA={
 'combat_elephant4':('remaining-donors/run-004/decoded/016_sul_elephant_combined_armor_age04','exact_reachable'),
 'combat_elephant4_upgrade':('remaining-donors/run-004/decoded/017_sul_elephant_combined_armor_age04_upgrade','exact_reachable'),
 'siege_tower3':('remaining-donors/run-004/decoded/013_eng_siege_tower','exact_chinese_attached_skin'),
 'ram3_candidate':('inherited-render-bodies-v2/run-003/decodes/english-battering-ram-exact','candidate_only'),
 'springald3_candidate':('inherited-render-bodies-v2/run-003/decodes/english-springald-exact','candidate_only'),
 'trebuchet4_counterweight_candidate':('inherited-render-bodies-v2/run-003/decodes/english-counterweight-trebuchet-exact','candidate_only'),
 'trebuchet4_traction_candidate':('inherited-render-bodies-v2/run-003/decodes/english-traction-trebuchet-exact','candidate_only'),
 'bow_recurve':('weapon-rig-supplement/decodes/bow_recurve','reached_attachment_stock_weapon'),
 'bow_cross':('weapon-rig-supplement/decodes/bow_cross','reached_attachment_stock_weapon'),
 'bow_arbalest':('weapon-rig-supplement/decodes/bow_arbalest','reached_attachment_stock_weapon'),
 'monk_staff3':('equipment-and-crew-models/monk_staff3','reached_monk_iii_staff'),
 'monk_staff4':('equipment-and-crew-models/monk_staff4','reached_monk_iv_staff'),
 'spear_basic':('equipment-and-crew-models/spear_basic','reached_spear_i_ii_attachment'),
 'spear_ji':('equipment-and-crew-models/spear_ji','reached_spear_iii_iv_charge_brace_attachment'),
 'combat_elephant3':('equipment-and-crew-models/combat_elephant3','exact_reachable'),
 'siege_cart3':('equipment-and-crew-models/siege_cart3','reached_trebuchet_cart_skin'),
}

def recolor(source,material,key,target):
    node=next((n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.name.lower()),None)
    if node is None:return None,0
    original=node.image
    image=original.copy();image.name='CCP060_'+key+'_'+material.name+'_albedo'
    width,height=image.size
    if width<8 or height<8:return None,0
    values=array('f',[0])*(width*height*4)
    try:original.pixels.foreach_get(values)
    except RuntimeError:return None,0
    role='rider' if 'rider' in material.name else 'mount' if key.startswith('combat') else 'siege'
    color=((.16,.32,.31) if role=='rider' else (.19,.29,.38) if role=='mount'
           else (.30,.24,.18) if material.name in ('page','roof') else (.25,.29,.24))
    rect=((.27,.34,1,1) if role=='rider' else (.55,.37,1,1) if role=='mount' else (0,0,1,1))
    changed=0
    for y in range(height):
        v=1-(y+.5)/height
        if not rect[1]<=v<=rect[3]:continue
        for x in range(width):
            u=(x+.5)/width
            if not rect[0]<=u<=rect[2]:continue
            i=(y*width+x)*4
            r,g,b,a=values[i:i+4]
            if a<.1 or max(r,g,b)-min(r,g,b)>.22:continue
            lum=.26*r+.66*g+.08*b
            if not .15<=lum<=.90:continue
            for channel in range(3):
                values[i+channel]=min(1,values[i+channel]*.28+color[channel]*lum*1.10)
            changed+=1
    if changed<100:return None,changed
    image.pixels.foreach_set(values);image.update()
    target.parent.mkdir(parents=True,exist_ok=True)
    image.filepath_raw=str(target);image.file_format='PNG';image.save()
    node.image=image
    return str(target),changed

def main(key):
    guard()
    revision='v3' if key.startswith('bow_') else 'v1'
    folder,status=DATA[key]
    manifest=next((ROOT/folder).rglob('decoded-static.json'))
    decoded=read(manifest);model=decoded['request']['logical_path']
    groups=decoded['geometry']['groups']
    target=owned(ART/'remaining_roster/nonhumanoid'/key/(key+'_'+revision+'.blend'))
    export=owned(EXPORT/'remaining_roster/nonhumanoid'/key/revision)
    receipt=owned(OUT/'qualification/remaining_roster/nonhumanoid'/key/revision/'authoring.json')
    if target.exists() or export.exists() or receipt.exists():raise FileExistsError('Preserve previous candidate')
    if bpy.data.filepath:raise RuntimeError('Use unsaved Blender process')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    import addon_utils
    mods=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(mods)!=1:raise RuntimeError('Garrison extension missing')
    addon_utils.enable(mods[0],default_set=False,persistent=False)
    _,imported=donor.import_donor(key,manifest,model,
                                 require_armature=not key.startswith(('monk_staff','spear_')))
    sources=[o for o in imported if o.type=='MESH' and o.data.polygons]
    if len(sources)!=len(groups):raise RuntimeError(f'Exact group count {len(sources)} != {len(groups)}')
    final=bpy.data.collections.new('CCP060_'+key+'_final')
    stock=bpy.data.collections.new('CCP060_'+key+'_stock')
    draft=bpy.data.collections.new('CCP060_'+key+'_draft_empty')
    for collection in (final,stock,draft):bpy.context.scene.collection.children.link(collection)
    remaining=set(sources);ordered=[]
    for group in groups:
        hits=[o for o in remaining if group['name'] in o.name and group['material'] in o.name
              and sum(len(p.vertices)-2 for p in o.data.polygons)==group['triangle_count']]
        if not hits and key.startswith(('monk_staff','spear_')):
            hits=[o for o in remaining if
                  sum(len(p.vertices)-2 for p in o.data.polygons)==group['triangle_count']]
        if not hits:raise RuntimeError('Cannot match donor group: '+str(group['name']))
        selected=sorted(hits,key=lambda o:o.name)[0]
        remaining.remove(selected);ordered.append(selected)
    material_cache={};material_rows=[]
    for index,(source,group) in enumerate(zip(ordered,groups)):
        native_mat=group['material']
        if native_mat not in material_cache:
            material=source.data.materials[0].copy()
            material.name='CCP060_'+key+'_'+native_mat
            path,changed=recolor(source,material,key,owned(export/(native_mat+'_albedo.png')))
            material_cache[native_mat]=(material,path,changed)
        material,path,changed=material_cache[native_mat]
        clone=source.copy();clone.data=source.data.copy()
        clone.name='CCP060_'+key+'_material_'+str(index)
        final.objects.link(clone)
        clone.data.materials.clear();clone.data.materials.append(material)
        for collection in tuple(source.users_collection):collection.objects.unlink(source)
        stock.objects.link(source)
        visible=(index==0 if key.startswith(('bow_','monk_staff','spear_')) else
                 native_mat.endswith('lod1') if key.startswith('combat')
                 else 'build_05' in group['name'] if key=='siege_tower3'
                 else 'build05' in group['name'] if 'build' in group['name']
                 else True)
        if not visible:
            clone.hide_set(True);clone.hide_render=True
            source.hide_set(True);source.hide_render=True
        material_rows.append({'group_index':index,'native_group':group['name'],
                              'native_material':native_mat,'effect':group.get('effect'),
                              'texture_slot':'albedoTexture','albedo_png':path,
                              'changed_pixels':changed,
                              'native_texture_unchanged':path is None,
                              'projection_mesh':source.name,
                              'preview_visible':visible})
    donor.set_comparison_layers(final,stock,draft)
    bpy.context.scene['ccp060_exact_donor_model']=model
    bpy.context.scene['ccp060_reachability']=status
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    preview=max((source for source,row in zip(ordered,material_rows) if row['preview_visible']),
                key=lambda source:len(source.data.polygons))
    review._review_folder_override=owned(OUT/'qualification/remaining_roster/nonhumanoid'/key/revision/'review')
    game=review.render_match(key,revision,preview,final)
    try:
        close=review.render_match(key,revision,preview,final,extra=True)
    except RuntimeError as error:
        if not key.startswith(('bow_','monk_staff','spear_')) or 'Native team-color preview controls missing' not in str(error):raise
        folder=review._review_folder_override
        close={'images':{name:{'path':str(folder/(name+'.png')),'sha256':sha(folder/(name+'.png'))}
                         for name in ('stock_close','finish_close')},
               'team_color_controls':'absent on standalone weapon material; native weapon attachment unchanged'}
    spec={'schema':'ccp-060-nonhumanoid-compatible-material-map/1',
          'exact_donor_model':model,'donor_manifest':str(manifest),
          'donor_manifest_sha256':sha(manifest),'donor_status':status,
          'native_group_count':len(groups),'groups':material_rows,
          'geometry_route':'exact stock geometry + per-material atlas only',
          'equipment_animations_and_crews':'native unchanged; no attachment override'}
    write(export/'material-map.json',spec)
    albedos=sorted({r['albedo_png'] for r in material_rows if r['albedo_png']})
    write(receipt,{'schema':'ccp-060-nonhumanoid-compatible-authoring/1',
                   'key':key,'status':status,'exact_donor_model':model,
                   'donor_manifest':str(manifest),'donor_manifest_sha256':sha(manifest),
                   'blend':str(target),'blend_sha256':sha(target),
                   'material_map':str(export/'material-map.json'),
                   'material_map_sha256':sha(export/'material-map.json'),
                   'albedos':[{'path':path,'sha256':sha(Path(path))} for path in albedos],
                   'review':{'game':game,'close':close},'native_cook':'not_run'})
    print(json.dumps({'key':key,'receipt':str(receipt),'materials':len(material_cache),
                      'albedos':len(albedos),'status':status}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--key',choices=tuple(DATA),required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.key)
