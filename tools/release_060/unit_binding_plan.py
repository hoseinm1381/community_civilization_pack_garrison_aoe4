"""Freeze exact native body-list/actor slots before private identity integration.

This prepares private Garrison attachment identities only. It cannot apply a
model or change the active project; qualified art receipts are a later gate.
"""
import argparse
import json
import msvcrt
import re
import subprocess
from pathlib import Path
from common import CFG, CORE, NATIVE_LOCK, OUT, RECIPES, STAGING, guard, owned, read, sha, write

INVENTORY=OUT/'inventory/visual-bindings.json'
INVENTORY_SHA='9ba07a2bb420366ec662e850c84a0bee1fe36a744938592391be5a093e0a791a'
PLAN=RECIPES/'foot-body-private-binding-plan.json'
PROJECT=STAGING/'i/Mods/v60ids'
EVIDENCE=OUT/'integration/private-foot-identities'


def normalize(value):
    return value.replace('\\','/').removesuffix('.rgm')


def select_slots(resources,model):
    """Select render slots only; animation owners can never become art targets."""
    result={}
    for member,record in resources.items():
        matches=[s for s in record['slots'] if normalize(s['before_value'])==normalize(model)
                 and s['role']=='render_model_slot'
                 and re.fullmatch(r'animator\d+',s['field'])]
        if matches:
            if not member.startswith('attrib/attachments/attachment_lists/'):
                raise ValueError('Body owner is not an attachment list')
            result[member]=matches
    if len(result)!=1:
        raise ValueError(f'Expected exactly one body list for {model}; got {list(result)}')
    return next(iter(result.items()))


def prepare_plan():
    guard()
    if sha(INVENTORY)!=INVENTORY_SHA:raise ValueError('Binding inventory changed')
    inventory=read(INVENTORY)
    ranged=read(RECIPES/'ranged-roster-060.json')
    feet=read(RECIPES/'representative-foot-tier-batch.json')
    models=[(x['slug'],x['exact_native_body_model']) for x in ranged['tiers']]
    models += [('spear'+str(x['age']),x['model_path']) for x in feet['models']
               if '/chi_infantry_light_age' in x['model_path']]
    if len(models)!=10 or len({x[0] for x in models})!=10:
        raise ValueError('All six ranged and four spear body tiers required')
    records=[]
    for slug,model in models:
        member,slots=select_slots(inventory['native_attachment_resources'],model)
        original_ref=member.removeprefix('attrib/').removesuffix('.rgd').replace('/','\\')
        consumers=[]
        seen=set()
        for family in inventory['families']:
            for actor in family['actor_bindings']:
                for node in actor['visual_and_owner_references']:
                    if node['before_value']!=original_ref:continue
                    key=(node['source']['asset_relative_path'],node['node_path'])
                    if key in seen:continue
                    seen.add(key)
                    if node['edit_policy']!='visual_override_reference_only':
                        raise ValueError('Nonvisual actor field requested')
                    if sha(node['source']['path'])!=node['source']['sha256']:
                        raise ValueError('Pinned consumer source changed')
                    consumers.append(node)
        if not consumers:raise ValueError('No local body-list consumers: '+slug)
        for slot in slots:
            if sha(slot['raw_archive_member_path'])!=slot['raw_archive_member_sha256']:
                raise ValueError('Official body attachment changed')
        records.append({'slug':slug,'stock_model':normalize(model),
                        'stock_member':member,'stock_slots':slots,'actor_consumers':consumers,
                        'derived_name':'vn060_body_'+slug,
                        'private_reference':'attachments/attachment_lists/vietnam/release_060/vn060_body_'+slug,
                        'private_model':None,'qualified_art_receipt':None,
                        'parent_animator_policy':'preserve every native owner byte-for-byte'})
    data={'schema':'ccp-060-private-foot-body-plan/v1',
          'status':'exact_slots_pinned_art_not_integrated',
          'inventory_sha256':INVENTORY_SHA,'final_baseline_version':'0.5.3',
          'project_guid':CFG['project_guid'],'entries':records,
          'limits':'Identity preparation only; no source changes, art activation, cook or native acceptance.'}
    if PLAN.exists():
        if read(PLAN)!=data:raise ValueError('Preserve existing binding plan')
    else:write(PLAN,data)
    return data


def prepare_identities():
    data=prepare_plan()
    receipt=EVIDENCE/'prepare.json'
    if PROJECT.exists() or EVIDENCE.exists():
        raise FileExistsError('Preserve existing identities; never allocate replacement PBG IDs')
    EVIDENCE.mkdir(parents=True)
    proof={'schema':'ccp-060-private-foot-identity-preparation/v1','status':'preparing',
           'plan':str(PLAN),'plan_sha256':sha(PLAN),'project':str(PROJECT),'steps':[]}
    def run(label,args):
        proc=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True,
                            encoding='utf-8',errors='replace',timeout=180)
        log=EVIDENCE/(label+'.log')
        log.write_text('EXIT '+str(proc.returncode)+'\n'+proc.stdout+'\n'+proc.stderr,encoding='utf-8')
        proof['steps'].append({'step':label,'exit_code':proc.returncode,'log':str(log),'sha256':sha(log)})
        write(receipt,proof)
        if proc.returncode:raise RuntimeError('Identity preparation failed: '+label)
    with NATIVE_LOCK.open('r+b') as lock:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try:
            run('create',['mod-project','create','--library',PROJECT.parent.parent,'--name',PROJECT.name])
            run('settings',['mod-project','settings','--project',PROJECT,'--live-reload','off','--mod-id',CFG['project_guid']])
            for row in data['entries']:
                run(row['slug'],['mod-project','derive','--project',PROJECT,
                                 '--source',row['stock_member'].removeprefix('attrib/').removesuffix('.rgd'),
                                 '--name',row['derived_name']])
            config=read(PROJECT/'mod-project.json')
            if (config.get('game_mode',{}).get('enabled') or config.get('animated_units')
                    or len(config['derived_blueprints'])!=10):
                raise ValueError('Unexpected private identity content')
            proof.update(status='identities_prepared_native_cook_pending',
                         configuration_sha256=sha(PROJECT/'mod-project.json'))
            write(receipt,proof)
        except BaseException as error:
            proof.update(status='failed_diagnostics_preserved',error=str(error));write(receipt,proof)
            raise
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    return proof


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('plan','prepare-identities'))
    args=parser.parse_args()
    result=prepare_plan() if args.action=='plan' else prepare_identities()
    print(json.dumps({'status':result['status'],'plan':str(PLAN)},indent=2))
