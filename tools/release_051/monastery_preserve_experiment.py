"""Retain the first 051 degenerate-index experiment before native compaction."""
from pathlib import Path
import shutil
from common import ROOT, OUT, guarded, sha, write

def main():
    guarded(); source=OUT/'monastery';dest=source/'diagnostic-suppression-051'
    assert not dest.exists(),dest
    dest.mkdir()
    targets=[source/'receipt.json',source/'verification.json',
             ROOT/'tools/release_051/monastery_repair.py',
             ROOT/'tools/release_051/monastery_preview_extract.py']
    for age in (3,4):
        targets.append(source/f'payload/art/scenario/cccastle/monastery_age{age:02}/model.rrgeom')
    rows=[]
    for item in targets:
        assert item.is_file(),item
        target=dest/item.name
        if item.name=='model.rrgeom':
            parsed_age='03' if 'age03' in str(item) else '04'
            target=dest/f'age{parsed_age}-model.rrgeom'
        shutil.copy2(item,target)
        assert sha(item)==sha(target)
        rows.append({'source':str(item),'copy':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
    shutil.copytree(source/'previews',dest/'previews')
    write(dest/'preservation.json',{'status':'prior_degenerate_experiment_retained','files':rows,
                                    'previews':str(dest/'previews')})
    print('MONASTERY051_FIRST_EXPERIMENT_PRESERVED',len(rows))

if __name__=='__main__':main()
