"""Archer II authoring-only finishing passes on pinned, stock-weighted v2c."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import sys
from collections import Counter

import bmesh
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, RECIPES, guard, owned, sha, write

SOURCE = ART / 'archer/archer-garment-v2c.blend'
SOURCE_SHA = '5a4a32ed8e55e19feb9f863cd10788daaa38e64c9e91a409ebf07786069e0754'
V3A = ART / 'archer/archer-garment-v3a.blend'
V3A_SHA = '5d210ab7b717e1a38be2dbefe64fe1a83dfb77944b2f8f55afeb676aa9b540d9'
V3B = ART / 'archer/archer-garment-v3b.blend'
V3C = ART / 'archer/archer-base-v3c.blend'
V3D = ART / 'archer/archer-base-v3d-quiver-restored.blend'
V3D_SHA = '65abf6b3669aeeb869e92b43194a82c15af70ef05a0301b3ed8a291a85158ab4'
V3E = ART / 'archer/archer-base-v3e-headcloth.blend'
V3E_SHA = 'b4de3dfe8b7e918c4c8ee5c332af2833b817afd578713fb87e44411c46932375'
V3F = ART / 'archer/archer-base-v3f-shoulders.blend'
V3F_SHA = '28b070a64e03a5f8fb2c1b0cbdc002755f704a7a64c2b40dd6b1b1e246d92b7f'
V3G = ART / 'archer/archer-base-v3g-fitted-shoulders.blend'
V3G_SHA = 'e358b3657fc590cd1652038cd824a223602b1be513020a13ac50a28dd416f662'
V3H = ART / 'archer/archer-base-v3h-closure.blend'
V3H_SHA = 'b80da3a1a518f804d19698a9fe6e4b5e7e1e76a72deb68a332330d9fccba2370'
V3I = ART / 'archer/archer-base-v3i-clean.blend'
V3B_SHA = 'db48771efbe47bc69f0e6ea5be5ed82d5f561711b430e14cfb93af56acc3009c'
BODY = 'CCP060 · Archer II weighted body · base'
PANTS = 'CCP060 · Archer v2 fitted upper trousers'
WRAP = 'CCP060 · Bound hair cloth headwrap'


def _components(mesh):
    adjacency = {v.index: set() for v in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen = set()
    for vertex in mesh.vertices:
        if vertex.index in seen:
            continue
        todo = [vertex.index]
        seen.add(vertex.index)
        part = set()
        while todo:
            current = todo.pop()
            part.add(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    todo.append(neighbor)
        yield part


def _weighted_body():
    body = bpy.data.objects[BODY]
    if body.type != 'MESH' or body.data.users != 1:
        raise RuntimeError('Expected one private weighted body mesh')
    return body


def _remove_components(body, predicate):
    mesh = body.data
    victims = []
    for part in _components(mesh):
        coords = [mesh.vertices[i].co for i in part]
        if predicate(part, coords):
            victims.append(part)
    indices = set().union(*victims) if victims else set()
    faces = [p.index for p in mesh.polygons if all(i in indices for i in p.vertices)]
    if any(any(i in indices for i in p.vertices) and p.index not in faces for p in mesh.polygons):
        raise RuntimeError('Selected part touches an unselected face')
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in sorted(indices)], context='VERTS')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return {'components': len(victims), 'vertices': len(indices), 'faces': len(faces)}


def garment_hem_and_cuffs():
    body = _weighted_body()
    if (len(body.data.vertices), len(body.data.polygons)) != (942, 1160):
        raise RuntimeError('Pinned v2c body topology changed')
    # The source robe cut left three *disconnected* strips beside the rear-left
    # vent. Their exact component sizes and bounds were measured in v2c.
    def old_flap(part, coords):
        low, high = min(v.z for v in coords), max(v.z for v in coords)
        return (len(part) in (5, 6, 10) and .79 <= low <= .97
                and .91 <= high <= 1.11 and max(v.x for v in coords) < -.03
                and min(v.x for v in coords) > -.34
                and min(v.y for v in coords) >= .015)
    removed = _remove_components(body, old_flap)
    if removed != {'components': 3, 'vertices': 21, 'faces': 16}:
        raise RuntimeError(f'Unexpected detached rear flap selection: {removed}')
    # The native lower trouser cuffs are two separate 40-vertex islands. Keep
    # their geometry, 48-bone binding and weights; remap only these cloth loops
    # to the same muted burgundy atlas region as the fitted upper trousers.
    mesh = body.data
    cuff_parts = []
    for part in _components(mesh):
        coords = [mesh.vertices[i].co for i in part]
        if len(part) == 40 and .302 < min(v.z for v in coords) < .305 and .525 < max(v.z for v in coords) < .531:
            cuff_parts.append(part)
    if len(cuff_parts) != 2 or sorted(1 if sum(mesh.vertices[i].co.x for i in p) > 0 else -1 for p in cuff_parts) != [-1, 1]:
        raise RuntimeError('Did not isolate exactly two native trouser cuffs')
    uv = mesh.uv_layers.active.data
    mapped = 0
    for poly in mesh.polygons:
        if not any(all(i in part for i in poly.vertices) for part in cuff_parts):
            continue
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv[li].uv = (.855 + .024 * math.atan2(co.y, abs(co.x) - .135) / math.pi,
                          .705 + .115 * (co.z - .303) / .226)
        mapped += 1
    if mapped != 112:
        raise RuntimeError(f'Unexpected native trouser cuff faces: {mapped}')
    mesh.update()
    return {'detached_rear_flap': removed, 'native_cuff_faces_uv_remapped': mapped,
            'cuff_material': 'original donor atlas and player-pattern mechanism',
            'body_faces': len(mesh.polygons)}


def stage_garment():
    guard()
    owned(V3A)
    receipt = owned(OUT/'qualification/archer-v3a-garment.json')
    if V3A.exists() or receipt.exists():
        raise FileExistsError('v3a output already exists')
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve() or sha(SOURCE) != SOURCE_SHA:
        raise RuntimeError('Open the pinned saved v2c source')
    detail = garment_hem_and_cuffs()
    bpy.ops.wm.save_as_mainfile(filepath=str(V3A), check_existing=False)
    write(receipt, {'schema':'ccp-060-archer-v3a/v1', 'status':'authoring_only',
                   'source':str(SOURCE), 'source_sha256':SOURCE_SHA,
                   'blend':str(V3A), 'blend_sha256':sha(V3A), 'garment':detail,
                   'next_gate':'actual six-side material renders and weighted-motion preview'})
    return detail


def _copy_rig_and_weights(obj, body, weights):
    obj.parent = body.parent
    obj.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    obj.matrix_world = body.matrix_world.copy()
    arm = obj.modifiers.new('AoE4 Armature', 'ARMATURE')
    arm.object = next(mod.object for mod in body.modifiers if mod.type == 'ARMATURE')
    for source in body.vertex_groups:
        obj.vertex_groups.new(name=source.name)
    for index, group_weights in enumerate(weights):
        selected = sorted(group_weights.items(), key=lambda item: item[1], reverse=True)[:4]
        total = sum(value for _, value in selected)
        if not selected or total <= 0:
            raise RuntimeError(f'Unweighted new cloth vertex {index}')
        for name, value in selected:
            obj.vertex_groups[name].add([index], value / total, 'REPLACE')


def _nearest_weights(body, coordinates):
    kd = KDTree(len(body.data.vertices))
    for v in body.data.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    out = []
    for xyz in coordinates:
        _co, index, _dist = kd.find(Vector(xyz))
        v = body.data.vertices[index]
        out.append({body.vertex_groups[g.group].name:g.weight for g in v.groups})
    return out


def remake_lower_tunic():
    body = _weighted_body()
    mesh = body.data
    if (len(mesh.vertices), len(mesh.polygons)) not in ((921,1144),(942,1160)):
        raise RuntimeError('Expected pinned v2c or diagnostic v3a body topology')
    # Exact 1.108 m ring measured on the original weighted donor. The center
    # front stock point is 1.103 m; top replacement lip overlaps by 8 mm.
    front = [(-.201,-.006),(-.184,-.091),(-.122,-.181),(0,-.208),
             (.115,-.180),(.190,-.106),(.202,-.009)]
    back = [(-.201,-.006),(-.178,.063),(-.090,.101),(0,.114),
            (.095,.109),(.171,.054),(.202,-.009)]
    rings = [(1.116,1.0,0.0),(1.020,1.028,0.0),(.930,1.060,.003),
             (.840,1.087,.028),(.760,1.110,.052)]
    vertices=[]; faces=[]; face_uv=[]
    for rear, profile in [(False,front),(True,back)]:
        offset=len(vertices)
        for z,scale,slit in rings:
            for i,(x,y) in enumerate(profile):
                yy=y*scale
                if i in (0,6):
                    yy += slit if rear else -slit
                vertices.append((x*scale,yy,z))
        for ri in range(len(rings)-1):
            for i in range(6):
                low=offset+ri*7+i; high=offset+(ri+1)*7+i
                quad=(low,low+1,high+1,high)
                if rear:
                    quad=tuple(reversed(quad))
                faces.append(quad)
                u0=.515+.140*i/6;u1=.515+.140*(i+1)/6
                v0=.145+.188*(rings[ri][0]-.760)/.356
                v1=.145+.188*(rings[ri+1][0]-.760)/.356
                uvquad=((u0,v0),(u1,v0),(u1,v1),(u0,v1))
                face_uv.append(tuple(reversed(uvquad)) if rear else uvquad)
    weights=_nearest_weights(body, vertices)
    garment=bpy.data.meshes.new('CCP060 Archer v3 split tunic mesh')
    garment.from_pydata(vertices,[],faces)
    garment.update()
    uv=garment.uv_layers.new(name=mesh.uv_layers.active.name)
    for poly,coords in zip(garment.polygons,face_uv):
        for li,point in zip(poly.loop_indices,coords):
            uv.data[li].uv=point
    garment.materials.append(mesh.materials[0])
    obj=bpy.data.objects.new('CCP060 · Archer v3 clean split tunic',garment)
    body.users_collection[0].objects.link(obj)
    _copy_rig_and_weights(obj,body,weights)
    # Delete only the central robe panels at/below the native waist seam.
    # Other disconnected parts (face, limbs, boots, quiver) cannot qualify.
    part=next(p for p in _components(mesh) if len(p)==184)
    doomed=[p.index for p in mesh.polygons if all(i in part for i in p.vertices)
            and max(mesh.vertices[i].co.z for i in p.vertices)<=1.110]
    if len(doomed)!=88:
        raise RuntimeError(f'Native lower robe face count changed: {len(doomed)}')
    bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.faces[i] for i in doomed],context='FACES')
    bm.to_mesh(mesh);bm.free();mesh.update()
    # No new skirt vertex uses more than four normalized stock bone groups.
    if any(abs(sum(g.weight for g in v.groups)-1)>1e-5 or len(v.groups)>4
           for v in garment.vertices):
        raise RuntimeError('New skirt skin weights failed normalization')
    return {'native_lower_robe_faces_replaced':len(doomed),
            'new_panel_vertices':len(garment.vertices),
            'new_panel_quads':len(garment.polygons),
            'vent_top_m':.930,'hem_m':.760,
            'top_lip_native_waist_overlap_m':.008,
            'source_uv_chart':'original owner-tinted robe chart u=.515..655 v=.145..333',
            'weighted_bones_per_vertex_max':4}


def stage_clean_split_tunic():
    guard();owned(V3B)
    receipt=owned(OUT/'qualification/archer-v3b-garment.json')
    if V3B.exists() or receipt.exists():
        raise FileExistsError('Preserve v3b output')
    if Path(bpy.data.filepath).resolve()!=V3A.resolve() or sha(V3A)!=V3A_SHA:
        raise RuntimeError('Open the pinned saved v3a checkpoint')
    detail=remake_lower_tunic()
    bpy.ops.wm.save_as_mainfile(filepath=str(V3B),check_existing=False)
    write(receipt,{'schema':'ccp-060-archer-v3b/v1','status':'authoring_only',
                   'source':str(V3A),'source_sha256':V3A_SHA,
                   'blend':str(V3B),'blend_sha256':sha(V3B),
                   'replacement':detail,'next_gate':'six-side material review and motion pose'})
    return detail


def stage_cloth_shader_contract():
    guard();owned(V3C)
    receipt=owned(OUT/'qualification/archer-v3c-cloth.json')
    if V3C.exists() or receipt.exists():
        raise FileExistsError('Preserve v3c output')
    if Path(bpy.data.filepath).resolve()!=V3B.resolve() or sha(V3B)!=V3B_SHA:
        raise RuntimeError('Open the pinned saved v3b checkpoint')
    body=bpy.data.objects[BODY].data
    coat=bpy.data.objects['CCP060 · Archer v3 clean split tunic'].data
    if 'ccp060_cloth_mask' not in body.attributes or 'ccp060_cloth_mask' in coat.attributes:
        raise RuntimeError('Unexpected preview cloth shader contract')
    attr=coat.attributes.new('ccp060_cloth_mask','FLOAT_COLOR','CORNER')
    for corner in attr.data:
        corner.color=(1.0,1.0,1.0,1.0)
    if len(attr.data)!=len(coat.loops) or any(abs(c.color[0]-1.0)>1e-5 for c in attr.data):
        raise RuntimeError('Preview cloth-mask corner assignment failed')
    bpy.ops.wm.save_as_mainfile(filepath=str(V3C),check_existing=False)
    write(receipt,{'schema':'ccp-060-archer-v3c/v1','status':'authoring_only',
                   'source':str(V3B),'source_sha256':V3B_SHA,
                   'blend':str(V3C),'blend_sha256':sha(V3C),
                   'preview_shader_attribute':'ccp060_cloth_mask',
                   'domain':'CORNER','cloth_corners':len(attr.data),'value':1.0,
                   'scope':'Blender preview tint only; native variant remains a separate gate'})
    return {'blend':str(V3C),'cloth_corners':len(attr.data)}


def _face_rows(body, excluded=None):
    mesh=body.data
    uv=mesh.uv_layers.active.data
    mask=mesh.attributes.get('ccp060_cloth_mask')
    rows=[]
    for face in mesh.polygons:
        if excluded is not None and all(index in excluded for index in face.vertices):
            continue
        corners=[]
        for li in face.loop_indices:
            vertex=mesh.vertices[mesh.loops[li].vertex_index]
            weights=sorted((body.vertex_groups[g.group].name,round(g.weight,7)) for g in vertex.groups)
            corners.append((tuple(round(x,7) for x in vertex.co),
                            tuple(round(x,7) for x in uv[li].uv),
                            tuple(weights),
                            tuple(round(x,7) for x in mask.data[li].color) if mask else None))
        rows.append(tuple(corners))
    return rows


def stage_restore_quiver():
    """Rebuild garment from v2c, preserving every native non-robe face."""
    guard();owned(V3D)
    receipt=owned(OUT/'qualification/archer-v3d-quiver-restored.json')
    if V3D.exists() or receipt.exists():
        raise FileExistsError('Preserve v3d output')
    if Path(bpy.data.filepath).resolve()!=SOURCE.resolve() or sha(SOURCE)!=SOURCE_SHA:
        raise RuntimeError('Open the pinned saved v2c checkpoint')
    body=_weighted_body()
    central=next(part for part in _components(body.data) if len(part)==184)
    before_rows=_face_rows(body,excluded=central)
    before={'faces':len(before_rows),'sha256':hashlib.sha256(
        json.dumps(sorted(before_rows,key=str),sort_keys=True).encode()).hexdigest()}
    detail=remake_lower_tunic()
    after_counts=Counter(_face_rows(body))
    missing=Counter(before_rows)-after_counts
    if missing or len(body.data.polygons)!=1160-detail['native_lower_robe_faces_replaced']:
        raise RuntimeError(f'Native non-robe faces changed; missing={sum(missing.values())}')
    coat=bpy.data.objects['CCP060 · Archer v3 clean split tunic'].data
    cloth=coat.attributes.new('ccp060_cloth_mask','FLOAT_COLOR','CORNER')
    for corner in cloth.data:
        corner.color=(1.0,1.0,1.0,1.0)
    bpy.ops.wm.save_as_mainfile(filepath=str(V3D),check_existing=False)
    write(receipt,{'schema':'ccp-060-archer-v3d/v1','status':'authoring_only',
                   'source':str(SOURCE),'source_sha256':SOURCE_SHA,
                   'blend':str(V3D),'blend_sha256':sha(V3D),
                   'native_non_robe_exact_preservation':before,
                   'quiver':'preserved from native v2c with geometry, UV, weights, mask',
                   'central_robe_replacement':detail,
                   'new_tunic_preview_cloth_mask_corners':len(cloth.data)})
    return {'blend':str(V3D),'native_non_robe_preserved':before,
            'central_robe_faces_replaced':detail['native_lower_robe_faces_replaced']}


def finish_headcloth():
    body=_weighted_body()
    obj=bpy.data.objects[WRAP]
    mesh=obj.data
    if len(mesh.vertices)!=128 or len(mesh.polygons)!=96:
        raise RuntimeError('Unexpected source wrap topology')
    if any(len(v.groups)>2 or abs(sum(g.weight for g in v.groups)-1)>1e-5
           or not any(obj.vertex_groups[g.group].name=='metarig_head' and g.weight>=.95
                      for g in v.groups) for v in mesh.vertices):
        raise RuntimeError('Headwrap no longer has measured head-dominant binding')
    for v in mesh.vertices:
        x,y,z=v.co
        ring=round((z-1.755)/(.035/3))
        if ring not in range(4):
            raise RuntimeError('Unexpected wrap ring')
        # Break the straight forehead bar with an asymmetric folded course.
        slope=.009*(x/.098)*max(0.15,(-y+.02)/.175)
        fold=(0,.0015,.0030,.0010)[ring]
        v.co.z=z+slope+fold
        radial=(1.0,1.012,.990,1.008)[ring]
        v.co.x*=radial
        v.co.y=-.034+(y+.034)*radial
    mesh.materials.clear();mesh.materials.append(body.data.materials[0])
    uv=mesh.uv_layers.active.data
    for loop in mesh.loops:
        vi=loop.vertex_index
        ring=vi//32
        angle=2*math.pi*(vi%32)/32
        uv[loop.index].uv=(.494+.009*math.sin(3*angle),.530+.024*ring/3)
    mesh.update()
    # Two tapered folded tails emerge from a shallow knot seated behind the
    # donor hair at y=.084 m. All new corners bind to the native head bone.
    verts=[(-.027,.081,1.775),(.027,.081,1.775),(.022,.111,1.755),
           (-.022,.111,1.755),(-.024,.102,1.747),(-.043,.118,1.690),
           (-.023,.113,1.702),(.024,.102,1.747),(.045,.119,1.707),
           (.022,.113,1.695)]
    faces=[(0,1,2,3),(4,5,6),(7,8,9)]
    knot_mesh=bpy.data.meshes.new('CCP060 Archer v3 folded headcloth knot')
    knot_mesh.from_pydata(verts,[],faces);knot_mesh.update()
    knot_uv=knot_mesh.uv_layers.new(name=body.data.uv_layers.active.name)
    for poly in knot_mesh.polygons:
        for li in poly.loop_indices:
            co=knot_mesh.vertices[knot_mesh.loops[li].vertex_index].co
            knot_uv.data[li].uv=(.494+.008*co.x/.05,.535+.015*(co.z-1.69)/.085)
    knot_mesh.materials.append(body.data.materials[0])
    knot=bpy.data.objects.new('CCP060 · Archer v3 rear headcloth knot',knot_mesh)
    body.users_collection[0].objects.link(knot)
    _copy_rig_and_weights(knot,body,[{'metarig_head':1.0} for _ in verts])
    return {'wrap_vertices':len(mesh.vertices),'wrap_faces':len(mesh.polygons),
            'head_dominant_source_weights_preserved':True,'brown_stock_uv':[[.485,.503],[.530,.554]],
            'knot_vertices':len(verts),'knot_faces':len(faces),
            'rear_knot_headcloth_overlap_m':.003}


def stage_headcloth():
    guard();owned(V3E)
    receipt=owned(OUT/'qualification/archer-v3e-headcloth.json')
    if V3E.exists() or receipt.exists():
        raise FileExistsError('Preserve v3e output')
    if Path(bpy.data.filepath).resolve()!=V3D.resolve() or sha(V3D)!=V3D_SHA:
        raise RuntimeError('Open pinned v3d with intact quiver')
    detail=finish_headcloth()
    bpy.ops.wm.save_as_mainfile(filepath=str(V3E),check_existing=False)
    write(receipt,{'schema':'ccp-060-archer-v3e/v1','status':'authoring_only',
                   'source':str(V3D),'source_sha256':V3D_SHA,
                   'blend':str(V3E),'blend_sha256':sha(V3E),
                   'headcloth':detail,'native_quiver':'unchanged from v3d'})
    return detail


def finish_cloth_shoulders():
    body=_weighted_body()
    mesh=body.data
    if len(mesh.polygons)!=1072:
        raise RuntimeError('Expected quiver-preserving v3d body')
    # Measured donor metal islands: four 14-vertex panels, x=.232..460,
    # y=-.090..126, z=1.306..1.532. The padded shell seats over them
    # without deleting donor source or changing arm weights/bones.
    rings=[(.220,1.425,.125,.118),(.280,1.420,.145,.135),
           (.360,1.405,.151,.145),(.440,1.385,.150,.145),
           (.490,1.365,.115,.118)]
    segments=12
    verts=[];faces=[];uvquads=[]
    for side in (-1,1):
        offset=len(verts)
        for x,center,ry,rz in rings:
            for j in range(segments):
                angle=2*math.pi*j/segments
                verts.append((side*x,.018+ry*math.sin(angle),center+rz*math.cos(angle)))
        for r in range(len(rings)-1):
            for j in range(segments):
                nxt=(j+1)%segments
                quad=(offset+r*segments+j,offset+(r+1)*segments+j,
                      offset+(r+1)*segments+nxt,offset+r*segments+nxt)
                if side<0:quad=tuple(reversed(quad))
                faces.append(quad)
                u0,u1=.515+.135*r/4,.515+.135*(r+1)/4
                v0,v1=.17+.15*j/segments,.17+.15*(j+1)/segments
                uvquad=((u0,v0),(u1,v0),(u1,v1),(u0,v1))
                uvquads.append(tuple(reversed(uvquad)) if side<0 else uvquad)
    weights=_nearest_weights(body,verts)
    shell=bpy.data.meshes.new('CCP060 Archer v3 padded cloth shoulder mesh')
    shell.from_pydata(verts,[],faces);shell.update()
    uv=shell.uv_layers.new(name=mesh.uv_layers.active.name)
    for poly,coords in zip(shell.polygons,uvquads):
        for li,point in zip(poly.loop_indices,coords):uv.data[li].uv=point
    shell.materials.append(mesh.materials[0])
    mask=shell.attributes.new('ccp060_cloth_mask','FLOAT_COLOR','CORNER')
    for corner in mask.data:corner.color=(1,1,1,1)
    obj=bpy.data.objects.new('CCP060 · Archer v3 cloth shoulders',shell)
    body.users_collection[0].objects.link(obj)
    _copy_rig_and_weights(obj,body,weights)
    # Check every original metal-island vertex lies within the nearest shell
    # section; required contact/occlusion, including both lower plate tips.
    donor=[]
    for part in _components(mesh):
        coords=[mesh.vertices[i].co for i in part]
        if len(part)==14 and 1.30<min(v.z for v in coords)<1.32 and max(v.z for v in coords)>1.50:
            donor.extend(coords)
    if len(donor)!=56:
        raise RuntimeError(f'Expected four native shoulder plate islands: {len(donor)} vertices')
    max_ratio=0
    for co in donor:
        x=abs(co.x)
        nearest=min(range(len(rings)),key=lambda i:abs(rings[i][0]-x))
        _x,zc,ry,rz=rings[nearest]
        ratio=((co.y-.018)/ry)**2+((co.z-zc)/rz)**2
        max_ratio=max(max_ratio,ratio)
    if max_ratio>1.12:
        raise RuntimeError(f'Cloth shell misses original metal vertices: {max_ratio:.3f}')
    return {'vertices':len(verts),'quads':len(faces),'triangles':len(faces)*2,
            'original_metal_components_retained':4,
            'max_donor_radial_ratio_nearest_section':round(max_ratio,4),
            'material':'stock donor atlas with preview cloth CORNER mask',
            'weighted_influences_per_vertex_max':4}


def stage_shoulders():
    guard();owned(V3F)
    receipt=owned(OUT/'qualification/archer-v3f-shoulders.json')
    if V3F.exists() or receipt.exists():raise FileExistsError('Preserve v3f output')
    if Path(bpy.data.filepath).resolve()!=V3E.resolve() or sha(V3E)!=V3E_SHA:
        raise RuntimeError('Open pinned v3e source')
    detail=finish_cloth_shoulders()
    bpy.ops.wm.save_as_mainfile(filepath=str(V3F),check_existing=False)
    write(receipt,{'schema':'ccp-060-archer-v3f/v1','status':'authoring_only',
                   'source':str(V3E),'source_sha256':V3E_SHA,
                   'blend':str(V3F),'blend_sha256':sha(V3F),
                   'cloth_shoulders':detail,'native_quiver':'unchanged from v3d'})
    return detail


def refine_native_shoulders_and_knot():
    body=_weighted_body();mesh=body.data
    shell=bpy.data.objects.get('CCP060 · Archer v3 cloth shoulders')
    if shell is None or len(shell.data.vertices)!=120:
        raise RuntimeError('Expected only the rejected owned bulky shell')
    bpy.data.objects.remove(shell,do_unlink=True)
    parts=[]
    for part in _components(mesh):
        cs=[mesh.vertices[i].co for i in part]
        if len(part)==14 and 1.30<min(v.z for v in cs)<1.32 and max(v.z for v in cs)>1.50:
            parts.append(part)
    if len(parts)!=4 or sum(map(len,parts))!=56:
        raise RuntimeError('Expected four measured native metal shoulder plate islands')
    selected=set().union(*parts)
    preserved=Counter(_face_rows(body,excluded=selected))
    for part in parts:
        cs=[mesh.vertices[i].co for i in part]
        yc=sum(v.y for v in cs)/len(cs)
        zc=sum(v.z for v in cs)/len(cs)
        for i in part:
            v=mesh.vertices[i]
            v.co.y=yc+.86*(v.co.y-yc)
            v.co.z=zc-.008+.73*(v.co.z-zc)
    attr=mesh.attributes['ccp060_cloth_mask']
    uv=mesh.uv_layers.active.data
    faces_changed=0
    for poly in mesh.polygons:
        if not all(i in selected for i in poly.vertices):continue
        faces_changed+=1
        for li in poly.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            uv[li].uv=(.515+.130*(abs(co.x)-.232)/.228,
                        .175+.125*(co.z-1.32)/.19)
            attr.data[li].color=(1,1,1,1)
    if not 50<=faces_changed<=100:
        raise RuntimeError(f'Unexpected native shoulder faces: {faces_changed}')
    mesh.update()
    if Counter(_face_rows(body,excluded=selected))!=preserved:
        raise RuntimeError('A non-armor body or quiver face changed')
    old=bpy.data.objects['CCP060 · Archer v3 rear headcloth knot']
    bpy.data.objects.remove(old,do_unlink=True)
    # Compact tied fold straddles the existing rear band at y=.084 m.
    verts=[(-.024,.078,1.754),(.024,.078,1.754),(.019,.078,1.786),
           (-.019,.078,1.786),(-.024,.099,1.754),(.024,.099,1.754),
           (.019,.099,1.786),(-.019,.099,1.786)]
    faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),
           (2,6,7,3),(3,7,4,0)]
    km=bpy.data.meshes.new('CCP060 Archer v3 seated headcloth knot mesh')
    km.from_pydata(verts,[],faces);km.update()
    kuv=km.uv_layers.new(name=mesh.uv_layers.active.name)
    for p in km.polygons:
        for li in p.loop_indices:
            c=km.vertices[km.loops[li].vertex_index].co
            kuv.data[li].uv=(.49+.012*(c.x+.024)/.048,
                             .53+.022*(c.z-1.754)/.032)
    km.materials.append(mesh.materials[0])
    knot=bpy.data.objects.new('CCP060 · Archer v3 rear headcloth knot',km)
    body.users_collection[0].objects.link(knot)
    _copy_rig_and_weights(knot,body,[{'metarig_head':1.0} for _ in verts])
    return {'native_padded_cloth_islands':4,'native_plate_vertices_preserved':56,
            'native_plate_faces_retextured':faces_changed,
            'plate_y_relief_scale':.86,'plate_z_relief_scale':.73,
            'native_non_armor_faces_exact_preservation':len(preserved),
            'new_shell_removed':True,
            'headcloth_knot_overlap_at_rear_band_m':.006,
            'floating_tails_removed':True}


def stage_fitted_shoulders():
    guard();owned(V3G)
    receipt=owned(OUT/'qualification/archer-v3g-fitted-shoulders.json')
    if V3G.exists() or receipt.exists():raise FileExistsError('Preserve v3g output')
    if Path(bpy.data.filepath).resolve()!=V3F.resolve() or sha(V3F)!=V3F_SHA:
        raise RuntimeError('Open pinned v3f diagnostic source')
    detail=refine_native_shoulders_and_knot()
    bpy.ops.wm.save_as_mainfile(filepath=str(V3G),check_existing=False)
    write(receipt,{'schema':'ccp-060-archer-v3g/v1','status':'authoring_only',
                   'source':str(V3F),'source_sha256':V3F_SHA,
                   'blend':str(V3G),'blend_sha256':sha(V3G),
                   'fitted_shoulders_and_knot':detail,
                   'native_quiver':'unchanged from v3d'})
    return detail


def _cloth_piece(body,name,vertices,faces,uvfaces):
    mesh=bpy.data.meshes.new(name+' mesh')
    mesh.from_pydata(vertices,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name=body.data.uv_layers.active.name)
    for poly,points in zip(mesh.polygons,uvfaces):
        for li,point in zip(poly.loop_indices,points):uv.data[li].uv=point
    mesh.materials.append(body.data.materials[0])
    obj=bpy.data.objects.new(name,mesh)
    body.users_collection[0].objects.link(obj)
    _copy_rig_and_weights(obj,body,_nearest_weights(body,vertices))
    return obj


def finish_closure_and_waist():
    body=_weighted_body();mesh=body.data
    components=list(_components(mesh))
    central=max((p for p in components if max(mesh.vertices[i].co.z for i in p)>1.67
                 and min(mesh.vertices[i].co.z for i in p)<1.17),key=len)
    if not 100<=len(central)<=200:
        raise RuntimeError(f'Unexpected central upper robe island: {len(central)}')
    untouched=Counter(_face_rows(body,excluded=central))
    high=[i for i in central if mesh.vertices[i].co.z>1.60]
    if not 12<=len(high)<=24:
        raise RuntimeError(f'Unexpected high collar vertices: {len(high)}')
    for i in high:
        v=mesh.vertices[i]
        v.co.z=1.60+(v.co.z-1.60)*.32
        v.co.x*=.92
        v.co.y=.015+(v.co.y-.015)*.92
    mesh.update()
    if Counter(_face_rows(body,excluded=central))!=untouched:
        raise RuntimeError('Collar reshaping changed a non-garment or quiver face')
    verts=[tuple(v.co) for v in mesh.vertices]
    polys=[tuple(p.vertices) for p in mesh.polygons if all(i in central for i in p.vertices)]
    bvh=BVHTree.FromPolygons(verts,polys,all_triangles=False)
    def front_y(x,z):
        hit,normal,_face,distance=bvh.ray_cast(Vector((x,-1.0,z)),Vector((0,1,0)),1.5)
        if hit is None or distance>.95:
            raise RuntimeError(f'No donor upper-tunic front contact at x={x}, z={z}')
        return hit.y-.004
    # Broad but light asymmetric facing, fitted to actual donor front surface.
    path=[(-.068,1.568,.018),(-.025,1.488,.024),(.018,1.408,.028),
          (.066,1.322,.031),(.103,1.245,.029),(.096,1.165,.023)]
    closure_verts=[];closure_faces=[];closure_uv=[]
    for x,z,width in path:
        for dx in (-width/2,width/2):
            xx=x+dx;closure_verts.append((xx,front_y(xx,z),z))
    for i in range(len(path)-1):
        closure_faces.append((2*i+2,2*i+3,2*i+1,2*i))
        t0,t1=i/(len(path)-1),(i+1)/(len(path)-1)
        closure_uv.append(((.489,.53+.025*t1),(.509,.53+.025*t1),
                           (.509,.53+.025*t0),(.489,.53+.025*t0)))
    closure=_cloth_piece(body,'CCP060 · Archer v3 front overlap',closure_verts,
                         closure_faces,closure_uv)
    # The native torso ray surface sets a 48-mm waist tie that covers the
    # previously abrupt skirt seam at z=1.108 m. Bow/quiver remain behind it.
    segments=16;belt_verts=[];belt_faces=[];belt_uv=[]
    for z in (1.099,1.157):
        sample_z=max(z,1.122)
        for i in range(segments):
            angle=2*math.pi*i/segments
            dx,dy=math.cos(angle),math.sin(angle)
            hit,_normal,_face,_distance=bvh.ray_cast(
                Vector((dx,-.02+dy,sample_z)),Vector((-dx,-dy,0)),1.5)
            if hit is None:
                raise RuntimeError(f'No native torso seat for tie angle {i}')
            belt_verts.append((hit.x+.004*dx,hit.y+.004*dy,z))
    for i in range(segments):
        j=(i+1)%segments
        belt_faces.append((i,j,segments+j,segments+i))
        a,b=i/segments,(i+1)/segments
        belt_uv.append(((.486+.021*a,.531),(.486+.021*b,.531),
                        (.486+.021*b,.553),(.486+.021*a,.553)))
    belt=_cloth_piece(body,'CCP060 · Archer v3 waist tie',belt_verts,belt_faces,belt_uv)
    # Belt knot and two short tails share the front waist anchor; no loose
    # pieces or external supports. 3 mm protrusion ensures surface contact.
    knot_x=-.095;knot_z=1.126;knot_y=front_y(knot_x,knot_z)-.006
    tieverts=[(knot_x-.018,knot_y,knot_z-.017),(knot_x+.018,knot_y,knot_z-.017),
              (knot_x+.018,knot_y,knot_z+.017),(knot_x-.018,knot_y,knot_z+.017),
              (knot_x-.013,knot_y,1.105),(knot_x-.028,knot_y-.003,1.006),
              (knot_x-.004,knot_y-.003,1.020),
              (knot_x+.012,knot_y,1.105),(knot_x+.019,knot_y-.004,1.041),
              (knot_x+.040,knot_y-.004,1.029)]
    tiefaces=[(0,1,2,3),(4,5,6),(7,8,9)]
    tieuv=[((.489,.53),(.509,.53),(.509,.552),(.489,.552)),
           ((.49,.54),(.5,.555),(.505,.548)),
           ((.49,.54),(.5,.555),(.505,.548))]
    tails=_cloth_piece(body,'CCP060 · Archer v3 waist tie knot',tieverts,tiefaces,tieuv)
    return {'collar_vertices_lowered':len(high),'collar_highest_m':round(max(mesh.vertices[i].co.z for i in high),4),
            'native_non_garment_faces_preserved':len(untouched),
            'front_overlap_quads':len(closure.data.polygons),
            'front_overlap_surface_offset_m':.004,
            'waist_tie_quads':len(belt.data.polygons),
            'waist_tie_bottom_m':1.099,'waist_tie_top_m':1.157,
            'waist_knot_faces':len(tails.data.polygons),
            'stock_brown_cloth_uv':[[.486,.509],[.530,.555]]}


def stage_closure():
    guard();owned(V3H)
    receipt=owned(OUT/'qualification/archer-v3h-closure.json')
    if V3H.exists() or receipt.exists():raise FileExistsError('Preserve v3h output')
    if Path(bpy.data.filepath).resolve()!=V3G.resolve() or sha(V3G)!=V3G_SHA:
        raise RuntimeError('Open pinned v3g source')
    detail=finish_closure_and_waist()
    bpy.ops.wm.save_as_mainfile(filepath=str(V3H),check_existing=False)
    write(receipt,{'schema':'ccp-060-archer-v3h/v1','status':'authoring_only',
                   'source':str(V3G),'source_sha256':V3G_SHA,
                   'blend':str(V3H),'blend_sha256':sha(V3H),
                   'collar_closure_waist':detail,
                   'native_quiver':'unchanged from v3d'})
    return detail


def stage_clean_representative_base():
    """Discard only the three fractured v3h additions; retain native equipment."""
    guard(); owned(V3I)
    receipt = owned(OUT/'qualification/archer-v3i-clean-base.json')
    if V3I.exists() or receipt.exists():
        raise FileExistsError('Preserve v3i output')
    if Path(bpy.data.filepath).resolve() != V3H.resolve() or sha(V3H) != V3H_SHA:
        raise RuntimeError('Open pinned v3h source')
    names = ('CCP060 · Archer v3 front overlap',
             'CCP060 · Archer v3 waist tie',
             'CCP060 · Archer v3 waist tie knot')
    objects = []
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != 'MESH':
            raise RuntimeError(f'Missing v3h-only mesh: {name}')
        objects.append(obj)
    native = _weighted_body()
    native_faces = len(native.data.polygons)
    native_vertices = len(native.data.vertices)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = native
    native.select_set(True)
    removed = {obj.name: {'vertices': len(obj.data.vertices),
                          'faces': len(obj.data.polygons)} for obj in objects}
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    if (len(native.data.polygons), len(native.data.vertices)) != (native_faces, native_vertices):
        raise RuntimeError('Native body changed during representative cleanup')
    bpy.ops.wm.save_as_mainfile(filepath=str(V3I), check_existing=False)
    write(receipt, {'schema': 'ccp-060-archer-v3i/v1', 'status': 'authoring_only',
                    'source': str(V3H), 'source_sha256': V3H_SHA,
                    'blend': str(V3I), 'blend_sha256': sha(V3I),
                    'removed_v3h_additions': removed,
                    'native_body_faces_preserved': native_faces,
                    'native_body_vertices_preserved': native_vertices,
                    'native_quiver': 'unchanged from v3d',
                    'style_approved': False, 'native_game': False})
    return removed
