"""Freeze active inputs and inventory the exact current owning archive."""
from common import *
import os
def files(root):
    for parent,dirs,names in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(parent)/d).is_junction() and not (Path(parent)/d).is_symlink()]
        for n in names:yield Path(parent)/n
def main():
    guard();dest=OUT/'baseline'
    if (dest/'inventory.json').exists():raise FileExistsError('Immutable baseline already exists')
    assert sha(BASE/'community_civilization_pack.sga')==EXPECTED
    paths=list(files(ROOT/'assets'))+[ROOT/'workspace.json',ROOT/'community_civilization_pack.aoe4mod']
    paths+=list(files(ROOT/'art/authoring'))+list(files(ROOT/'art/exports'))+list(files(ROOT/'art/recipes'))
    normal=ROOT.parent/'Community_civilization_pack_normal'
    if not (dest/'protected.json').exists():write(dest/'protected.json',{str(p):sha(p) for p in paths})
    normal_paths=[p for branch in ('assets','tools','tests','docs') for p in files(normal/branch)]
    normal_paths += [p for p in normal.iterdir() if p.is_file()]
    write(dest/'normal.json',{str(p):sha(p) for p in normal_paths})
    archive=BASE/'community_civilization_pack.sga'
    listing=json.loads(run('baseline-list',[CFG['archive_tool'],'list',archive,'--verify']))
    run('baseline-readback',[CFG['archive_tool'],'extract',archive,dest/'readback','--filter','.'])
    write(dest/'inventory.json',{'archive':str(archive),'sha256':EXPECTED,'listing':listing,'members':{p.relative_to(dest/'readback').as_posix():sha(p) for p in files(dest/'readback')}})
    for key in ['F/output/release_0710/buffalo/art/buffalo/r1/export.json','F/output/release_0710/buffalo/donors.json','F/output/release_079/donors.json','F/output/release_075/inspection/current-consumers.json','F/output/release_075/references/retained/3-owners.json','F/output/release_075/references/retained/feudal-donor-graph.json']:
        ensure(key)
    row=read(ensure('F/output/release_079/donors.json'))['buffalo']
    p=Path(row['manifest']);key='F/'+p.resolve().relative_to(EXT.resolve()).as_posix()
    ensure(key)
    write(OUT/'donors.json',{'buffalo':row})
    print('BASELINE_FROZEN',len(paths),len(listing['members']))
if __name__=='__main__':main()
