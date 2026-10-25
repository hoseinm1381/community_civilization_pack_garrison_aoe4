"""Freeze exact 050 delivery/current source; normal and older art stay read-only."""
from __future__ import annotations
import json, os, shutil, sys
from zipfile import ZipFile
from common import *
FREEZE=OUT/'baseline/freeze.json'
def files(root):
    result={}
    if not root.exists():return result
    for folder,dirs,names in os.walk(root,followlinks=False):
        for name in list(dirs):
            p=Path(folder)/name
            assert not p.is_symlink() and not p.is_junction(),p
            if name in ('__pycache__','release_051'):dirs.remove(name)
        for name in names:
            p=Path(folder)/name
            assert not p.is_symlink(),p
            result[p.relative_to(root).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
    return result
def capture():
    return {'assets':files(ROOT/'assets'),'normal':files(Path(CONFIG['source_root'])),
            'prior_art':{key:files(ROOT/'art'/key) for key in ('authoring','exports','recipes')},
            'prior_tools':{p.name:files(p) for p in (ROOT/'tools').iterdir() if p.is_dir() and p.name!='release_051'},
            'tests':files(ROOT/'tests'),
            'identity':{p:{'sha256':sha(ROOT/p)} for p in ('workspace.json',CONFIG['project_file'])}}
def freeze():
    guarded(); assert not FREEZE.exists(),'Freeze already exists'
    assert sha(ZIP050)==ZIP050_SHA
    with ZipFile(ZIP050) as z:
        assert z.testzip() is None
        assert z.namelist()==['garrison.json',KEY+'.sga','START-HERE.txt','EVIDENCE.json']
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.5.0'
        BASELINE.parent.mkdir(parents=True,exist_ok=True);assert not BASELINE.exists()
        BASELINE.write_bytes(z.read(KEY+'.sga'))
    assert sha(BASELINE)==SGA050_SHA
    value=capture();value.update({'status':'immutable_pre051','zip050_sha256':ZIP050_SHA,'sga050_sha256':SGA050_SHA})
    shutil.copytree(ROOT/'assets',OUT/'baseline/source/assets')
    assert files(OUT/'baseline/source/assets')==value['assets']
    for p in ('workspace.json',CONFIG['project_file']):shutil.copy2(ROOT/p,OUT/'baseline/source'/p)
    evidence=OUT/'baseline/user-regressions';evidence.mkdir()
    for name in ('8d967c2b-eb66-4170-a0aa-d486090dab66','f1826e22-0695-427e-baa5-f6d9f14ca819','66707c8b-724d-41cd-a119-e925d2e21844','290c8252-c74f-4fa9-b664-2bf1f1231668'):
        p=Path('C:/Users/RS/AppData/Local/Temp')/('codex-clipboard-'+name+'.png');shutil.copy2(p,evidence/p.name)
    warning=Path('C:/Users/RS/Documents/My Games/Age of Empires IV/warnings.log')
    if warning.exists():shutil.copy2(warning,evidence/'warnings-050.log')
    write(FREEZE,value);print('FROZEN051',len(value['assets']),'source files;',len(value['normal']),'normal files')
def verify():
    guarded(); before=read(FREEZE);now=capture()
    assert sha(ZIP050)==before['zip050_sha256']==ZIP050_SHA
    assert sha(BASELINE)==before['sga050_sha256']==SGA050_SHA
    for key in ('normal','prior_art','prior_tools','identity'):assert now[key]==before[key],f'Protected {key} changed'
    print('PROTECTED051_VERIFIED');return True
if __name__=='__main__':freeze() if len(sys.argv)==1 else verify()
