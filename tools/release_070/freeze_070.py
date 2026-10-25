"""Immutable pre-070 delivery, source, art and voice baseline."""
from pathlib import Path
import hashlib,json,os,sys,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CFG=configuration(ROOT); EXT=Path(CFG['external_root']); OUT=EXT/'output/release_070'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inventory(root):
    root=Path(root); result={}
    if root.is_symlink() or root.is_junction():raise ValueError('Linked inventory root')
    for folder,dirs,names in os.walk(root,followlinks=False):
        for n in dirs:
            p=Path(folder)/n
            if p.is_symlink() or p.is_junction():raise ValueError('Nested link: '+str(p))
        dirs[:]=sorted(d for d in dirs if d!='__pycache__')
        for n in sorted(names):
            p=Path(folder)/n
            if p.is_symlink():raise ValueError('Linked file')
            result[p.relative_to(root).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
    return result
def main():
    check_storage(ROOT,CFG)
    target=OUT/'baseline/freeze.json'
    if target.exists():raise SystemExit('070 baseline already exists; never overwrite')
    sga=EXT/'output/release_061/final-r1/community_civilization_pack.sga'
    z=EXT/'output/release_061/community_civilization_pack-0.6.1.zip'
    assert sha(sga)=='9e797ab14faf293ec1570c6dc38f1e7cab2ffda9df7d5078b7a0ecf564233c85'
    assert sha(z)=='7f20839e5a7da38619312e33992bbd029e28b9e22e0f26a68dc6e10c69374785'
    with zipfile.ZipFile(z) as f:
        assert f.testzip() is None
        assert hashlib.sha256(f.read('community_civilization_pack.sga')).hexdigest()==sha(sga)
    data={'schema':'ccp-070-baseline/v1','baseline_sga':str(sga),'baseline_sga_sha256':sha(sga),
          'baseline_zip':str(z),'baseline_zip_sha256':sha(z),'source':inventory(ROOT/'assets'),
          'normal':inventory(Path(CFG['source_root'])),'voice_preparation':inventory(ROOT/'0.7.0'),
          'art':{n:inventory(ROOT/'art'/n) for n in ('authoring','exports','recipes')},
          'identity':{n:sha(ROOT/n) for n in ('workspace.json',CFG['project_file'])},
          'archive_receipt_sha256':sha(EXT/'output/release_061/qualification/final-r1/receipt.json'),
          'user_report':'All models fine except monk; remaining native action/state coverage unspecified.'}
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,ensure_ascii=False)
    print(json.dumps({'freeze':str(target),'source_files':len(data['source']),'voice_files':len(data['voice_preparation']),
                      'art_files':sum(map(len,data['art'].values()))}))
if __name__=='__main__':main()
