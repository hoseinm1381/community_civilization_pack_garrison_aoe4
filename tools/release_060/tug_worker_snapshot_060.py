"""Pin the 24-group tug source geometry, including exact crate corners/skin."""
from __future__ import annotations
import copy,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import EXPORT,OUT,guard,owned,read,sha,write

SOURCE=OUT/'qualification/remaining_roster/tug_worker/v6-tug24-cargo/export.json'
REV='v7-snapshot'


def main():
    guard()
    prior=read(SOURCE)
    blend=Path(prior['blend'])
    if sha(blend)!=prior['blend_sha256']:raise RuntimeError('Tug v6 source changed')
    native_path=Path(prior['donor_manifest'])
    if sha(native_path)!=prior['donor_manifest_sha256']:raise RuntimeError('Tug donor changed')
    native=read(native_path)
    out=owned(EXPORT/'remaining_roster/tug_worker'/REV/'authored-snapshot.json')
    receipt=owned(OUT/'qualification/remaining_roster/tug_worker'/REV/'snapshot.json')
    if out.exists() or receipt.exists():raise FileExistsError('Preserve existing tug snapshot')
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    result={'schema':'ccp-060-tug24-authored-snapshot/1','status':'source_geometry_only',
            'source_v6_receipt':str(SOURCE),'source_v6_receipt_sha256':sha(SOURCE),
            'source_blend':str(blend),'source_blend_sha256':sha(blend),
            'donor_manifest':str(native_path),'donor_manifest_sha256':sha(native_path),
            'skeleton':native['skeleton'],'geometry':copy.deepcopy(native['geometry'])}
    groups=result['geometry']['groups']
    if len(groups)!=24 or len(prior['export_group_order'])!=24:raise RuntimeError('Group count changed')
    changed=[]
    for index,row in enumerate(prior['export_group_order']):
        obj=bpy.data.objects.get(row['mesh'])
        if obj is None or obj.type!='MESH':raise RuntimeError(f'Missing saved export mesh {index}')
        group=groups[index]
        if row['material_name']!=group['material']:raise RuntimeError('Native material order changed')
        if index>=3:
            if row['export_triangles']!=group['triangle_count']:
                raise RuntimeError(f'Untouched group {index} triangle count changed')
            continue
        mesh=obj.data
        mesh.calc_loop_triangles()
        if len(mesh.loop_triangles)!=96 or {g.name for g in obj.vertex_groups}!={'chest_m'}:
            raise RuntimeError(f'Basket {index} source is not 96tri chest_m')
        triangles=[];corner_uvs=[];corner_normals=[]
        uv=mesh.uv_layers.active.data
        vertex_uv=[None]*len(mesh.vertices)
        for tri in mesh.loop_triangles:
            loops=list(tri.loops)
            triangles.append([mesh.loops[i].vertex_index for i in loops])
            one=[];norm=[]
            for loop_index in loops:
                vertex=mesh.loops[loop_index].vertex_index
                values=[float(uv[loop_index].uv.x),float(1-uv[loop_index].uv.y)]
                one.append(values)
                norm.append(list(mesh.corner_normals[loop_index].vector))
                if vertex_uv[vertex] is None:vertex_uv[vertex]=values
            corner_uvs.append(one);corner_normals.append(norm)
        if any(value is None for value in vertex_uv):raise RuntimeError('Unmapped cargo UV vertex')
        group['positions']=[list(v.co) for v in mesh.vertices]
        group['normals']=[list(v.normal) for v in mesh.vertices]
        group['uv_layers']={'UVMap':vertex_uv}
        group['triangles']=triangles
        group['corner_uvs']=corner_uvs
        group['corner_normals']=corner_normals
        group['skin_indices']=[[1,0,0,0] for _ in mesh.vertices]
        group['skin_weights']=[[1.0,0.0,0.0,0.0] for _ in mesh.vertices]
        group['skin_indices_raw_lod']=group['skin_indices']
        group['vertex_count']=len(mesh.vertices)
        group['triangle_count']=len(triangles)
        group['uv_basis']='native_intended_before_export_preflip'
        group['authored_change']='approved_open_crate_weighted_to_chest_m'
        changed.append({'group_index':index,'vertices':len(mesh.vertices),
                        'triangles':len(triangles),'corner_count':len(corner_uvs)*3,
                        'material':group['material'],'bone':'chest_m'})
    out.parent.mkdir(parents=True,exist_ok=True)
    write(out,result)
    write(receipt,{'schema':'ccp-060-tug24-snapshot-receipt/1',
        'source_v6_receipt':str(SOURCE),'source_v6_receipt_sha256':sha(SOURCE),
        'source_v6_fbx_sha256':prior['files']['model.fbx']['sha256'],
        'snapshot':str(out),'snapshot_sha256':sha(out),'changed_groups':changed,
        'unchanged_groups':'native decoded manifest groups 3-23 byte-equivalent in snapshot',
        'native_cook':'not_run'})
    print(json.dumps({'receipt':str(receipt),'snapshot_sha256':sha(out),
                      'changed_groups':changed}))


if __name__=='__main__':main()
