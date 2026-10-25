"""Deterministic visual sample on the exact decoded Chinese Archer II donor.

Run inside the claimed Blender 5.2 Garrison session after importing the donor.
This creates only CCP060-named sample data. It keeps the stock reference, rig,
body proportions, hands, head, quiver, LODs and native weight source intact.
The Rattan collection is a separate optional overlay for future native gating.
"""
from __future__ import annotations

import bpy
from mathutils import Vector, kdtree

SCENE = bpy.context.scene
REFERENCE = bpy.data.collections['CCP060_Archer_Reference']
DONOR = next(o for o in SCENE.objects if o.type == 'MESH' and 'lod1' in o.name
             and 'chi_ranged_bow_age02' in o.name and not o.name.startswith('CCP060'))
RIG = next(m.object for m in DONOR.modifiers if m.type == 'ARMATURE')
ROOT = DONOR.parent
SAMPLE_NAME = 'CCP060_Archer_Sample'


def color(name, rgb, roughness=0.8):
    old = bpy.data.materials.get(name)
    if old is not None:
        return old
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


MATS = {
    'cloth': color('CCP060 · Indigo worn cotton', (0.105, 0.160, 0.180)),
    'hems': color('CCP060 · Warm charcoal textile', (0.105, 0.090, 0.065)),
    'sash': color('CCP060 · Muted owner-colour placeholder', (0.38, 0.23, 0.15)),
    'rattan_a': color('CCP060 · Rattan mid reed', (0.43, 0.34, 0.21)),
    'rattan_b': color('CCP060 · Rattan dark reed', (0.39, 0.30, 0.18)),
    'rattan_edge': color('CCP060 · Rattan edge binding', (0.23, 0.18, 0.11)),
}


if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
# The MCP bridge retains the active-object RNA pointer while executing. Make
# the preserved native root active before deleting a previous sample; deleting
# the active duplicate otherwise reports a stale StructRNA after successful work.
for selected in list(bpy.context.selected_objects):
    selected.select_set(False)
ROOT.select_set(True)
bpy.context.view_layer.objects.active = ROOT
prior = bpy.data.collections.get(SAMPLE_NAME)
if prior:
    for o in list(prior.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for child in list(prior.children):
        bpy.data.collections.remove(child)
    bpy.data.collections.remove(prior)
sample = bpy.data.collections.new(SAMPLE_NAME)
SCENE.collection.children.link(sample)
base_col = bpy.data.collections.new('CCP060 · Base archer')
upgrade_col = bpy.data.collections.new('CCP060 · Rattan upgrade only')
sample.children.link(base_col)
sample.children.link(upgrade_col)

# Skin weights on newly fitted fabric come from the nearest real stock mesh
# vertex. This avoids an arbitrary new armature or unweighted body substitute.
tree = kdtree.KDTree(len(DONOR.data.vertices))
for v in DONOR.data.vertices:
    tree.insert(v.co, v.index)
tree.balance()


def fitted(x, z, side='front', gap=0.012):
    origin = Vector((x, -1 if side == 'front' else 1, z))
    direction = Vector((0, 1 if side == 'front' else -1, 0))
    hit, location, normal, face = DONOR.ray_cast(origin, direction)
    if not hit:
        raise ValueError(f'No donor surface at {side} x={x:.3f} z={z:.3f}')
    return (x, location.y + (-gap if side == 'front' else gap), z)


def weighted_mesh(name, vertices, faces, material_ids, materials, collection, uv_scale=(1, 1)):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for m in materials:
        mesh.materials.append(m)
    for poly, mid in zip(mesh.polygons, material_ids):
        poly.material_index = mid
    uv = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            p = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = ((p.x + 0.6) * uv_scale[0], p.z * uv_scale[1])
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = ROOT
    for v in mesh.vertices:
        _, nearest, _ = tree.find(v.co)
        source = DONOR.data.vertices[nearest]
        weights = sorted(((DONOR.vertex_groups[g.group].name, g.weight) for g in source.groups),
                         key=lambda x: -x[1])[:4]
        total = sum(w for _, w in weights)
        for bone, weight in weights:
            obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
            obj.vertex_groups[bone].add([v.index], weight / total, 'REPLACE')
    mod = obj.modifiers.new('CCP060 native archer armature', 'ARMATURE')
    mod.object = RIG
    return obj


# Base: retain the weighted native silhouette/anatomy and all albedo, normal,
# roughness, skin, owner-colour and quiver texture nodes. Tint only cloth via a
# corner-domain mask instead of replacing native fabric detail with flat paint.
body = DONOR.copy()
body.data = DONOR.data.copy()
body.name = 'CCP060 · Archer II weighted body · base'
base_col.objects.link(body)
native = DONOR.data.materials[0]
tinted = native.copy()
tinted.name = 'CCP060 · Donor cloth-tint preserving native maps'
body.data.materials[0] = tinted
mask = body.data.color_attributes.new(name='ccp060_cloth_mask',type='FLOAT_COLOR',domain='CORNER')
for face in body.data.polygons:
    p = face.center
    cloth = (0.40 < p.z < 1.55 and
             not (abs(p.x) > 0.40 and p.z < 1.30) and
             not (p.y > 0.18 and p.x > 0.04))
    for li in face.loop_indices:
        mask.data[li].color = (1,1,1,1) if cloth else (0,0,0,1)
nodes, links = tinted.node_tree.nodes, tinted.node_tree.links
surface = next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
old_link = next(l for l in links if l.to_node==surface and l.to_socket.name=='Base Color')
original_colour = old_link.from_socket
links.remove(old_link)
attribute=nodes.new('ShaderNodeAttribute');attribute.name='CCP060 cloth region';attribute.attribute_name=mask.name
multiply=nodes.new('ShaderNodeMixRGB');multiply.name='CCP060 subdued indigo';multiply.blend_type='MULTIPLY'
multiply.inputs[0].default_value=1.0
multiply.inputs[2].default_value=(.34,.50,.52,1)
links.new(original_colour,multiply.inputs[1])
mix=nodes.new('ShaderNodeMixRGB');mix.name='CCP060 preserve exposed skin';mix.blend_type='MIX'
links.new(attribute.outputs['Fac'],mix.inputs[0]);links.new(original_colour,mix.inputs[1])
links.new(multiply.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],surface.inputs['Base Color'])
DONOR.hide_set(True)


