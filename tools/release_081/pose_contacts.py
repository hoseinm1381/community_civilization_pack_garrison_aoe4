"""Measure cloth-border contact through source-only Actions, never native proof."""
import bpy,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from common import *
guard();bpy.ops.wm.open_mainfile(filepath=str(ART/'animation/buffalo-trial.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='POSE'
cloth=bpy.data.objects['081_Padded_saddlecloth'];borders=[o for o in bpy.data.objects if o.name.startswith(('081_Cloth_border_','081_Lower_cloth_border_'))]
results=[]
for action in bpy.data.actions:
    if not action.name.startswith('buffalo_'):continue
    rig.animation_data.action=action;frames=[1,16,31,46,61,76,91,106,121] if 'idle' in action.name else [1,4,7,10,13,16,19,22,25]
    samples=[]
    for frame in frames:
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
        ec=cloth.evaluated_get(deps);cm=ec.to_mesh();bvh=BVHTree.FromPolygons([v.co for v in cm.vertices],[tuple(p.vertices) for p in cm.polygons])
        distances=[]
        for o in borders:
            eo=o.evaluated_get(deps);mesh=eo.to_mesh()
            distances.extend(bvh.find_nearest(v.co)[3] for v in mesh.vertices);eo.to_mesh_clear()
        ec.to_mesh_clear();samples.append({'frame':frame,'maximum_surface_distance':max(distances)})
    drift=max(s['maximum_surface_distance'] for s in samples)-min(s['maximum_surface_distance'] for s in samples)
    assert drift<.025,('Cloth border separates during source trial',action.name,drift)
    results.append({'action':action.name,'samples':samples,'distance_drift':drift,'maximum_admitted_source_drift':.025})
write(OUT/'art/animation/cloth-contact.json',{'passed':True,'checks':results,'source_only':True,'native_motion_contact_tested':False})
print('SOURCE_POSED_CLOTH_CONTACTS_PASSED',[(r['action'],r['distance_drift']) for r in results])
