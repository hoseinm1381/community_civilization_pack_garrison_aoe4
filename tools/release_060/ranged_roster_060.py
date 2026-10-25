"""Author and export one exact native ranged donor tier under the 0.6.0 lease.

This is geometry/authoring proof. Each call starts in a disposable unsaved scene,
keeps the tier's own 48-bone rig and all three weighted LODs, and writes a new
editable blend plus a separate three-LOD geometry source. No weapon model or
native gameplay binding is changed.
"""
from __future__ import annotations

import importlib
import json
import math
import sys
import copy
import bmesh
from array import array
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, EXPORT, OUT, RECIPES, guard, owned, read, sha, write
import pilot_author_blender as pilot
import representative_batch as review

RECIPE=RECIPES/'ranged-roster-060.json'
RECIPE_SHA='f70d71377461cd594e8588ce440680d69d71aa41aa6fb9bc68a65ddcbdcd977b'
ARCHER_CONTROL=EXPORT/'archer-matched-control/action.json'
MAX_SHOULDER={'archer2':.010,'archer3':.010,'archer4':.016,'crossbow3':.010,
              'crossbow4':.020,'handcannon4':.017}
HEM_EXPAND={'archer2':.026,'archer3':.026,'archer4':.028,'crossbow3':.023,
            'crossbow4':.032,'handcannon4':.030}
REVISION='v5b'


def cloth_albedo_variant(lods, clones, slug, target, include_all=False):
    """Tint pixels covered by the tier's own garment UVs; retain other maps."""
    sources=[]
    for number in (1,2,3):
        mat=clones[number].data.materials[0]
        node=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'
                   and n.image and 'albedo' in n.name.casefold()),None)
        if node is None:raise RuntimeError(f'LOD{number} has no native albedo node')
        sources.append(node)
    images=[node.image for node in sources]
    if len({(i.size[0],i.size[1],i.filepath) for i in images})!=1:
        raise RuntimeError('Native LODs do not share the exact same albedo atlas')
    image=images[0].copy();image.name=f'CCP060_{slug}_cloth_albedo_{REVISION}'
    w,h=image.size
    pixels=array('f',[0])*(w*h*4);image.pixels.foreach_get(pixels)
    covered=set()
    for number,mesh_obj in clones.items():
        mesh=mesh_obj.data;uv=mesh.uv_layers.active.data
        central=components(mesh)[0] if not include_all else set(range(len(mesh.vertices)))
        for face in mesh.polygons:
            if (not all(i in central for i in face.vertices) or
                not .78<face.center.z<(1.92 if include_all else 1.68) or
                abs(face.center.x)>.44):
                continue
            points=[tuple(uv[li].uv) for li in face.loop_indices]
            for k in range(1,len(points)-1):
                a,b,c=points[0],points[k],points[k+1]
                den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-9:continue
                x0=max(0,int(min(a[0],b[0],c[0])*w)-1)
                x1=min(w-1,int(max(a[0],b[0],c[0])*w)+1)
                y0=max(0,int(min(a[1],b[1],c[1])*h)-1)
                y1=min(h-1,int(max(a[1],b[1],c[1])*h)+1)
                for y in range(y0,y1+1):
                    py=(y+.5)/h
                    for x in range(x0,x1+1):
                        px=(x+.5)/w
                        u=((b[1]-c[1])*(px-c[0])+(c[0]-b[0])*(py-c[1]))/den
                        v=((c[1]-a[1])*(px-c[0])+(a[0]-c[0])*(py-c[1]))/den
                        if u>=-1e-5 and v>=-1e-5 and u+v<=1+1e-5:
                            covered.add(y*w+x)
    changed=0
    for pixel in covered:
        i=4*pixel;r,g,b,a=pixels[i:i+4]
        if a<.1 or max(r,g,b)-min(r,g,b)>.21:continue
        lum=r*.26+g*.66+b*.08
        if not .16<lum<.95:continue
        for channel,tint in enumerate((.13,.34,.32)):
            pixels[i+channel]=min(1,pixels[i+channel]*.25+tint*lum*1.6)
        changed+=1
    if changed<100:
        raise RuntimeError(f'Native cloth albedo pixel coverage too small: {changed}')
    image.pixels.foreach_set(pixels);image.update()
    target.parent.mkdir(parents=True,exist_ok=True)
    image.filepath_raw=str(target);image.file_format='PNG';image.save()
    for node in sources:node.image=image
    return {'shared_native_albedo':str(target),'shared_native_albedo_sha256':sha(target),
            'cloth_uv_covered_pixels':len(covered),'tinted_neutral_pixels':changed,
            'other_native_texture_nodes':'unchanged'}


