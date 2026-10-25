"""Strict 061 package, gated by native asset cook plus full byte/mount readback."""
import hashlib
import zipfile
from common import *

CREDITS='hosein81 and chilly5'
KEY=CFG['package_key']
GATES={'archive_bytes_and_tocs':True,'castle_asset_cook_readback':True,
       'source_normal_and_prior_art_preservation':True,'import':False,
       'native_appearance':False,'native_gameplay':False,'multiplayer':False}


def inspect_zip(path):
    path=Path(path)
    if path.name!=KEY+'-0.6.1.zip':raise ValueError('Strict061filename required')
    before=sha(path)
    with zipfile.ZipFile(path) as z:
        expected={'garrison.json',KEY+'.sga','START-HERE.txt','EVIDENCE.json'}
        if len(z.namelist())!=4 or set(z.namelist())!=expected:raise ValueError('Unexpected ZIP members')
        if z.testzip() is not None:raise ValueError('Unreadable ZIP')
        manifest=json.loads(z.read('garrison.json'));details=manifest['details']
        if (manifest['schema']!='garrison.mod/v1' or manifest['bundle_key']!=KEY
            or details['id']!=KEY or details['version']!='0.6.1' or details['author']!=CREDITS
            or details['content_types']!=['game-mode','tuning-pack']):raise ValueError('Manifest/version/identity/credits mismatch')
        with z.open(KEY+'.sga') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        if manifest['members']!=[{'mod_key':KEY,'role':'tuning','path':KEY+'.sga','sha256':digest}]:raise ValueError('Wrong owning SGA')
        ev=json.loads(z.read('EVIDENCE.json'))
        if (ev['schema']!='ccp.release061.evidence/v1' or ev['sga_sha256']!=digest
            or ev['baseline060_sga_sha256']!=SGA060_SHA or ev['credits']!=CREDITS
            or ev['version']!='0.6.1' or ev['is_final_release'] is not True):raise ValueError('Evidence basis differs')
        if any(ev['gates'].get(k) is not v for k,v in GATES.items()):raise ValueError('Native gates must remain explicitly unrun')
        text=z.read('START-HERE.txt').decode('utf-8')
        if CREDITS not in text or 'rollback' not in text.lower() or '0.6.0' not in text:raise ValueError('Missing instructions/rollback')
    if sha(path)!=before:raise ValueError('ZIP changed during inspection')
    return {'schema':'ccp-061-package-verification/v1','status':'zip_crc_manifest_identity_and_embedded_sga_hash_verified',
        'zip':str(path.resolve()),'zip_sha256':before,'zip_bytes':path.stat().st_size,
        'sga_sha256':digest,'gates':GATES,'members':sorted(expected),'native_match_verified':False}


