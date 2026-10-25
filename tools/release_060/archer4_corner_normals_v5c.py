"""Copy Archer IV v5b to v5c with only four LOD2 unit-normal repairs."""
from __future__ import annotations

import copy
import importlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART, EXPORT, OUT, guard, owned, read, sha, write
import ranged_roster_060 as ranged
import representative_batch as review


def main():
    guard()
    old=read(OUT/'qualification/ranged_roster/archer4/v5b/export.json')
    source=Path(old['source_blend'])
    if sha(source)!=old['source_blend_sha256']:
        raise RuntimeError('Archer IV v5b source changed')
    target=owned(ART/'ranged_roster/archer4/archer4_v5c.blend')
    export=owned(EXPORT/'ranged_roster/archer4/v5c')
    receipt=owned(OUT/'qualification/ranged_roster/archer4/v5c/export.json')
    if target.exists() or export.exists() or receipt.exists():
        raise FileExistsError('Preserve any existing v5c candidate')
    bpy.ops.wm.open_mainfile(filepath=str(source))
    clones={n:bpy.data.objects[f'CCP060_archer4_author_lod{n}'] for n in (1,2,3)}
    mesh=clones[2].data
    old_tri=[tuple(t.vertices) for t in mesh.loop_triangles]
    old_pos=[tuple(v.co) for v in mesh.vertices]
    old_uv=[tuple(uv.uv) for uv in mesh.uv_layers.active.data]
    old_weights=[[(g.group,g.weight) for g in v.groups] for v in mesh.vertices]
    normals=[Vector(n.vector) for n in mesh.corner_normals]
    bad=[(i,len_n) for i,n in enumerate(normals) if (len_n:=n.length)<.9]
    if len(bad)!=4:
        raise RuntimeError(f'Expected exactly four degenerate corner normals; found {bad}')
    positions=[]
    for i,_ in bad:
        p=mesh.vertices[mesh.loops[i].vertex_index].co
        positions.append(tuple(round(float(x),6) for x in p))
    expected={(-.151489,-.152588,1.262695),(.117798,-.022736,1.785156)}
    if not all(any(max(abs(a-b) for a,b in zip(position,target))<.0002
                   for target in expected) for position in positions):
        raise RuntimeError(f'Unexpected normal repair positions: {positions}')
    for i,_ in bad: normals[i].normalize()
    mesh.normals_split_custom_set([tuple(n) for n in normals])
    mesh.update()
    repaired=[mesh.corner_normals[i].vector.length for i,_ in bad]
    if min(repaired)<.98:
        raise RuntimeError(f'Blender refused unit normals: {repaired}')
    if ([tuple(t.vertices) for t in mesh.loop_triangles]!=old_tri or
        [tuple(v.co) for v in mesh.vertices]!=old_pos or
        [tuple(uv.uv) for uv in mesh.uv_layers.active.data]!=old_uv or
        [[(g.group,g.weight) for g in v.groups] for v in mesh.vertices]!=old_weights):
        raise RuntimeError('Normal repair changed geometry, UV, or skin')
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    export.mkdir(parents=True,exist_ok=False)
    old_folder=Path(old['folder'])
    for name in ('albedo.png','action.json'):
        (export/name).write_bytes((old_folder/name).read_bytes())
    import addon_utils
    mods=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(mods)!=1: raise RuntimeError('Garrison extension missing')
    addon_utils.enable(mods[0],default_set=False,persistent=False)
    module=importlib.import_module(mods[0]+'.unit_export')
    rig=review.rig_of(clones[1])
    copies=[]
    for n,obj in clones.items():
        c=obj.copy(); c.data=obj.data.copy(); c.name=f'chi_ranged_bow_age04_lod{n}'
        bpy.context.scene.collection.objects.link(c)
        for loop in c.data.uv_layers.active.data: loop.uv.y=1-loop.uv.y
        for mat in c.data.materials:
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image and 'albedo' in node.name.casefold():
                    node.image.filepath_raw=str(export/'albedo.png')
        copies.append(c)
    bones=module.skeleton_records(rig)
    module.export_unit_model(rig,copies,export/'model.fbx',bones,three_lods=False)
    donor_manifest=Path(read(OUT/'qualification/ranged_roster/archer4/v5b/authoring.json')['decoded_manifest'])
    # Blender's custom-normal setter requantizes otherwise valid normals by
    # ~5e-5. Retain the pinned v5b snapshot byte values everywhere except the
    # four diagnosed corners; the FBX is exported from the corrected mesh.
    original_snapshot=read(old_folder/'authored-snapshot.json')
    corrected_snapshot=copy.deepcopy(original_snapshot)
    old_lod2=original_snapshot['geometry']['groups'][1]
    new_lod2=corrected_snapshot['geometry']['groups'][1]
    fixed=[]
    for tri_i,tri in enumerate(old_lod2['triangles']):
        for corner_i,vertex_i in enumerate(tri):
            normal=old_lod2['corner_normals'][tri_i][corner_i]
            length=sum(v*v for v in normal)**.5
            if length>=.9: continue
            position=old_lod2['positions'][vertex_i]
            if not any(max(abs(a-b) for a,b in zip(position,target))<.0002
                       for target in expected):
                raise RuntimeError(f'Unexpected snapshot normal position: {position}')
            new_lod2['corner_normals'][tri_i][corner_i]=[v/length for v in normal]
            fixed.append([tri_i,corner_i])
    if len(fixed)!=4: raise RuntimeError(f'Expected four snapshot repairs: {fixed}')
    write(export/'authored-snapshot.json',corrected_snapshot)
    snap={'path':str(export/'authored-snapshot.json'),
          'sha256':sha(export/'authored-snapshot.json'),
          'only_four_corner_normals_changed_from_v5b':True,
          'corner_locations':fixed}
    if sha(export/'albedo.png')!=sha(old_folder/'albedo.png') or sha(export/'action.json')!=sha(old_folder/'action.json'):
        raise RuntimeError('Copied albedo/action changed')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in export.iterdir() if p.is_file()}
    write(receipt,{'schema':'ccp-060-archer4-corner-normals-v5c/1','status':'three_lod_source_export_only',
        'source_v5b_receipt':str(OUT/'qualification/ranged_roster/archer4/v5b/export.json'),
        'source_v5b_blend_sha256':old['source_blend_sha256'],'blend':str(target),
        'blend_sha256':sha(target),'folder':str(export),'files':files,
        'repair':{'lod':2,'corner_indices':[i for i,_ in bad],
                  'corner_positions':positions,'prior_lengths':[n for _,n in bad],
                  'repaired_lengths':repaired,'only_normals_changed_in_source':True},
        'authored_snapshot':snap,'native_cook':'not_run'})
    print(json.dumps({'receipt':str(receipt),'repair_count':len(bad),
                      'albedo_sha256':sha(export/'albedo.png'),'fbx_sha256':sha(export/'model.fbx')}))


