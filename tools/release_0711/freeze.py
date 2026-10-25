"""Freeze verified baseline and current source hashes before 0.7.11 changes."""
import shutil
from common import *
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check
guard()
dest=OUT/'baseline'
if dest.exists():raise FileExistsError('Baseline already frozen; do not replace')
proof=read(BASE/'delivery-proof.json');archive=BASE/'community_civilization_pack.sga'
assert sha(archive)==EXPECTED==proof['sga_sha256']
assert sha(proof['zip'])==proof['zip_sha256']
check(ROOT,archive)
verification=read(BASE/'verification.json')
assert all(sha(BASE/'readback'/m)==h for m,h in verification['member_sha256'].items())
dest.mkdir(parents=True)
for p in (archive,Path(proof['zip']),BASE/'delivery-proof.json',BASE/'verification.json',BASE/'garrison.json'):
    shutil.copyfile(p,dest/p.name);assert sha(p)==sha(dest/p.name)
sources={str(p):sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
for p in (ROOT/'workspace.json',ROOT/CFG['project_file']):sources[str(p)]=sha(p)
normal=ROOT.parent/'Community_civilization_pack_normal'
normal_hashes={str(p):sha(p) for p in (normal/'assets').rglob('*') if p.is_file()}
write(dest/'source-hashes.json',sources);write(dest/'normal-hashes.json',normal_hashes)
write(dest/'freeze.json',{'baseline_sha256':EXPECTED,'zip_sha256':proof['zip_sha256'],'source_files':len(sources),'normal_files':len(normal_hashes),'archive_members':len(verification['member_sha256']),'native_acceptance':False})
import zipfile
with zipfile.ZipFile(dest/'source.zip','x',zipfile.ZIP_DEFLATED) as z:
    for p in sources:z.write(p,Path(p).relative_to(ROOT).as_posix())
protected=read(ROOT/'art/recipes/release_0710/integration.json')['rebuild_input_hashes']
assert all(sha(p)==h for p,h in protected.items())
write(dest/'protected-0710-inputs.json',protected)
print('BASELINE_FROZEN' ,len(sources),len(normal_hashes),len(verification['member_sha256']))
