"""Owned MCP-executed blockout runner. No cameras or existing-scene edits."""
import bpy,math,json,bmesh
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path('E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack/Community_civilization_pack_garrison')
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art')
DEST=ROOT/'art/authoring/buildings_070'
PREFIX='CCP070_'; SCENE_NAME='CCP070_Architecture_Blockouts'
OFFSETS={'CCP070_Imperial_Garden_Blockout':(-15,15,0),'CCP070_Trung_Foundaries_Blockout':(15,15,0),'CCP070_Kinh_Thien_Wonder_Blockout':(-15,-15,0),'CCP070_University_Additions_Blockout':(15,-15,0)}
COLORS={'stone':(.40,.38,.32,1),'wood':(.24,.13,.085,1),'plaster':(.72,.65,.49,1),'roof':(.32,.15,.105,1),'water':(.16,.34,.31,1),'clay':(.48,.29,.16,1),'metal':(.22,.25,.24,1),'stock':(.48,.48,.45,1),'ground':(.18,.23,.15,1)}
def init():
    global scene,mats,current,offset
    scene=bpy.data.scenes.get(SCENE_NAME) or bpy.data.scenes.new(SCENE_NAME)
    bpy.context.window.scene=scene
    mats={}
    for key,color in COLORS.items():
        m=bpy.data.materials.get(PREFIX+key) or bpy.data.materials.new(PREFIX+key)
        m.diffuse_color=color;mats[key]=m
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
    scene.world=bpy.data.worlds.new(PREFIX+'World') if not scene.world else scene.world
    scene.world.color=(.10,.10,.10)
    current=None;offset=Vector((0,0,0));OUT.mkdir(parents=True,exist_ok=True);DEST.mkdir(parents=True,exist_ok=True)
def collection(name,unused_offset):
    global current,offset
    if not name.startswith(PREFIX):raise ValueError('Unowned collection')
    current=bpy.data.collections.get(name)
    if current:
        archive=bpy.data.collections.get(PREFIX+'Revision_Archive') or bpy.data.collections.new(PREFIX+'Revision_Archive')
        for o in list(current.objects):
            if not o.get('stock_geometry_unchanged'):
                # Keep revision datablocks: installed MCP reports deleted RNA
                # after execution, so deletion can misreport a completed build.
                o.name=PREFIX+'ARCHIVE_'+o.name
                archive.objects.link(o);current.objects.unlink(o)
    else:
        current=bpy.data.collections.new(name);scene.collection.children.link(current)
    offset=Vector(OFFSETS[name])
    return current
def mesh(name,verts,faces,mat):
    name=PREFIX+name;me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    # Closed custom surfaces get explicit outward winding before approval views.
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);current.objects.link(o);o.location=offset;o.data.materials.append(mats[mat]);return o
def box(name,loc,size,material):
    x,y,z=loc;w,d,h=[v/2 for v in size]
    v=[(x+sx*w,y+sy*d,z+sz*h) for sz in (-1,1) for sy in (-1,1) for sx in (-1,1)]
    f=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    return mesh(name,v,f,material)
def hip_roof(name,center_xy,width,depth,eave_z,rise,material,upturn=.3):
    x,y=center_xy;w=width/2;d=depth/2
    # Outer sweep, lower pitch break, upper pitch break, then hip ridge.
    rings=[(w,d,eave_z+upturn),(w*.80,d*.80,eave_z+.12*rise),(w*.45,d*.45,eave_z+.62*rise)]
    v=[]
    for a,b,z in rings:v.extend([(x-a,y-b,z),(x+a,y-b,z),(x+a,y+b,z),(x-a,y+b,z)])
    r=max(.12,w*.32);v.extend([(x-r,y,eave_z+rise),(x+r,y,eave_z+rise)])
    f=[]
    for i in range(2):
        for j in range(4):f.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    f.extend([(8,9,13,12),(9,10,13),(10,11,12,13),(11,8,12)])
    # A closed lower shell makes edge thickness visible; no paper roof planes.
    for a,b,z in rings[:1]:v.extend([(x-a,y-b,eave_z-.12),(x+a,y-b,eave_z-.12),(x+a,y+b,eave_z-.12),(x-a,y+b,eave_z-.12)])
    for j in range(4):f.append((j,14+j,14+(j+1)%4,(j+1)%4))
    f.append((14,17,16,15))
    return mesh(name,v,f,material)
