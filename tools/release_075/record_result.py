"""Feed actual reviewed evidence to the installed orchestrator, without workers."""
from pathlib import Path
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'output/release_075/orchestration/seven-building-upgrade'
spec=importlib.util.spec_from_file_location('orchestrator',Path('C:/Users/RS/.codex/skills/blender-superskill/scripts/blender_orchestrator.py'))
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
p=Path(sys.argv[1]).resolve();state=o.load_state(RUN)
state=o.apply_result(RUN,state,p,RUN/'logs/root-adapter.txt',0)
if state.get('last_validation_errors') and json.loads(p.read_text()).get('status')!='needs_repair':raise RuntimeError(state['last_validation_errors'])
o.save_state(RUN,state);print(json.dumps({'phase':state['phase'],'completed_steps':state['completed_steps']}))
