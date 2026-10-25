"""Prepare, cook and register one native identity batch; no active source writes."""
from __future__ import annotations

import argparse
import json
import msvcrt
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, CFG, CORE, NATIVE_LOCK, OUT, ROOT, STAGING, guard, owned, read, sha, write

PLAN = OUT/'integration/private-land-identities/derive-plan-v5.json'
EVIDENCE = OUT/'integration/private-land-identities/native-batch-v5'
PROJECT = STAGING/'i/Mods/v6ic'
FIRST = OUT/'integration/private-foot-identities/registered-identities.json'
LAND = OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
STOCK_IDS = OUT/'inventory/stock-pbgid-audit-r1/report.json'
STOCK_IDS_SHA = 'd73867eb4c53ff09c6de9c9e9004c7baf02f70f586c8d442c6505106224670c1'


def invoke(label, args, timeout=180):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout)
    path = owned(EVIDENCE/(label+'.log'))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('EXIT '+str(result.returncode)+'\n'+result.stdout+'\n'+result.stderr,
                    encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{label} failed; preserved {path}')
    return path


def locked(action):
    with NATIVE_LOCK.open('r+b') as handle:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            return action()
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def prepare():
    if PROJECT.exists() or EVIDENCE.exists():
        raise FileExistsError('Preserve existing identity project and evidence')
    plan = read(PLAN)
    owned(PROJECT)
    owned(EVIDENCE).mkdir(parents=True)
    state = {'schema':'ccp-060-private-land-identity-batch/v1',
             'status':'preparing', 'plan_sha256':sha(PLAN), 'project':str(PROJECT),
             'steps':[], 'active_source_changed':False}
    receipt = EVIDENCE/'prepare.json'
    def operation():
        def step(label, args):
            log = invoke(label, args)
            state['steps'].append({'label':label,'log':str(log),'sha256':sha(log)})
            write(receipt,state)
        step('create',[CORE,'mod-project','create','--library',PROJECT.parent.parent,'--name',PROJECT.name])
        step('settings',[CORE,'mod-project','settings','--project',PROJECT,
                         '--live-reload','off','--mod-id',CFG['project_guid']])
        for row in plan['entries']:
            step('derive-'+row['derived_name'],[CORE,'mod-project','derive','--project',PROJECT,
                 '--source',row['stock_source'],'--name',row['derived_name']])
        config = read(PROJECT/'mod-project.json')
        if config.get('game_mode',{}).get('enabled') or config.get('animated_units'):
            raise ValueError('Unexpected project content')
        if len(config['derived_blueprints']) != len(plan['entries']):
            raise ValueError('Derived identity count differs')
        state.update(status='prepared_one_cook_pending', configuration_sha256=sha(PROJECT/'mod-project.json'))
        write(receipt,state)
    try:
        locked(operation)
    except BaseException as error:
        state.update(status='failed_diagnostics_preserved',error=str(error));write(receipt,state)
        raise
    return state


def cook():
    prep = read(EVIDENCE/'prepare.json')
    if prep['status'] != 'prepared_one_cook_pending' or prep['plan_sha256'] != sha(PLAN):
        raise ValueError('Prepared plan is not current')
    if sha(PROJECT/'mod-project.json') != prep['configuration_sha256']:
        raise ValueError('Native project drift')
    receipt = EVIDENCE/'cook.json'
    if receipt.exists() or read(PROJECT/'mod-project.json')['cooks']:
        raise FileExistsError('Identity cook already attempted; retain IDs and diagnostics')
    state = {'schema':'ccp-060-private-land-identity-cook/v1','status':'starting',
             'plan_sha256':sha(PLAN),'prepare_sha256':sha(EVIDENCE/'prepare.json')}
    def operation():
        write(receipt,state)
        log = invoke('native-cook',[CORE,'mod-project','cook','--project',PROJECT,
                     '--editor',CFG['art_editor'],'--timeout','1200'],timeout=1300)
        config = read(PROJECT/'mod-project.json')
        if len(config['cooks']) != 1:
            raise ValueError('Exactly one native cook required')
        archive = owned(config['cooks'][0]['archive'])
        if sha(archive) != config['cooks'][0]['sha256']:
            raise ValueError('Cooked archive hash mismatch')
        state.update(status='cooked_readback_pending',archive=str(archive),
                     archive_sha256=sha(archive),log=str(log),log_sha256=sha(log),
                     configuration_sha256=sha(PROJECT/'mod-project.json'))
        write(receipt,state)
    try:
        locked(operation)
    except BaseException as error:
        state.update(status='failed_diagnostics_preserved',error=str(error));write(receipt,state)
        raise
    return state


def readback():
    sys.path.insert(0,CFG['garrison_extension'])
    from garrison_shared import rgd
    plan = read(PLAN)
    cooked = read(EVIDENCE/'cook.json')
    target = EVIDENCE/'registered-identities.json'
    if target.exists() or cooked['status'] != 'cooked_readback_pending':
        raise ValueError('Cook not pending readback or registration already exists')
    archive = Path(cooked['archive'])
    if sha(archive) != cooked['archive_sha256']:
        raise ValueError('Cooked archive drift')
    listing = json.loads(subprocess.check_output([str(ARCH),'list','--verify',str(archive)],text=True))
    if not listing['archive']['verification']['verified']:
        raise ValueError('Cooked archive failed native verification')
    generated = [m['path'] for m in listing['members'] if m['path'].startswith('attrib/')]
    by_name = {}
    for row in plan['entries']:
        matches = [m for m in generated if m.endswith('/'+row['derived_name']+'.rgd')]
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous cooked identity '+row['derived_name'])
        by_name[row['derived_name']] = matches[0]
    if sha(STOCK_IDS) != STOCK_IDS_SHA:
        raise ValueError('Complete official stock PBG ID audit drift')
    stock_audit=read(STOCK_IDS)
    if stock_audit['member_count'] != 28059 or stock_audit['unique_pbgids'] != 27106:
        raise ValueError('Complete official stock PBG ID inventory differs')
    prior_ids = {int(x) for x in stock_audit['identities']}
    prior_ids.update(x['pbgid'] for x in read(FIRST)['entries'])
    if LAND != target and LAND.is_file():
        prior_ids.update(x['pbgid'] for x in read(LAND)['entries'])
    baseline = OUT/'baseline/final053/archive-members/attrib'
    for path in baseline.rglob('*.rgd'):
        native = rgd.read(path.read_bytes())
        for leaf, node in rgd.flatten(native.nodes):
            if node.key == 'pbgid' and type(node.value) is int:
                prior_ids.add(node.value)
    source = ROOT/'assets/attrib/instances'
    for path in source.rglob('*.xml'):
        for node in ET.parse(path).getroot().iter('uniqueid'):
            if node.attrib.get('name') == 'pbgid':
                prior_ids.add(int(node.attrib['value']))
    rows = []
    official = Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga')
    for row in plan['entries']:
        name = row['derived_name']
        native_path = owned(EVIDENCE/'readback'/(name+'.rgd'))
        stock_path = owned(EVIDENCE/'stock'/(name+'.rgd'))
        native_path.parent.mkdir(parents=True,exist_ok=True)
        stock_path.parent.mkdir(parents=True,exist_ok=True)
        if native_path.exists() or stock_path.exists():
            raise FileExistsError('Preserve readback identity material: '+name)
        subprocess.run([str(ARCH),'extract-member',str(archive),by_name[name],str(native_path)],
                       check=True,capture_output=True,text=True)
        subprocess.run([str(ARCH),'extract-member',str(official),row['stock_member'],str(stock_path)],
                       check=True,capture_output=True,text=True)
        cooked_rgd = rgd.read(native_path.read_bytes())
        original = stock_path.read_bytes()
        stock_rgd = rgd.read(original)
        if rgd.write(stock_rgd) != original:
            raise ValueError('Stock codec roundtrip differs: '+name)
        identity = rgd.find(cooked_rgd.nodes,'default/pbgid').value
        if type(identity) is not int or identity in prior_ids:
            raise ValueError('Native ID invalid or collides with first ten')
        for path,node in rgd.flatten(stock_rgd.nodes):
            if node.key == 'pbgid':
                node.value = identity
        changed = rgd.write(stock_rgd)
        restored = rgd.read(changed)
        for path,node in rgd.flatten(restored.nodes):
            if node.key == 'pbgid':
                node.value = rgd.find(rgd.read(original).nodes,path).value
        if rgd.write(restored) != original:
            raise ValueError('Original native resource cannot be cloned byte-reversibly: '+name)
        rows.append({**row,'pbgid':identity,'generated_member':by_name[name],
                     'generated_path':str(native_path),'generated_sha256':sha(native_path),
                     'stock_path':str(stock_path),'stock_sha256':sha(stock_path),
                     'identity_only_native_clone_sha256':__import__('hashlib').sha256(changed).hexdigest(),
                     'original_resource_byte_reversible_after_identity_change':True})
        prior_ids.add(identity)
    if len(rows) != len(plan['entries']):
        raise ValueError('Partial identity readback')
    data = {'schema':'ccp-060-private-land-registered-identities/v1',
            'status':'native_identities_registered_no_visual_activation',
            'plan_sha256':sha(PLAN),'archive':str(archive),'archive_sha256':sha(archive),
            'entries':rows,'stock_pbgid_audit_sha256':STOCK_IDS_SHA,
            'excluded_generated_scaffolding':sorted(set(generated)-set(by_name.values())),
            'active_source_or_final_archive_changed':False,'native_match_acceptance':False}
    write(target,data)
    return {'registered':len(rows),'receipt':str(target)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','cook','readback'))
    args=parser.parse_args()
    guard()
    print(json.dumps({'prepare':prepare,'cook':cook,'readback':readback}[args.action](),indent=2))
