"""Record root's serialized MCP results in the installed orchestrator state.

This adapter records already executed MCP steps; it does not launch another
Blender-owning Codex process or imply that automatic CLI workers ran.
"""
from pathlib import Path
import importlib.util,json
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art')
RUN=OUT/'orchestration/architecture-blockout'
MODULE=Path('C:/Users/RS/.codex/skills/blender-superskill/scripts/blender_orchestrator.py')
spec=importlib.util.spec_from_file_location('blender_orchestrator',MODULE);o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
state=o.load_state(RUN)
if state['phase']!='plan':raise SystemExit('Existing orchestrator checkpoint retained')
titles={'garden':'Royal pond and animal-service court','foundry':'Asymmetric casting workshops','wonder':'Double-tier Kinh Thien-inspired palace','university':'Exact stock L-plan with limited scholarly court'}
steps=[{'id':key,'title':title,'objective':'Review silhouette and layout before detailed art',
        'reference_features':['Primary source references and clearly labeled reconstruction'],
        'anchors':['Grade, plinth, roof eaves and measured native University positions'],
        'forbidden':['Detailed production before user approval','Changed native gameplay or footprints'],
        'required_inspections':['Six orthographic sides','Isometric','Numeric contact audit'],
        'pass_criteria':['Finite geometry','No shared mesh datablocks','Connected planned interfaces','User massing decision still required']} for key,title in titles.items()]
plan={'status':'ok','view_analysis':{'reference_scope':'Kinh Thien reconstruction is interpretive; surviving stairs and stock University are measured controls'},
      'anatomy':{'garden':['Pavilion','Pond','Bridge','Gallery','Service yard'],'foundry':['Forge','Shed','Furnaces','Casting court','Store'],
                 'wonder':['Podium','Three stair aisles','Double-tier hall','Side galleries','Gate'],'university':['Unchanged stock L-body','Courtyard gate','Stele masses']},
      'proportions':[{'name':'Wonder podium plan','target':'57:41.5','evidence':'Official Kinh Thien dimensions, scaled design-space blockout','tolerance':'.003 ratio'},
                     {'name':'Garden pavilion','target':'7:4.2 plan','evidence':'Interpretive royal garden pavilion, not a recovered plan'},
                     {'name':'University existing envelope','target':'14.09:12.41 approximate XY','evidence':'Exact native stock decode; additions stay inside measured bounds'}],
      'steps':steps,'risks':['Native inherited footprints and exact target comparator budgets remain unresolved','No detailed art or native building lifecycle qualification yet']}
log=RUN/'logs/root-mcp-adapter.txt';log.write_text('Root serialized BlenderMCP. State reconciled at the review checkpoint from actual saved artifacts. No automatic CLI workers launched.\n',encoding='utf-8')
def record(name,result):
    global state
    p=RUN/'step-results'/name;p.write_text(json.dumps(result,indent=2),encoding='utf-8')
    state=o.apply_result(RUN,state,p,log,0)
    if state.get('last_validation_errors'):raise RuntimeError(state['last_validation_errors'])
    o.save_state(RUN,state)
record('root-plan.json',plan)
for step in steps:
    key=step['id'];screens=[str(OUT/f'{key}-{s}-review.png') for s in ('front','rear','left','right','top','bottom','iso')]
    assert all(Path(p).exists() for p in screens)
    record('root-'+key+'.json',{'status':'pass','step_id':key,'attempt':1,'objects_created':[titles[key]],'objects_modified':[],
        'anchors_used':step['anchors'],'inspections_done':step['required_inspections'],'screenshots':screens,
        'reference_comparison':{'matches':['Distinct approved historical direction and preserved stock University'],
           'mismatches':['No ornament/material completion at blockout stage; foundry and animal yard are interpretive'],
           'proportion_checks':json.loads((OUT/'contact-audit.json').read_text())['checks']},
        'remaining_differences':[{'detail_stage':'Pending user approval'}], 'coverage_updates':[],
        'why_acceptable_to_continue':'Only advances to blockout review, not detailed production or runtime acceptance','next_action':'advance'})
record('root-review-gate.json',{'status':'blocked','top_differences':['All four remain basic massing with provisional colours'],
    'missing_features':['Detailed ornament, textures, equipment, plants, lifecycle export/cook and native tests'],
    'repair_steps':[],'final_checks':['Contact audit passed','All six sides captured','Corrected r2 saved','Original scene retained'],
    'blocker':'User blockout approval required by the approved plan','next_action':'ask_user'})
print(json.dumps({'phase':state['phase'],'completed_blockout_steps':len(state['completed_steps']),'review_gate':'pending user approval'}))