def authored_snapshot(manifest, clones, target):
    """Pin the actual authored surfaces and donor skin for native readback."""
    original=read(manifest)
    result={'schema':'ccp-060-authored-ranged-snapshot/v1','status':'decoded',
            'source_manifest':str(manifest),'source_manifest_sha256':sha(manifest),
            'skeleton':original['skeleton'],
            'geometry':copy.deepcopy(original['geometry'])}
    groups=result['geometry']['groups']
    if len(groups)!=3:raise RuntimeError('Expected exactly three donor geometry groups')
    for number,obj in clones.items():
        mesh=obj.data;mesh.update()
        group=next((g for g in groups if g['material']==f'lod{number}'),None)
        if group is None:raise RuntimeError(f'Missing native group lod{number}')
        if len(mesh.vertices)!=len(group['positions']):
            palette={b['name']:b['palette_index'] for b in
                     original['skeleton']['skin_palettes'][0]['bones']}
            skin_indices=[];skin_weights=[]
            for vertex in mesh.vertices:
                influences=sorted(((palette[obj.vertex_groups[w.group].name],w.weight)
                                   for w in vertex.groups if w.weight>0),
                                  key=lambda pair:-pair[1])[:4]
                if not influences:
                    raise RuntimeError(f'LOD{number} unweighted authored vertex {vertex.index}')
                total=sum(weight for _,weight in influences)
                skin_indices.append([bone for bone,_ in influences]+[0]*(4-len(influences)))
                skin_weights.append([weight/total for _,weight in influences]+[0]*(4-len(influences)))
            group['skin_indices']=skin_indices;group['skin_weights']=skin_weights
            group['skin_indices_raw_lod']=skin_indices
        if len(mesh.vertices)!=len(group['skin_indices']):
            raise RuntimeError(f'LOD{number} authored skin count mismatch')
        triangles=[];corner_uvs=[];corner_normals=[]
        uv=mesh.uv_layers.active.data
        for tri in mesh.loop_triangles:
            chosen=tuple(tri.loops)
            triangles.append([mesh.loops[i].vertex_index for i in chosen])
            corner_uvs.append([list(uv[i].uv) for i in chosen])
            corner_normals.append([list(mesh.corner_normals[i].vector) for i in chosen])
        if len(triangles)!=group['triangle_count'] and len(mesh.vertices)==len(group['positions']):
            raise RuntimeError(f'Native LOD{number} triangle count changed')
        group['positions']=[list(v.co) for v in mesh.vertices]
        group['normals']=[list(v.normal) for v in mesh.vertices]
        group['triangles']=triangles
        group['corner_uvs']=corner_uvs
        group['corner_normals']=corner_normals
        group['uv_basis']='native_intended_before_export_preflip'
        group['vertex_count']=len(mesh.vertices)
        group['triangle_count']=len(triangles)
        group['material']=f'lod{number}'
        group['effect']='unit'
    write(target,result)
    return {'path':str(target),'sha256':sha(target),
            'lod_counts':[{'material':g['material'],'vertices':g['vertex_count'],
                           'triangles':g['triangle_count']} for g in groups]}


