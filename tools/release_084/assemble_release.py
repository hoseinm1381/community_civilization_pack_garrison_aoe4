"""Strict ordinary 0.8.4 ZIP, preserving the 083 owning archive and all art.

No incomplete bank can reach assembly. Native in-game acceptance stays separate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from pipeline import digest,save_json
from local_bank import local_guard as guard
from providers import ROOT,OUT
from local_bank_validation import verify_bank
from local_compress import compressed_recordings,enforce_zip_budget
from voice_lifecycle import patch_mode,patch_precache
from voice_bank import compose_bank,lua_value
from voice_scope import delivery_manifest,require_stock_effort_preservation


def require_complete(audio,bank,overlay):
    if (not audio['technical_coverage_complete'] or audio['errors'] or
        audio['verified_jobs']!=audio['required_jobs'] or not bank['complete'] or bank['partial_preview'] or
        bank['verified_recordings']!=audio['required_jobs'] or bank['codec']!='vorbis-64k-mono-48k' or overlay['plan_only']):
        raise RuntimeError('Full 0.8.4 delivery requires complete verified audio, compressed bank and private suppression coverage')


def require_bank_coherence(stored_scar,expected_scar,stored_payload,exports):
    expected={r['member']:r['sha256'] for r in exports.values()}
    if stored_scar!=expected_scar or {k:r['sha256'] for k,r in stored_payload.items()}!=expected:
        raise RuntimeError('Bank routing/payload hashes differ from the freshly verified compressed recordings')


def main():
    guard();parser=argparse.ArgumentParser();parser.add_argument('--label',required=True)
    parser.add_argument('--bank',type=Path,required=True);parser.add_argument('--overlay',type=Path,required=True)
    args=parser.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,50}',args.label):raise ValueError('Invalid immutable release label')
    cfg=json.loads((ROOT/'workspace.json').read_text());bank_file=args.bank/'receipt.json';overlay_file=args.overlay/'receipt.json'
    bank=json.loads(bank_file.read_text());overlay=json.loads(overlay_file.read_text())
    audio=verify_bank();require_complete(audio,bank,overlay)
    if audio.get('delivery_scope_sha256'):
        require_stock_effort_preservation(overlay.get('stock_effort_proof'))
        if bank.get('delivery_scope_sha256')!=audio['delivery_scope_sha256']:
            raise RuntimeError('Bank delivery scope differs')
    if bank['manifest_sha256']!=audio['manifest_sha256'] or bank['bank_sha256']!=digest(args.bank/'voice_bank_084.scar'):
        raise RuntimeError('Complete bank changed')
    if overlay['bank_receipt_sha256']!=digest(bank_file):raise RuntimeError('Suppression coverage proof changed')
    identities_file=OUT/'integration/voice-identities-complete.json';identities=json.loads(identities_file.read_text())
    if bank['identity_receipt_sha256']!=digest(identities_file) or overlay['identity_receipt_sha256']!=digest(identities_file):
        raise RuntimeError('Identity mapping changed')
    consumers=OUT/'inventory/consumers-complete.json'
    if bank['consumer_inventory_sha256']!=digest(consumers) or overlay['consumer_inventory_sha256']!=digest(consumers):
        raise RuntimeError('Consumer scope changed')
    native_process=subprocess.run([cfg['blender_python'],'-B',str(ROOT/'tools/release_084/native_reference_proof.py')],
                                  capture_output=True,text=True,encoding='utf-8',errors='replace')
    if native_process.returncode:
        raise RuntimeError('Fresh native reference provenance audit failed: '+native_process.stderr[-2000:])
    native_proof=json.loads(native_process.stdout)
    if native_proof!=overlay.get('native_reference_proof'):
        raise RuntimeError('Native reference compilation proof differs from suppression overlay')
    exports=compressed_recordings(audio)
    manifest=json.loads((OUT/'local/recording-manifest.json').read_text())
    manifest=delivery_manifest(manifest)
    derived={r['source']:r['name'] for r in identities['identities'] if r['category']=='sbps'}
    recomposed=compose_bank(manifest,exports,json.loads(consumers.read_text())['rows'],derived,cfg['project_guid'].replace('-',''))
    stock=None;all_exports=dict(exports)
    if audio.get('delivery_scope_sha256'):
        from stock_efforts import load_stock_efforts,attach_stock_efforts
        stock=load_stock_efforts(verify_audio=True)
        stock_receipt=OUT/'integration/stock-efforts-v1/receipt.json'
        if (bank.get('stock_effort_receipt_sha256')!=digest(stock_receipt) or
            overlay['stock_effort_proof']['receipt_sha256']!=digest(stock_receipt)):
            raise RuntimeError('Fresh stock effort proof differs from bank/overlay')
        attach_stock_efforts(recomposed,json.loads(consumers.read_text())['rows'],derived,cfg['project_guid'].replace('-',''),stock)
        all_exports.update({'stock:'+k:r for k,r in stock['exports'].items()})
    expected_scar=('-- Generated Vietnamese presentation-only voice bank.\nVietnamVoiceBank='+lua_value(recomposed)+'\n').encode('utf-8')
    require_bank_coherence((args.bank/'voice_bank_084.scar').read_bytes(),expected_scar,
                           json.loads((args.bank/'payload-map.json').read_text()),all_exports)
    subprocess.run([cfg['python'],'-B',str(ROOT/'tools/release_084/check_preservation.py')],check=True)
    sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
    base=ROOT/'output/release_083/delivery/final-v2';proof=json.loads((base/'verification.json').read_text())
    baseline=base/'community_civilization_pack.sga'
    if digest(baseline)!=proof['sga_sha256'] or digest(base/'community_civilization_pack-0.8.3.zip')!=proof['zip_sha256']:
        raise RuntimeError('083 final-v2 delivery changed')
    check(ROOT,baseline)
    dest=OUT/'delivery'/args.label
    if dest.exists():raise FileExistsError('Preserve release attempts; use a new label')
    dest.mkdir(parents=True)
    save_json(dest/'audio-verification.json',audio)
    attr=json.loads((args.overlay/'payload-map.json').read_text())
    delta={r['member']:r['after_sha256'] for r in overlay['deltas']}
    if {k:v['sha256'] for k,v in attr.items()}!=delta or any(not k.startswith('attrib/') or not k.endswith('.rgd') for k in attr):
        raise RuntimeError('Attribute payload differs from the reversible overlay audit')
    data={}
    def emit(member,content):
        target=dest/'generated'/member;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content.encode('utf-8') if isinstance(content,str) else content)
        data[member]=dict(file=str(target),sha256=digest(target))
    def read_original(member):
        path=base/'readback'/member
        if digest(path)!=proof['member_sha256'][member]:raise RuntimeError('083 script readback changed')
        return path.read_text(encoding='utf-8')
    mode='scar/winconditions/vietnammode.scar';precache='scar/vietnam/prematch_precache.scar'
    emit(mode,patch_mode(read_original(mode)))
    emit(precache,patch_precache(read_original(precache),identities['identities'],cfg['project_guid'].replace('-','')))
    emit('scar/vietnam/voices_084.scar',(ROOT/'tools/release_084/templates/voices.scar').read_bytes())
    emit('scar/vietnam/voice_bank_084.scar',(args.bank/'voice_bank_084.scar').read_bytes())
    helper=Path(cfg['garrison_extension'])/'garrison_shared/scar_modules/garrison.scar'
    emit('scar/garrison/garrison.scar',helper.read_bytes())
    for row in all_exports.values():
        member=row['member']
        if member in data:
            if data[member]['sha256']!=row['sha256']:raise RuntimeError('Conflicting audio payload')
            continue
        data[member]=dict(file=row['path'],sha256=row['sha256'])
    payload={**attr,**data}
    if len(payload)!=len(attr)+len(data):raise RuntimeError('Payload member collision')
    for member,row in payload.items():
        if digest(row['file'])!=row['sha256']:raise RuntimeError('Payload changed: '+member)
    save_json(dest/'changed-member-policy.json',dict(payload=payload,baseline_archive_sha256=proof['sga_sha256'],
              unchanged_members={k:v for k,v in proof['member_sha256'].items() if k not in payload},
              bank_receipt_sha256=digest(bank_file),overlay_receipt_sha256=digest(overlay_file)))
    def run(label,command):
        proc=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding='utf-8',errors='replace')
        (dest/(label+'.log')).write_text('EXIT '+str(proc.returncode)+'\n'+proc.stdout+'\n'+proc.stderr,encoding='utf-8')
        if proc.returncode:raise RuntimeError('Archive step failed: '+label)
        return proc.stdout
    # New blueprint resources need attrib TOC; audio and SCAR need data TOC.
    attr_list=dest/'attrib-members.txt';data_list=dest/'data-members.txt'
    for path,mapping in [(attr_list,attr),(data_list,data)]:
        path.write_text('\n'.join(k+'='+v['file'] for k,v in sorted(mapping.items()))+'\n',encoding='utf-8')
    intermediate=dest/'attributes-overlay.sga';final=dest/'community_civilization_pack.sga'
    run('assemble-attributes',[cfg['archive_tool'],'set-members',baseline,attr_list,intermediate,'--alias','attrib'])
    check(ROOT,intermediate)
    run('assemble-data',[cfg['archive_tool'],'set-members',intermediate,data_list,final,'--alias','data'])
    check(ROOT,final)
    listing=json.loads(run('list-verify',[cfg['archive_tool'],'list',final,'--verify']))
    mounts={m['path']:m['toc'] for m in listing['members']}
    if not listing['archive']['verification']['verified']:raise RuntimeError('Final SGA verification failed')
    if any(mounts.get(k)!=v for k,v in proof['mounts'].items()):raise RuntimeError('Original TOC changed')
    if any(mounts.get(k)!=('attrib' if k.startswith('attrib/') else 'data') for k in payload):raise RuntimeError('New resource TOC differs')
    readback=dest/'fresh-readback';run('fresh-extract',[cfg['archive_tool'],'extract',final,readback,'--filter','.'])
    actual={p.relative_to(readback).as_posix():digest(p) for p in readback.rglob('*') if p.is_file()}
    expected=dict(proof['member_sha256']);expected.update({k:v['sha256'] for k,v in payload.items()})
    if actual!=expected:raise RuntimeError('Final readback differs from the exact changed-member policy')
    if any(not k.endswith('.ogg') for k in actual if k.startswith(('audio/voices/','audio/stock_efforts/'))):raise RuntimeError('Uncompressed voice payload in final archive')
    manifest=json.loads((base/'garrison.json').read_text());manifest['members'][0]['sha256']=digest(final)
    manifest['details'].update(version='0.8.4',updated='2026-10-25',
        summary='Vietnamese human unit voices across available ages, gender variations and naval crews.',
        description='Northern Dai Viet voice candidates with six alternative lines and three takes per supported spoken response pool, plus original stock effort media. Preserves the 0.8.3 artwork, buffalo animations and gameplay.',
        changelog='Compressed Vietnamese spoken dialogue and original stock effort media; private speech owners and local presentation routing. Stock effort timing and the documented female infantry fallback, pronunciation, audible quality, age routing, overlap, save/load and multiplayer require acceptance.')
    save_json(dest/'garrison.json',manifest)
    (dest/'START-HERE.txt').write_text('Garrison 0.8.4\n\nOrdinary Garrison ZIP; select its Tuning Pack and Vietnam Game Mode as before. No voice installer or new configuration.\n\nRequired candidate audio coverage is complete and compressed. Original masters remain in the authoring workspace. All unrelated 0.8.3 archive members, artwork and buffalo animation bytes are retained.\n\nNative editable identity reference compilation and typed reversible post-cook voice overlays are separate evidence. Full native voice playback, compressed decoder behavior in-game, pronunciation/acting, age/gender routing, original-voice overlap, save/load and multiplayer remain independent acceptance gates. Historical pronunciation is a creative approximation. No installation/publication was performed.\n',encoding='utf-8')
    with (dest/'START-HERE.txt').open('a',encoding='utf-8') as note:
        note.write('\n'+str(audio.get('user_accepted_minor_speech_exceptions',0))+' final saved spoken takes retain user-accepted minor pronunciation, word recognition or short repetition imperfections. They passed audio integrity checks; they did not pass the exact-word screen. Native-speaker approval remains pending.\n')
    package=dest/'community_civilization_pack-0.8.4.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in [dest/'garrison.json',final,dest/'START-HERE.txt']:z.write(path,path.name)
    try:size=enforce_zip_budget(package)
    except RuntimeError:
        save_json(dest/'budget-exceeded.json',dict(bytes=package.stat().st_size,limit_bytes=400000000,notify_user=True,delivered=False))
        raise
    with zipfile.ZipFile(package) as z:
        if z.testzip() is not None or set(z.namelist())!={'garrison.json',final.name,'START-HERE.txt'}:raise RuntimeError('Final ZIP integrity/member failure')
        if z.read('garrison.json')!=(dest/'garrison.json').read_bytes():raise RuntimeError('Embedded manifest differs')
        with z.open(final.name) as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest(final):raise RuntimeError('Embedded SGA differs')
    save_json(dest/'verification.json',dict(version='0.8.4',zip=str(package),zip_sha256=digest(package),zip_bytes=size,
        audio_verification_sha256=digest(dest/'audio-verification.json'),
        final_zip_limit_bytes=400000000,sga_sha256=digest(final),archive_identity=listing['archive']['name'],
        member_sha256=actual,mounts=mounts,changed=sorted(k for k in payload if k in proof['member_sha256']),
        added=sorted(set(payload)-set(proof['member_sha256'])),deleted=[],required_recordings=audio['required_jobs'],
        user_accepted_minor_speech_exceptions=audio.get('user_accepted_minor_speech_exceptions',0),
        all_compressed_voice_hashes_verified=True,all_unrelated_members_and_original_mounts_exact=True,
        stock_effort_sources=len(stock['exports']) if stock else 0,stock_effort_aliases=stock['aliases'] if stock else [],
        original_stock_effort_scheduling_preserved=False,
        actual_native_reference_compilation=True,post_cook_voice_overlay=True,full_voice_native_compile=False,
        native_reference_proof=native_proof,
        client_import=False,native_compressed_playback=False,audible_quality=False,save_load=False,multiplayer=False,
        installed=False,published=False))
    print('084_FULL_CANDIDATE_PACKAGE_VERIFIED',size,'bytes;',package,flush=True)


if __name__=='__main__':main()
