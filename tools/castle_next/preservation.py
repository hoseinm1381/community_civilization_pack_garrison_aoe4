"""Task-start preservation snapshot; recognizes concurrent 040 work explicitly."""
from __future__ import annotations
import argparse
from pathlib import Path
from common import ROOT, OUT, guarded, read, sha, write

RECEIPT = OUT / 'preservation/start.json'

def files():
    locations = [ROOT/'assets', ROOT/'art/authoring', ROOT/'art/exports', ROOT/'art/recipes',
                 ROOT.parent/'Community_civilization_pack_normal/assets']
    paths = [ROOT/'workspace.json', ROOT/'community_civilization_pack.aoe4mod']
    for folder in locations:
        for path in folder.rglob('*'):
            if path.is_file() and 'castle_next' not in path.parts:
                paths.append(path)
    return sorted(set(paths))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    guarded()
    if not args.verify:
        if RECEIPT.exists():raise FileExistsError(RECEIPT)
        rows={str(p):sha(p) for p in files()}
        write(RECEIPT,{'schema':'ccp.castle-preservation/v1','files':rows,
                      'note':'040 is concurrently changing; differences are reported, never used to refresh snapshot.'})
        print('PRESERVATION_CAPTURED',len(rows));return
    old=read(RECEIPT)['files'];changed=[];missing=[]
    for path,digest in old.items():
        p=Path(path)
        if not p.exists():missing.append(path)
        elif sha(p)!=digest:changed.append(path)
    protected=[p for p in changed if ('Community_civilization_pack_normal' in p or
               ('\\art\\' in p and '_040' not in p and 'release_040' not in p))]
    result={'status':'passed' if not protected and not missing else 'failed',
            'checked_files':len(old),'missing':missing,'protected_changes':protected,
            'concurrent_active_or_040_differences':changed,
            'scope':'Castle tools must never write any listed input; concurrent040 differences remain attributable separately.'}
    write(OUT/'preservation/verification.json',result)
    print('PRESERVATION',result['status'],len(old),'files;',len(changed),'concurrent differences')
    if protected or missing:raise SystemExit(1)

if __name__=='__main__':main()
