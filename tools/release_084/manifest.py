"""Recording order contains only the currently admitted role/age/event pools."""
import hashlib
import json
import sys
from pipeline import save_json, guard, same_recording
from providers import ROOT, OUT


def recording_identity(row):
    fields={k:row.get(k) for k in ['role','age','text','take','direction','casting']}
    return hashlib.sha256(json.dumps(fields,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def supported_contexts(role):
    base={'select','acknowledge','hold','under_attack'}
    if role in ['SCOUT_F','INFANTRY_F']:return supported_contexts(role[:-2])
    if role.startswith('NAVAL_'):
        base.update(['sail','naval_stop'])
        if role in ['NAVAL_MILITARY','NAVAL_FIRE']:base.add('naval_attack')
        if role=='NAVAL_FISH':base.add('fish')
        if role=='NAVAL_TRADE':base.add('naval_trade')
        if role=='NAVAL_TRANSPORT':base.update(['transport_load','transport_unload'])
        return base
    base.update(['move','stop','retreat'])
    if role in ['CIV_M','CIV_F']:
        base.update(['build','wood','gold','stone','attack','garrison','ability_ack'])
    elif role=='TRADER':base.add('trade')
    elif role=='OFFICIAL':base.add('garrison')
    elif role=='MONK':base.update(['garrison','ability_ack'])
    else:
        base.update(['attack','attack_move'])
        if role in ['INFANTRY','ARCHER','SKIRMISHER','CROSSBOW','GUNNER']:base.add('garrison')
        if role in ['INFANTRY','ARCHER','SKIRMISHER','CAVALRY']:base.add('ability_ack')
    return base


def main():
    guard()
    cfg=json.loads((ROOT/'workspace.json').read_text())
    sys.path.insert(0,str(ROOT/'tools/release_071'))
    from resources import ResourceStore
    store=ResourceStore(Path(cfg['external_root'])/'resources_071')
    script=store.read_json('E/0.8.0/VOICE_SCRIPTS.json')
    consumers=json.loads((OUT/'inventory/consumers.json').read_text())['rows']
    casting=json.loads((OUT/'casting.json').read_text())['roles']
    active={}
    for consumer in consumers:
        if consumer['generation_admitted']:
            for role in consumer['roles']:active.setdefault(role,set()).update(consumer['ages'])
    by_pool={}
    for row in script['lines']:
        by_pool.setdefault((row['profile'],row['age_bank'],row['context']),[]).append(row)
    dest=OUT/'recording-manifest.json'
    previous=json.loads(dest.read_text())['jobs'] if dest.exists() else []
    # Preserve legacy IDs only for the identical performance and casting recipe.
    prior_ids={recording_identity(j):j['id'] for j in previous}
    started_roles=set()
    state_file=OUT/'generation/state.json'
    if state_file.exists():
        for row in json.loads(state_file.read_text()).values():
            started_roles.add(row.get('metadata',{}).get('job',{}).get('role'))
    for receipt in (OUT/'generation').glob('**/jobs.json'):
        if (receipt.parent/'request-started.json').exists():
            started_roles.update(j['role'] for j in json.loads(receipt.read_text()))
    for j in previous:
        if j['role'] in started_roles and j['casting']!=casting.get(j['role']):
            raise ValueError('Cannot change casting of a started role: '+j['role'])
    jobs={};aliases=[];pools=[]
    tones={1:'plain and direct',2:'disciplined readiness',3:'seasoned confidence',4:'composed authority'}
    performance={'T1':'natural and measured','T2':'prompt and purposeful','T3':'assured with a fresh rhythm'}
    # Record complete roles in a stable order; caller can checkpoint without changing voices.
    role_order=['CIV_M','CIV_F','SCOUT','SCOUT_F','SKIRMISHER','INFANTRY','INFANTRY_F','ARCHER','CROSSBOW','GUNNER',
                'CAVALRY','MONK','OFFICIAL','TRADER','SIEGE','NAVAL_FISH','NAVAL_TRADE',
                'NAVAL_MILITARY','NAVAL_TRANSPORT','NAVAL_FIRE']
    for role in role_order:
        if role not in active:continue
        if role not in casting:raise ValueError('Role has no qualified casting: '+role)
        source_role='INFANTRY' if role=='SKIRMISHER' else (role[:-2] if role in ['SCOUT_F','INFANTRY_F'] else role)
        for age in sorted(active[role]):
            for event in sorted(supported_contexts(role)|{'pain_light','death'}):
                lines=by_pool.get((source_role,f'A{age}',event),[])
                if len(lines)!=6:raise ValueError(f'Incomplete six-line source pool {role} A{age} {event}: {len(lines)}')
                pool=[]
                for row in sorted(lines,key=lambda x:x['phrase_number']):
                    for take in row['takes']:
                        effort=row.get('kind')=='nonverbal_effort'
                        urgent=event in ['attack','attack_move','naval_attack','under_attack','retreat']
                        style='urgent, clearly articulated' if urgent else performance[take['take']]
                        direction=(row['performance_description']+' '+take['direction']) if effort else 'Northern Vietnamese; '+tones[age]+'; '+style
                        text=('[grunt]' if event=='pain_light' else '[groan]') if effort else row['vietnamese']
                        job=dict(role=role,age='ANY' if effort else f'A{age}',event=event,text=text,take=take['take'],
                                 direction=direction,source_phrase_id=row['id'],source_take_direction=take['direction'],
                                 phrase_number=row['phrase_number'],kind='nonverbal_effort' if effort else 'dialogue')
                        job['casting']=casting[role]
                        identity=recording_identity(job)
                        key=prior_ids.get(identity,identity)
                        alias_id=row['id']+'_'+take['take']
                        if role=='SKIRMISHER':alias_id=alias_id.replace('VN070_INFANTRY','VN084_SKIRMISHER')
                        if role in ['SCOUT_F','INFANTRY_F']:
                            alias_id=alias_id.replace('VN070_'+source_role,'VN084_'+role)
                        if key not in jobs:
                            jobs[key]=dict(id=key,**job)
                        aliases.append(dict(id=alias_id,source_phrase_id=row['id'],role=role,age=f'A{age}',event=event,
                                            job=key,reason='same actor human nonverbal effort deliberately shared across ages' if effort else
                                            ('identical actor, age, words, take and delivery' if jobs[key]['event']!=event else 'direct')))
                        pool.append(key)
                pools.append(dict(role=role,age=f'A{age}',event=event,jobs=pool))
    data=dict(schema='ccp-084-recording-manifest/v1',jobs=list(jobs.values()),aliases=aliases,pools=pools,
              source_script_sha256=hashlib.sha256(store.read('E/0.8.0/VOICE_SCRIPTS.json')).hexdigest(),
              scope='supported scripted response events; no claim of native dialogue-tree parity',
              missing_qualification=['naval private-owner suppression','audible pronunciation and acting'],
              age_performance='creative age-specific delivery; modern Northern pronunciation, no medieval reconstruction claim')
    dest=OUT/'recording-manifest.json'
    if dest.exists():
        if json.loads(dest.read_text())!=data:
            if '--revise' not in sys.argv:raise ValueError('Recording manifest drift: preserve old manifest and explicitly revise')
            old=dest.read_bytes();prior=OUT/('recording-manifest-'+hashlib.sha256(old).hexdigest()[:12]+'.json')
            if prior.exists():assert prior.read_bytes()==old
            else:prior.write_bytes(old)
            save_json(dest,data)
    else:save_json(dest,data)
    save_json(OUT/'generation-summary.json',dict(required_jobs=len(jobs),directed_slots=len(aliases),pools=len(pools),
              deliberate_reuse=len(aliases)-len(jobs),roles={k:sorted(v) for k,v in active.items()},
              inworld_characters=sum(len(j['text'])+len(j['direction'])+3 for j in jobs.values() if j['casting']['provider']=='inworld')))
    print('084_RECORDING_ORDER',len(jobs),'UNIQUE_JOBS',len(aliases),'DIRECTED_SLOTS',len(pools),'POOLS')


if __name__=='__main__':
    from pathlib import Path
    main()
