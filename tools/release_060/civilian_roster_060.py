"""Author exact native Vietnamese villager bodies, one gender and age at a time.

This is a visual source export only. Tools, task models, actors and animations
remain owned by their existing native attachments and bindings.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from array import array
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART,EXPORT,OUT,guard,owned,read,sha,write
import pilot_author_blender as pilot
import ranged_roster_060 as ranged
import representative_batch as review

DONORS={
 ('male',1):('pilots/male_villager1/decoded/verified-e3063bb713d2082fd551/e5ce7670942848a6269a/decoded-static.json','51c16bb1a686dad4a1f5adf6f65b9af0e0d7ef579d0602de26051e08d3bd4628'),
 ('female',1):('pilots/female_villager1/decoded/verified-8964bb4bf22cdbe80064/64a1992b4502e6ae79ba/decoded-static.json','820ce2d611fe675f50e6537e26c87dcacde5bc879f02512159ecf31b81e1ef4e'),
 ('male',2):('inventory/complete-donors/decoded/chi_villager_male_age02/verified-29be5183975cbf24ec93/49455a5f1b77c19d2da6/decoded-static.json','13e442c4c91a475ee79d843f8b2714aca2a0822f4dcc38d179a000860c931f71'),
 ('female',2):('inventory/complete-donors/decoded/chi_villager_female_age02/verified-2f3db9a7394ff4cc6c84/9bf705b8f5f491faa722/decoded-static.json','51d057bfff05badec3006a0c86db92be64d88ff0b35c127144e09a02d102658c'),
 ('male',3):('inventory/complete-donors/decoded/chi_villager_male_age03/verified-91e88df94bdbdf7e98c6/90b32d096216ac801ac9/decoded-static.json','5a26fa78ece150e516c14925e6863c58fd973aea3e26eaf41b2dabfaacf49bb4'),
 ('female',3):('inventory/complete-donors/decoded/chi_villager_female_age03/verified-b40a19dc1fc1135c0478/4b08c727fc4817dc4b81/decoded-static.json','a3ebb993ed8f41ecab5ea692fe5807203971d37be4086f36c034e9fd8665cc8c'),
 ('male',4):('inventory/remaining-donors/run-004/decoded/018_chi_villager_male_age04/6fdeecb8b5aa7b258f1b/decoded-static.json','978c41476867a508bfc9e0537f396e1d7c9ee671c5daf0fc25ac2a4667a6e1e8'),
 ('female',4):('inventory/remaining-donors/run-004/decoded/019_chi_villager_female_age04/95cef01c8b1513ab37b8/decoded-static.json','3bcbea1fc429a76bc15e899405c2e149bc94b17bf5b18dd7197ebb7a626430d9'),
}
REVISION='v2'


def garment_component(mesh):
    parts=ranged.components(mesh)
    return max(parts,key=lambda part:sum(
        .72<mesh.vertices[i].co.z<1.50 and abs(mesh.vertices[i].co.x)<.47
        for i in part))


def native_albedo(clones,slug,age,target):
    nodes=[]
    for number in (1,2,3):
        found=[n for n in clones[number].data.materials[0].node_tree.nodes
               if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.name.casefold()]
        if len(found)!=1:raise RuntimeError(f'{slug} LOD{number} needs one native albedo')
        nodes.append(found[0])
    images=[n.image for n in nodes]
    if len({(image.size[0],image.size[1],image.filepath) for image in images})!=1:
        raise RuntimeError(f'{slug} native LOD atlases differ')
    image=images[0].copy();image.name=f'CCP060_{slug}_workcloth'
    width,height=image.size
    pixels=array('f',[0])*(width*height*4);image.pixels.foreach_get(pixels)
    covered=set()
    for obj in clones.values():
        mesh=obj.data;uv=mesh.uv_layers.active.data
        central=garment_component(mesh)
        for face in mesh.polygons:
            if (not all(index in central for index in face.vertices) or
                not .73<face.center.z<1.57 or abs(face.center.x)>.47):
                continue
            points=[tuple(uv[index].uv) for index in face.loop_indices]
            for k in range(1,len(points)-1):
                a,b,c=points[0],points[k],points[k+1]
                den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-9:continue
                for y in range(max(0,int(min(a[1],b[1],c[1])*height)-1),
                               min(height,int(max(a[1],b[1],c[1])*height)+2)):
                    py=(y+.5)/height
                    for x in range(max(0,int(min(a[0],b[0],c[0])*width)-1),
                                   min(width,int(max(a[0],b[0],c[0])*width)+2)):
                        px=(x+.5)/width
                        u=((b[1]-c[1])*(px-c[0])+(c[0]-b[0])*(py-c[1]))/den
                        v=((c[1]-a[1])*(px-c[0])+(a[0]-c[0])*(py-c[1]))/den
                        if u>=-1e-5 and v>=-1e-5 and u+v<=1+1e-5:
                            covered.add(y*width+x)
    # Progressive work-worn ochre and red-brown, with neutral fabric only.
    tint=((.54,.34,.16),(.49,.29,.14),(.43,.24,.13),(.38,.19,.11))[age-1]
    changed=0
    for pixel in covered:
        i=4*pixel;r,g,b,a=pixels[i:i+4]
        if a<.1 or max(r,g,b)-min(r,g,b)>.23:continue
        lum=r*.26+g*.66+b*.08
        if not .13<lum<.96:continue
        for channel,target_color in enumerate(tint):
            pixels[i+channel]=min(1,pixels[i+channel]*.20+target_color*lum*1.35)
        changed+=1
    if changed<100:raise RuntimeError(f'{slug} work cloth tint only {changed} pixels')
    image.pixels.foreach_set(pixels);image.update()
    target.parent.mkdir(parents=True,exist_ok=True)
    image.filepath_raw=str(target);image.file_format='PNG';image.save()
    for node in nodes:node.image=image
    return {'path':str(target),'sha256':sha(target),'cloth_uv_pixels':len(covered),
            'neutral_cloth_pixels_changed':changed,'work_color':tint}


def remodel(obj,slug,number):
    mesh=obj.data;central=garment_component(mesh)
    moved=0;maximum=0.0
    for index in central:
        vertex=mesh.vertices[index]
        x,y,z=vertex.co
        if not .72<z<1.50 or abs(x)>.47:continue
        hem=max(0,1-abs(z-.93)/.39)
        waist=max(0,1-abs(z-1.18)/.18)
        delta=.030*hem+.010*waist
        if abs(x)>.035:
            vertex.co.x+=delta*(1 if x>0 else -1)
            moved+=1;maximum=max(maximum,delta)
        if y<-.05:vertex.co.y-=.006*hem
    if moved<6 or maximum<.019:
        raise RuntimeError(f'{slug} LOD{number} garment shape unchanged: '
                           f'moved={moved} max={maximum:.4f} '
                           f'central_z={[min(mesh.vertices[i].co.z for i in central),max(mesh.vertices[i].co.z for i in central)]}')
    mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),
                          quad_method='BEAUTY',ngon_method='BEAUTY')
    bm.to_mesh(mesh);bm.free();mesh.update()
    if any(len(face.vertices)!=3 for face in mesh.polygons):
        raise RuntimeError(f'{slug} LOD{number} not triangulated')
    return {'garment_vertices_moved':moved,'maximum_delta_m':maximum,
            'native_uv':'unchanged','native_vertex_groups':'unchanged'}


def stage(gender,age):
    guard()
    slug=f'chi_villager_{gender}_age{age:02d}'
    manifest=OUT/DONORS[gender,age][0]
    if sha(manifest)!=DONORS[gender,age][1]:raise RuntimeError('Exact villager donor changed')
    original=read(manifest)
    groups=original['geometry']['groups']
    palette_bones=len(original['skeleton']['skin_palettes'][0]['bones'])
    expected_palette=58 if gender=='female' and age>=3 else 46
    if (len(original['skeleton']['bones'])!=73 or
        len(original['skeleton']['skin_palettes'])!=1 or
        palette_bones!=expected_palette or
        len(groups)!=3 or {g['material'] for g in groups}!={'lod1','lod2','lod3'}):
        raise RuntimeError(f'{slug} is not exact native 73/{expected_palette}/3 body')
    target=owned(ART/'civilian_roster'/slug/(slug+'_'+REVISION+'.blend'))
    export=owned(EXPORT/'civilian_roster'/slug/REVISION)
    receipt=owned(OUT/'qualification/civilian_roster'/slug/REVISION/'export.json')
    if any(path.exists() for path in (target,export,receipt)):
        raise FileExistsError(f'Preserve existing {slug} {REVISION}')
    if bpy.data.filepath:raise RuntimeError('Use a new unsaved Blender scene')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    import addon_utils
    modules=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(modules)!=1:raise RuntimeError('Installed Garrison extension absent')
    addon_utils.enable(modules[0],default_set=False,persistent=False)
    logical=f'art/civilizations/chinese/humans/{slug}/{slug}.rgm'
    root,imported=pilot.import_donor(slug,manifest,logical)
    lods={n:pilot.source_for_triangles(imported,
          next(g['triangle_count'] for g in groups if g['material']==f'lod{n}'))
          for n in (1,2,3)}
    rig=review.rig_of(lods[1])
    if len(rig.data.bones)!=73 or any(review.rig_of(lods[n])!=rig for n in (2,3)):
        raise RuntimeError('Villager exact native rig mismatch')
    for n,source in lods.items():source.data.materials[0].name=f'CCP060_{slug}_stock_lod{n}'
    final=bpy.data.collections.new('CCP060_'+slug+'_final')
    stock=bpy.data.collections.new('CCP060_'+slug+'_stock')
    draft=bpy.data.collections.new('CCP060_'+slug+'_draft_empty')
    for c in (final,stock,draft):bpy.context.scene.collection.children.link(c)
    produced={};details={}
    for n,source in lods.items():
        clone=source.copy();clone.data=source.data.copy()
        clone.name=f'CCP060_{slug}_author_lod{n}';final.objects.link(clone)
        material=source.data.materials[0].copy();material.name=f'lod{n}'
        clone.data.materials.clear();clone.data.materials.append(material)
        details[n]=remodel(clone,slug,n);produced[n]=clone
        for c in tuple(source.users_collection):c.objects.unlink(source)
        stock.objects.link(source)
        if n>1:
            source.hide_set(True);source.hide_render=True
            clone.hide_set(True);clone.hide_render=True
    atlas=native_albedo(produced,slug,age,owned(export/'albedo.png'))
    pilot.set_comparison_layers(final,stock,draft)
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    # Blender makes paths relative to the new .blend; the exporter resolves
    # source images against that file, so pin the owned atlas absolute again.
    for obj in produced.values():
        for node in obj.data.materials[0].node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image and 'albedo' in node.name.casefold():
                node.image.filepath_raw=str(export/'albedo.png')
    review._review_folder_override=owned(OUT/'qualification/civilian_roster'/slug/REVISION/'review')
    game=review.render_match(slug,REVISION,lods[1],final)
    close=review.render_match(slug,REVISION,lods[1],final,extra=True)
    module=importlib.import_module(modules[0]+'.unit_export')
    export.mkdir(parents=True,exist_ok=True)
    meshes=[]
    for n,obj in produced.items():
        copy=obj.copy();copy.data=obj.data.copy();copy.name=slug+f'_lod{n}'
        bpy.context.scene.collection.objects.link(copy)
        for loop in copy.data.uv_layers.active.data:loop.uv.y=1-loop.uv.y
        meshes.append(copy)
    bones=module.skeleton_records(rig)
    module.export_unit_model(rig,meshes,export/'model.fbx',bones,three_lods=False)
    snapshot=ranged.authored_snapshot(manifest,produced,export/'authored-snapshot.json')
    action=read(EXPORT/'villager-geometry-route'/gender/'stock-three-lod-control/action.json')
    if action.get('overrides') or action.get('attachments'):
        raise RuntimeError('Villager body source must leave task attachments native')
    action['bones']=bones;action['material_name']='lod1';action['textures']=['albedo']
    (export/'action.json').write_text(json.dumps(action,indent=2)+'\n',encoding='utf-8')
    payload=(export/'model.fbx').read_bytes()
    skins=payload.count(b'DeformerS\x04\x00\x00\x00Skin')
    clusters=payload.count(b'DeformerS\x07\x00\x00\x00Cluster')
    if skins!=3 or clusters<3*46:
        raise RuntimeError(f'{slug} lacks exact weighted three LOD source')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in export.iterdir() if p.is_file()}
    write(receipt,{'schema':'ccp-060-civilian-tier-export/v1',
                   'status':'three_lod_source_export_only','slug':slug,'gender':gender,
                   'age':age,'logical_model':logical,'donor_manifest':str(manifest),
                   'donor_manifest_sha256':sha(manifest),'blend':str(target),
                   'blend_sha256':sha(target),'folder':str(export),'files':files,
                   'native_rig_bones':73,'native_skin_palette_bones':palette_bones,
                   'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters,
                   'authored_snapshot':snapshot,'native_albedo_variant':atlas,
                   'lod_remodel':details,'review':{'game':game,'close':close},
                   'preexport_uv':'u unchanged; v := 1-v',
                   'native_tools_tasks_attachments':'unchanged',
                   'native_cook':'not_run'})
    return {'slug':slug,'blend':str(target),'export':str(export),
            'fbx_skin_nodes':skins,'fbx_cluster_nodes':clusters,'files':files}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--gender',choices=('male','female'),required=True)
    parser.add_argument('--age',type=int,choices=(1,2,3,4),required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    print(json.dumps(stage(args.gender,args.age),indent=2))
