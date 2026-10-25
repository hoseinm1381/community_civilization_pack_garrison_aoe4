"""Record real candidate review without promoting below-target art to a pass."""
from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'output/release_075/orchestration/seven-building-upgrade'
spec=importlib.util.spec_from_file_location('orchestrator',Path('C:/Users/RS/.codex/skills/blender-superskill/scripts/blender_orchestrator.py'))
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
state=o.load_state(RUN)
cards=json.loads((ROOT/'output/release_075/review/scorecards.json').read_text())['families']
proof=json.loads((ROOT/'output/release_075/candidates/review-v1/verification.json').read_text())
assert all(not c['target_met'] for c in cards.values()) and proof['status']=='verified_package_review_candidate'
for item in state['plan']['proportions']:
 if item['name']=='One Pillar final scale':
  corrected={'name':item['name'],'target':'Existing approved source scale and packaged transform','evidence':'040 source already includes the approved 2.5 scale; no additional scale applied in 075','tolerance':'exact'}
  (RUN/'plan-scale-erratum.json').write_text(json.dumps({'previous':item,'corrected':corrected,'reason':'Correct plan wording only. Actual source and stamp transforms were preserved; the earlier native-scale wording was inaccurate.'},indent=2)+'\n')
  item.update(corrected)
result={'status':'needs_repair','step_id':'garden','attempt':state.get('current_attempt',1),
 'objects_created':[],'objects_modified':[],
 'anchors_used':['Final per-building support and export-fit receipts','Native stock flag pole base'],
 'inspections_done':['Eight source views per final revision','Independent seven-building weighted review','Before/after and scoped official geometry comparisons','Numeric contact audits','Final native cooks and member-by-member package verification'],
 'screenshots':[str(ROOT/'output/release_075/review'/(key+'-comparison.png')) for key in cards],
 'reference_comparison':{'matches':['Seven reviewed source revisions preserve established identities','Technical corner/material/contact defects repaired','Full native attachment model costs inventoried'],
  'mismatches':[c['name']+': '+c['deductions'][0] for c in cards.values()],
  'proportion_checks':['Approved One Pillar scale retained without a second multiplication','Three original Ministry elephants retained','Conservative complete mesh bounds recorded; Garden/Foundry reference qualification remains inconclusive']},
 'remaining_differences':['The requested 9–10 quality target is not met','Native appearance, two-colour ownership and lifecycle acceptance pending','Garden/Foundry healthy-state budget qualification pending'],
 'why_acceptable_to_continue':'The user permits an honestly scored review candidate below target. Package verification is complete, while source quality remains needs_repair. No completed quality step or runtime pass is inferred.',
 'next_action':'retry','all_family_source_scores':{key:c['source_score'] for key,c in cards.items()},
 'candidate':str(ROOT/'output/release_075/candidates/review-v1/community_civilization_pack-0.7.5.zip')}
path=RUN/'step-results/candidate-review.json';assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
state=o.apply_result(RUN,state,path,RUN/'logs/root-adapter.txt',0);o.save_state(RUN,state)
print(json.dumps({'phase':state['phase'],'completed_quality_steps':state['completed_steps'],'candidate_package_verified':True,'visual_target_met':False}))