def components(mesh):
    adjacency=[set() for _ in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices
        adjacency[a].add(b);adjacency[b].add(a)
    visited=set();parts=[]
    for start in range(len(adjacency)):
        if start in visited:continue
        todo=[start];visited.add(start);part=set()
        while todo:
            vertex=todo.pop();part.add(vertex)
            for nxt in adjacency[vertex]:
                if nxt not in visited:visited.add(nxt);todo.append(nxt)
        parts.append(part)
    return sorted(parts,key=len,reverse=True)


def owner_chart(material):
    nodes=material.node_tree.nodes
    def image(tag):
        found=[n.image for n in nodes if n.type=='TEX_IMAGE' and n.image
               and tag in n.name.casefold()]
        if len(found)!=1:raise RuntimeError(f'Expected one {tag} stock texture')
        return found[0]
    pattern,albedo,metal=(image(key) for key in ('pattern','albedo','metal'))
    if pattern.size[:]!=albedo.size[:] or pattern.size[:]!=metal.size[:]:
        raise RuntimeError('Native material atlas maps have unequal dimensions')
    w,h=pattern.size[:]
    pp,aa,mm=pattern.pixels[:],albedo.pixels[:],metal.pixels[:]
    good=[]
    for y in range(h):
        row=[]
        for x in range(w):
            i=4*(y*w+x)
            rgb=aa[i:i+3]
            lum=rgb[0]*.26+rgb[1]*.66+rgb[2]*.08
            row.append(pp[i]>.82 and max(rgb)-min(rgb)<.16 and
                       .20<lum<.88 and mm[i]<.10)
        good.append(row)
    candidates=[]
    width,height=7,11
    for y in range(2,h-height-2):
        for x in range(2,w-width-2):
            if all(good[j][i] for j in range(y,y+height) for i in range(x,x+width)):
                u,v=(x+width/2)/w,(y+height/2)/h
                candidates.append(((u-.42)**2+(v-.36)**2,x,y))
    if not candidates:
        raise RuntimeError('No contiguous safe native owner-color fabric swatch')
    _,x,y=min(candidates)
    return (x/w,(x+width)/w,y/h,(y+height)/h),{
        'pixels':[x,y,width,height],
        'uv_bounds':[x/w,(x+width)/w,y/h,(y+height)/h],
        'pattern_red_minimum':min(pp[4*(j*w+i)] for j in range(y,y+height)
                                  for i in range(x,x+width)),
        'atlas_size':[w,h],
    }


def preview_material(source,number,slug):
    material=source.data.materials[0].copy()
    material.name=f'lod{number}'
    if material.name!=f'lod{number}':
        raise RuntimeError(f'Exact native material lod{number} name occupied')
    nodes,links=material.node_tree.nodes,material.node_tree.links
    bsdf=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bsdf is None or not bsdf.inputs['Base Color'].is_linked:
        raise RuntimeError('Imported native shader Base Color link absent')
    old=bsdf.inputs['Base Color'].links[0]
    origin=old.from_socket
    links.remove(old)
    attr=nodes.new('ShaderNodeAttribute')
    attr.attribute_name='ccp060_cloth_mask'
    tint=nodes.new('ShaderNodeMixRGB')
    tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.34,.52,.51,1)
    links.new(origin,tint.inputs[1])
    mix=nodes.new('ShaderNodeMixRGB')
    mix.blend_type='MIX'
    links.new(attr.outputs['Fac'],mix.inputs[0])
    links.new(origin,mix.inputs[1])
    links.new(tint.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],bsdf.inputs['Base Color'])
    return material


def remodel(source,clone,slug,number,owner_uv):
    mesh=clone.data
    parts=components(mesh)
    if not parts or len(parts[0])<15:
        raise RuntimeError(f'No continuous native torso in {slug} LOD{number}')
    central=parts[0]
    zs=[mesh.vertices[i].co.z for i in central]
    if min(zs)>.72 or max(zs)<1.55:
        raise RuntimeError(f'Largest component is not garment/anatomy: {slug} LOD{number}')
    changed=0;maximum=0.0
    for i in central:
        vertex=mesh.vertices[i]
        prior=vertex.co.copy()
        x,y,z=vertex.co
        hem=max(0,1-abs(z-1.00)/.45)
        shoulder=max(0,1-abs(z-1.48)/.16)
        if .75<z<1.64 and abs(x)<.39:
            delta=(HEM_EXPAND[slug]*hem+MAX_SHOULDER[slug]*shoulder)
            vertex.co.x+=math.copysign(delta*min(1,abs(x)/.09),x)
            if y<-.055:vertex.co.y-=.009*hem+.006*shoulder
            elif y>.055:vertex.co.y+=.006*hem
        distance=(vertex.co-prior).length
        if distance>1e-5:changed+=1;maximum=max(maximum,distance)
    if changed<6 or maximum<.012:
        raise RuntimeError(f'No meaningful donor garment shape change: {slug} LOD{number}')
    mesh.update()
    # v4 recolored whole donor triangles by centroid and left a sawtooth edge.
    # v5 keeps every native donor UV and seats one regular weighted cloth panel
    # on the continuous front garment, with straight authored boundaries.
    mask=mesh.color_attributes.new(name='ccp060_cloth_mask',
                                   type='FLOAT_COLOR',domain='CORNER')
    for face in mesh.polygons:
        cloth=(all(i in central for i in face.vertices) and
               .74<face.center.z<1.67)
        value=(1,1,1,1) if cloth else (0,0,0,1)
        for li in face.loop_indices:mask.data[li].color=value
    panel=owner_panel(clone,central,slug,number,owner_uv)
    return {'central_component_vertices':len(central),
            'changed_vertices':changed,'maximum_position_delta_m':maximum,
            'owner_panel':panel,
            'all_other_uv_corners_preserved':True,
            'material_preview_cloth_mask':'ccp060_cloth_mask'}


