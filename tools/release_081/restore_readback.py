"""Recreate only generated readback caches from preserved, hash-pinned archives."""
from common import *
def restore(kind):
    guard()
    if kind=='baseline':
        data=read(OUT/'baseline/inventory.json');archive=Path(data['archive']);digest=EXPECTED;expected=data['members'];target=OUT/'baseline/readback'
    elif kind=='final':
        data=read(OUT/'delivery/final-v1/verification.json');archive=OUT/'delivery/final-v1/community_civilization_pack.sga';digest=data['sga_sha256'];expected=data['member_sha256'];target=OUT/'delivery/final-v1/readback'
    else:raise ValueError('Unknown readback owner')
    assert sha(archive)==digest
    if not target.exists():run('restore-'+kind,[CFG['archive_tool'],'extract',archive,target,'--filter','.'])
    actual={p.relative_to(target).as_posix():sha(p) for p in target.rglob('*') if p.is_file()}
    assert actual==expected,'Restored native members differ from frozen SHA-256 inventory'
    write(OUT/'recovery'/('readback-'+kind+'.json'),{'archive':str(archive),'archive_sha256':digest,'target':str(target),'verified_files':len(actual),'full_hash_comparison':True})
    return target
if __name__=='__main__':print('READBACK_RESTORED_AND_VERIFIED',restore(sys.argv[1]))
