"""Finalize verified 0.5.0; clean only reproducible final-archive readbacks."""
from __future__ import annotations
import hashlib
import json
import os
import shutil
from pathlib import Path
from zipfile import ZipFile
from common import ROOT,OUT,BASELINE,KEY,guarded,read,sha,write

def safe_files(folder):
    result={};pending=[folder]
    while pending:
        current=pending.pop();stat=current.lstat()
        assert not current.is_symlink() and not (getattr(stat,'st_file_attributes',0)&0x400),current
        with os.scandir(current) as entries:
            for entry in entries:
                path=Path(entry.path);stat=path.lstat()
                assert not entry.is_symlink() and not (getattr(stat,'st_file_attributes',0)&0x400),path
                if entry.is_dir(follow_symlinks=False):pending.append(path)
                else:
                    assert entry.is_file(follow_symlinks=False)
                    result[path.relative_to(folder).as_posix()]={'sha256':sha(path),'bytes':stat.st_size}
    return result

def finalize():
    guarded()
    delivery=read(OUT/'package-verification.json');audit=read(OUT/'archive-verification.json')
    checks=read(OUT/'release-checks.json');candidate=read(OUT/'candidate.json')
    assert delivery['status']==audit['status']=='passed'
    assert checks['status']=='baseline-equivalent-with-two-inherited-failures'
    assert sha(delivery['zip'])==delivery['zip_sha256']
    assert sha(delivery['sga'])==delivery['sga_sha256']==audit['sga_sha256']==candidate['sha256']
    assert sha(BASELINE)==candidate['baseline_sha256']==audit['baseline_sha256']
    with ZipFile(delivery['zip']) as bundle:
        assert bundle.testzip() is None
        assert bundle.namelist()==['garrison.json',KEY+'.sga','START-HERE.txt','EVIDENCE.json']
        assert hashlib.sha256(bundle.read(KEY+'.sga')).hexdigest()==delivery['sga_sha256']
        for name in ('garrison.json','START-HERE.txt','EVIDENCE.json'):
            assert bundle.read(name)==(OUT/'package'/name).read_bytes(),('Staged package differs',name)
        evidence=json.loads(bundle.read('EVIDENCE.json'))
        assert evidence['checks']==checks and evidence['archive']==audit,'Package evidence is stale'
        assert evidence['asset_verification']==read(OUT.parent/'castle_next/verification.json')
    targets=[]
    parent=OUT/'readback'
    for folder in parent.glob('*') if parent.exists() else ():
        marker=folder/'.complete.json'
        if not folder.is_dir() or not marker.is_file():continue
        digest=read(marker).get('archive_sha256')
        if digest not in (candidate['sha256'],candidate['baseline_sha256']):continue
        absolute=folder.resolve()
        assert absolute.is_relative_to(OUT.resolve()) and absolute.parent==parent.resolve()
        files=safe_files(folder)
        targets.append({'path':str(folder),'archive_sha256':digest,'files':files,
                        'bytes':sum(row['bytes'] for row in files.values())})
    # Inventory is saved before deletion so an interruption retains evidence.
    write(OUT/'cleanup-plan.json',{'status':'verified_regenerable_readbacks','targets':targets,
                                  'restoration':'sga-archiver unpack the retained baseline/candidate SGA'})
    for row in targets:shutil.rmtree(Path(row['path']).resolve())
    assert sha(delivery['zip'])==delivery['zip_sha256'] and sha(delivery['sga'])==delivery['sga_sha256']
    value={'status':'passed','reclaimed_bytes':sum(row['bytes'] for row in targets),
           'targets':targets,'zip_sha256':delivery['zip_sha256'],'sga_sha256':delivery['sga_sha256'],
           'retained':['completed040 ZIP and exact embedded SGA rollback','050 delivery/candidate and successful native cook archives',
                       'all editable blends, source textures, exports and recipes','all registered Garrison inputs',
                       'all donor manifests and required decoded resources','native cook/readback evidence and failed diagnostics'],
           'restoration':'sga-archiver unpack retained archives; tools/build_release_050.ps1 -VerifyOnly regenerates final readbacks'}
    previous=OUT/'cleanup-verification.json'
    if previous.exists():
        old=read(previous)
        value['previously_reclaimed_bytes']=old.get('previously_reclaimed_bytes',0)+old['reclaimed_bytes']
        history=OUT/'cleanup-history'/(sha(previous)+'.json')
        write(history,old)
    write(previous,value)
    print('RELEASE050_FINALIZED',value['reclaimed_bytes'],'bytes reclaimed')
    return value

if __name__=='__main__':finalize()