def owner_panel(body,central,slug,number,owner_uv):
    mesh=body.data
    vertices=[tuple(v.co) for v in mesh.vertices]
    polygons=[tuple(f.vertices) for f in mesh.polygons
              if all(i in central for i in f.vertices)]
    surface=BVHTree.FromPolygons(vertices,polygons,all_triangles=False)
    kd=KDTree(len(central))
    for index in central:kd.insert(mesh.vertices[index].co,index)
    kd.balance()
    cols,rows=5,4
    locations=[];weights=[];front_depths=[]
    for row in range(rows):
        t=row/(rows-1)
        z=.87+.31*t
        half_width=.18-.025*t
        for col in range(cols):
            s=col/(cols-1)
            x=(2*s-1)*half_width
            hit,normal,_,_=surface.ray_cast((x,-.8,z),(0,1,0),1.6)
            if hit is None or hit.y>-.03:
                raise RuntimeError(f'No front garment contact for {slug} LOD{number} at {x:.3f},{z:.3f}')
            point=Vector((x,hit.y-.009,z))
            locations.append(point);front_depths.append(hit.y)
            near=kd.find_n(hit,4)
            accum={}
            for _,index,distance in near:
                factor=1/max(.004,distance)
                for source_weight in mesh.vertices[index].groups:
                    name=body.vertex_groups[source_weight.group].name
                    accum[name]=accum.get(name,0)+factor*source_weight.weight
            total=sum(accum.values())
            if total<1e-6:raise RuntimeError('Owner panel contact has no donor skin')
            top=sorted(accum.items(),key=lambda pair:-pair[1])[:4]
            total=sum(value for _,value in top)
            weights.append({name:value/total for name,value in top})
    faces=[]
    for row in range(rows-1):
        for col in range(cols-1):
            a=row*cols+col;b=a+1;c=a+cols;d=c+1
            faces.extend(((a,c,d),(a,d,b)))
    panel_mesh=bpy.data.meshes.new(f'CCP060_{slug}_owner_panel_lod{number}')
    panel_mesh.from_pydata(locations,[],faces);panel_mesh.update()
    panel_mesh.materials.append(mesh.materials[0])
    uv=panel_mesh.uv_layers.new(name=mesh.uv_layers.active.name)
    u0,u1,v0,v1=owner_uv
    for face in panel_mesh.polygons:
        for li in face.loop_indices:
            index=panel_mesh.loops[li].vertex_index
            row,col=divmod(index,cols)
            uv.data[li].uv=(u0+(u1-u0)*col/(cols-1),
                            v0+(v1-v0)*row/(rows-1))
    panel_obj=bpy.data.objects.new(panel_mesh.name,panel_mesh)
    bpy.context.scene.collection.objects.link(panel_obj)
    for group in body.vertex_groups:panel_obj.vertex_groups.new(name=group.name)
    for index,values in enumerate(weights):
        for name,value in values.items():
            if value>1e-7:panel_obj.vertex_groups[name].add([index],value,'REPLACE')
    modifier=panel_obj.modifiers.new('Native armature','ARMATURE')
    modifier.object=next(m.object for m in body.modifiers if m.type=='ARMATURE')
    if bpy.context.object and bpy.context.object.mode!='OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True);panel_obj.select_set(True)
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.join()
    body.data.update()
    return {'vertices':len(locations),'triangles':len(faces),
            'contact_depth_min_max_m':[min(front_depths),max(front_depths)],
            'outward_offset_m':.009,'straight_panel_boundary':True,
            'all_vertices_weighted':all(bool(x) for x in weights)}


