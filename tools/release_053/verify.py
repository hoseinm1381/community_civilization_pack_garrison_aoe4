"""Read-only verification of the delivered 0.5.3 package and source policy."""
from package import *

check_storage(ROOT, CFG)
receipt = read(OUT / 'package-verification.json')
target = Path(receipt['zip'])
assert sha(target) == receipt['zip_sha256']
with ZipFile(target) as z:
    assert z.testzip() is None
    assert sorted(z.namelist()) == sorted(['garrison.json', KEY + '.sga', 'START-HERE.txt', 'EVIDENCE.json'])
    manifest = json.loads(z.read('garrison.json'))
    assert manifest['schema'] == 'garrison.mod/v1'
    assert manifest['details']['version'] == '0.5.3'
    assert manifest['details']['author'] == 'hosein81 and chilly5'
    assert manifest['bundle_key'] == KEY == manifest['details']['id']
    assert hashlib.sha256(z.read(KEY + '.sga')).hexdigest() == receipt['sga_sha256'] == EXPECTED_SGA
    assert manifest['members'][0]['sha256'] == receipt['sga_sha256']
    evidence = json.loads(z.read('EVIDENCE.json'))
    assert evidence['is_final_release'] and evidence['unchanged_members'] == 807
    assert evidence['changed_members'] == receipt['changed_members']
recipe = read(ROOT / 'art/recipes/release_053/integration.json')
assert all(sha(r['file']) == r['sha256'] for r in recipe['payloads'])
assert sha(recipe['base']) == recipe['base_sha256']
preservation(recipe['source_overlay_sha256'])
assert sha(OUT / 'package' / (KEY + '.sga')) == EXPECTED_SGA
archive_listing(OUT / 'package' / (KEY + '.sga'))
assert all(sha(p) == digest for p, digest in read(OUT / 'baseline/receipt.json')['rollback_zips'].items())
print('PASS: final 0.5.3 ZIP, SGA CRC/identity, exact payloads, active source and protected inputs')
