"""Inventory native effort sources separately from generated spoken dialogue."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import sys
import warnings
from pipeline import guard, digest, save_json
from providers import ROOT, OUT
from stock_profile import read_stock_profile


def attach_stock_efforts(bank,consumers,derived,guid,stock):
    for row in consumers:
        if not row['generation_admitted']:continue
        name=derived.get(row['member']) if row['member'].startswith('attrib/sbps/races/') else row['name']
        key=guid+':'+name if name else None
        if key not in bank['units'] or row['name'] not in stock['consumers']:
            raise RuntimeError('Stock effort consumer binding differs')
        mapping=stock['consumers'][row['name']]
        bank['units'][key]['stock_speaker']=mapping['male']
        if mapping.get('female'):bank['units'][key]['stock_female_speaker']=mapping['female']
    bank['stock_efforts']={speaker:{event:[[r['member'],r['duration']] for r in rows]
                         for event,rows in events.items()} for speaker,events in stock['clips'].items()}


def load_stock_efforts(verify_audio=False):
    folder=OUT/'integration/stock-efforts-v1';receipt=folder/'receipt.json'
    stock=json.loads(receipt.read_text());recipe_file=folder/'recipe.json'
    recipe=json.loads(recipe_file.read_text())
    source=OUT/'integration/stock-effort-inventory-v1/inventory.json'
    inventory=json.loads(source.read_text())
    consumer_file=OUT/'inventory/consumers-complete.json'
    if (stock['recipe_sha256']!=digest(recipe_file) or stock['inventory_sha256']!=digest(source) or
        recipe['inventory_sha256']!=digest(source) or
        stock['consumer_inventory_sha256']!=digest(consumer_file) or
        digest(inventory['archive'])!=inventory['archive_sha256']):
        raise RuntimeError('Stock effort source/recipe provenance changed')
    for path,sha in recipe['tool_sha256'].items():
        if digest(path)!=sha:raise RuntimeError('Stock effort decoder/encoder changed')
    expected_members={m for p in inventory['profiles'].values() for r in p['records'] for m in r['media']}
    if set(stock['exports'])!=expected_members:raise RuntimeError('Stock effort source coverage differs')
    clips={}
    for speaker,profile in inventory['profiles'].items():
        if digest(profile['file'])!=profile['sha256']:raise RuntimeError('Stock effort profile changed')
        events={}
        for record in profile['records']:
            events.setdefault(record['event'],[]).extend(stock['exports'][m] for m in record['media'])
        clips[speaker]={event:list({r['sha256']:r for r in rows}.values()) for event,rows in events.items()}
    if clips!=stock['clips']:raise RuntimeError('Stock effort event routing differs from native inventory')
    actual_consumers=stock['consumers'];expected_consumers=json.loads(json.dumps(inventory['consumers']))
    expected_aliases=[]
    for name,mapping in expected_consumers.items():
        for sex,speaker in list(mapping.items()):
            key=speaker.lower()
            if key not in clips:
                if key!='manatarmsfemale' or 'villagerfemale' not in clips:raise RuntimeError('Unresolved stock speaker')
                expected_aliases.append((name,sex,speaker,'villagerfemale'));key='villagerfemale'
            mapping[sex]=key
    if actual_consumers!=expected_consumers or sorted((r['consumer'],r['sex'],r['original'],r['reuse']) for r in stock['aliases'])!=sorted(expected_aliases):
        raise RuntimeError('Stock effort consumer/alias mapping differs')
    def inspect_stock(row):
        if row['recipe_sha256']!=digest(recipe_file):raise RuntimeError('Stock effort recipe differs')
        for path,sha in row['saved_sha256'].items():
            if digest(path)!=sha:raise RuntimeError('Stock effort audio changed')
        if digest(row['path'])!=row['sha256'] or row['member']!='audio/stock_efforts/'+row['sha256']+'.ogg':
            raise RuntimeError('Stock effort embedded hash differs')
        if verify_audio:
            from stock_export import metrics
            if metrics(row['path'])!=row['encoded_metrics']:raise RuntimeError('Stock effort full decode differs')
    with ThreadPoolExecutor(max_workers=8) as readers:
        for count,_ in enumerate(readers.map(inspect_stock,stock['exports'].values()),1):
            if count%200==0:print('STOCK_EFFORTS_RECHECKED',count,flush=True)
    if stock.get('stock_effort_preservation_complete') is not True:raise RuntimeError('Stock effort export incomplete')
    return stock


def context_event(context):
    match=re.fullmatch(r'(effortDeath|effortPain|effortPainBig)_i[A-Za-z]+_cNone',context)
    return {'effortDeath':'death','effortPain':'pain_light','effortPainBig':'pain_heavy'}.get(match[1]) if match else None


def consumer_speakers(row):
    male={r['value'] for r in row['speech'] if r['path'].startswith('/default/') and r['value']}
    if len(male)!=1:raise ValueError('Ambiguous native primary speaker')
    result=dict(male=next(iter(male)))
    if len(row['roles'])>1:
        female={r['value'] for r in (row.get('attachment_speakers') or []) if r['value'].lower().endswith('female')}
        if len(female)!=1:raise ValueError('Ambiguous native female speaker')
        result['female']=next(iter(female))
    return result


def inventory():
    guard()
    dest=OUT/'integration/stock-effort-inventory-v1'
    if (dest/'inventory.json').exists():raise FileExistsError('Preserve completed stock effort inventory')
    runtime=Path('C:/Users/RS/.codex/cache/aoe4-sga-extractor-session-20260717/_skill_sga_live_runtime')
    sys.path[:0]=[str(runtime/'site-packages'),str(runtime/'SGA-V10/src'),
                 'C:/Users/RS/.codex/skills/aoe4-garrison-blender/scripts']
    warnings.filterwarnings('ignore')
    from relic.sga.v10 import EssenceFSHandler
    from relic.sga.core.definitions import Version
    EssenceFSHandler.version=Version(10,0)
    source=OUT/'inventory/consumers-complete.json'
    rows=[r for r in json.loads(source.read_text())['rows'] if r['generation_admitted']]
    consumers={r['name']:consumer_speakers(r) for r in rows}
    speakers={speaker.lower() for mapping in consumers.values() for speaker in mapping.values()}
    archive=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/SoundSpeechChinese.sga')
    profiles={};missing=[]
    dest.mkdir(parents=True,exist_ok=True)
    with archive.open('rb') as stream:
        fs=EssenceFSHandler.read(stream)
        files={p.lower().lstrip('/'):p for p in fs.walk.files()}
        for speaker in sorted(speakers):
            member=files.get('chinese_'+speaker+'.spd')
            if not member:
                missing.append(speaker);continue
            raw=fs.readbytes(member);target=dest/'profiles'/Path(member).name
            target.parent.mkdir(exist_ok=True)
            if target.exists():
                if target.read_bytes()!=raw:raise RuntimeError('Saved stock profile changed')
            else:target.write_bytes(raw)
            records=[]
            for r in read_stock_profile(raw):
                event=context_event(r['context']['text'])
                if event is None:continue
                if r['race']['text'].lower()!='chinese' or r['speaker']['text'].lower()!=speaker:
                    raise RuntimeError('Native profile speaker identity differs')
                media=[]
                for item in r['media']:
                    name=item['text'].replace('\\','/').lower()
                    if name not in files:raise RuntimeError('Missing stock effort media: '+name)
                    media.append(files[name])
                records.append(dict(context=r['context']['text'],event=event,media=media))
            profiles[speaker]=dict(profile=member,file=str(target),sha256=digest(target),records=records)
    result=dict(archive=str(archive),archive_sha256=digest(archive),
                consumer_inventory_sha256=digest(source),consumers=consumers,profiles=profiles,
                missing_speaker_profiles=missing,aliases=[],stock_effort_preservation_complete=False,
                native_scheduling_preserved=False,active_source_modified=False)
    save_json(dest/'inventory.json',result)
    print('STOCK_EFFORT_INVENTORY',len(profiles),'profiles;',len(consumers),'consumers; missing:',missing,flush=True)


if __name__=='__main__':inventory()