def hall(name,xy,width,depth,plinth_z,body_h,roof_h,material):
    x,y=xy
    if not name.startswith('Wonder_'):
        box(name+'_Plinth',(x,y,max(.1,plinth_z)/2),(width+.5,depth+.5,max(.1,plinth_z)),'stone')
    if any(t in name for t in ('Gate','Pavilion','Gallery','Audience_Hall')):
        # Broad colonnade volumes are part of massing; ornament waits for approval.
        body=box(name+'_Core',(x,y+.15*depth,plinth_z+body_h/2),(width*.70,depth*.45,body_h),material) if 'Gate' not in name else None
        for side,px in [('W',x-width/2+.18),('E',x+width/2-.18)]:
            for end,py in [('F',y-depth/2+.18),('B',y+depth/2-.18)]:post(name+'_'+side+end+'_Post',(px,py,plinth_z),body_h,.16)
        box(name+'_Eave_Tie',(x,y,plinth_z+body_h-.1),(width,.25,.25),'wood')
    else:body=box(name+'_Body',(x,y,plinth_z+body_h/2),(width,depth,body_h),material)
    roof=hip_roof(name+'_Roof',xy,width+1,depth+1,plinth_z+body_h,roof_h,'roof')
    return body,roof
def post(name,loc,height,radius):
    x,y,z=loc;n=10
    v=[(x+radius*math.cos(i*2*math.pi/n),y+radius*math.sin(i*2*math.pi/n),z+dz) for dz in (0,height) for i in range(n)]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,'wood')
def basin(name,xy,width,depth,z):
    # Actual recessed bed with four retaining sides, independent of solid ground.
    x,y=xy
    box(name+'_Water',(x,y,z-.22),(width-.38,depth-.38,.05),'water')
    for suffix,l,s in [('N',(x,y+depth/2-.1,z-.16),(width,.2,.5)),('S',(x,y-depth/2+.1,z-.16),(width,.2,.5)),('W',(x-width/2+.1,y,z-.16),(.2,depth,.5)),('E',(x+width/2-.1,y,z-.16),(.2,depth,.5))]:box(name+'_'+suffix,l,s,'stone')
def import_university():
    collection('CCP070_University_Additions_Blockout',(0,0,0))
    p=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/inventory/university/decoded/012f675cd6b5f5cb1222/decoded-static.json')
    d=json.loads(p.read_text(encoding='utf-8'))
    for i,g in enumerate(d['geometry']['groups']):
        o=mesh('University_STOCK_UNCHANGED_'+str(i),g['positions'],g['triangles'],'stock')
        for key,uvs in g.get('uv_layers',{}).items():
            layer=o.data.uv_layers.new(name=key)
            for poly in o.data.polygons:
                for li in poly.loop_indices:layer.data[li].uv=uvs[o.data.loops[li].vertex_index]
        o['native_source_model']=d['request']['logical_path'];o['stock_geometry_unchanged']=True
    return d['geometry']['group_count']
def view(asset=None,direction='iso',save=None,color='MATERIAL'):
    wanted=OFFSETS.get(asset) if asset else None
    for c in scene.collection.children:
        if c.name.startswith(PREFIX):
            for o in c.objects:o.hide_set(bool(asset and c.name!=asset))
    for o in bpy.context.selected_objects:o.select_set(False)
    target=Vector(wanted or (0,0,0))+Vector((0,0,1.5))
    rotations={'front':(0,-1,0),'rear':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'top':(0,0,1),'bottom':(0,0,-1),'iso':(1,-1,1.0),'iso_back':(-1,1,1.0)}
    eye=Vector(rotations[direction]);q=eye.to_track_quat('Z','Y')
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_rotation=q
            area.spaces.active.region_3d.view_perspective='ORTHO'
            area.spaces.active.region_3d.view_distance=(22 if 'University' in asset else 29) if asset else 85
            area.spaces.active.region_3d.view_location=target
            area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type=color
            scene.display.shading.color_type=color
            area.spaces.active.overlay.show_overlays=False
            if save:
                region=next(r for r in area.regions if r.type=='WINDOW')
                scene.render.filepath=str(OUT/save)
                with bpy.context.temp_override(area=area,region=region):bpy.ops.render.opengl(write_still=True,view_context=True)
            area.tag_redraw()
            return
    raise RuntimeError('No VIEW3D area')
def audit():
    rows={}
    for c in scene.collection.children:
        if c.name.startswith(PREFIX):
            objects=list(c.objects);verts=[o.matrix_world@v.co for o in objects if o.type=='MESH' for v in o.data.vertices]
            rows[c.name]={'objects':len(objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects if o.type=='MESH'),
                'finite':all(math.isfinite(x) for v in verts for x in v),
                'bounds':{'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)]},
                'shared_mesh_datablocks':[o.name for o in objects if o.type=='MESH' and o.data.users>1]}
    (OUT/'blockout-audit.json').write_text(json.dumps({'schema':'ccp-070-blockout-review/v1','assets':rows,'native_export':False,'native_cook':False,'native_render':False},indent=2),encoding='utf-8')
    return rows
init()
