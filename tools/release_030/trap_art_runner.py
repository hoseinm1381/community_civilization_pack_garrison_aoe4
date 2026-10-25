"""Small deterministic Blender helpers for the owned 0.3.0 trap art only."""
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf8')

def mesh(name, verts, faces, mat, uv_kind='wood'):
    data=bpy.data.meshes.new(name); data.from_pydata(verts, [], faces); data.update()
    obj=bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(obj)
    data.materials.append(mat)
    bm=bmesh.new(); bm.from_mesh(data); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(data); bm.free()
    uv=data.uv_layers.new(name='UVMap')
    # Each complete island occupies a padded region of the shared atlas.
    for poly in data.polygons:
        coords=[data.vertices[data.loops[li].vertex_index].co for li in poly.loop_indices]
        tangent=Vector((-poly.normal.y,poly.normal.x,0))
        if tangent.length<.01: tangent=Vector((1,0,0))
        tangent.normalize(); bitangent=poly.normal.cross(tangent).normalized()
        points=[(co.dot(tangent),co.dot(bitangent)) for co in coords]
        low=[min(p[i] for p in points) for i in (0,1)]; high=[max(p[i] for p in points) for i in (0,1)]
        region={'wood':(.025+((sum(map(ord,name))+poly.index*17)%31)/100,.045,.10,.90),'earth':(.52,.03,.45,.43),'leaf':(.52,.53,.45,.43),'cut':(.53,.04,.18,.90)}[uv_kind]
        for li,point in zip(poly.loop_indices,points):
            uv.data[li].uv=tuple(region[i]+region[i+2]*(point[i]-low[i])/max(high[i]-low[i],1e-9) for i in (0,1))
    return obj

def join_parts(objs, name, stage):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs: obj.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join()
    obj=bpy.context.object; obj.name=name; obj['garrison_building_first_stage']=stage
    return obj

def aim(obj, point): obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

def validate(objects):
    result=[]
    for obj in objects:
        bm=bmesh.new(); bm.from_mesh(obj.data)
        row={'object':obj.name,'vertices':len(bm.verts),'polygons':len(bm.faces),
             'triangles':sum(len(f.verts)-2 for f in bm.faces),
             'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),
             'degenerate_faces':sum(f.calc_area()<1e-9 for f in bm.faces),
             'uv_loops':len(obj.data.uv_layers.active.data),
             'material_count':len(obj.data.materials),'single_user':obj.data.users==1,
             'volume':bm.calc_volume(signed=True)}
        bm.free(); result.append(row)
        assert row['non_manifold_edges']==0 and row['degenerate_faces']==0 and row['volume']>0,row
    return result

def render(objects, output, width):
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=8
    scene.render.resolution_x=900; scene.render.resolution_y=740; scene.render.resolution_percentage=100
    scene.world.color=(.18,.18,.18); scene.view_settings.view_transform='AgX'
    lightdata=bpy.data.lights.new('TrapPreview_Key','AREA'); light=bpy.data.objects.new('TrapPreview_Key',lightdata)
    scene.collection.objects.link(light); light.location=(width*.4,-width*.5,width*1.5); lightdata.energy=width*width*90; lightdata.shape='DISK'; lightdata.size=width
    camera_data=bpy.data.cameras.new('TrapPreview_Camera'); camera=bpy.data.objects.new('TrapPreview_Camera',camera_data); scene.collection.objects.link(camera); scene.camera=camera
    camera_data.type='ORTHO'
    views=[('game_angle',(width*.75,-width*.95,width*1.1),width*1.25),('close',(width*.65,-width*.8,width*.6),width*1.05),('top',(0,0,width*2),width*1.15),('front',(0,-width*2,.25*width),width*1.15),('back',(0,width*2,.25*width),width*1.15),('left',(-width*2,0,.25*width),width*1.15),('right',(width*2,0,.25*width),width*1.15),('bottom',(0,0,-width*2),width*1.15)]
    for label, position, ortho in views:
        camera.location=position; aim(camera,(0,0,width*.08)); camera_data.ortho_scale=ortho
        scene.render.filepath=str(output/(label+'.png')); bpy.ops.render.render(write_still=True)
    # Camera is a presentation helper added after geometry validation.
    for obj in [light,camera]: bpy.data.objects.remove(obj,do_unlink=True)

def export_building(objects, target, schema):
    from garrison import building_project
    building_project.parts([{'name':o.name,'first_stage':o.get(building_project.STAGE_PROPERTY)} for o in objects], 'english-house')
    target.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    names=[]
    for index,obj in enumerate(objects):
        clone=obj.copy(); clone.data=obj.data.copy(); bpy.context.scene.collection.objects.link(clone)
        clone.name=f'garrison_part_{index:04}'
        for loop in clone.data.uv_layers.active.data: loop.uv.y=1-loop.uv.y
        clone.select_set(True); names.append(clone)
    bpy.context.view_layer.objects.active=names[0]
    bpy.ops.export_scene.fbx(filepath=str(target/'model.fbx'), use_selection=True, object_types={'MESH'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',use_custom_props=False)
    manifest={'schema':schema,'profile':'english-house','parts':[{'name':o.name,'first_stage':int(src['garrison_building_first_stage'])} for o,src in zip(names,objects)],'material_name':objects[0].data.materials[0].name,'textures':{'albedo':'albedo.png','normal':'normal.png','roughness':'roughness.png','metalness':'metalness.png'}}
    write(target/'building.json',manifest)
    for obj in names: bpy.data.objects.remove(obj,do_unlink=True)
    return manifest