def main():
    guard();frozen=baseline()
    proof_path=OUT/'qualification/final-r1/receipt.json';proof=read(proof_path)
    asset_path=OUT/'castle-object-payload-r1/verification.json';asset=read(asset_path)
    repair_path=OUT/'castle-object-payload-r1/receipt.json';repair=read(repair_path)
    assembly=read(OUT/'final-r1/assembly.json');candidate=owned(assembly['candidate'])
    review_path=OUT/'qualification/independent-final-review.json';review=read(review_path)
    if review.get('blockers')!=[] or review.get('candidate_sha256')!=sha(candidate):
        raise ValueError('Independent candidate review required')
    if (proof['status']!='complete_archive_bytes_mounts_source_normal_and_identity_verified'
        or sha(candidate)!=proof['candidate_sha256'] or sha(candidate)!=assembly['candidate_sha256']
        or proof['member_count']!=1202 or len(proof['mount_changes'])!=80
        or len(proof['changed_members'])!=15 or proof['unchanged_member_count']!=1187
        or not proof['prior_art_unchanged']):raise ValueError('Final archive proof differs')
    if (asset['status']!='passed_offline_fresh_cook_readback_and_scoped_payload'
        or not asset['native_cook_archive_crc_sha1_verified'] or asset['model_count']!=3
        or asset['payload_count']!=15 or assembly['repair_sha256']!=sha(repair_path)):
        raise ValueError('Separate native Castle asset qualification required')
    if sha(repair['native_cook_archive'])!=asset['native_cook_archive_sha256']:raise ValueError('Qualified native cook changed')
    for row in repair['payloads']:
        if sha(owned(row['path']))!=row['sha256'] or proof['member_hashes'][row['member']]['sha256']!=row['sha256']:
            raise ValueError('Qualified Castle payload changed')
    if files(ROOT/'assets')!=frozen['source'] or files(Path(CFG['source_root']))!=frozen['normal']:
        raise ValueError('Current source/normal differs from qualification')
    with zipfile.ZipFile(ZIP060) as z:manifest=json.loads(z.read('garrison.json'))
    digest=sha(candidate)
    manifest['members']=[{'mod_key':KEY,'role':'tuning','path':KEY+'.sga','sha256':digest}]
    manifest['details'].update(version='0.6.1',author=CREDITS,updated='2026-10-18',
        summary='Private unit blueprint mount and Castle landmark rendering repairs',
        description='Corrects 80 private unit blueprint archive sections and recooks custom Castle landmark models through the native object-PBR route used by working Berber buildings. Geometry and gameplay preserved. Fresh native visibility and player-colour testing remains required.',
        changelog='Private RGDs now mount in attrib; art remains in data. Custom Castle model/material triples freshly cooked as object/object_collection, retaining native lifecycle owners, selectors and markers.')
    reports={'archive':proof_path,'castle_assets':asset_path,'castle_recipe':repair_path,
        'freeze':OUT/'baseline/freeze.json','prior_art':OUT/'baseline/art-inputs.json',
        'tests':OUT/'qualification/tests-r1.json','independent_review':review_path}
    if read(reports['tests'])['exit_code']!=0:raise ValueError('Release regression tests have not passed')
    evidence={'schema':'ccp.release061.evidence/v1','version':'0.6.1','is_final_release':True,
        'credits':CREDITS,'sga_sha256':digest,'baseline060_sga_sha256':SGA060_SHA,
        'gates':GATES,'counts':{'members':1202,'unchanged060_payloads':1187,'changed060_payloads':9,
            'added_texture_payloads':6,'corrected_blueprint_mounts':80},
        'reports':{k:{'path':str(p),'sha256':sha(p)} for k,p in reports.items()},
        'limits':['Unit mount defect confirmed by exact archive sections and working Berber comparison.',
            'Castle object-PBR renderer is a fresh supported paired native-cook repair; native visibility causality is not proven until user test.',
            'Castle dynamic team tint may be reduced. Verify two player colours, healthy, damage, ruins and repair.',
            'Rattan visual switch and custom worker-elephant crate remain deferred as in060; stock siege crews retained.',
            'No native match, gameplay or multiplayer acceptance is claimed.'],
        'preservation':'All060payloads except nine explicitly allowed Castle model/material/geometry files are byte-identical; six private textures added. All80blueprint bytes unchanged; only TOCs corrected. Source, normal edition, prior art, project identity, abilities, statistics, voices, localization, all other civilizations and old releases retained.'}
    instructions='''Community Civilization Pack 0.6.1
Credits: hosein81 and chilly5

Close AoE4, import this ZIP through Garrison and select Community Civilization Pack
as both Game Mode and Tuning Pack. Start China and select Vietnam as usual.
This is a full replacement ZIP, not an incremental patch.

The 80 private unit blueprints now load from attrib rather than data. The custom
Castle landmark model/material assets use a fresh native object-PBR cook matching
the working Berber building route. Custom geometry, native lifecycle owners,
selectors, markers, footprints, statistics, abilities and production are retained.

Fresh native testing is still required: every unit/tier plus both completed Castle
landmarks, healthy/damaged/ruins/repair states, near/far views and two player colours.
Full dynamic Castle team tint may be reduced with object-PBR materials.
Rattan visual switching and the custom worker-elephant crate remain deferred.

Rollback: exact 0.6.0 ZIP is retained, but has the reported visibility failures.
The exact earlier final 0.5.3 ZIP is also retained; its custom Castle visibility was
not verified. Neither is presented as a proven visibility fallback.
Keep editable art, source, recipes, diagnostics and all earlier releases.

See tools/release_061/RELEASE_061_REPORT.md and NATIVE_TEST_CHECKLIST.md in the
editable project for source paths, precise evidence and reproducible rebuild steps.
'''
    folder=owned(OUT/'package-r1');delivery=owned(OUT/(KEY+'-0.6.1.zip'))
    if folder.exists() or delivery.exists():raise FileExistsError('Preserve previous packaging attempt')
    folder.mkdir(parents=True);write(folder/'garrison.json',manifest);write(folder/'EVIDENCE.json',evidence)
    (folder/'START-HERE.txt').write_text(instructions,encoding='utf-8')
    staged=folder/delivery.name
    with zipfile.ZipFile(staged,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in ('garrison.json','START-HERE.txt','EVIDENCE.json'):z.write(folder/name,name)
        z.write(candidate,KEY+'.sga')
    inspect_zip(staged);staged.replace(delivery);result=inspect_zip(delivery)
    write(OUT/'qualification/package-r1.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
