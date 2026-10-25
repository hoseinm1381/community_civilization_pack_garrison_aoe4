"""Create distinct one-corner native-normal repairs for saved 0.6.0 art."""
from __future__ import annotations
import argparse
import copy
import importlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART, EXPORT, OUT, guard, owned, read, sha, write
import representative_batch as review

DATA={
    'female3': {'tree':'civilian_roster','slug':'chi_villager_female_age03',
                'previous':'v2','revision':'v3','lod':3,
                'position':(0.0,.06561279,1.833984375)},
    'monk4': {'tree':'remaining_roster','slug':'monk4',
              'previous':'v1','revision':'v2','lod':2,
              'position':(.5673828,-.1815186,1.00390625)},
}


def main(family):
    guard()
    item=DATA[family]
    tree,slug,oldrev,rev=item['tree'],item['slug'],item['previous'],item['revision']
    source_receipt=read(OUT/'qualification'/tree/slug/oldrev/'export.json')
    source=Path(source_receipt.get('source_blend') or source_receipt['blend'])
    expected_sha=source_receipt.get('source_blend_sha256') or source_receipt['blend_sha256']
    if sha(source)!=expected_sha: raise RuntimeError('Pinned source blend changed')
    model=source_receipt.get('exact_native_body_model') or source_receipt['logical_model']
    old_export=EXPORT/tree/slug/oldrev
    new_export=owned(EXPORT/tree/slug/rev)
    new_blend=owned(ART/tree/slug/(slug+'_'+rev+'.blend'))
    new_receipt=owned(OUT/'qualification'/tree/slug/rev/'export.json')
    if new_export.exists() or new_blend.exists() or new_receipt.exists():
        raise FileExistsError('Preserve existing corrected candidate')
    bpy.ops.wm.open_mainfile(filepath=str(source))
    clones={n:bpy.data.objects[f'CCP060_{slug}_author_lod{n}'] for n in (1,2,3)}
    target=clones[item['lod']].data
    before_positions=[tuple(v.co) for v in target.vertices]
    before_triangles=[tuple(t.vertices) for t in target.loop_triangles]
    before_uv=[tuple(u.uv) for u in target.uv_layers.active.data]
    before_weights=[[(g.group,g.weight) for g in v.groups] for v in target.vertices]
    normals=[Vector(n.vector) for n in target.corner_normals]
    bad=[i for i,n in enumerate(normals) if n.length<.9]
    if len(bad)!=1: raise RuntimeError(f'Expected one nonunit corner: {bad}')
    point=target.vertices[target.loops[bad[0]].vertex_index].co
    if max(abs(a-b) for a,b in zip(point,item['position']))>.0002:
        raise RuntimeError(f'Unexpected corner point: {tuple(point)}')
    prior=normals[bad[0]].length
    normals[bad[0]].normalize()
    target.normals_split_custom_set([tuple(n) for n in normals]); target.update()
    after=target.corner_normals[bad[0]].vector.length
    if after<.98 or before_positions!=[tuple(v.co) for v in target.vertices] or before_triangles!=[tuple(t.vertices) for t in target.loop_triangles] or before_uv!=[tuple(u.uv) for u in target.uv_layers.active.data] or before_weights!=[[(g.group,g.weight) for g in v.groups] for v in target.vertices]:
        raise RuntimeError('Corner repair changed another geometry field')
    new_blend.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(new_blend),check_existing=False)
    new_export.mkdir(parents=True,exist_ok=False)
    for name in ('albedo.png','action.json'):
        (new_export/name).write_bytes((old_export/name).read_bytes())
    import addon_utils
    modules=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
    if len(modules)!=1: raise RuntimeError('Garrison extension missing')
    addon_utils.enable(modules[0],default_set=False,persistent=False)
    module=importlib.import_module(modules[0]+'.unit_export')
    rig=review.rig_of(clones[1]); records=module.skeleton_records(rig)
    copies=[]
    for n,obj in clones.items():
        clone=obj.copy();clone.data=obj.data.copy();clone.name=Path(model).stem+f'_lod{n}'
        bpy.context.scene.collection.objects.link(clone)
        for loop in clone.data.uv_layers.active.data:loop.uv.y=1-loop.uv.y
        for mat in clone.data.materials:
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image and 'albedo' in node.name.lower():
                    node.image.filepath_raw=str(new_export/'albedo.png')
        copies.append(clone)
    module.export_unit_model(rig,copies,new_export/'model.fbx',records,three_lods=False)
    old_snapshot=read(old_export/'authored-snapshot.json')
    snapshot=copy.deepcopy(old_snapshot)
    group=snapshot['geometry']['groups'][item['lod']-1]
    locations=[]
    for i,tri in enumerate(group['triangles']):
        for j,v in enumerate(tri):
            normal=group['corner_normals'][i][j]
            length=sum(x*x for x in normal)**.5
            if length>=.9:continue
            p=group['positions'][v]
            if max(abs(a-b) for a,b in zip(p,item['position']))>.0002:
                raise RuntimeError(f'Unexpected snapshot corner: {p}')
            group['corner_normals'][i][j]=[x/length for x in normal]
            locations.append((i,j))
    if len(locations)!=1:raise RuntimeError(f'Expected one snapshot repair: {locations}')
    write(new_export/'authored-snapshot.json',snapshot)
    if sha(new_export/'albedo.png')!=sha(old_export/'albedo.png') or sha(new_export/'action.json')!=sha(old_export/'action.json'):
        raise RuntimeError('Texture or action changed')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in new_export.iterdir() if p.is_file()}
    write(new_receipt,{'schema':'ccp-060-single-corner-normal-repair/v1','status':'three_lod_source_export_only',
        'family':family,'source_receipt':str(OUT/'qualification'/tree/slug/oldrev/'export.json'),
        'exact_native_body_model':model,'blend':str(new_blend),'blend_sha256':sha(new_blend),
        'folder':str(new_export),'files':files,
        'repair':{'lod':item['lod'],'corner':locations[0],'source_loop':bad[0],
                  'position':list(item['position']),'prior_length':prior,'repaired_length':after,
                  'snapshot_only_one_corner_changed':True},
        'authored_snapshot':{'path':str(new_export/'authored-snapshot.json'),
                             'sha256':sha(new_export/'authored-snapshot.json')},
        'native_cook':'not_run'})
    print(json.dumps({'receipt':str(new_receipt),'snapshot_sha256':sha(new_export/'authored-snapshot.json'),
                      'albedo_sha256':sha(new_export/'albedo.png'),'action_sha256':sha(new_export/'action.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--family',choices=tuple(DATA),required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.family)
