"""Compose presentation-only age/gender routing and a hash-addressed WAV map."""
import argparse
import json
import math
import re
from pathlib import Path

from local_bank import local_guard
from local_bank_validation import validate_structure,coverage,verify_bank
from pipeline import digest,save_json
from providers import OUT,ROOT
from voice_scope import delivery_manifest


def compose_bank(manifest,recordings,consumers,derived,guid):
    validate_structure(manifest)
    jobs={j['id']:j for j in manifest['jobs']}
    clips={};units={}
    for pool in manifest['pools']:
        ordered=sorted(pool['jobs'],key=lambda key:(jobs[key]['take'],jobs[key]['phrase_number']))
        choices=[[recordings[key].get('member','audio/voices/'+recordings[key]['sha256']+'.wav'),recordings[key]['duration']]
                 for key in ordered if key in recordings]
        clips.setdefault(pool['role'],{}).setdefault(pool['age'],{})[pool['event']]=choices
    complete=coverage(manifest,set(recordings))['technical_coverage_complete']
    for row in consumers:
        if not row['generation_admitted']:continue
        for role in row['roles']:
            for age in row['ages']:
                events=clips.get(role,{}).get('A'+str(age),{})
                if not events or any(len(choices)!=18 for choices in events.values()):complete=False
        official=row['member'].startswith('attrib/sbps/races/')
        name=derived.get(row['member']) if official else row['name']
        if not name:
            complete=False
            continue
        config=dict(role=row['roles'][0],private=True)
        if len(row['roles'])>1:config['female_role']=row['roles'][1]
        if row['age_policy']=='unit_tier':
            if len(row['ages'])!=1:raise ValueError('Ambiguous fixed unit tier')
            config['age']=row['ages'][0]
        elif row['age_policy']!='player_age':raise ValueError('Unsupported age-routing policy')
        key=guid+':'+name
        if key in units:raise ValueError('Duplicate voice consumer identity')
        units[key]=config
    return dict(complete=complete,units=units,clips=clips)


def lua_value(value):
    if isinstance(value,bool):return 'true' if value else 'false'
    if isinstance(value,str):return json.dumps(value,ensure_ascii=False)
    if isinstance(value,(int,float)) and math.isfinite(value):return repr(value)
    if isinstance(value,list):return '{'+','.join(lua_value(v) for v in value)+'}'
    if isinstance(value,dict):return '{'+','.join('['+lua_value(k)+']='+lua_value(v) for k,v in sorted(value.items()))+'}'
    raise ValueError('Unsupported Lua bank value')


def write_bank(path,bank):
    path.write_bytes(('-- Generated Vietnamese presentation-only voice bank.\nVietnamVoiceBank='+lua_value(bank)+'\n').encode('utf-8'))


def main():
    local_guard()
    parser=argparse.ArgumentParser();parser.add_argument('--partial-preview',action='store_true')
    parser.add_argument('--label');parser.add_argument('--compressed',action='store_true');args=parser.parse_args()
    if args.label and not re.fullmatch('[a-z0-9-]{1,50}',args.label):raise ValueError('Invalid immutable bank label')
    bank_root=OUT/'local'
    manifest_path=bank_root/'recording-manifest.json';manifest=json.loads(manifest_path.read_text())
    manifest=delivery_manifest(manifest)
    if args.partial_preview:
        verification=json.loads((bank_root/'bank-verification.json').read_text())
        if verification['manifest_sha256']!=digest(manifest_path):raise RuntimeError('Refresh changed-manifest verification first')
        scope_file=bank_root/'delivery-scope.json'
        if verification.get('delivery_scope_sha256')!=(digest(scope_file) if scope_file.exists() else None):
            raise RuntimeError('Refresh changed-scope verification first')
    else:verification=verify_bank()
    if verification['errors']:raise RuntimeError('Invalid recordings cannot enter a bank')
    if not args.partial_preview and not verification['technical_coverage_complete']:
        raise RuntimeError('Required coverage is incomplete; only an explicit partial preview can be written')
    cfg=json.loads((ROOT/'workspace.json').read_text())
    complete=OUT/'integration/voice-identities-complete.json'
    identities_path=complete if complete.exists() else OUT/'integration/voice-identities-v1/receipt.json'
    identities=json.loads(identities_path.read_text())
    audit_file=OUT/'integration/voice-identities-complete-audit.json' if complete.exists() else identities_path.parent/'identity-audit.json'
    identity_audit=json.loads(audit_file.read_text())
    if not identity_audit['passed'] or identity_audit['receipt_sha256']!=digest(identities_path):
        raise RuntimeError('Identity derivation is not verified')
    for component in identities.get('component_receipts',[]):
        if digest(component['file'])!=component['sha256']:raise RuntimeError('Changed identity component')
    derived={r['source']:r['name'] for r in identities['identities'] if r['category']=='sbps'}
    consumer_file=OUT/'inventory/consumers-complete.json'
    if not consumer_file.exists():raise RuntimeError('Complete default production reconciliation is required')
    consumers=json.loads(consumer_file.read_text())['rows']
    recordings=verification['recordings'];payload={}
    if args.compressed:
        from local_compress import compressed_recordings
        recordings=compressed_recordings(verification)
    for key,row in recordings.items():
        if digest(row['path'])!=row['sha256']:raise RuntimeError('Changed verified playback file')
        member=row.get('member','audio/voices/'+row['sha256']+'.wav')
        if member in payload:raise RuntimeError('Duplicate recording performance')
        payload[member]=dict(file=row['path'],sha256=row['sha256'])
    bank=compose_bank(manifest,recordings,consumers,derived,cfg['project_guid'].replace('-',''))
    stock_receipt=None
    if verification.get('delivery_scope_sha256'):
        from stock_efforts import load_stock_efforts,attach_stock_efforts
        stock=load_stock_efforts(verify_audio=True)
        attach_stock_efforts(bank,consumers,derived,cfg['project_guid'].replace('-',''),stock)
        stock_receipt=OUT/'integration/stock-efforts-v1/receipt.json'
        for row in stock['exports'].values():
            payload[row['member']]=dict(file=row['path'],sha256=row['sha256'])
    if args.partial_preview:bank['complete']=False
    elif not bank['complete']:raise RuntimeError('Consumer identity or role/age coverage is incomplete')
    dest=OUT/'integration'/(args.label or ('bank-partial-preview' if args.partial_preview else 'bank-complete'))
    if dest.exists():raise FileExistsError('Preserve previous bank evidence; use a new --label')
    dest.mkdir(parents=True)
    scar=dest/'voice_bank_084.scar'
    write_bank(scar,bank)
    save_json(dest/'payload-map.json',payload)
    save_json(dest/'receipt.json',dict(manifest_sha256=digest(manifest_path),bank_sha256=digest(scar),
              delivery_scope_sha256=verification.get('delivery_scope_sha256'),
              stock_effort_receipt_sha256=digest(stock_receipt) if stock_receipt else None,
              identity_receipt_sha256=digest(identities_path),verified_recordings=len(recordings),
              consumer_inventory_sha256=digest(consumer_file),
              admitted_consumers=len(bank['units']),complete=bank['complete'],partial_preview=args.partial_preview,
              codec='vorbis-64k-mono-48k' if args.compressed else 'pcm16-mono-48k',final_zip_limit_bytes=400000000,
              native_suppression=False,active_source_modified=False,package=False,
              note='Bank data preparation only; native speech suppression and lifecycle integration are separate.'))
    print('VOICE_BANK_PREPARED',len(recordings),'recordings',len(bank['units']),'consumers; complete=',bank['complete'])


if __name__=='__main__':main()
