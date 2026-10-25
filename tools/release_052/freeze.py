"""Freeze the tested 051 delivery and record its still-failing landmarks."""
import shutil
from zipfile import ZipFile
from common import *

def main():
    guard();assert not (OUT/'baseline/freeze.json').exists()
    assert sha(BASELINE)==SGA051_SHA and sha(ZIP051)==ZIP051_SHA
    with ZipFile(ZIP051) as z:
        assert z.testzip() is None
        assert hashlib.sha256(z.read(KEY+'.sga')).hexdigest()==SGA051_SHA
    inputs=snapshot()
    regression=OUT/'baseline/user-regressions';regression.mkdir(parents=True,exist_ok=True)
    for name in ('0f79e10e-3490-477b-a4c0-025ba7abff77','a3ee5565-dadb-48b6-bd8a-ebda5674c94e'):
        p=Path('C:/Users/RS/AppData/Local/Temp')/('codex-clipboard-'+name+'.png')
        shutil.copy2(p,regression/p.name)
    warning=Path('C:/Users/RS/Documents/My Games/Age of Empires IV/warnings.log')
    if warning.exists():shutil.copy2(warning,regression/'warnings-051-user-match.log')
    installed=Path('C:/Users/RS/AppData/Local/Garrison/library')/KEY/(KEY+'.sga')
    installed_hash=sha(installed) if installed.exists() else None
    # Garrison imports are user-owned and can be removed while source hashing
    # runs. The baseline is the verified delivered archive, not a mutable client
    # installation. Reject a conflicting installed file; record absence honestly.
    assert installed_hash in (None,SGA051_SHA),'Conflicting installed archive: resolve before a native comparison'
    write(OUT/'baseline/freeze.json',{'status':'immutable_pre052','baseline_sga':str(BASELINE),'baseline_sga_sha256':SGA051_SHA,'baseline_zip':str(ZIP051),'baseline_zip_sha256':ZIP051_SHA,'installed_sga_sha256':installed_hash,'user_acceptance':{'traps':'good','monastery':'good','castle_landmarks':'both invisible after completion'},'inputs':inputs})
    print('FROZEN052',len(inputs['assets']),len(inputs['normal']),flush=True)

if __name__=='__main__':verify_frozen() if len(sys.argv)>1 else main()
