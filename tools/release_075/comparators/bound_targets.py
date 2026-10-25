"""Conservative per-variant sum of all retained model geometry, including scaffolds."""
from pathlib import Path
import json,collections
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/release_075/comparators'
closure=json.loads((OUT/'target-closure.json').read_text());models=json.loads((OUT/'target-models.json').read_text());result={}
for family,row in closure['families'].items():
 cases=[]
 for actor in row['actors']:
  branches=sorted({e['field'].split('/')[0] for e in actor['attachments']})
  for branch in branches:
   entries=[e for e in actor['attachments'] if e['field'].split('/')[0]==branch]
   chosen=[];blocked=[]
   for entry in entries:
    if 'blocker'in entry:blocked.append(entry['blocker'])
    available={s['field'].split('/')[0] for s in entry['stamps']}
    selection=branch if branch in available else 'default'
    chosen += [s for s in entry['stamps'] if s['field'].split('/')[0]==selection]
   body=[];total=0;instances=[];nonmesh=[]
   for stamp in chosen:
    for v in stamp['visuals']:
     model=v['model']+'.rgm'
     if model.startswith('art/scenario/'):
      body.append({'model':model,'stamp':stamp['member'],'transform':v['transform']});continue
     metric=models.get(model,{})
     if 'metric'not in metric:blocked.append(model);continue
     cost=metric['metric']['upper'];total+=cost
     instances.append({'model':model,'upper':cost,'stamp':stamp['member'],'object_id':v['id'],'transform':v['transform']})
     if metric['status']=='proven_no_model_mesh':nonmesh.append(model)
   cases.append({'actor':actor['member'],'branch':branch,'retained_native_mesh_triangle_upper':total,'body_instances':body,'flag_addition_upper':304,'nonmesh_model_references':nonmesh,'model_instances':instances,'blockers':blocked,'stamps':[s['member'] for s in chosen]})
 result[family]={'cases':cases,'retained_native_mesh_upper_max':max((c['retained_native_mesh_triangle_upper'] for c in cases),default=0),'max_body_instances':max((len(c['body_instances']) for c in cases),default=0)}
report={'schema':'ccp075-conservative-target-model-bounds/v1','status':'native_mesh_remainder_measured','method':'For each actor variant, select matching attachment-list variant or default fallback. Sum every referenced native model upper bound, including all construction scaffolds/debris, never remove a cost because of an unqualified visibility predicate. Add the final custom body all-state geometry and one 304-triangle owner flag separately. Distinct actor variants are alternative cases, not simultaneous compounds.','limits':['This is a mesh triangle upper bound, not an exact healthy visible count.','Typed splat and strip blueprints render terrain decals; their GPU cost is not inferred from mesh triangles.','Native animation effects, terrain tessellation and runtime draw calls require native profiling.'],'families':result}
(OUT/'target-bounds.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:{'remainder_max':v['retained_native_mesh_upper_max'],'max_body_instances':v['max_body_instances'],'cases':[(c['branch'],c['retained_native_mesh_triangle_upper'],len(c['body_instances']),c['blockers'])for c in v['cases']]}for k,v in result.items()},indent=2))
