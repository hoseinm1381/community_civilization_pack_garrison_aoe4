"""070 preservation policy, distinct from historical release checkpoint tools."""
from pathlib import Path
import sys,json,zipfile,hashlib,ast
sys.path.insert(0,str(Path(__file__).parent))
from freeze_070 import ROOT,OUT,CFG,sha,inventory,check_storage
def main():
    check_storage(ROOT,CFG)
    f=json.loads((OUT/'baseline/freeze.json').read_text())
    assert sha(f['baseline_sga'])==f['baseline_sga_sha256']
    assert sha(f['baseline_zip'])==f['baseline_zip_sha256']
    normal_current=inventory(Path(CFG['source_root']))
    normal_frozen=normal_current==f['normal']
    if not normal_frozen:
        drift=json.loads((OUT/'external-normal-drift.json').read_text())
        assert drift['schema']=='ccp-070-external-normal-drift/v1'
        assert drift['freeze_sha256']==sha(OUT/'baseline/freeze.json')
        assert normal_current==drift['normal_observed_inventory']
        assert {k for k in set(normal_current)|set(f['normal']) if normal_current.get(k)!=f['normal'].get(k)}==set(drift['changed_paths'])
        assert drift['normal_frozen_preservation_passed'] is False
    for rel,digest in f['identity'].items():assert sha(ROOT/rel)==digest,rel
    art=0
    for directory,files in f['art'].items():
        for rel,row in files.items():assert sha(ROOT/'art'/directory/rel)==row['sha256'],(directory,rel)
        art+=len(files)
    current=inventory(ROOT/'assets')
    activation=OUT/'source-activation/receipt.json'
    if activation.exists():
        r=json.loads(activation.read_text());assert {k:v['sha256'] for k,v in current.items()}==r['source_sha256']
        assert set(r['modified'])|set(r['added'])==set(r['allowed_paths'])
        assert len(r['modified'])==5 and len(r['added'])==9
        source_state='qualified_070_overlay_5_modified_9_added'
    else:assert current==f['source'];source_state='frozen_061_source_unchanged'
    migration=json.loads((OUT/'voices/migration-080.json').read_text())
    assert sha(migration['original_archive'])==migration['original_archive_sha256']
    assert not (ROOT/'0.7.0').exists()
    for row in migration['files']:assert sha(ROOT/'0.8.0'/row['path'])==row['current_sha256'],row['path']
    with zipfile.ZipFile(migration['original_archive']) as z:
        assert z.testzip() is None
        for rel,row in f['voice_preparation'].items():assert hashlib.sha256(z.read('0.7.0/'+rel)).hexdigest()==row['sha256'],rel
    scripts=list((ROOT/'tools/release_070').rglob('*.py'))
    for p in scripts:ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    result={'schema':'ccp-070-preservation/v1','status':'passed_garrison_scope_with_observed_external_normal_drift' if not normal_frozen else 'passed','baseline_sga_sha256':f['baseline_sga_sha256'],'baseline_zip_sha256':f['baseline_zip_sha256'],'normal_frozen_preservation_passed':normal_frozen,'normal_frozen_unchanged_files':sum(normal_current.get(k)==v for k,v in f['normal'].items()),'normal_observed_files_preserved':len(normal_current),'prior_art_unchanged_files':art,'source_state':source_state,'identity_unchanged':True,'voice_original_frozen_files':len(f['voice_preparation']),'voice_migrated_files_verified':len(migration['files']),'voice_changed_text_paths':migration['changed_paths'],'historical_voice_preservation_drift_retained':True,'release_python_syntax_files':len(scripts),'native_runtime_proof':False}
    (OUT/'preservation-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