def panel(name, x0, x1, z0, z1, nx, nz, side, gap, materials, col, alternating=False):
    verts = [fitted(x0 + (x1-x0)*ix/nx, z0 + (z1-z0)*iz/nz, side, gap)
             for iz in range(nz+1) for ix in range(nx+1)]
    faces = []
    mids = []
    for iz in range(nz):
        for ix in range(nx):
            a = iz*(nx+1)+ix
            faces.append((a,a+1,a+nx+2,a+nx+1))
            mids.append((ix+iz)%len(materials) if alternating else 0)
    return weighted_mesh(name,verts,faces,mids,materials,col,(3,3))


import math
def wrapped_surface(name, bottom, top, segments, rows, material, collection,
                    gap=0.012, flare=0.0):
    verts=[]
    for row in range(rows+1):
        t=row/rows
        for segment in range(segments):
            theta=math.tau*segment/segments
            # A slightly uneven hem reads as overlapping cloth at the knee.
            hem=bottom + (.018*math.sin(theta*2)) if flare else bottom
            z=hem+(top-hem)*t
            direction=Vector((math.cos(theta),math.sin(theta),0))
            hit,place,_,_=DONOR.ray_cast(Vector((0,0,z)),direction)
            if not hit: raise ValueError(f'Native wrap missed: z={z} angle={theta}')
            radial=gap + flare*(1-t)
            verts.append(tuple(place+direction*radial))
    faces=[(r*segments+i,r*segments+(i+1)%segments,
            (r+1)*segments+(i+1)%segments,(r+1)*segments+i)
           for r in range(rows) for i in range(segments)]
    return weighted_mesh(name,verts,faces,[0]*len(faces),[material],collection,(3,3))


wrapped_surface('CCP060 · Continuous tied waist sash',1.025,1.105,32,3,
                MATS['sash'],base_col,.022)
wrapped_surface('CCP060 · Short overlapping lower tunic',.79,1.005,32,8,
                MATS['hems'],base_col,.016,.028)
wrapped_surface('CCP060 · Bound hair cloth headwrap',1.755,1.790,32,3,
                MATS['sash'],base_col,.006)

# One torso-conforming vest surface continues through both side seams. The
# interlaced strips below sit 5-8 mm above it; their low contrast and narrow
# aspect ratio make this a woven garment instead of a checkerboard decal.
wrapped_surface('CCP060 · Continuous torso rattan vest',1.14,1.445,32,12,
                MATS['rattan_a'],upgrade_col,.015)

# Bound reed strips give the checker weave actual shallow overlap and a clear
# edge at game distance. Each strip follows the decoded chest surface.
for i,x in enumerate((-.112,-.045,.022,.089)):
    panel(f'CCP060 · Raised vertical reed {i+1}',x-.004,x+.004,1.13,1.44,1,16,
          'front',.019,[MATS['rattan_a']],upgrade_col)
for i,z in enumerate((1.16,1.245,1.33,1.415)):
    panel(f'CCP060 · Cross reed {i+1}',-.145,.145,z-.004,z+.004,16,1,
          'front',.022,[MATS['rattan_b']],upgrade_col)
for i,x in enumerate((-.15,.15)):
    panel(f'CCP060 · Vest edge {i+1}',x-.003,x+.003,1.125,1.445,1,14,
          'front',.024,[MATS['rattan_edge']],upgrade_col)

