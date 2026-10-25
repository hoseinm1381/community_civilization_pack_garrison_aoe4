"""Version-owned compatibility runner; inherited implementations remain frozen."""
from common import *
import runpy,shutil
sys.path.append(str(ROOT/'tools/release_079'))
sys.path.append(str(ROOT/'tools/release_076'))
if __name__=='__main__':
    guard();mode=sys.argv[1]
    if mode=='cook':
        RECIPES.mkdir(parents=True,exist_ok=True)
        p=RECIPES/'art-burn-rules.xml'
        if not p.exists():shutil.copyfile(ROOT/'art/recipes/release_079/art-burn-rules.xml',p)
        module('cook81',ROOT/'tools/release_081/cook.py').main({'buffalo':sys.argv[3]},sys.argv[2])
    elif mode=='control':
        old=read(ROOT/'output/release_0710/buffalo/art/buffalo/r1/export.json')
        dest=EXPORT/'buffalo/control'
        if dest.exists():raise FileExistsError('Immutable donor control')
        shutil.copytree(ROOT/'art/exports/release_0710/buffalo/r1',dest)
        write(OUT/'art/buffalo/control/export.json',old)
        module('cook81',ROOT/'tools/release_076/cook.py').main({'buffalo':'control'},sys.argv[2])
    elif mode=='decode':
        label=sys.argv[2];sys.argv=[str(ROOT/'tools/release_079/decode_diagnostic.py'),label]
        runpy.run_path(str(ROOT/'tools/release_079/decode_diagnostic.py'),run_name='__main__')
