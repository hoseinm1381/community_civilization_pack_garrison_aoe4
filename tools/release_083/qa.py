"""Selected-source QA bound to the exact fresh cook and inherited native poses."""
from pathlib import Path
import sys,math,importlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy,numpy as np
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from author import preview
guard();label=sys.argv[sys.argv.index('--')+1];selection=read(RECIPES/'selection.json');cook=read(OUT/'cooks'/label/'receipt.json');decoded=read(OUT/'cooks'/label/'decoded-proof.json')
key=next(k for k in bpy.context.preferences.addons.keys() if k.endswith('.garrison'));animation_module=importlib.import_module(key+'.unit_animation');import_action=animation_module.import_clip_action
rc=importlib.import_module(key+'.relic_chunky')
weapon_to_socket=Matrix(animation_module.BONE_AXES).inverted()@Matrix(animation_module.COOKED_TO_BLENDER).inverted()
dest=OUT/(sys.argv[sys.argv.index('--')+2] if len(sys.argv)>sys.argv.index('--')+2 else 'qa-v2');dest.mkdir(exist_ok=False);result={}
for family,revision in selection.items():
    export=read(OUT/'art'/family/revision/'export.json');assert sha(export['source'])==export['source_sha256'];bpy.ops.wm.open_mainfile(filepath=export['source'])
    scene=bpy.context.scene;lods=[bpy.data.objects['body_lod'+str(i)] for i in [1,2,3]]
    record={'source_sha256':export['source_sha256'],'export_receipt_sha256':sha(OUT/'art'/family/revision/'export.json'),'all_lods':{},'contacts':export['contacts']}
    native_manifest=read(decoded[family]['manifest'])
    for i,obj in enumerate(lods,1):
        assert len(obj.data.polygons)==export['lod_triangles'][i-1]
        assert obj.data.materials[0].name=='lod'+str(i)
        assert all(math.isfinite(x) for v in obj.data.vertices for x in v.co)
        assert all(0<=uv.uv.x<=1 and 0<=uv.uv.y<=1 for uv in obj.data.uv_layers.active.data)
        record['all_lods'][obj.name]={'triangles':len(obj.data.polygons),'vertices':len(obj.data.vertices),'uv_finite_inside_atlas':True}
        positions=native_manifest['geometry']['groups'][i-1]['positions'];tree=KDTree(len(positions))
        for j,position in enumerate(positions):tree.insert(Vector(position),j)
        tree.balance();geometry_error=max(tree.find(v.co)[2] for v in obj.data.vertices)
        assert geometry_error<.003,(family,i,geometry_error)
        record['all_lods'][obj.name]['native_vertex_maximum_quantization_error']=geometry_error
    if not family.startswith('skirmisher'):
        tipaxis=1 if family.startswith('projectile') else 2
        vs=[v.co for v in lods[0].data.vertices];tip=min(v[tipaxis] for v in vs);butt=max(v[tipaxis] for v in vs)
        assert tip<-.1 and butt>1.3
        native_points=native_manifest['geometry']['groups'][0]['positions']
        ntip=min(p[tipaxis] for p in native_points);nbutt=max(p[tipaxis] for p in native_points)
        assert abs(ntip-tip)<.003 and abs(nbutt-butt)<.003
        grip=Vector((.605*.037,.605*.027,.605))
        if tipaxis==1:grip=Vector((grip.x,(grip.z+.12)/1.805*1.709-.3535,-grip.y))
        native_grip_distance=min((Vector(p)-grip).length for p in native_points)
        assert native_grip_distance<.03,(family,native_grip_distance)
        record.update(tip_axis='-Y' if tipaxis==1 else '-Z',tip=tip,butt=butt,native_tip=ntip,native_butt=nbutt,grip_anchor=list(grip),native_grip_surface_distance=native_grip_distance)
        result[family]=record;continue
    rig=next(mod.object for mod in lods[0].modifiers if mod.type=='ARMATURE');assert len(rig.data.bones)==48
    old_binds={b['name']:b['local_reference_transform'] for b in read(next((OUT/'cooks'/label/'decoded'/family).glob('*/decoded-static.json')))['skeleton']['bones']}
    assert set(old_binds)==set(b.name for b in rig.data.bones)
    modelpath='art/scenario/garrison/cc076/'+family+'/model.rgm'
    packed=(OUT/'cooks'/label/'readback'/modelpath).read_bytes()
    baseline=(ROOT/'output/release_081/delivery/final-v1/readback'/modelpath).read_bytes()
    def bind_bytes(raw):
        chunk=next(c for c in rc.walk(rc.parse(raw).roots) if c.tag==b'SKLN')
        return chunk.payload[export['donor_contract']['bind_offset']:]
    assert bind_bytes(packed)==bind_bytes(baseline),(family,'native bind transforms changed')
    record['native_bind_transform_bytes_exact']=True
    # Compare native packed mask pixels with source map and all LOD UV areas.
    source=bpy.data.images.get('083_pattern');assert source
    a=np.empty(len(source.pixels),np.float32);source.pixels.foreach_get(a);a=a.reshape(2048,2048,4)
    dds=bpy.data.images.load(decoded[family]['pattern_projections'][0],check_existing=False);dds.colorspace_settings.name='Non-Color'
    b=np.empty(len(dds.pixels),np.float32);dds.pixels.foreach_get(b);b=b.reshape(dds.size[1],dds.size[0],4)
    assert b.shape==a.shape
    # Native decode projects DDS rows and mesh UV V in the opposite convention
    # to the source PNG/FBX. Compare pixels after that documented paired change;
    # measure coverage on actual decoded UVs below, never source UVs with DDS.
    points=np.arange(13,2048,31);error=float(np.max(np.abs(a[points[:,None],points[None,:],:3]-b[::-1][points[:,None],points[None,:],:3])))
    assert error<.04,(family,error)
    manifest=Path(decoded[family]['manifest']);data=read(manifest);data['manifest_path']=str(manifest)
    parent=bpy.data.objects.new('083 actual native mask check',None);scene.collection.objects.link(parent)
    before=set(bpy.data.objects)
    importlib.import_module(key+'.decode_projection')._apply_decoded_static(parent,data,create_controls=False)
    native_objects=set(bpy.data.objects)-before
    native_lods=sorted((o for o in native_objects if o.type=='MESH'),key=lambda o:o['garrison_lod_level'])
    assert [o['garrison_lod_level'] for o in native_lods]==[1,2,3]
    mask_areas=[]
    for obj in native_lods:
        total=masked=0
        for face in obj.data.polygons:
            uv=sum((obj.data.uv_layers.active.data[i].uv for i in face.loop_indices),Vector((0,0)))/len(face.vertices);total+=face.area
            if b[min(int(uv.y*2048),2047),min(int(uv.x*2048),2047),0]>.5:masked+=face.area
        mask_areas.append(masked/total)
    assert max(abs(x-y) for x,y in zip(mask_areas,export['owner_mask_surface_fraction_by_lod']))<.01
    for obj in native_objects:bpy.data.objects.remove(obj,do_unlink=True)
    leftover=bpy.data.objects.get('083 actual native mask check')
    if leftover is not None:bpy.data.objects.remove(leftover,do_unlink=True)
    record.update(packed_pattern_maximum_grid_error=error,packed_owner_mask_surface_fraction_by_lod=mask_areas,mask_coordinate_convention='DDS rows and decoded mesh UV V paired; source pixel comparison uses vertical reflection',motions={})
    # Source-to-native hierarchy is unchanged; sample the actually consumed owner.
    rig.data.pose_position='POSE';hand_ids={g.index for g in lods[0].vertex_groups if g.name.startswith('metarig_rarm') and any(w in g.name for w in ['palm','thumb','index','middle'])}
    hand_vertices=[v.index for v in lods[0].data.vertices if any(g.group in hand_ids and g.weight>.5 for g in v.groups)];assert hand_vertices
    for motion in ['idle','walk','throw','reload','stop','death']:
        payload=read(OUT/'motion-samples'/(motion+'.json'));_,action=import_action(rig,payload,fps=30,root_motion=False)
        count=payload['frame_count'];frames=sorted({1,count,1+int((count-1)*.2),1+int((count-1)*.4),1+int((count-1)*.6),1+int((count-1)*.8)})
        clearances=[];max_extent=0
        for frame in frames:
            scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();er=rig.evaluated_get(deps)
            for obj in lods:
                evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();points=[v.co for v in mesh.vertices]
                assert all(math.isfinite(x) for p in points for x in p)
                extent=max(max(p[i] for p in points)-min(p[i] for p in points) for i in range(3));assert extent<4,(family,motion,frame,extent);max_extent=max(max_extent,extent)
                if obj==lods[0]:
                    tree=KDTree(len(hand_vertices))
                    for j,index in enumerate(hand_vertices):tree.insert(mesh.vertices[index].co,j)
                    tree.balance();grip=er.pose.bones['metarig_rarmpalmsocket'].matrix@weapon_to_socket@Vector((.605*.037,.605*.027,.605));clearances.append(tree.find(grip)[2])
                evaluated.to_mesh_clear()
        # Native death releases/stows the weapon; the grip need not stay in-hand.
        if motion!='death':assert max(clearances)<.11,(family,motion,max(clearances))
        record['motions'][motion]={'sampled_frames':frames,'maximum_extent':max_extent,'maximum_transformed_grip_to_hand_vertex_distance':max(clearances),'grip_contact_required':motion!='death'}
        if motion=='throw':
            # Retain the throw pose for a later source review render.
            record['throw_review_frame']=frames[len(frames)//2]
    rig.animation_data.action=None;rig.data.pose_position='REST';scene.frame_set(1)
    # Three LODs, two contrasting owners, same views and lights.
    renderdest=dest/family;renderdest.mkdir()
    for lod,obj in enumerate(lods,1):
        # preview renders source nodes, after packed-channel equivalence above.
        for helper in list(scene.objects):
            if helper.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(helper,do_unlink=True)
        chosen=[obj]+[x for x in lods if x!=obj]
        preview(chosen,rig,obj.data.materials[0],renderdest/('lod'+str(lod)))
    record['all_lod_owner_previews']=True;result[family]=record
    print('083_SOURCE_QA',family,mask_areas,flush=True)
proof={'passed':True,'selection':selection,'cook_sha256':cook['archive_sha256'],'export_receipt_sha256':{f:sha(OUT/'art'/f/r/'export.json') for f,r in selection.items()},'families':result,'native_game_appearance':False,'motion_owner':'base_spearshield; native javelin and reaction samples'}
write(OUT/'source-qa.json',proof);print('083_SOURCE_QA_PASSED')
