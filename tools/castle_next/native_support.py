"""Reuse read-only native codecs with all writable state redirected to Castle."""
from __future__ import annotations
import importlib.util
import sys
from common import CFG, ROOT, OUT, WORK, CORE, ARCH, ART_EDITOR, read, write, sha, guarded, run_logged

sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import relic_chunky as rc, rgd, model_variants as mv, building_project as bp
sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native
native.WORK = WORK
native.CACHEWORK = OUT / 'native-stock'
native.OUT = OUT
native.STAGING = OUT / 'isolated-source'
native.run_logged = run_logged
native.write = write

def legacy_module(name, relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

lifecycle=legacy_module('castle_lifecycle_codec','tools/release_040/lifecycle.py')
from integration_codec import intact_damage_conditions, copy_native_markers
