"""Serialized Blender authoring, source QA, native FBX/rig exports and previews."""
import sys,math,importlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy,numpy as np
from mathutils import Vector,Matrix
from mesh import Builder,charts
from materials import atlas
from recipe import body,weapon
sys.path.append(str(ROOT/'tools/release_079'))
from rig_contract import read_contract,rig_text,fold_weights
def addon(name):return importlib.import_module(next(k for k in bpy.context.preferences.addons.keys() if k.endswith('.garrison'))+'.'+name)

def donor_anatomy(w,obj,source_rig,pattern):
    raw=np.empty(len(pattern.pixels),np.float32);pattern.pixels.foreach_get(raw);raw=raw.reshape(pattern.size[1],pattern.size[0],4)
    groups={g.index:g.name for g in obj.vertex_groups};uv=obj.data.uv_layers.active
    cache={}
    def fitted(vertex):
        if vertex.index not in cache:
            ws={groups[g.group]:g.weight for g in vertex.groups if g.weight>1e-7};co=Vector((0,0,0));total=sum(ws.values())
            for name,weight in ws.items():co+=(w.rig.data.bones[name].matrix_local@source_rig.data.bones[name].matrix_local.inverted()@(obj.matrix_world@vertex.co))*weight/total
            if co.z>1.56:co.z+=.09
            cache[vertex.index]=(co,ws)
        return cache[vertex.index]
    vertices=[];coords=[];weights=[];faces=[];keys={};accepted=0
    for face in obj.data.polygons:
        samples=[uv.data[li].uv for li in face.loop_indices]
        green=sum(float(raw[min(int(p.y*pattern.size[1]),pattern.size[1]-1),min(int(p.x*pattern.size[0]),pattern.size[0]-1),1]) for p in samples)/len(samples)
        head_fraction=sum(sum(g.weight for g in obj.data.vertices[i].groups if groups[g.group]=='metarig_head') for i in face.vertices)/len(face.vertices)
        if green<.25 and head_fraction<.8:continue
        fitted_points=[fitted(obj.data.vertices[i])[0] for i in face.vertices]
        if head_fraction>.5 and (max(p.z for p in fitted_points)>1.885 or min(p.z for p in fitted_points)<1.695):continue
        points=[obj.matrix_world@obj.data.vertices[i].co for i in face.vertices]
        # Mask selects skin. Position excludes any stray cloth/leg tint islands.
        if not (max(p.z for p in points)>1.57 or any(abs(p.x)>.47 and p.z<1.25 for p in points)):continue
        output=[];accepted+=1
        for li in face.loop_indices:
            vertex=obj.data.vertices[obj.data.loops[li].vertex_index];tuv=uv.data[li].uv;key=(vertex.index,round(tuv.x,6),round(tuv.y,6))
            if key not in keys:
                co,ws=fitted(vertex)
                keys[key]=len(vertices);vertices.append(co);coords.append(tuple(x if 0<=x<=1 else x%1 for x in tuv));weights.append(ws)
            output.append(keys[key])
        faces.append(output)
    assert accepted>30,accepted
    result=w.mesh('Reworked official Chinese head and hands',vertices,faces,coords,weights,charts()['skin'],'skin')
    bpy.context.view_layer.objects.active=result
    sub=result.modifiers.new('Anatomy surface refinement','SUBSURF');sub.levels=1;sub.subdivision_type='CATMULL_CLARK';bpy.ops.object.modifier_apply(modifier=sub.name)
    # Native skin-mask projection includes a tiny detached collar fragment.
    # Keep the main face and both hands; remove only that isolated fragment.
    links={v.index:set() for v in result.data.vertices}
    for edge in result.data.edges:
        a,b=edge.vertices;links[a].add(b);links[b].add(a)
    unseen=set(links);remove=[]
    while unseen:
        todo=[unseen.pop()];ids=set(todo)
        while todo:
            vertex=todo.pop();new=links[vertex]&unseen;unseen-=new;ids|=new;todo+=list(new)
        points=[result.data.vertices[i].co for i in ids]
        if len(ids)<40 and max(p.z for p in points)>1.5:remove.extend(ids)
    if remove:
        import bmesh
        bm=bmesh.new();bm.from_mesh(result.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(result.data);bm.free()
    # Fit the donor face to a readable game-scale head, rather than elongating
    # the neck to reach its source rest-space offset. Hand anatomy stays exact.
    for vertex in result.data.vertices:
        if vertex.co.z>1.5:
            vertex.co=Vector((vertex.co.x*1.25,(vertex.co.y+.03)*1.25-.015,(vertex.co.z-1.75)*1.25+1.71))
    return {'donor_skin_faces':accepted,'refined_vertices':len(result.data.vertices),'source':'official Chinese archer II','rest_transfer':'named-bone bind-space weighted transfer'}

def fold(obj,contract,lod):
    names={g.index:g.name for g in obj.vertex_groups};samples=[{names[g.group]:g.weight for g in v.groups if g.weight>1e-7} for v in obj.data.vertices]
    obj.vertex_groups.clear()
    for i,ws in enumerate(samples):
        value=fold_weights(ws,contract,lod);value=dict(sorted(value.items(),key=lambda p:-p[1])[:4]);total=sum(value.values())
        for name,weight in value.items():(obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)).add([i],weight/total,'REPLACE')

