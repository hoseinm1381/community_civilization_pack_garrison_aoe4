"""Record the accepted plan; no art step is declared passed by this adapter."""
from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'output/release_075/orchestration/seven-building-upgrade'
spec=importlib.util.spec_from_file_location('orchestrator',Path('C:/Users/RS/.codex/skills/blender-superskill/scripts/blender_orchestrator.py'))
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
state=o.load_state(RUN)
if state['phase']!='plan':raise SystemExit('Existing plan retained')
anatomy={'garden':['Royal pavilion','Pond and bridge','Broadleaf planting','Service access'],
 'foundry':['Main forge','Furnace mouths and vents','Casting lane','Store and fuel'],
 'citadel':['Main hall and gate','Thick return walls','Roof and brick/plaster hierarchy'],
 'hq':['Command hall','Reed roof skins','Palisade and supply court'],
 'ministry':['Civic hall','Storage wing','Three preserved elephants and pens'],
 'pho_minh':['Tapering masonry tower','Cornice transitions','Base entrance and court'],
 'one_pillar':['Single column','Support frame and shrine','Stair','Pond and lotus']}
plan={'status':'ok','view_analysis':{'scope':'Accepted seven-building art plan; comparison and source review are distinct from native acceptance','references':'docs/RELEASE_075_REFERENCES.md'},
 'anatomy':anatomy,'proportions':[{'name':'One Pillar final scale','target':'Existing approved source scale and packaged transform','evidence':'040 source already includes 2.5 scale; do not apply again','tolerance':'exact'},
 {'name':'Ministry elephant count','target':'3 static original elephants','evidence':'Current compound','tolerance':'exact'},
 {'name':'Source envelopes and fit','target':'Current source-receipt model-local fit and native footprint','evidence':'Verified 0.7.4 readback and source inspections','tolerance':'No gameplay footprint change'}],
 'steps':[{'id':key,'title':key+' source refinement','objective':'Improve documented weaknesses while retaining identity and lifecycle',
 'reference_features':parts,'anchors':['Existing grade and source transforms','Measured support faces','Preserved production route'],
 'forbidden':['Historical source overwrite','Whole-body structure shader conversion','Gameplay changes','Unsupported quality score'],
 'required_inspections':['Six orthographic sides','Gameplay and isometric review','Numeric connection audit','Native-state preservation'],
 'pass_criteria':['References compared','No unexplained gaps','Finite single-user geometry','Budget measured','Export preflight']} for key,parts in anatomy.items()],
 'risks':['Complete-compound official budgets remain pending','Native owner colour deferred to final candidate','Art drafts have known material shortcomings']}
path=RUN/'step-results/root-plan.json';path.write_text(json.dumps(plan,indent=2)+'\n')
log=RUN/'logs/root-adapter.txt';log.write_text('Accepted plan recorded by root; serialized isolated Blender processes. No automatic worker or completed art step implied.\n')
state=o.apply_result(RUN,state,path,log,0)
if state.get('last_validation_errors'):raise RuntimeError(state['last_validation_errors'])
o.save_state(RUN,state)
print(json.dumps({'phase':state['phase'],'completed_steps':state['completed_steps']}))
