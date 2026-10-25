"""One supported native cook for many isolated exact-donor material variants.

Input jobs retain individual donor/image hashes. Each result is independently
read back with the existing strict verifier and an exact private-folder selector.
Only the caller with the native scheduler grant may run this command.
"""
import argparse
import json
import msvcrt
from pathlib import Path
import re
import shutil
import subprocess
from common import CFG, CORE, NATIVE_LOCK, OUT, STAGING, TOOLS, guard, owned, read, sha, write


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true',help='Validate and pin inputs without any native operation')
    args=parser.parse_args();guard();plan=read(owned(args.plan))
    if plan.get('schema')!='ccp-060-bulk-material-plan/v1':raise ValueError('Plan schema')
    key=plan['project_key']
    if not re.fullmatch(r'v60[a-z0-9]{1,8}',key):raise ValueError('Short private project key required')
    jobs=plan['jobs']
    if not jobs or len({j['key'].casefold() for j in jobs})!=len(jobs):raise ValueError('Empty/duplicate jobs')
    for job in jobs:
        if not re.fullmatch(r'[a-z][a-z0-9]{1,11}',job['key']):raise ValueError('Unsafe private variant key')
        if job['slot'] not in ('albedoTexture','albedoTex'):raise ValueError('Exact native albedo slot required')
        donor=read(owned(job['donor_manifest']))
        if sha(job['donor_manifest'])!=job['donor_manifest_sha256']:
            raise ValueError('Exact donor manifest drift')
        if donor['resources']['model']['logical_path']!=job['model']:
            raise ValueError('Native variant is not the pinned donor model')
        if sha(owned(job['albedo']))!=job['albedo_sha256']:raise ValueError('Saved native albedo drift')
    folder=owned(OUT/'qualification/bulk-materials'/key)
    pinned=folder/'plan.json'
    if pinned.exists():
        if read(pinned)!=plan:raise ValueError('Bulk native plan changed')
    else:write(pinned,plan)
    if args.prepare_only:
        print(json.dumps({'status':'inputs_pinned_no_native_operation','jobs':len(jobs),'plan':str(pinned)}));return
    library=owned(STAGING/'b');project=owned(library/'Mods'/key)
    if project.exists() or (folder/'cook.json').exists():
        raise FileExistsError('Preserve existing batch project/cook; use retained result or a fresh labeled attempt')
    record={'schema':'ccp-060-bulk-native-material-cook/v1','status':'prepared',
            'plan':str(pinned),'plan_sha256':sha(pinned),'project':str(project),'steps':[]}
    receipt=folder/'cook.json';write(receipt,record)
    def run(label,command,timeout=300):
        result=subprocess.run(list(map(str,command)),capture_output=True,text=True,
                              encoding='utf-8',errors='replace',timeout=timeout)
        log=owned(folder/(label+'.log'))
        log.write_text('COMMAND '+subprocess.list2cmdline(list(map(str,command)))+
                       '\nEXIT '+str(result.returncode)+'\n'+result.stdout+'\n'+result.stderr,encoding='utf-8')
        record['steps'].append({'label':label,'exit_code':result.returncode,'log':str(log),'sha256':sha(log)})
        write(receipt,record)
        if result.returncode:raise RuntimeError('Native material batch failed: '+str(log))
        return result.stdout
    with NATIVE_LOCK.open('r+b') as lock:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try:
            run('create',[CORE,'mod-project','create','--library',library,'--name',key])
            run('settings',[CORE,'mod-project','settings','--project',project,'--live-reload','off'])
            for job in jobs:
                image=owned(library/(key+'_'+job['key']+'.png'))
                if image.exists():raise FileExistsError('Preserve staged native image: '+str(image))
                shutil.copy2(job['albedo'],image)
                if sha(image)!=job['albedo_sha256']:raise ValueError('Short native image copy drift')
                run(job['key']+'-variant',[CORE,'mod-project','variant','--project',project,
                    '--source',job['model'].removesuffix('.rgm'),'--name',job['key']])
                run(job['key']+'-image',[CORE,'mod-project','variant-set','--project',project,
                    '--name',job['key'],'--slot',job['slot'],'--image',image])
            config=read(project/'mod-project.json')
            if config['game_mode'].get('enabled') or config.get('animated_units') or len(config['model_variants'])!=len(jobs):
                raise ValueError('Unexpected gameplay/variant content')
            run('cook',[CORE,'mod-project','cook','--project',project,'--editor',CFG['art_editor'],
                '--timeout','1800'],1900)
            config=read(project/'mod-project.json')
            if len(config['cooks'])!=1:raise ValueError('One fresh batch cook required')
            cook=config['cooks'][0];archive=owned(cook['archive'])
            if sha(archive)!=cook['sha256'] or len(cook['model_variants'])!=len(jobs):
                raise ValueError('Fresh batch output/variant inventory differs')
            actual={v['name']:v['source'].replace('\\','/').removesuffix('.rgm') for v in cook['model_variants']}
            expected={j['key']:j['model'].removesuffix('.rgm') for j in jobs}
            if actual!=expected:raise ValueError('Native cooked variant source differs from exact selected donor')
            for job in jobs:
                if sha(job['albedo'])!=job['albedo_sha256'] or sha(job['donor_manifest'])!=job['donor_manifest_sha256']:
                    raise ValueError('Pinned native input changed during batch cook')
                if sha(library/(key+'_'+job['key']+'.png'))!=job['albedo_sha256']:
                    raise ValueError('Staged native image changed during batch cook')
            listing=json.loads(run('archive-verify',[CFG['archive_tool'],'list',archive,'--verify']))
            if not listing['archive']['verification']['verified']:raise ValueError('Native archive verification failed')
            record.update(status='fresh_bulk_cook_verified_readbacks_pending',archive=str(archive),archive_sha256=sha(archive))
            write(receipt,record)
        except BaseException as error:
            record.update(status='failed_diagnostics_preserved',error=repr(error));write(receipt,record);raise
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    # Native editor has exited; retain scheduler until this process finishes its readbacks.
    native_receipt=folder/'native-cook.json'
    write(native_receipt,record)
    by_name={v['name']:v for v in cook['model_variants']};reports={}
    for job in jobs:
        variant=by_name[job['key']];prefix=variant['art'].replace('\\','/').rsplit('/',1)[0]+'/'
        sub=owned(folder/'variants'/job['key']);subreceipt=sub/'cook.json'
        write(subreceipt,{'schema':'ccp-060-albedo-only-variant/v1',
            'status':'cooked_archive_verified_material_readback_pending',
            'archive':str(archive),'archive_sha256':sha(archive),'batch_cook_receipt':str(native_receipt),
            'batch_cook_receipt_sha256':sha(native_receipt),'batch_variant_name':job['key'],
            'source_model':job['model'].removesuffix('.rgm'),'source_image':job['albedo'],
            'source_image_sha256':job['albedo_sha256'],'only_overridden_slot':job['slot'],
            'one_shared_native_cook':True})
        run(job['key']+'-verify',['py','-3.13','-B',TOOLS/'verify_unit_albedo_variant.py',
            '--cook',subreceipt,'--donor',job['donor_manifest'],'--private-prefix',prefix])
        report=sub/'material-verification.json';reports[job['key']]={'path':str(report),'sha256':sha(report)}
        print('QUALIFIED '+job['key'],flush=True)
    record.update(status='all_bulk_variants_independently_readback_qualified',reports=reports)
    write(receipt,record)
    print(json.dumps({'status':record['status'],'jobs':len(jobs),'receipt':str(receipt)}))


if __name__=='__main__':main()
