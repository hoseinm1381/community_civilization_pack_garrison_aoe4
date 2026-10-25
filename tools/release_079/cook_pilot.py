"""Run the retained native cook implementation with isolated 0.7.9 paths.

Pilot deliberately replaces the same private model keys to isolate .rig changes.
The historical implementation is read-only; common is bound to this release.
"""
from common import *
import importlib.util
sys.path.insert(1,str(ROOT/'tools/release_076'))
spec=importlib.util.spec_from_file_location('pilot_native_cook',ROOT/'tools/release_076/cook.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
if __name__=='__main__':module.main(read(RECIPES/('control-selection.json' if '--controls' in sys.argv else 'pilot-selection.json')),sys.argv[1])
