"""Pin the failed 060 delivery and user evidence without overwriting anything."""
import shutil
import zipfile
from common import *

def main():
    guard();target=OUT/'baseline/freeze.json'
    if target.exists():baseline();print('Existing061baseline verified');return
    if sha(ZIP060)!=ZIP060_SHA or sha(SGA060)!=SGA060_SHA:raise ValueError('060baseline changed')
    with zipfile.ZipFile(ZIP060) as z:
        if z.testzip() is not None:raise ValueError('060ZIP unreadable')
        import hashlib
        if hashlib.sha256(z.read(CFG['package_key']+'.sga')).hexdigest()!=SGA060_SHA:raise ValueError('Embedded060SGA differs')
    frozen_source=read(OLD/'qualification/final-source-r2.json')
    active=files(ROOT/'assets')
    if active!=frozen_source['active_assets']:raise ValueError('Source changed after060; inspect first')
    folder=owned(OUT/'baseline');folder.mkdir(parents=True,exist_ok=True)
    for rel in active:
        dest=owned(folder/'source/assets'/rel);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'assets'/rel,dest)
    evidence=[]
    for path in (Path('C:/Users/RS/AppData/Local/Temp/codex-clipboard-576caf63-5734-4eda-8c4a-8ba361398d5e.png'),
                 Path('C:/Users/RS/AppData/Local/Temp/codex-clipboard-1710b190-74d6-44b7-88db-ea3848cc02f3.png'),
                 Path('C:/Users/RS/Documents/My Games/Age of Empires IV/warnings.log')):
        dest=owned(folder/'user-evidence'/path.name);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dest);evidence.append({'file':str(dest),'sha256':sha(dest),'bytes':dest.stat().st_size})
    listing=command('list',SGA060,'--verify')
    if not listing['archive']['verification']['verified']:raise ValueError('060SGA CRC fail')
    write(folder/'listing060.json',listing)
    normal=files(Path(CFG['source_root']))
    if len(normal)!=frozen_source['normal_file_count']:raise ValueError('Normal file count changed')
    write(target,{'schema':'ccp-061-baseline/v1','zip':str(ZIP060),'zip_sha256':ZIP060_SHA,
        'sga':str(SGA060),'sga_sha256':SGA060_SHA,'source':active,'normal':normal,
        'identities':{n:sha(ROOT/n) for n in ('workspace.json',CFG['project_file'])},
        'archive_members':read(OLD/'qualification/final-archive-r2/receipt.json')['members'],
        'evidence':evidence,'user_runtime_result':'All units except scouts/villagers invisible; both Castle landmarks invisible',
        'historical_source_receipt_sha256':sha(OLD/'qualification/final-source-r2.json')})
    print('Frozen exact060delivery, source and user evidence')

if __name__=='__main__':main()