# Separate diagonal rattan back shield: shoulder-blades to belt, clear of the
# right-side quiver. Rounded rectangular silhouette and shallow convex face.
cx, zc, y0 = -.20, 1.34, .158
shield_w, shield_h = .11, .18
nx, nz = 12, 16
verts=[]
for iz in range(nz+1):
    z = zc-shield_h + 2*shield_h*iz/nz
    for ix in range(nx+1):
        x = cx-shield_w + 2*shield_w*ix/nx
        verts.append((x,y0+.015*(1-((x-cx)/shield_w)**2)*(1-((z-zc)/shield_h)**2),z))
faces=[]; mids=[]
for iz in range(nz):
    for ix in range(nx):
        xn=abs((ix+.5-nx/2)/(nx/2)); zn=abs((iz+.5-nz/2)/(nz/2))
        if xn**4+zn**4>1.03: continue
        a=iz*(nx+1)+ix
        faces.append((a,a+1,a+nx+2,a+nx+1))
        mids.append(0)
weighted_mesh('CCP060 · Back carried rattan shield',verts,faces,mids,
              [MATS['rattan_a']],upgrade_col,(5,4))

def shield_surface(x,z,rise=.002):
    return (x,y0+.015*(1-((x-cx)/shield_w)**2)*
            (1-((z-zc)/shield_h)**2)+rise,z)

# Long, fine woven strands are alternately lifted where they cross. The base
# and strands have close hues; this reads as material texture at game distance.
for i in range(7):
    x=cx-.075+.025*i
    width=.0035
    vs=[]
    for j in range(15):
        z=zc-.15+.30*j/14
        rise=.0025 + (.0015 if (j+i)%2 else 0)
        vs.extend((shield_surface(x-width,z,rise),shield_surface(x+width,z,rise)))
    weighted_mesh(f'CCP060 · Shield longitudinal reed {i+1}',vs,
                  [(2*j,2*j+1,2*j+3,2*j+2) for j in range(14)],
                  [0]*14,[MATS['rattan_b']],upgrade_col,(5,4))
for i in range(9):
    z=zc-.13+.0325*i
    width=.0035
    vs=[]
    for j in range(15):
        x=cx-.088+.176*j/14
        rise=.004 if (j+i)%2 else .0025
        vs.extend((shield_surface(x,z-width,rise),shield_surface(x,z+width,rise)))
    weighted_mesh(f'CCP060 · Shield transverse reed {i+1}',vs,
                  [(2*j,2*j+1,2*j+3,2*j+2) for j in range(14)],
                  [0]*14,[MATS['rattan_b']],upgrade_col,(5,4))

# Superellipse rim follows the shield's rounded corners; face loops and rim
# share an explicit radial interface instead of floating decorative strokes.
import math
def rounded_rect(theta, scale):
    c,s=math.cos(theta),math.sin(theta)
    return (cx + shield_w*scale*math.copysign(abs(c)**.45,c),
            zc + shield_h*scale*math.copysign(abs(s)**.45,s))
rim=[]
for scale in (1.0,.88):
    for i in range(32):
        x,z=rounded_rect(2*math.pi*i/32,scale)
        rim.append((x,y0+.004,z))
rim_faces=[(i,(i+1)%32,(i+1)%32+32,i+32) for i in range(32)]
weighted_mesh('CCP060 · Shield bound rounded rim',rim,rim_faces,[0]*32,
              [MATS['rattan_edge']],upgrade_col,(5,4))

# One fitted front strap shows how the back shield is carried while clearing
# hands and the right-side quiver. Shoulder and waist end planes are measured.
strap=[]
for i in range(17):
    t=i/16
    x=-.13+.26*t; z=1.465-.39*t
    strap.extend((fitted(x-.012,z,'front',.029),fitted(x+.012,z,'front',.029)))
weighted_mesh('CCP060 · Shield diagonal carrying strap',strap,
              [(2*i,2*i+1,2*i+3,2*i+2) for i in range(16)],
              [0]*16,[MATS['rattan_edge']],upgrade_col,(4,4))

# A second load path touches the shield's upper rim and travels over the left
# shoulder. It follows the native back and avoids the separate quiver corridor.
back_strap=[]
for i in range(17):
    t=i/16
    x=-.215+.16*t
    z=1.512-.055*t
    back_strap.extend((fitted(x-.011,z,'back',.034),
                       fitted(x+.011,z,'back',.034)))
weighted_mesh('CCP060 · Shield rear shoulder strap',back_strap,
              [(2*i,2*i+1,2*i+3,2*i+2) for i in range(16)],
              [0]*16,[MATS['rattan_edge']],upgrade_col,(4,4))

print('CCP060 Archer II sample geometry built; presentation toggles are separate')
