"""Read-only encoder investigation; keeps release 0.8.1 immutable."""
from pathlib import Path
import importlib, inspect, json, sys, traceback

ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / 'workspace.json').read_text())
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import check_storage
check_storage(ROOT, CFG)
OUT = ROOT / 'output/release_081_animation/retry-1'
OUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, CFG['garrison_extension'])
report = {}
for name in ['unit_project', 'unit_prototypes', 'animation_catalog',
             'animation', 'rhka', 'havok', 'unit_animation', 'predictive_animation',
             'animation_export', 'unit_animation_export', 'unit_animation_library']:
    try:
        m = importlib.import_module('garrison_shared.' + name)
        report[name] = {k: str(inspect.signature(v)) for k,v in vars(m).items()
                        if callable(v) and getattr(v, '__module__', None) == m.__name__}
    except Exception as e:
        report[name] = {'error': type(e).__name__ + ': ' + str(e)}
(OUT / 'installed-apis.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