def preview(lods,rig,mat,dest):
    scene=bpy.context.scene
    for o in scene.objects:
        if o.type=='MESH':o.hide_render=o!=lods[0]
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=960;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('083 studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.06,.075,.095,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    for name,position,power,size in [('Key',(3,-4,5),500,4),('Fill',(-3,-2,2),220,3),('Rim',(1,3,4),450,3)]:
        light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(light);light.location=position;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=power;light.data.shape='DISK';light.data.size=size
    vs=[lods[0].matrix_world@v.co for v in lods[0].data.vertices];lo=Vector([min(p[i] for p in vs) for i in range(3)]);hi=Vector([max(p[i] for p in vs) for i in range(3)]);center=(lo+hi)/2
    cam=bpy.data.objects.new('083 review camera',bpy.data.cameras.new('083 review camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=max(hi-lo)*1.19
    scene.view_settings.view_transform='AgX'
    directions={'front':(0,-5,.1),'back':(0,5,.1),'left':(-5,0,.1),'right':(5,0,.1),'top':(0,.01,5),'bottom':(0,.01,-5),'threequarter':(3,-5,1.5)}
    for label,position in directions.items():
        cam.location=center+Vector(position);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(dest/(label+'.png'));bpy.ops.render.render(write_still=True)
    for label,color in [('red',(.65,.025,.018,1)),('yellow',(.8,.52,.02,1))]:
        mat.node_tree.nodes['OWNER PREVIEW'].outputs[0].default_value=color
        cam.location=center+Vector((3,-5,1.5));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(dest/(label+'.png'));bpy.ops.render.render(write_still=True)
    mat.node_tree.nodes['OWNER PREVIEW'].outputs[0].default_value=(.025,.18,.65,1)

def main():
    guard();assert bpy.app.background
    family,revision=sys.argv[sys.argv.index('--')+1:];age=int(family[-1]);human=family.startswith('skirmisher')
    a=ART/family/revision;e=EXPORT/family/revision;o=OUT/'art'/family/revision
    for p in (a,e,o):p.mkdir(parents=True,exist_ok=False)
    source=ROOT/f'art/authoring/release_079/skirmisher{age}/r3/model.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
    rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST';original_binds={b.name:[list(r) for r in b.matrix_local] for b in rig.data.bones}
    # Import a separate official donor, keeping the target skeleton untouched.
    manifest=next((OUT/'references/chinese-archer').glob('*/decoded-static.json'));data=read(manifest);data['manifest_path']=str(manifest)
    parent=bpy.data.objects.new('083 official anatomy reference',None);bpy.context.scene.collection.objects.link(parent)
    before=set(bpy.data.objects);addon('decode_projection')._apply_decoded_static(parent,data,create_controls=False);refs=set(bpy.data.objects)-before
    donor=next(x for x in refs if x.type=='MESH' and x.get('garrison_lod_level')==1);donor_rig=next(x for x in refs if x.type=='ARMATURE')
    nodes=donor.data.materials[0].node_tree.nodes;images={name:next(n.image for n in nodes if n.type=='TEX_IMAGE' and n.image and slot in n.label) for name,slot in [('albedo','Albedo'),('pattern','Pattern masks')]}
    for x in list(bpy.data.objects):
        if x not in refs and x!=rig and x!=parent:bpy.data.objects.remove(x,do_unlink=True)
    for old_material in bpy.data.materials:old_material.name='Reference_'+old_material.name
    material,textures=atlas(e,age,images);w=Builder(rig if human else None,material)
    provenance={}
    if human:provenance=donor_anatomy(w,donor,donor_rig,images['pattern']);body(w,age)
    else:weapon(w,age,family.startswith('projectile'))
    for x in refs|{parent}:
        try:bpy.data.objects.remove(x,do_unlink=True)
        except ReferenceError:pass  # decode helper may already consume its root
    if not human:bpy.data.objects.remove(rig,do_unlink=True);rig=None
    contract=read(OUT/f'baseline/contract{age}.json') if human else None
    components=[{'name':x.name,'vertices':len(x.data.vertices),'triangles':sum(len(p.vertices)-2 for p in x.data.polygons),'surface':x['083_surface']} for x in w.parts]
    # Keep editable individual construction parts and separate export LOD copies.
    bpy.ops.object.select_all(action='DESELECT');copies=[]
    for obj in w.parts:
        c=obj.copy();c.data=obj.data.copy();scene=bpy.context.scene;scene.collection.objects.link(c);c.hide_set(False);c.select_set(True);copies.append(c)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();lod1=bpy.context.object;lod1.name='body_lod1'
    # Triangulate before LOD generation so native triangulation is deterministic.
    tri=lod1.modifiers.new('Explicit triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name);lods=[lod1]
    for lod,ratio in [(2,.52),(3,.27)]:
        obj=lod1.copy();obj.data=lod1.data.copy();obj.name='body_lod'+str(lod);bpy.context.scene.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj
        dec=obj.modifiers.new('Native geometry LOD','DECIMATE');dec.ratio=ratio;bpy.ops.object.modifier_apply(modifier=dec.name)
        tri=obj.modifiers.new('Explicit triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
        mat=material.copy();mat.name='lod'+str(lod);obj.data.materials.clear();obj.data.materials.append(mat);lods.append(obj)
    for i,obj in enumerate(lods,1):
        import bmesh
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        if human:fold(obj,contract,i)
        assert len(obj.data.uv_layers)==1
        assert all(math.isfinite(f) for v in obj.data.vertices for f in v.co)
        assert all(0<=uv.uv.x<=1 and 0<=uv.uv.y<=1 for uv in obj.data.uv_layers.active.data)
    counts=[len(obj.data.polygons) for obj in lods];assert all(n<=cap for n,cap in zip(counts,[20000,10000,5000])),counts
    mask_areas=[]
    arr=np.empty(len(textures['pattern'].pixels),np.float32);textures['pattern'].pixels.foreach_get(arr);arr=arr.reshape(2048,2048,4)
    for obj in lods:
        total=masked=0
        for face in obj.data.polygons:
            uv=sum((obj.data.uv_layers.active.data[i].uv for i in face.loop_indices),Vector((0,0)))/len(face.vertices)
            total+=face.area
            if arr[min(int(uv.y*2048),2047),min(int(uv.x*2048),2047),0]>.5:masked+=face.area
        mask_areas.append(masked/total)
    if human:assert all(.20<f<.85 for f in mask_areas),mask_areas
    for obj in w.parts:obj.hide_render=True;obj.hide_set(True)
    for obj in lods[1:]:obj.hide_render=True;obj.hide_set(True)
    if human:
        assert original_binds=={b.name:[list(r) for r in b.matrix_local] for b in rig.data.bones}
        addon('unit_export').export_unit_model(rig,lods,e/'model.fbx',addon('unit_export').skeleton_records(rig),three_lods=False)
        (e/'model.rig').write_text(rig_text(contract))
    else:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in lods:
            obj.hide_set(False);obj.select_set(True)
            for uv in obj.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
        bpy.ops.export_scene.fbx(filepath=str(e/'model.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
        for obj in lods:
            for uv in obj.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(a/'model.blend'))
    result={'family':family,'revision':revision,'source':str(a/'model.blend'),'source_sha256':sha(a/'model.blend'),'export':str(e),'files':{p.name:sha(p) for p in e.iterdir() if p.is_file()},'lod_triangles':counts,'donor_contract':contract,'owner_mask_surface_fraction_by_lod':mask_areas,'components':components,'contacts':w.contacts,'anatomy_provenance':provenance,'rest_binds_exact':human,'native_acceptance':False,'texture_size':2048}
    write(o/'export.json',result)
    preview(lods,rig,material,o)
    print('083_ART_EXPORTED',family,counts,mask_areas)
if __name__=='__main__':main()
