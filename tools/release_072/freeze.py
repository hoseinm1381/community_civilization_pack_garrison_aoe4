"""Immutable source/art/identity inputs for the approved normal-v12 port."""
from pathlib import Path
import hashlib,json,zipfile,sys
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
NORMAL=Path(CFG['source_root'])
OUT=ROOT/'output/release_072'
GUID=CFG['project_guid'].replace('-','')
OLD=CFG['source_project_guid'].replace('-','')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def files(root):return sorted(p for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
def freeze():
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace_support import check_storage
    check_storage(ROOT,CFG)
    dest=OUT/'freeze';dest.mkdir(parents=True,exist_ok=True)
    for label,root,project in [('normal',NORMAL,'Vietnam_v2.aoe4mod'),('garrison',ROOT,CFG['project_file'])]:
        rows={p.relative_to(root).as_posix():sha(p) for p in files(root/'assets')}
        for name in (project,'workspace.json'):
            if (root/name).exists():rows[name]=sha(root/name)
        receipt=dest/(label+'.json')
        if receipt.exists():
            if label=='normal':assert json.loads(receipt.read_text())==rows,'Normal source drift'
        else:
            dump(receipt,rows)
            with zipfile.ZipFile(dest/(label+'.zip'),'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for key in rows:z.write(root/key,key)
            with zipfile.ZipFile(dest/(label+'.zip')) as z:
                assert z.testzip() is None
                assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in rows.items())
    protected={}
    for directory in ('art/authoring','art/exports','art/recipes','archives/release_070_rollback','output/release_071/delivery'):
        for p in files(ROOT/directory):protected[p.relative_to(ROOT).as_posix()]=sha(p)
    receipt=dest/'protected.json'
    if receipt.exists():assert json.loads(receipt.read_text())==protected,'Protected art/delivery drift'
    else:dump(receipt,protected)
    print(json.dumps({'normal_assets':len(json.loads((dest/'normal.json').read_text())), 'garrison_assets':len(json.loads((dest/'garrison.json').read_text())), 'protected_files':len(protected)}))
if __name__=='__main__':freeze()
