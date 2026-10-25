"""Fresh final-archive extraction, strict ZIP checks and preservation recheck."""
from common import *
from policy import validate_changes,FAMILIES
import zipfile,datetime
sys.path.append(str(ROOT/'tools/release_073'))
from check_identity import check

def main():
    guard();dest=OUT/'delivery/final-v2';proof=read(dest/'verification.json')
    archive=dest/'community_civilization_pack.sga';package=dest/'community_civilization_pack-0.8.3.zip'
    assert sha(archive)==proof['sga_sha256'] and sha(package)==proof['zip_sha256']
    identity=check(ROOT,archive);baseline=read(OUT/'baseline/archive.json')
    assert sha(baseline['archive'])==baseline['sha256']==EXPECTED
    assert sha(baseline['zip'])==baseline['zip_sha256']
    qa=read(OUT/'source-qa.json');selection=read(RECIPES/'selection.json')
    assert qa['passed'] and qa['selection']==selection and set(selection)==FAMILIES
    for family,revision in selection.items():
        export=read(OUT/'art'/family/revision/'export.json')
        assert sha(export['source'])==export['source_sha256']
        assert qa['export_receipt_sha256'][family]==sha(OUT/'art'/family/revision/'export.json')
        assert export['files']=={p.name:sha(p) for p in Path(export['export']).iterdir() if p.is_file()}
    for name in ['normal','protected']:
        assert all(sha(p)==digest for p,digest in read(OUT/f'baseline/{name}.json').items()),name
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    audit=OUT/'verification'/runid;audit.mkdir(parents=True,exist_ok=False)
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',archive,'--verify'],audit))
    mounts={m['path']:m['toc'] for m in listing['members']}
    assert mounts==proof['mounts'] and all(mounts[k]==v for k,v in baseline['mounts'].items())
    run('extract',[CFG['archive_tool'],'extract',archive,audit/'readback','--filter','.'],audit)
    actual={p.relative_to(audit/'readback').as_posix():sha(p) for p in (audit/'readback').rglob('*') if p.is_file()}
    assert actual==proof['member_sha256']
    changed={k for k in actual if actual[k]!=baseline['members'].get(k)}
    assert changed==set(proof['changed']);validate_changes(changed)
    assert not set(baseline['members'])-set(actual)
    assert all(actual[k]==v for k,v in baseline['members'].items() if k not in changed)
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None and set(z.namelist())=={'garrison.json','community_civilization_pack.sga','START-HERE.txt'}
        manifest=json.loads(z.read('garrison.json'));assert manifest==read(dest/'garrison.json')
        assert manifest['details']['version']=='0.8.3'
        assert manifest['members'][0]['sha256']==sha(archive)
        assert z.read('START-HERE.txt')==(dest/'START-HERE.txt').read_bytes()
        with z.open(archive.name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(archive)
    result={'passed':True,'archive_identity':identity,'zip_sha256':sha(package),'sga_sha256':sha(archive),'members':len(actual),'changed':len(changed),'added':len(set(actual)-set(baseline['members'])),'untouched':len(set(baseline['members'])-changed),'all_original_mounts_exact':True,'normal_and_protected_sources_exact':True,'fresh_full_extraction':str(audit/'readback'),'client_import':False,'native_skirmisher_acceptance':False}
    write(audit/'result.json',result);write(OUT/'final-recheck.json',result)
    print('083_FINAL_RECHECK_PASS',json.dumps(result))

if __name__=='__main__':main()
