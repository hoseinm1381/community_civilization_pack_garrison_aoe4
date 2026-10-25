"""Deterministic 0.3.0 scratch landmark art. Background Blender only; no native cook.

Run with -- pho_minh or -- one_pillar after the release_030 storage guard.
The historical buildings inform the silhouettes; these compact game compounds are
interpretations that fit the existing landmark placement, not reconstructions.
"""
import bpy
import hashlib
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / 'tools/release_020'))
from model_ministry_farm_hideout_runner import (box, mesh, hipped_tile_roof,
    faceted_vessel, join_stage, validate, export_building, write)

sys.path.insert(0, r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com')
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material

NAME = sys.argv[sys.argv.index('--') + 1]
assert NAME in ('pho_minh', 'one_pillar')
assert bpy.app.background and not bpy.data.filepath
SOURCE = ROOT / 'art/authoring/landmarks_030' / NAME
EXPORT = ROOT / 'art/exports/landmarks_030' / NAME
OUT = ROOT / 'output/release_030/landmarks' / NAME
for path in (SOURCE, EXPORT, OUT): path.mkdir(parents=True, exist_ok=True)
for obj in tuple(bpy.context.scene.objects): bpy.data.objects.remove(obj, do_unlink=True)

# One atlas/material is required by the qualified Garrison building route.
# Regions correspond exactly to the UV table in the 0.2.0 mesh helper.
PALETTE = {
    'pho_minh': [(0.38,.18,.125),(.29,.20,.15),(.34,.16,.12),(.43,.45,.38),
                 (.31,.34,.29),(.15,.24,.22),(.25,.33,.16),(.37,.32,.26)],
    'one_pillar':[(.44,.24,.17),(.32,.22,.15),(.33,.16,.12),(.46,.47,.40),
                  (.43,.42,.36),(.14,.26,.22),(.22,.33,.14),(.36,.31,.22)]}

def atlas():
    import numpy as np
    size=1024; yy,xx=np.mgrid[0:size,0:size]
    rng=np.random.default_rng(3041 if NAME=='pho_minh' else 3042)
    noise=rng.normal(0,.027,(size,size))
    broad=np.sin(xx*.042+np.sin(yy*.011))* .017 + np.sin(yy*.074)*.013
    arr=np.ones((size,size,4),dtype=np.float32)
    rough=np.ones((size,size,4),dtype=np.float32)
    rough[:,:,:3]=.84
    for index,color in enumerate(PALETTE[NAME]):
        col,row=index%4,index//4
        sl=np.s_[row*512:(row+1)*512,col*256:(col+1)*256]
        u=xx[sl]-col*256; v=yy[sl]-row*512
        grain=noise[sl]+broad[sl]
        if index==0: # staggered fired brick and mortar
            course=v//28
            mortar=(v%28<2)|((u+20*(course%2))%55<2)
            grain+=np.where(mortar,-.085,.014)
        elif index==1: # dark, aged timber grain
            grain+=np.sin(u*.17+np.sin(v*.025))* .026
        elif index==2: # overlapping clay roof tiles
            course=v//24
            seam=((u+12*(course%2))%18<2)|(v%24<2)
            grain+=np.where(seam,-.075,.010)
        elif index==3 or index==4: # subtle green-grey mineral weather
            grain-=.035*np.maximum(0,np.sin(u*.024+v*.037))
        elif index==5: # modeled opaque water: no alpha dependency
            grain+=np.sin(u*.075+v*.062)*.023
        elif index==7:
            grain+=np.sin(u*.26)*.012
        for ch in range(3): arr[sl+(ch,)]=np.clip(color[ch]+grain,0,1)
        rough[sl+(slice(0,3),)]=(.70 if index==5 else .91 if index in (3,4,7) else .82)
    def save(label,data,noncolor=False):
        image=bpy.data.images.new('CCP030_'+NAME+'_'+label,width=size,height=size,alpha=True)
        image.pixels.foreach_set(data.ravel())
        if noncolor: image.colorspace_settings.name='Non-Color'
        image.filepath_raw=str(SOURCE/(label+'.png'));image.file_format='PNG';image.save();image.pack()
        shutil.copy2(SOURCE/(label+'.png'),EXPORT/(label+'.png'))
        return image
    albedo=save('albedo',arr)
    save('roughness',rough,True)
    for label,color in (('normal',(.5,.5,1,1)),('metalness',(0,0,0,1))):
        image=bpy.data.images.new('CCP030_'+NAME+'_'+label,width=16,height=16,alpha=False)
        image.generated_color=color;image.colorspace_settings.name='Non-Color'
        image.filepath_raw=str(SOURCE/(label+'.png'));image.file_format='PNG';image.save();image.pack()
        shutil.copy2(SOURCE/(label+'.png'),EXPORT/(label+'.png'))
    mat=bpy.data.materials.new('CCP030_'+NAME+'_atlas');mat.use_nodes=True
    nodes=mat.node_tree.nodes; links=mat.node_tree.links; bs=nodes.get('Principled BSDF')
    bs.inputs['Specular IOR Level'].default_value=.06
    for label,socket in (('albedo','Base Color'),('roughness','Roughness'),('metalness','Metallic'),('normal','Normal')):
        im=albedo if label=='albedo' else bpy.data.images.load(str(SOURCE/(label+'.png')),check_existing=True)
        if label!='albedo':im.colorspace_settings.name='Non-Color';im.pack()
        node=nodes.new('ShaderNodeTexImage');node.image=im
        if label=='normal':
            nm=nodes.new('ShaderNodeNormalMap');links.new(node.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs[socket])
        else:links.new(node.outputs['Color'],bs.inputs[socket])
    return mat

MAT=atlas(); foundation=[]; upper=[]; contacts=[]; steps=[]
def render_landmark_views(objects,target):
    """Seven proof views with bounded lighting; avoid clipped atlas highlights."""
    from mathutils import Vector
    # The atlas is the deliverable. A diffuse preview removes path-traced
    # specular triangles from the many small, steep clay roof courses.
    nodes=MAT.node_tree.nodes;links=MAT.node_tree.links
    output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
    original=output.inputs['Surface'].links[0].from_socket
    albedo=next(n for n in nodes if n.type=='TEX_IMAGE' and 'albedo' in n.image.name)
    diffuse=nodes.new('ShaderNodeBsdfDiffuse')
    links.new(albedo.outputs['Color'],diffuse.inputs['Color'])
    links.new(diffuse.outputs['BSDF'],output.inputs['Surface'])
    co=[v.co for o in objects for v in o.data.vertices]
    lo=Vector([min(v[i] for v in co) for i in range(3)])
    hi=Vector([max(v[i] for v in co) for i in range(3)])
    center=(lo+hi)/2;size=max(hi-lo)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
    scene.cycles.max_bounces=2;scene.cycles.diffuse_bounces=1;scene.cycles.glossy_bounces=0
    scene.render.resolution_x=900;scene.render.resolution_y=750;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    if scene.world is None:scene.world=bpy.data.worlds.new('CCP030 preview world')
    scene.world.use_nodes=True
    background=scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value=(.36,.39,.42,1)
    background.inputs['Strength'].default_value=.8
    lights=[]
    for label,direction,power in (('key',(.8,-.8,1.6),9),('fill',(-.6,-.8,.65),5)):
        data=bpy.data.lights.new('CCP030 '+label,'AREA')
        obj=bpy.data.objects.new('CCP030 '+label,data);scene.collection.objects.link(obj)
        obj.location=center+Vector(direction)*size;data.energy=size*size*power;data.size=size*1.2
        lights.append(obj)
    cam=bpy.data.objects.new('CCP030 preview camera',bpy.data.cameras.new('CCP030 preview camera'))
    scene.collection.objects.link(cam);cam.data.type='ORTHO';scene.camera=cam
    for label,direction in (('iso',(1,-1,.8)),('front',(0,-1,.2)),('back',(0,1,.2)),
                            ('left',(-1,0,.2)),('right',(1,0,.2)),('top',(0,0,1)),('bottom',(0,0,-1))):
        cam.location=center+Vector(direction).normalized()*size*2
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.ortho_scale=size*1.5
        scene.render.filepath=str(target/(label+'.png'));bpy.ops.render.render(write_still=True)
    scene.camera=None
    links.new(original,output.inputs['Surface'])
    nodes.remove(diffuse)
    for obj in lights+[cam]:bpy.data.objects.remove(obj,do_unlink=True)
def add(obj,stage=20):
    (foundation if stage==0 else upper).append(obj)
    return obj
def block(name,center,size,tile='stone',stage=20):
    return add(box(name,center,size,MAT,{'stone':'plaster'}.get(tile,tile)),stage)
def contact(label,a,b,tolerance=.04):
    gap=a-b
    contacts.append({'interface':label,'first_plane':a,'second_plane':b,'gap':gap,'tolerance':tolerance,'pass':abs(gap)<=tolerance})
    assert abs(gap)<=tolerance,(label,gap)
def square_frustum(name,center,z0,z1,w0,w1,tile):
    cx,cy=center; verts=[]
    for z,w in ((z0,w0),(z1,w1)):
        q=w/2;verts.extend([(cx-q,cy-q,z),(cx+q,cy-q,z),(cx+q,cy+q,z),(cx-q,cy+q,z)])
    faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return add(mesh(name,verts,faces,MAT,{'stone':'plaster'}.get(tile,tile)))
def recessed_tower_body(name, center, z0, z1, w0, w1, openings, tile):
    """Closed tapered masonry with actual inset wall pockets, not surface decals.

    Each side is a four-by-four grid with the central cell removed. Pocket
    returns and back face close that cut; coincident side corners are welded.
    """
    import bmesh
    cx,cy=center;verts=[];faces=[];bottom_ring=[];top_ring=[]
    _,height_ref,low_ref,_=next(iter(openings.values()))
    side_vectors=[((0,-1),(1,0)),((1,0),(0,1)),((0,1),(-1,0)),((-1,0),(0,-1))]
    for side,(normal,tangent) in enumerate(side_vectors):
        do_cut=side in openings
        width,height,low,depth=openings.get(side,(.30,.38,.24,.12))
        rows=(z0,z0+low_ref,z0+low_ref+height_ref,z1)
        grid=[]
        for z in rows:
            half=(w0+(w1-w0)*(z-z0)/(z1-z0))/2
            row=[]
            for u in (-half,-width/2,width/2,half):
                row.append(len(verts))
                verts.append((cx+normal[0]*half+tangent[0]*u,
                              cy+normal[1]*half+tangent[1]*u,z))
            grid.append(row)
        bottom_ring.extend(grid[0][:3]);top_ring.extend(grid[-1][:3])
        for j in range(3):
            for i in range(3):
                if do_cut and i==j==1:continue
                faces.append((grid[j][i],grid[j][i+1],grid[j+1][i+1],grid[j+1][i]))
        if do_cut:
            opening=(grid[1][1],grid[1][2],grid[2][2],grid[2][1])
            back=[]
            for front in opening:
                x,y,z=verts[front];back.append(len(verts))
                verts.append((x-normal[0]*depth,y-normal[1]*depth,z))
            for k in range(4):faces.append((opening[k],opening[(k+1)%4],back[(k+1)%4],back[k]))
            faces.append(tuple(reversed(back)))
    # Twelve-edge caps exactly follow side-grid perimeter; no T-junctions.
    faces.append(tuple(reversed(bottom_ring)))
    faces.append(tuple(top_ring))
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.materials.append(MAT);data.update()
    bm=bmesh.new();bm.from_mesh(data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    probe=bmesh.new();probe.from_mesh(data)
    broken=[(tuple(e.verts[0].co),tuple(e.verts[1].co)) for e in probe.edges if not e.is_manifold]
    probe.free()
    assert not broken,(name,len(broken),broken[:8])
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj)
    uv=data.uv_layers.new(name='UVMap')
    tile_index={'brick':0,'timber':1,'tile':2,'plaster':3}[tile]
    col,row=tile_index%4,tile_index//4
    for poly in data.polygons:
        positions=[data.vertices[data.loops[k].vertex_index].co for k in poly.loop_indices]
        span=[max(p[i] for p in positions)-min(p[i] for p in positions) for i in range(3)]
        axes=sorted(range(3),key=lambda i:span[i],reverse=True)[:2]
        for li,p in zip(poly.loop_indices,positions):
            uv.data[li].uv=((col+.04+.92*(p[axes[0]]-min(v[axes[0]] for v in positions))/max(span[axes[0]],1e-8))/4,
                             (row+.04+.92*(p[axes[1]]-min(v[axes[1]] for v in positions))/max(span[axes[1]],1e-8))/2)
    return add(obj)
def cylinder(name,center,radius,z0,z1,tile,sides=12,stage=20):
    profile=[(0,radius),(z1-z0,radius)]
    return add(faceted_vessel(name,(center[0],center[1],z0),profile,MAT,{'stone':'plaster'}.get(tile,tile),sides),stage)
def prism_beam(name,a,b,thick,tile='timber'):
    from mathutils import Vector
    start,end=Vector(a),Vector(b); d=end-start;mid=(start+end)*.5
    obj=box(name,(0,0,0),(thick,thick,d.length+thick*.55),MAT,{'stone':'plaster'}.get(tile,tile))
    obj.location=mid
    obj.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return add(obj)
def oriented_box(name,center,size,tile,angle=0):
    obj=box(name,(0,0,0),size,MAT,{'stone':'plaster'}.get(tile,tile))
    obj.location=center;obj.rotation_euler[2]=angle
    return add(obj)
def roof_surface(x,y,cx,cy,width,depth,eave,rise):
    local_x=x-cx;local_y=y-cy
    side=abs(local_y)/(depth/2);end=abs(local_x)/(width/2)
    hip=1-.29*max(0,(end-.73)/.27)
    kick=.12*max(0,(side-.78)/.22)**2
    corner=.06*max(0,(end-.77)/.23)*max(0,(side-.75)/.25)
    return eave+rise*(1-side)*hip+kick+corner
def tiled_roof_detail(name,center,width,depth,eave,rise,nx,ny):
    """Closed overlapping tile courses and eave rafters anchored to roof profile."""
    cx,cy=center
    sx=width/nx;sy=depth/ny
    for j in range(ny):
        for i in range(nx):
            x0=cx-width/2+i*sx+.007;x1=cx-width/2+(i+1)*sx-.007
            y0=cy-depth/2+j*sy+.006;y1=cy-depth/2+(j+1)*sy-.006
            xy=((x0,y0),(x1,y0),(x1,y1),(x0,y1))
            z=[roof_surface(x,y,cx,cy,width,depth,eave,rise)+.075 for x,y in xy]
            verts=[(x,y,h) for (x,y),h in zip(xy,z)]
            verts += [(x,y,h-.105) for (x,y),h in zip(xy,z)]
            faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
            add(mesh(f'{name}_tile_{j:02}_{i:02}',verts,faces,MAT,'tile'))
    for side in (-1,1):
        y=cy+side*(depth/2-.18)
        for i in range(nx):
            x=cx-width/2+(i+.5)*sx
            z=roof_surface(x,y,cx,cy,width,depth,eave,rise)-.095
            block(f'{name}_rafter_{side}_{i}',(x,y,z),(.065,.35,.12),'timber')
    # Shallow terra-cotta eave fascia follows the front/back of the actual roof.
    for side in (-1,1):
        y=cy+side*(depth/2-.04)
        for i in range(nx):
            x=cx-width/2+(i+.5)*sx
            z=roof_surface(x,y,cx,cy,width,depth,eave,rise)-.055
            block(f'{name}_fascia_{side}_{i}',(x,y,z),(sx+.002,.075,.095),'tile')
def pho_minh():
    # Ref: 19.51 m monument, one broad stone lower stage plus thirteen brick tiers.
    # Tower center is forward of a compact rear temple court; all ground XY <= 3.82.
    block('PM_00_stone_court',(0,0,.105),(7.45,7.45,.21),'stone',0)
    for x in (-3.60,3.60):block('PM_00_court_side_coping_'+str(x),(x,0,.25),(.18,7.50,.12),'stone',0)
    for y in (-3.60,3.60):block('PM_00_court_end_coping_'+str(y),(0,y,.25),(7.35,.18,.12),'stone',0)
    # Slightly weathered square stone lower plinth with inset doorway.
    center=(0,-.70)
    block('PM_00_tower_splayed_foot',(0,-.70,.34),(3.32,3.32,.30),'stone',0)
    recessed_tower_body('PM_00_tower_lower_stone',(0,-.70),.47,1.89,2.96,2.96,
                        {0:(.58,.93,.12,.16)},'plaster')
    # The lower body is stone and is visible from first construction stage.
    foundation.append(upper.pop())
    block('PM_00_tower_base_cap',(0,-.70,1.91),(3.12,3.12,.20),'stone',0)
    contact('tower plinth to court',.19,.21,.03)
    contact('tower stone stage to plinth top',.47,.49,.03)
    # A real entrance void is suggested by two jamb stones, a dark inset door,
    # and a projecting threshold. The tower mass remains closed for preflight.
    block('PM_20_south_recessed_door',(0,-2.025,1.03),(.53,.025,.88),'timber')
    for x in (-.33,.33):block('PM_20_south_jamb_'+str(x),(x,-2.225,1.04),(.09,.08,1.03),'stone')
    block('PM_20_south_lintel',(0,-2.23,1.62),(.77,.09,.11),'stone')
    block('PM_20_threshold',(0,-2.31,.49),(.82,.35,.10),'stone')
    # Stone lotus relief repeats as short wedges around the four lower walls.
    for side in range(4):
        angle=side*math.pi/2
        for i in range(5):
            shift=(i-2)*.42
            cx=math.sin(angle)*1.53+math.cos(angle)*shift
            cy=-.70-math.cos(angle)*1.53+math.sin(angle)*shift
            oriented_box(f'PM_20_lotus_petal_{side}_{i}',(cx,cy,1.70),(.22,.07,.26),'stone',angle)
    # One prototype tier, parameterised from measured base and taper.
    tier_height=1.27
    first_z=2.02
    for tier in range(1,14):
        z0=first_z+(tier-1)*tier_height
        z1=z0+tier_height
        width=2.63-(tier-1)*.119
        next_width=width-.09
        recessed_tower_body(f'PM_20_tier{tier:02}_brick',center,z0,z1-.20,width,next_width,
                            {side:(.24,.37,.22,.12) for side in range(4)},'brick')
        # Separate stone-colored overhanging cornice, dark shadow reveal, and
        # two lighter horizontal brick courses. These give every stage depth.
        block(f'PM_20_tier{tier:02}_shadow',(0,-.70,z1-.225),(width+.20,width+.20,.06),'timber')
        block(f'PM_20_tier{tier:02}_cornice',(0,-.70,z1-.17),(width+.38,width+.38,.12),'stone')
        block(f'PM_20_tier{tier:02}_upper_lip',(0,-.70,z1-.055),(width+.25,width+.25,.11),'stone')
        for side in range(4):
            angle=side*math.pi/2
            for index,offset in enumerate((-.31,0,.31)):
                nx=math.sin(angle);ny=-math.cos(angle)
                tx=math.cos(angle);ty=math.sin(angle)
                px=nx*(width/2+.055)+tx*offset*width
                py=-.70+ny*(width/2+.055)+ty*offset*width
                oriented_box(f'PM_20_tier{tier:02}_corbel_{side}_{index}',
                             (px,py,z1-.315),(.12,.20,.18),'stone',angle)
            # A paired returned corner at each projecting ledge preserves the
            # upturned shadow line visible in the tower photograph.
            for sign in (-1,1):
                px=nx*(width/2+.19)+tx*sign*(width/2+.17)
                py=-.70+ny*(width/2+.19)+ty*sign*(width/2+.17)
                oriented_box(f'PM_20_tier{tier:02}_corner_return_{side}_{sign}',
                             (px,py,z1-.09),(.12,.12,.13),'stone',angle)
        contact(f'tier {tier:02} brick to shadow',z1-.20,z1-.195,.01)
        contact(f'tier {tier:02} cornice to upper lip',z1-.11,z1-.11,.001)
    top=first_z+13*tier_height
    square_frustum('PM_20_crown_stone',center,top,top+.55,.70,.30,'stone')
    add(faceted_vessel('PM_20_lotus_bud_finial',center+(top+.53,),
                       [(0,.13),(.08,.24),(.22,.20),(.40,.08),(.50,.035)],MAT,'plaster',12))
    # Modest west/east courts and a low tiled rear temple roof keep the tower
    # the recognizable dominant form within the 8x8 native placement.
    block('PM_00_rear_temple_plinth',(0,2.75,.32),(5.20,1.72,.22),'stone',0)
    block('PM_20_rear_temple_back_wall',(0,3.48,1.31),(4.84,.14,1.82),'plaster')
    for x in (-2.35,2.35):block(f'PM_20_rear_temple_side_{x}',(x,2.92,1.31),(.14,1.18,1.82),'plaster')
    for x in (-1.45,1.45):block(f'PM_20_rear_temple_front_panel_{x}',(x,2.33,1.19),(1.85,.13,1.58),'plaster')
    block('PM_20_rear_temple_door_lintel',(0,2.33,2.06),(1.12,.15,.32),'timber')
    block('PM_20_rear_temple_recessed_double_door',(0,2.48,1.22),(.86,.07,1.48),'timber')
    for x in (-.46,0,.46):block(f'PM_20_rear_temple_door_jamb_{x}',(x,2.29,1.23),(.08,.12,1.61),'timber')
    for x in (-2.32,-1.17,0,1.17,2.32):
        block(f'PM_20_rear_column_{x:+.2f}',(x,2.08,1.25),(.15,.16,1.84),'timber')
        contact(f'rear column {x} to plinth',.33,.43,.11)
    # Carved screen joinery gives the temple readable front and rear elevations.
    for side,y in (('front',2.23),('back',3.57)):
        for i in range(17):
            x=-2.24+i*.28
            if side=='front' and abs(x)<.58:continue
            block(f'PM_20_{side}_screen_mullion_{i}',(x,y,1.43),(.045,.07,1.34),'timber')
        for z in (.78,1.15,1.54,1.91):
            if side=='front':
                for x in (-1.51,1.51):
                    block(f'PM_20_{side}_screen_rail_{x}_{z}',(x,y,z),(1.73,.075,.045),'timber')
            else:block(f'PM_20_{side}_screen_rail_{z}',(0,y,z),(4.52,.075,.045),'timber')
    add(hipped_tile_roof('PM_20_rear_hipped_tile_roof',(0,2.75),5.35,2.00,2.32,.80,.14,MAT))
    tiled_roof_detail('PM_20_rear_hipped',(0,2.75),5.35,2.00,2.32,.80,20,8)
    for i in range(20):
        x=-2.45+(i+.5)*4.90/20
        z=roof_surface(x,2.75,0,2.75,5.35,2.00,2.32,.80)+.095
        block(f'PM_20_rear_roof_ridge_cap_{i}',(x,2.75,z),(.22,.13,.11),'tile')
    for x in (-2.35,2.35):
        cylinder(f'PM_20_court_lantern_{x}',(x,-2.98),.18,.29,.66,'stone',8)
        block(f'PM_20_lantern_cap_{x}',(x,-2.98,.74),(.47,.47,.14),'stone')
    return {'anatomy':['square stone court','broad green-grey stone lower tower with recessed entrance',
        'thirteen individually tapered red brick tiers','repeated deep cornices, niches and lotus relief',
        'modest rear temple with tiled roof'],
        'source':'https://en.vietnamplus.vn/pho-minh-pagoda-where-tran-dynasty-glory-preserved-in-stone-post323407.vnp',
        'interpretation':'Compact game compound; 14-tier tower anatomy follows source, not exact survey.'}

def one_pillar():
    # Official report: historic square shrine ~3 m each side; column ~1.2 m
    # diameter and 4 m high. Game version has an 8x8 visual compound.
    block('OP_00_court_ground',(0,0,.08),(7.50,7.50,.16),'earth',0)
    block('OP_00_pond_stone_underlay',(0,.30,.16),(5.00,5.00,.12),'stone',0)
    block('OP_00_opaque_pond_water',(0,.30,.235),(4.50,4.50,.035),'water',0)
    contact('opaque water to stone pond underlay',.2175,.22,.01)
    for x in (-2.39,2.39):block(f'OP_00_pond_coping_x{x}',(x,.30,.34),(.23,5.10,.22),'stone',0)
    for y in (-2.09,2.69):block(f'OP_00_pond_coping_y{y}',(0,y,.34),(5.00,.23,.22),'stone',0)
    # Individually seated capstones expose real joints at game-camera range.
    for side in (-1,1):
        for i in range(14):
            t=-2.24+(i+.5)*4.48/14
            block(f'OP_20_pond_cap_x{side}_{i}',(side*2.39,.30+t,.465),(.245,4.48/14-.014,.045),'stone')
            block(f'OP_20_pond_cap_y{side}_{i}',(t, .30+side*2.39,.465),(4.48/14-.014,.245,.045),'stone')
    # Pillar base starts below opaque water. One visible column only.
    cylinder('OP_00_single_stone_column',(0,.38),.52,.18,2.55,'stone',16,0)
    cylinder('OP_20_lotus_stone_cap',(0,.38),.75,2.45,2.76,'stone',16)
    contact('single pillar to lotus cap',2.55,2.45,.11)
    for i in range(12):
        a=math.tau*i/12
        obj=block(f'OP_20_lotus_petal_{i}',(.70*math.cos(a),.38+.70*math.sin(a),2.60),(.29,.12,.27),'plaster')
        obj.rotation_euler[2]=a+math.pi/2
    block('OP_20_shrine_floor',(0,.38,2.87),(3.34,3.34,.24),'timber')
    contact('lotus cap to floor',2.76,2.75,.02)
    # Diagonal timber brackets visibly carry the overhanging floor to its edges.
    for side in (-1,1):
        for axis in ('x','y'):
            a=(0,.38,2.46)
            b=(side*1.43,.38,2.78) if axis=='x' else (0,.38+side*1.43,2.78)
            prism_beam(f'OP_20_bracket_{axis}{side}',a,b,.17)
            contact(f'bracket {axis}{side} upper to floor',b[2]+.06,2.75,.10)
    for x in (-1.34,1.34):block(f'OP_20_floor_crossbeam_x{x}',(x,.38,2.72),(.17,3.25,.19),'timber')
    for y in (-.96,1.72):block(f'OP_20_floor_crossbeam_y{y}',(0,y,2.72),(3.25,.17,.19),'timber')
    # Four posts, timber wall/screen panels and open south entry.
    for x in (-1.35,1.35):
        for y in (-.97,1.73):
            block(f'OP_20_corner_post_{x}_{y}',(x,y,3.63),(.16,.16,1.46),'timber')
            contact(f'post {x},{y} bottom to shrine floor',2.90,2.99,.10)
    block('OP_20_rear_shrine_wall',(0,1.73,3.58),(2.54,.10,1.22),'timber')
    for i in range(15):
        x=-1.20+i*.17
        block(f'OP_20_back_joinery_mullion_{i}',(x,1.805,3.58),(.045,.065,1.17),'timber')
    for z in (3.11,3.48,3.86,4.08):
        block(f'OP_20_back_joinery_rail_{z}',(0,1.81,z),(2.55,.065,.055),'timber')
    for x in (-1.35,1.35):block(f'OP_20_side_shrine_wall_{x}',(x,.38,3.50),(.10,2.49,1.02),'timber')
    for side in (-1,1):
        x=side*1.425
        for i in range(12):
            y=-.82+i*.22
            block(f'OP_20_side_lattice_{side}_{i}',(x,y,3.53),(.05,.07,.88),'timber')
        for z in (3.13,3.55,3.94):
            block(f'OP_20_side_rail_{side}_{z}',(x,.38,z),(.06,2.58,.055),'timber')
    for x in (-.73,.73):
        block(f'OP_20_south_low_screen_{x}',(x,-.97,3.23),(1.05,.10,.50),'timber')
        for z in (3.20,3.39,3.58):block(f'OP_20_screen_rail_{x}_{z}',(x,-1.04,z),(1.02,.055,.045),'timber')
    for x in (-1.11,-.94,-.77,-.60,-.43,.43,.60,.77,.94,1.11):
        block(f'OP_20_south_carved_baluster_{x}',(x,-1.08,3.46),(.045,.07,.72),'timber')
    block('OP_20_south_head_rail',(0,-1.08,3.86),(2.58,.09,.075),'timber')
    block('OP_20_back_central_shrine_recess',(0,1.67,3.62),(.88,.025,.72),'plaster')
    # Swept hip roof, visible clay courses, projecting dragon-like corner tips.
    roof=hipped_tile_roof('OP_20_lotus_shrine_curved_tile_roof',(0,.38),3.82,3.82,4.34,1.07,.16,MAT)
    add(roof)
    tiled_roof_detail('OP_20_lotus_shrine',(0,.38),3.82,3.82,4.34,1.07,18,14)
    for i in range(18):
        x=-1.72+(i+.5)*3.44/18
        z=roof_surface(x,.38,0,.38,3.82,3.82,4.34,1.07)+.095
        block(f'OP_20_lotus_shrine_ridge_cap_{i}',(x,.38,z),(.18,.12,.11),'tile')
    contact('shrine corner posts to roof eave',4.36,4.34,.03)
    for x in (-1.78,1.78):
        for y in (-1.40,2.16):
            prism_beam(f'OP_20_upturned_eave_{x}_{y}',(x*.83,.38+(y-.38)*.83,4.43),(x,y,4.61),.095,'tile')
    for side in (-1,1):
        for x in (-1.25,-.75,-.25,.25,.75,1.25):
            prism_beam(f'OP_20_eave_bracket_{side}_{x}',(x,.38+side*1.24,4.15),
                       (x,.38+side*1.65,4.34),.095,'timber')
    # A measured stair bridge from the south court up to the elevated platform.
    n=8; y0=-3.49; y1=-1.26; ground=.30; z1=2.79
    for i in range(n):
        a=i/n; b=(i+1)/n
        y=(y0+(a+b)*(y1-y0)/2); z=ground+(i+1)*(z1-ground)/n
        block(f'OP_20_stair_riser_{i}',(0,y,(ground+z)/2),(1.20,(y1-y0)/n+.02,z-ground),'stone')
    contact('top stair to shrine floor',z1,2.75,.05)
    for side in (-1,1):
        prism_beam(f'OP_20_stair_side_rail_{side}',(side*.67,y0,.48),(side*.67,y1,3.00),.13,'stone')
    # Small rear side support hall, distinct and visibly subordinate.
    block('OP_00_support_hall_plinth',(2.90,2.88,.25),(1.68,1.68,.20),'stone',0)
    block('OP_20_support_hall_body',(2.90,2.88,.91),(1.40,1.40,1.12),'timber')
    block('OP_20_support_hall_framed_door',(2.90,2.16,.83),(.53,.035,.75),'plaster')
    for x in (2.57,3.23):block(f'OP_20_support_hall_doorpost_{x}',(x,2.15,.84),(.08,.09,.86),'timber')
    for x in (2.42,2.66,2.90,3.14,3.38):
        block(f'OP_20_support_hall_back_mullion_{x}',(x,3.60,.93),(.05,.05,.91),'timber')
    for z in (.56,1.14):block(f'OP_20_support_hall_back_rail_{z}',(2.90,3.60,z),(1.23,.05,.05),'timber')
    add(hipped_tile_roof('OP_20_support_hall_tile_roof',(2.90,2.88),1.65,1.65,1.48,.47,.11,MAT))
    tiled_roof_detail('OP_20_support_hall',(2.90,2.88),1.65,1.65,1.48,.47,8,8)
    for i in range(8):
        x=2.17+(i+.5)*1.46/8
        z=roof_surface(x,2.88,2.90,2.88,1.65,1.65,1.48,.47)+.09
        block(f'OP_20_support_hall_ridge_cap_{i}',(x,2.88,z),(.16,.10,.08),'tile')
    # A few planar lotus leaves read in orthographic game view.
    pads=((-2.08,.60,.22),(-1.81,1.36,.17),(1.83,-.30,.19),(1.78,1.40,.20),
          (-1.62,-1.08,.19),(1.44,-1.26,.14),(-1.02,1.83,.15),(.80,1.80,.18),
          (-1.63,.03,.14),(1.92,.42,.16),(-.80,-1.62,.15),(.42,-1.80,.13),
          (-1.30,1.12,.11),(1.13,.98,.10),(-.45,1.62,.12),(1.23,-.69,.11))
    for i,(x,y,r) in enumerate(pads):
        cylinder(f'OP_20_lotus_pad_{i}',(x,y),r,.254,.267,'rice',8)
    for i,(x,y) in enumerate(((-1.74,.62),(.91,1.43),(1.68,-.65))):
        cylinder(f'OP_20_lotus_stem_{i}',(x,y),.028,.25,.43,'rice',8)
        add(faceted_vessel(f'OP_20_lotus_bud_{i}',(x,y,.40),
                           [(0,.045),(.08,.105),(.18,.055),(.23,.016)],MAT,'plaster',8))
    return {'anatomy':['square modeled pond and coping','one stone pillar with lotus bracket cap',
        'raised timber shrine with open south approach','curved tiled roof with upturned eaves',
        'stair bridge and modest rear support hall'],
        'source':'https://thanglong.chinhphu.vn/english/the-one-pillar-pagoda-and-dien-huu-pagoda-110238.htm',
        'interpretation':'Compact scenic court; static opaque water and lotus pads, no water or terrain gameplay.'}

notes=pho_minh() if NAME=='pho_minh' else one_pillar()
assert foundation and upper
objects=[join_stage(foundation,'CCP030_'+NAME+'_00_foundation',0),
         join_stage(upper,'CCP030_'+NAME+'_20_superstructure',20)]
for obj in objects:obj['garrison_building_profile']='english-house'
# Native private actor includes animator_scale=112. Its engine interpretation
# still needs a native match, so leave margin inside the explicit 8x8 Pho site.
xy_max=max(abs(v.co[i]) for obj in objects for v in obj.data.vertices for i in (0,1))
xy_factor=min(1.0,3.45/xy_max)
for obj in objects:
    for v in obj.data.vertices:
        v.co.x*=xy_factor;v.co.y*=xy_factor
    obj.data.update()
points=[v.co for obj in objects for v in obj.data.vertices]
bounds={'min':[min(v[i] for v in points) for i in range(3)],
        'max':[max(v[i] for v in points) for i in range(3)]}
assert bounds['min'][2]>=-.0001,bounds
assert max(abs(bounds['min'][0]),abs(bounds['max'][0]),abs(bounds['min'][1]),abs(bounds['max'][1]))<=3.451,bounds
checks=validate(objects)
preflight=require_valid(objects,bpy.context);assert preflight['ok'],preflight
adopt_material(MAT)
col=bpy.data.collections.new('CCP030 '+NAME);bpy.context.scene.collection.children.link(col)
for key,value in {'garrison_asset_container':True,'garrison_asset_id':NAME,
        'garrison_namespace':'community_civilization_pack','garrison_display_name':NAME,
        'garrison_qualified_id':'community_civilization_pack:'+NAME,
        'garrison_archetype':'building','garrison_building_profile':'english-house',
        'garrison_building_integration':'script'}.items():col[key]=value
for obj in objects:
    col.objects.link(obj)
    for prior in tuple(obj.users_collection):
        if prior!=col:prior.objects.unlink(obj)
manifest=export_building(objects,EXPORT)
validation={'schema':'ccp.release030.landmark-art/v1','name':NAME,'bounds':bounds,
    'xy_compaction_factor':xy_factor,'authoring_xy_limit':3.45,
    'geometry':checks,'triangles':sum(row['triangles'] for row in checks),
    'contacts':contacts,'garrison_preflight':preflight,'construction_stages':[0,20],
    'owner_colour':'Neutral atlas; integration preserves native owner colour/flag handling.',
    'no_gameplay_edit':True,'native_cook':'not run','client_import':'not run','match':'not run',
    'notes':notes}
write(OUT/'validation.json',validation)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+'.blend')))
render_landmark_views(objects,OUT)
write(OUT/'handoff.json',{'name':NAME,'source_blend':str(SOURCE/(NAME+'.blend')),
    'source_blend_sha256':hashlib.sha256((SOURCE/(NAME+'.blend')).read_bytes()).hexdigest(),
    'export_directory':str(EXPORT),'export_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in EXPORT.iterdir() if p.is_file()},
    'building':manifest,'bounds':bounds,'triangles':validation['triangles'],
    'contacts':contacts,'validation':str(OUT/'validation.json'),
    'previews':[p.name for p in OUT.glob('*.png')],'native_model_keys':'integration owner decides from existing private bindings'})
print('CCP030_LANDMARK_COMPLETE '+NAME)
