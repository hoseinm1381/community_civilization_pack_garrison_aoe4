"""Verify preservation and explicit pre-detail 070 gates without claiming release."""
from pathlib import Path
import sys,json,ast,zipfile,hashlib
sys.path.insert(0,str(Path(__file__).parent))
from freeze_070 import ROOT,EXT,OUT,CFG,sha,inventory,check_storage
def main():
    links=check_storage(ROOT,CFG);f=json.loads((OUT/'baseline/freeze.json').read_text())
    assert sha(f['baseline_sga'])==f['baseline_sga_sha256']
    assert sha(f['baseline_zip'])==f['baseline_zip_sha256']
    assert inventory(ROOT/'assets')==f['source']
    assert inventory(Path(CFG['source_root']))==f['normal']
    for n,s in f['identity'].items():assert sha(ROOT/n)==s,n
    preserved_art=0
    for folder,files in f['art'].items():
        for rel,item in files.items():
            assert sha(ROOT/'art'/folder/rel)==item['sha256'],(folder,rel)
            preserved_art+=1
    migration=json.loads((OUT/'voices/migration-080.json').read_text())
    archive=Path(migration['original_archive'])
    assert sha(archive)==migration['original_archive_sha256']
    assert not (ROOT/'0.7.0').exists() and (ROOT/'0.8.0').is_dir()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for rel,row in f['voice_preparation'].items():assert hashlib.sha256(z.read('0.7.0/'+rel)).hexdigest()==row['sha256'],rel
        for rel in f['voice_preparation']:
            if rel not in migration['changed_paths']:assert sha(ROOT/'0.8.0'/rel)==f['voice_preparation'][rel]['sha256'],rel
    v=json.loads((OUT/'monk/verification.json').read_text())
    assert v['changed_members']==['scar/vietnam/prematch_precache.scar'] and v['unchanged_member_count']==1201
    assert sha(v['candidate'])==v['candidate_sha256'];assert sha(v['overlay'])==v['overlay_sha256']
    assert v['mounts_preserved'] and v['prematch_import_preserved'] and v['prematch_init_hook_preserved']
    contacts=json.loads((OUT/'art/contact-audit.json').read_text());assert contacts['status']=='passed'
    audit=json.loads((OUT/'art/blockout-audit.json').read_text());assert len(audit['assets'])==4
    for asset,row in audit['assets'].items():assert row['finite'] and not row['shared_mesh_datablocks'],asset
    py=list((ROOT/'tools/release_070').rglob('*.py'))
    for p in py:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    blend=ROOT/'art/authoring/buildings_070/architecture-blockouts-r2.blend';assert blend.is_file()
    screenshots={p.name:sha(p) for p in (OUT/'art').glob('*-review.png')}
    assert len(screenshots)>=29
    sheet=OUT/'art/four-blockouts-review.png';assert sheet.is_file()
    result={'schema':'ccp-070-checkpoint-verification/v1','status':'pre_detail_checkpoint_verified_not_release',
        'links':links,'baseline_sga_sha256':sha(f['baseline_sga']),'baseline_zip_sha256':sha(f['baseline_zip']),
        'source_unchanged_files':len(f['source']),'normal_unchanged_files':len(f['normal']),
        'prior_art_unchanged_files':preserved_art,'identity_unchanged':True,'voice_migration_changed_text_files':migration['changed_paths'],
        'voice_historical_receipts_preserved':True,'monk_candidate_sha256':sha(v['candidate']),
        'monk_other_archive_members_unchanged':1201,'contact_checks_passed':len(contacts['checks']),
        'python_scripts_syntax_checked':len(py),'blend':str(blend),'blend_sha256':sha(blend),
        'review_sheet':str(sheet),'review_sheet_sha256':sha(sheet),'screenshots':screenshots,
        'gates':{'user_blockout_approval':False,'detailed_art':False,'building_export':False,'building_cook':False,
                 'final_package':False,'native_import':False,'native_appearance':False,'native_gameplay':False,'multiplayer':False}}
    (OUT/'checkpoint-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('links','screenshots')},indent=2))
if __name__=='__main__':main()
