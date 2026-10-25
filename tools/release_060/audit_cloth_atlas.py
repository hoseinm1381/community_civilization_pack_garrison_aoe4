"""Read-only Blender UV coverage audit before an albedo-only variant bake.

Run on an explicitly pinned checkpoint and explicit body/garment object list.
The CORNER cloth preview can differ at the same UV; a single native albedo
cannot. Report shared texels before authoring a texture. No pixels are edited.
"""
from collections import defaultdict
from pathlib import Path
import bpy

from common import OUT, guard, owned, sha, write


def _pixels(points, size):
    (ax, ay), (bx, by), (cx, cy) = points
    den = (by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
    if abs(den) < 1e-12:
        return
    x0=max(0, int(min(ax,bx,cx)*size)-1)
    x1=min(size-1, int(max(ax,bx,cx)*size)+1)
    y0=max(0, int(min(ay,by,cy)*size)-1)
    y1=min(size-1, int(max(ay,by,cy)*size)+1)
    for y in range(y0,y1+1):
        py=(y+.5)/size
        for x in range(x0,x1+1):
            px=(x+.5)/size
            a=((by-cy)*(px-cx)+(cx-bx)*(py-cy))/den
            b=((cy-ay)*(px-cx)+(ax-cx)*(py-cy))/den
            if min(a,b,1-a-b)>=-1e-8:
                yield (x,y)


def audit(checkpoint, expected_sha256, names, label, size=256):
    guard()
    checkpoint=Path(checkpoint)
    if Path(bpy.data.filepath).resolve()!=checkpoint.resolve():
        raise RuntimeError('Open the requested saved checkpoint first')
    if sha(checkpoint)!=expected_sha256:
        raise RuntimeError('Checkpoint hash changed')
    target=owned(OUT/'qualification'/label/'cloth-atlas-audit.json')
    if target.exists():
        raise FileExistsError(target)
    if not names or len(names)!=len(set(names)):
        raise ValueError('Explicit unique object names required')
    coverage=defaultdict(lambda: defaultdict(set))
    rows=[]
    material_names=set()
    for name in names:
        obj=bpy.data.objects.get(name)
        if obj is None or obj.type!='MESH':
            raise RuntimeError(f'Missing requested mesh: {name}')
        mesh=obj.data
        uv=mesh.uv_layers.active
        if uv is None:
            raise RuntimeError(f'Missing active donor UVs: {name}')
        mask=mesh.attributes.get('ccp060_cloth_mask')
        if mask and (mask.domain!='CORNER' or mask.data_type!='FLOAT_COLOR'):
            raise RuntimeError(f'Unexpected cloth mask contract: {name}')
        mesh.calc_loop_triangles()
        counts=defaultdict(int)
        for tri in mesh.loop_triangles:
            material=obj.material_slots[tri.material_index].material
            if material is None:
                raise RuntimeError(f'Missing material: {name}')
            material_names.add(material.name)
            values=[mask.data[i].color[0] if mask else 0.0 for i in tri.loops]
            if any(abs(v-round(v))>1e-5 for v in values) or len(set(round(v) for v in values))!=1:
                raise RuntimeError(f'Non-binary or interpolated cloth triangle: {name}, {tri.polygon_index}')
            kind='cloth' if values[0]>.5 else 'unchanged'
            counts[kind]+=1
            points=[tuple(uv.data[i].uv) for i in tri.loops]
            if any(min(p)<0 or max(p)>1 for p in points):
                raise RuntimeError(f'Tiled UV requires an explicit wrap policy: {name}')
            for pixel in _pixels(points,size):
                # Material keyed: different atlases must never be conflated.
                coverage[(material.name,pixel)][kind].add(name)
        rows.append({'object':name,'triangles':dict(counts),'has_cloth_mask':bool(mask)})
    conflicts=[]
    bymaterial={}
    for material in sorted(material_names):
        entries=[(pixel,v) for (mat,pixel),v in coverage.items() if mat==material]
        both=[(p,v) for p,v in entries if len(v)==2]
        bymaterial[material]={'cloth_texels':sum('cloth' in v for _,v in entries),
                             'unchanged_texels':sum('unchanged' in v for _,v in entries),
                             'conflicting_texels':len(both)}
        for pixel,claims in both[:12]:
            conflicts.append({'material':material,'pixel_xy_blender_bottom_origin':pixel,
                              'claims':{k:sorted(v) for k,v in claims.items()}})
    result={'schema':'ccp-060-cloth-atlas-audit/v1','source':str(checkpoint),
            'source_sha256':expected_sha256,'sample_resolution':[size,size],
            'read_only_scene_and_pixels':True,'objects':rows,'materials':bymaterial,
            'conflict_examples':conflicts,
            'status':'uv_conflict_requires_remap_or_common_color' if conflicts else 'sampled_uv_coverage_no_conflict',
            'limits':'Pixel-center audit at source resolution; padding, mipmaps, subpixel overlap, native owner/skin masks and final bake/readback require separate checks. No native visual acceptance.'}
    write(target,result)
    return result
