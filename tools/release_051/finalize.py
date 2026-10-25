"""Verify delivery and remove only inventoried final archive readbacks."""
import hashlib,json,os,shutil
from zipfile import ZipFile
from common import *
def main():
    guarded();p=read(OUT/'package-verification.json');c=read(OUT/'candidate.json');a=read(OUT/'archive-verification.json')
    assert sha(p['zip'])==p['zip_sha256'] and sha(p['sga'])==p['sga_sha256']==c['sha256']==a['sga_sha256']
    with ZipFile(p['zip']) as z:
        assert z.testzip() is None and z.namelist()==['garrison.json',KEY+'.sga','START-HERE.txt','EVIDENCE.json']
        assert hashlib.sha256(z.read(KEY+'.sga')).hexdigest()==p['sga_sha256']
        for name in ('garrison.json','START-HERE.txt','EVIDENCE.json'):assert z.read(name)==(OUT/'package'/name).read_bytes()
        evidence=json.loads(z.read('EVIDENCE.json'));assert evidence['archive']==a and evidence['checks']==read(OUT/'checks.json')
    targets=[];parent=OUT/'readback'
    for folder in parent.iterdir():
        assert folder.resolve().parent==parent.resolve() and folder.resolve().is_relative_to(OUT.resolve())
        assert not folder.is_symlink() and not folder.is_junction()
        marker=folder/'.complete.json'
        if not marker.is_file() or read(marker)['sha256'] not in (SGA050_SHA,c['sha256']):continue
        inventory={}
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs:
                path=Path(current)/name;assert not path.is_symlink() and not path.is_junction()
            for name in files:
                path=Path(current)/name;assert not(path.lstat().st_file_attributes&0x400)
                inventory[path.relative_to(folder).as_posix()]={'sha256':sha(path),'bytes':path.stat().st_size}
        targets.append({'path':str(folder),'files':inventory,'bytes':sum(x['bytes'] for x in inventory.values())})
    write(OUT/'cleanup-plan.json',{'targets':targets,'restore':'sga-archiver unpack retained baseline/candidate SGA; release.py verify regenerates these caches'})
    for t in targets:shutil.rmtree(Path(t['path']).resolve())
    assert sha(p['zip'])==p['zip_sha256'] and sha(p['sga'])==p['sga_sha256']
    write(OUT/'cleanup-verification.json',{'status':'passed','reclaimed_bytes':sum(x['bytes'] for x in targets),'delivery_hashes_rechecked':True,'zip_sha256':p['zip_sha256'],'sga_sha256':p['sga_sha256'],'retained':'all source, textures, OBJ/Blend references, recipes, required native inputs, successful archives/readbacks, failure diagnostics, 040/050 and051 deliveries'})
    print('FINALIZED051',sum(x['bytes'] for x in targets))
if __name__=='__main__':main()
