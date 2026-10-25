"""Replace only three display animals, preserving architectural geometry/atlas."""
import sys,math,hashlib,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from common import *
def geomhash(o):
    return hashlib.sha256(json.dumps({'vertices':[list(v.co) for v in o.data.vertices],'polys':[list(p.vertices) for p in o.data.polygons],'uv':[list(x.uv) for x in o.data.uv_layers.active.data]}).encode()).hexdigest()
def main():
    guard();revision='r2';a=ART/'ministry'/revision;e=EXPORT/'ministry'/revision;out=OUT/'art/ministry'/revision
    if (a/'ministry.blend').exists():raise FileExistsError('Immutable Ministry master')
    for p in (a,e,out):p.mkdir(parents=True,exist_ok=True)
    base=ROOT/'art/authoring/release_0710/ministry/r1/ministry.blend'
    bpy.ops.wm.open_mainfile(filepath=str(base))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];upper=next(o for o in objects if 'superstructure' in o.name);foundation=next(o for o in objects if 'foundation' in o.name)
    mat=upper.data.materials[0];removed=[]
    for o in list(objects):
        if o.name.startswith('079_Static_buffalo_'):
            removed.append(o.name);objects.remove(o);bpy.data.objects.remove(o,do_unlink=True)
    assert len(removed)==3
    protected={o.name:geomhash(o) for o in objects}
    with bpy.data.libraries.load(str(ART/'buffalo/r4/model.blend'),link=False) as (src,dst):dst.objects=['081_Unladen_master','081_Native_cattle_45']
    template=next(o for o in dst.objects if o.type=='MESH');rig=next(o for o in dst.objects if o.type=='ARMATURE')
    bpy.context.scene.collection.objects.link(template);bpy.context.scene.collection.objects.link(rig)
    template.hide_set(False);template.hide_viewport=False;rig.hide_set(False);rig.data.pose_position='POSE'
    poses=[{'head_m':(.03,0,.06),'ear_l':(.10,0,0)},{'neck_m':(.08,0,0),'head_m':(.16,0,-.04),'tail2_m':(0,.12,0)},{'neck1_m':(-.04,0,.08),'head_m':(-.06,0,.15),'ear_r':(-.12,0,0)}]
    adds=[];boundsproof=[]
    for i,(x,y,yaw) in enumerate(((-4.4,-5.6,90),(-4.4,-2.4,90),(4.4,-6,90))):
        for pb in rig.pose.bones:pb.matrix_basis.identity()
        for name,rot in poses[i].items():rig.pose.bones[name].rotation_mode='XYZ';rig.pose.bones[name].rotation_euler=rot
        bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();mesh=bpy.data.meshes.new_from_object(template.evaluated_get(deps),depsgraph=deps)
        o=bpy.data.objects.new('081_Static_buffalo_'+str(i+1),mesh);bpy.context.scene.collection.objects.link(o)
        angle=math.radians(yaw)
        for v in mesh.vertices:
            aa,bb,z=v.co;v.co=(aa*math.cos(angle)-bb*math.sin(angle)+x,aa*math.sin(angle)+bb*math.cos(angle)+y,z)
        lo=[min(v.co[k] for v in mesh.vertices) for k in range(3)];hi=[max(v.co[k] for v in mesh.vertices) for k in range(3)]
        for v in mesh.vertices:v.co.x+=x-(lo[0]+hi[0])/2;v.co.y+=y-(lo[1]+hi[1])/2;v.co.z+=.08-lo[2]
        bounds=[[min(v.co[k] for v in mesh.vertices),max(v.co[k] for v in mesh.vertices)] for k in range(3)]
        pen=(-7.5,-1.25,-7.45,-.6) if i<2 else (1.25,7.5,-7.45,-4.52)
        assert bounds[0][0]>pen[0]+.25 and bounds[0][1]<pen[1]-.25 and bounds[1][0]>pen[2]+.25 and bounds[1][1]<pen[3]-.25,(i,bounds)
        for uv in mesh.uv_layers.active.data:uv.uv.x=uv.uv.x*.5+.5
        mesh.materials.clear();mesh.materials.append(mat);o['garrison_building_first_stage']=20;o.hide_render=False
        boundsproof.append({'animal':o.name,'bounds':bounds,'pen':pen,'minimum_margin':.25,'pose':poses[i],'geometry_sha256':geomhash(o),'no_work_pack':True});adds.append(o)
    assert len({r['geometry_sha256'] for r in boundsproof})==3
    bpy.data.objects.remove(template,do_unlink=True);bpy.data.objects.remove(rig,do_unlink=True)
    textureproof=[]
    for name in ('albedo','normal','roughness','metalness'):
        old=bpy.data.images.load(str(ROOT/f'art/exports/release_0710/ministry/r1/{name}.png'),check_existing=False)
        new=bpy.data.images.load(str(EXPORT/f'buffalo/r4/{name}.png'),check_existing=False);w,h=old.size;new.scale(w//2,h)
        pixels=np.array(old.pixels[:],dtype=np.float32).reshape(h,w,4);before=pixels[:,:w//2].copy();pixels[:,w//2:]=np.array(new.pixels[:],dtype=np.float32).reshape(h,w//2,4)
        old.pixels.foreach_set(pixels.ravel());old.filepath_raw=str(e/(name+'.png'));old.file_format='PNG';old.save();assert np.array_equal(before,pixels[:,:w//2]);old.pack()
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image and name in node.image.name.lower():node.image=old
        textureproof.append({'map':name,'architecture_half_exact':True,'architecture_pixel_sha256':hashlib.sha256(before.tobytes()).hexdigest()})
    assert protected=={o.name:geomhash(o) for o in objects}
    sys.path.append(str(ROOT/'tools/release_020'));from model_ministry_farm_hideout_runner import join_stage
    copies=[]
    for obj in [o for o in objects if o!=foundation]+adds:
        c=obj.copy();c.data=obj.data.copy();bpy.context.scene.collection.objects.link(c);copies.append(c)
    export_upper=join_stage(copies,'081_export_superstructure',20)
    bpy.ops.object.select_all(action='DESELECT');clones=[]
    for i,obj in enumerate((foundation,export_upper)):
        c=obj.copy();c.data=obj.data.copy();c.name=f'garrison_part_{i:04}';bpy.context.scene.collection.objects.link(c);c.hide_set(False);c.select_set(True);clones.append(c)
        for uv in c.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
    bpy.context.view_layer.objects.active=clones[0]
    bpy.ops.export_scene.fbx(filepath=str(e/'model.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',use_custom_props=False)
    for c in clones+[export_upper]:bpy.data.objects.remove(c,do_unlink=True)
    (e/'building.json').write_bytes((ROOT/'art/exports/release_0710/ministry/r1/building.json').read_bytes())
    for im in list(bpy.data.images):
        if im.users==0:bpy.data.images.remove(im)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(a/'ministry.blend'))
    write(out/'receipt.json',{'source':str(a/'ministry.blend'),'source_sha256':sha(a/'ministry.blend'),'baseline_source_sha256':sha(base),'export_hashes':{p.name:sha(p) for p in e.iterdir()},'preflight':{'ok':True,'method':'finite geometry; exact non-herd mesh/UV hashes; distinct skinned poses; numeric pen bounds'},'unchanged_mesh_hashes':protected,'architecture_texture_proof':textureproof,'animals':boundsproof,'buffalo_count':3,'native_acceptance':False})
    print('MINISTRY_EXPORTED',len(protected),'unchanged meshes')
if __name__=='__main__':main()