def reconcile_existing():
    guard()
    root=owned(EXPORT/'ranged_roster/archer4')
    old=read(root/'v5b/authored-snapshot.json')
    new=copy.deepcopy(old)
    lod=new['geometry']['groups'][1]
    expected={(-.151489,-.152588,1.262695),(.117798,-.022736,1.785156)}
    fixed=[]
    for i,tri in enumerate(lod['triangles']):
        for j,vindex in enumerate(tri):
            normal=lod['corner_normals'][i][j]
            length=sum(v*v for v in normal)**.5
            if length>=.9: continue
            position=lod['positions'][vindex]
            if not any(max(abs(a-b) for a,b in zip(position,target))<.0002
                       for target in expected):
                raise RuntimeError(f'Unexpected corner position {position}')
            lod['corner_normals'][i][j]=[v/length for v in normal]
            fixed.append([i,j])
    if len(fixed)!=4: raise RuntimeError(f'Expected four repairs: {fixed}')
    out=root/'v5c/authored-snapshot.json'
    if not out.exists(): raise FileNotFoundError(out)
    write(out,new)
    receipt_path=owned(OUT/'qualification/ranged_roster/archer4/v5c/export.json')
    receipt=read(receipt_path)
    receipt['files']['authored-snapshot.json']={'sha256':sha(out),'bytes':out.stat().st_size}
    receipt['authored_snapshot']={'path':str(out),'sha256':sha(out),
        'only_four_corner_normals_changed_from_v5b':True,'corner_locations':fixed}
    write(receipt_path,receipt)
    print(json.dumps({'receipt':str(receipt_path),'snapshot_sha256':sha(out),
                      'fixed':fixed}))


if __name__=='__main__':
    if '--reconcile-existing' in sys.argv:
        reconcile_existing()
    else:
        main()
