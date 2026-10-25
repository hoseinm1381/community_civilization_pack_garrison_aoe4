from pathlib import Path
import sys,importlib.util
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/release_079'))
import common
common.OUT=ROOT/'output/release_0710/buffalo';common.ART=ROOT/'art/authoring/release_0710';common.EXPORT=ROOT/'art/exports/release_0710';common.RECIPES=ROOT/'art/recipes/release_0710/buffalo';common.STAGE=Path(common.CFG['external_root'])/'staging/r710b'
from common import *
def execute(path):
 exec(compile(Path(path).read_text(),str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
if __name__=='__main__':
 mode=sys.argv.pop(1)
 if mode=='blender':execute(ROOT/'tools/release_079/blender_runner.py')
 elif mode=='cook':
  from cook_pilot import module
  module.main({'buffalo':'r1'},sys.argv[1])
 elif mode=='decode':execute(ROOT/'tools/release_079/decode_pilot.py')
