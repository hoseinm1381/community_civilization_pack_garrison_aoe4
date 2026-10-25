"""Read-only verification of delivered 0.8.1 and protected editable inputs."""
from common import *
import zipfile
def main():
    guard();dest=OUT/'delivery/final-v1';proof=read(dest/'verification.json')
    assert proof['version']=='0.8.1' and proof['all_untouched_members_and_mounts_exact']
    assert sha(proof['zip'])==proof['zip_sha256']
    assert sha(dest/'community_civilization_pack.sga')==proof['sga_sha256']
    assert sha(BASE/'community_civilization_pack.sga')==EXPECTED
    for name in ('protected.json','normal.json'):
        assert all(sha(p)==h for p,h in read(OUT/'baseline'/name).items()),name
    for family,revision,receiptname in [('buffalo','r6','export.json'),('ministry','r2','receipt.json')]:
        row=read(OUT/'art'/family/revision/receiptname);assert sha(row['source'])==row['source_sha256']
        expected=row['files'] if family=='buffalo' else row['export_hashes']
        assert expected=={p.name:sha(p) for p in (EXPORT/family/revision).iterdir() if p.is_file()}
    with zipfile.ZipFile(proof['zip']) as z:
        assert z.testzip() is None
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.8.1'
        with z.open('community_civilization_pack.sga') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==proof['sga_sha256']
    sys.path.append(str(ROOT/'tools/release_073'));from check_identity import check
    identity=check(ROOT,dest/'community_civilization_pack.sga')
    print('081_DELIVERY_AND_PRESERVATION_VERIFIED',len(proof['member_sha256']),len(proof['changed']),proof['zip_sha256'])
if __name__=='__main__':main()