def stage(slug):
    guard()
    if sha(RECIPE)!=RECIPE_SHA:
        raise RuntimeError('Pinned ranged roster recipe changed')
    entries=[item for item in read(RECIPE)['tiers'] if item['slug']==slug]
    if len(entries)!=1 or slug=='archer2':
        raise RuntimeError('Use the pinned approved Archer II source directly')
    entry=entries[0]
    manifest=Path(entry['decoded_manifest'])
    if sha(manifest)!=entry['decoded_manifest_sha256']:
        raise RuntimeError('Exact decoded native donor changed')
    target=owned(Path(entry['authoring_target']).with_name(f'{slug}_{REVISION}.blend'))
    export=owned(EXPORT/'ranged_roster'/slug/REVISION)
    receipt=owned(OUT/'qualification'/'ranged_roster'/slug/REVISION/'authoring.json')
    export_receipt=owned(OUT/'qualification'/'ranged_roster'/slug/REVISION/'export.json')
    if any(path.exists() for path in (target,export,receipt,export_receipt)):
        raise FileExistsError(f'Preserve existing {slug} authoring/export')
    if bpy.data.filepath:
        raise RuntimeError('Start in a fresh unsaved Blender scene')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    import addon_utils
    modules=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(modules)!=1:raise RuntimeError('Expected one installed Garrison extension')
    addon_utils.enable(modules[0],default_set=False,persistent=False)
    root,imported=pilot.import_donor(slug,manifest,entry['exact_native_body_model'])
    lods={number:pilot.source_for_triangles(imported,
          item['triangles']) for number,item in enumerate(entry['native_lods'],1)}
    rig=review.rig_of(lods[1])
    if len(rig.data.bones)!=48 or any(review.rig_of(lods[n])!=rig for n in (2,3)):
        raise RuntimeError('Native ranged three-LOD armature mismatch')
    # Free exact native export material names while retaining stock reference.
    for number,source in lods.items():
        stock=source.data.materials[0]
        stock.name=f'CCP060_{slug}_stock_lod{number}'
    owner_bounds,owner_audit=owner_chart(lods[1].data.materials[0])
    final=bpy.data.collections.new('CCP060_'+slug+'_final')
    stock=bpy.data.collections.new('CCP060_'+slug+'_stock')
    draft=bpy.data.collections.new('CCP060_'+slug+'_draft_empty')
    for collection in (final,stock,draft):bpy.context.scene.collection.children.link(collection)
    final_lods={};details={}
    for number,source in lods.items():
        clone=source.copy();clone.data=source.data.copy()
        clone.name=f'CCP060_{slug}_author_lod{number}'
        final.objects.link(clone)
        material=preview_material(source,number,slug)
        clone.data.materials.clear();clone.data.materials.append(material)
        details[number]=remodel(source,clone,slug,number,owner_bounds)
        bm=bmesh.new();bm.from_mesh(clone.data)
        bmesh.ops.triangulate(bm,faces=list(bm.faces),
                              quad_method='BEAUTY',ngon_method='BEAUTY')
        bm.to_mesh(clone.data);bm.free();clone.data.update()
        if any(len(face.vertices)!=3 for face in clone.data.polygons):
            raise RuntimeError(f'{slug} LOD{number} not explicitly triangulated')
        final_lods[number]=clone
        for collection in tuple(source.users_collection):collection.objects.unlink(source)
        stock.objects.link(source)
        if number>1:
            source.hide_set(True);source.hide_render=True
            clone.hide_set(True);clone.hide_render=True
    atlas=cloth_albedo_variant(lods,final_lods,slug,
                                owned(export/'albedo.png'))
    pilot.set_comparison_layers(final,stock,draft)
    bpy.context.scene['ccp060_exact_stock_model']=entry['exact_native_body_model']
    bpy.context.scene['ccp060_native_weapon_owner']=entry['primary_weapon_attachment']
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    write(receipt,{'schema':'ccp-060-ranged-tier-authoring/v1',
                   'status':'authoring_only','slug':slug,'ebp':entry['ebp'],
                   'exact_stock_model':entry['exact_native_body_model'],
                   'decoded_manifest':str(manifest),'decoded_manifest_sha256':sha(manifest),
                   'blend':str(target),'blend_sha256':sha(target),
                   'native_rig_bones':48,'native_lods':entry['native_lods'],
                   'owner_chart':owner_audit,'lod_remodel':details,
                   'native_albedo_variant':atlas,
                   'native_weapon_unchanged':entry['primary_weapon_models']})
    review._review_folder_override=owned(OUT/'qualification'/'ranged_roster'/slug/REVISION/'review')
    game=review.render_match(slug,REVISION,lods[1],final)
    close=review.render_match(slug,REVISION,lods[1],final,extra=True)
    # Export geometry from copies so authoring UVs/render materials remain
    # editable in the saved blend. The installed exporter needs V preflipped.
    module=importlib.import_module(modules[0]+'.unit_export')
    export.mkdir(parents=True,exist_ok=True)
    export_meshes=[]
    for number,obj in final_lods.items():
        copied=obj.copy();copied.data=obj.data.copy()
        copied.name=Path(entry['exact_native_body_model']).stem+f'_lod{number}'
        bpy.context.scene.collection.objects.link(copied)
        for loop in copied.data.uv_layers.active.data:
            loop.uv.y=1-loop.uv.y
        copied.hide_render=True
        export_meshes.append(copied)
    records=module.skeleton_records(rig)
    module.export_unit_model(rig,export_meshes,export/'model.fbx',records,three_lods=False)
    payload=(export/'model.fbx').read_bytes()
    skin_nodes=payload.count(b'DeformerS\x04\x00\x00\x00Skin')
    cluster_nodes=payload.count(b'DeformerS\x07\x00\x00\x00Cluster')
    if skin_nodes<3 or cluster_nodes<3:
        raise RuntimeError(f'Exported FBX lacks weighted LODs: {skin_nodes=} {cluster_nodes=}')
    snapshot=authored_snapshot(manifest,final_lods,export/'authored-snapshot.json')
    action=read(ARCHER_CONTROL)
    if action.get('overrides') or action.get('attachments'):
        raise RuntimeError('Ranged action must not replace motions or attachments')
    action['material_name']='lod1';action['textures']=['albedo']
    (export/'action.json').write_text(json.dumps(action,indent=2)+'\n',encoding='utf-8')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in export.iterdir() if p.is_file()}
    write(export_receipt,{'schema':'ccp-060-ranged-tier-export/v1',
                          'status':'three_lod_source_export_only',
                          'slug':slug,'source_blend':str(target),
                          'source_blend_sha256':sha(target),
                          'folder':str(export),'files':files,
                          'mesh_names':[o.name for o in export_meshes],
                          'material_names':[o.data.materials[0].name for o in export_meshes],
                          'preexport_uv':'u unchanged; v := 1-v',
                          'native_albedo_variant':atlas,
                          'authored_snapshot':snapshot,
                          'source_blend':str(target),'source_blend_sha256':sha(target),
                          'fbx_sha256':sha(export/'model.fbx'),
                          'albedo_sha256':sha(export/'albedo.png'),
                          'action_sha256':sha(export/'action.json'),
                          'fbx_skin_nodes':skin_nodes,'fbx_cluster_nodes':cluster_nodes,
                          'expected_source_lods':entry['native_lods'],
                          'lod_remodel':details,
                          'authoring_review':{'game':game,'close_owner':close},
                          'native_cook':'not_run',
                          'native_weapon_attachments':'unchanged'})
    return {'slug':slug,'blend':str(target),'blend_sha256':sha(target),
            'export':str(export),'files':files}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--tier',required=True,
                        choices=('archer3','archer4','crossbow3','crossbow4','handcannon4'))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    print(json.dumps(stage(args.tier),indent=2))
