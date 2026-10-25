"""Check actual decoded walk contacts, pack seating and all three LOD meshes."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
check_storage(ROOT,CFG)
DEST=ROOT/'output/release_082_animation/qa-v2';DEST.mkdir(parents=True,exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/release_082_animation/v2/buffalo-idle-walk.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;rig.animation_data.action=None
sys.path.insert(0,str(Path(CFG['garrison_extension']).parent))
from garrison.unit_animation import import_clip_action
proof=json.loads((ROOT/'output/release_082_animation/source-v2/proof.json').read_text())
cloth=bpy.data.objects['081_Padded_saddlecloth'];borders=[o for o in bpy.data.objects if o.name.startswith(('081_Cloth_border_','081_Lower_cloth_border_'))]
report={'rig_bones':len(rig.data.bones),'source_ik_maximum_error':proof['maximum_ik_target_error'],'motions':{}}
body=bpy.data.objects['body_lod1']
sole_groups={}
for foot,bones in [('front_l',{'fronttoes_l','fronttoesend_l'}),('front_r',{'fronttoes_r','fronttoesend_r'}),('back_l',{'backtoes3_l','backtoes4_l'}),('back_r',{'backtoes3_r','backtoes4_r'})]:
    indices={g.index for g in body.vertex_groups if g.name in bones}
    sole_groups[foot]=[v.index for v in body.data.vertices if any(g.group in indices and g.weight>.5 for g in v.groups)]
    assert sole_groups[foot],foot
for label,index in [('idle',10),('walk',3)]:
    payload=json.loads((ROOT/f'output/release_082_animation/encoded-v3/idle-walk-{index}-sampled.json').read_text())
    _,action=import_clip_action(rig,payload,fps=30,root_motion=False)
    count=payload['frame_count'];distances=[];lods={};contacts={};endpoints=[];sole_heights={k:[] for k in sole_groups}
    frames=list(range(1,count+1)) if label=='walk' else [1,38,75,112,149,186,223,260,297]
    for frame in frames:
        scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();er=rig.evaluated_get(deps)
        if frame in [1,count]:endpoints.append({b.name:b.matrix.copy() for b in er.pose.bones})
        if label=='walk':
            phase=(frame-1)/32
            root=payload['root_motion']['samples'][frame-1]['translation_xyz']
            travel=Vector((-root[0],-root[2],root[1]))
            for ankle,offset in [('backankle_l',0.),('frontankle_l',.25),('backankle_r',.5),('frontankle_r',.75)]:
                p=(phase+offset)%1.
                if p<proof['stance_fraction']:
                    bone=er.pose.bones[ankle];point=bone.matrix@Vector((0,bone.length,0))+travel
                    key=ankle+':'+str(math.floor(phase+offset))
                    contacts.setdefault(key,[]).append(list(point))
            eo=body.evaluated_get(deps);mesh=eo.to_mesh()
            for foot,offset in [('back_l',0.),('front_l',.25),('back_r',.5),('front_r',.75)]:
                if (phase+offset)%1.<proof['stance_fraction']:
                    sole_heights[foot].append(min(mesh.vertices[i].co.z for i in sole_groups[foot]))
            eo.to_mesh_clear()
        if frame not in [1,9,17,25,33,65,97,count] and label=='walk':continue
        for name in ['body_lod1','body_lod2','body_lod3']:
            obj=bpy.data.objects[name];evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
            assert all(math.isfinite(x) for v in mesh.vertices for x in v.co)
            lods[name]=len(mesh.vertices);evaluated.to_mesh_clear()
        ec=cloth.evaluated_get(deps);cm=ec.to_mesh();bvh=BVHTree.FromPolygons([v.co for v in cm.vertices],[tuple(p.vertices) for p in cm.polygons])
        maximum=0
        for obj in borders:
            eo=obj.evaluated_get(deps);mesh=eo.to_mesh()
            maximum=max(maximum,max(bvh.find_nearest(v.co)[3] for v in mesh.vertices));eo.to_mesh_clear()
        ec.to_mesh_clear();distances.append(maximum)
    loop=max(abs(a-b) for name in endpoints[0] for ra,rb in zip(endpoints[0][name],endpoints[1][name]) for a,b in zip(ra,rb))
    assert loop<.002,loop
    drift=max(distances)-min(distances);assert drift<.025,drift
    contact_drift=max((max((Vector(p)-Vector(points[0])).length for p in points) for points in contacts.values()),default=0)
    assert math.isfinite(contact_drift) and contact_drift<.01,contact_drift
    sole_summary={k:{'minimum':min(v),'maximum':max(v),'variation':max(v)-min(v)} for k,v in sole_heights.items() if v}
    assert all(v['variation']<.01 for v in sole_summary.values()),sole_summary
    report['motions'][label]={'all_lods_finite_vertices':lods,'loop_matrix_error':loop,'cloth_border_surface_distance_drift':drift,'maximum_native_reference_world_ankle_target_stance_drift':contact_drift,'weighted_toe_region_lowest_vertex_stance_heights':sole_summary,'stance_segments':contacts}
(DEST/'proof.json').write_text(json.dumps(report,indent=2))
print('QA_PASSED',{k:{a:b for a,b in v.items() if a!='stance_segments'} for k,v in report['motions'].items()})
