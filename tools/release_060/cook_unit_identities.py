"""Allocate native private body attachment identities; no art/gameplay activation."""
import json
import msvcrt
import subprocess
from common import ARCH, CFG, CORE, NATIVE_LOCK, guard, owned, read, sha, write
from unit_binding_plan import EVIDENCE, PROJECT, PLAN, prepare_plan


def main():
    guard();prepare_plan()
    prep=read(EVIDENCE/'prepare.json')
    if prep['status']!='identities_prepared_native_cook_pending':
        raise ValueError('Successful private identity preparation required')
    if sha(PROJECT/'mod-project.json')!=prep['configuration_sha256']:
        raise ValueError('Private identity configuration drift')
    receipt=EVIDENCE/'cook.json'
    if receipt.exists() or read(PROJECT/'mod-project.json')['cooks']:
        raise FileExistsError('Identity cook already attempted; preserve IDs and diagnostics')
    result={'schema':'ccp-060-private-body-identity-cook/v1','status':'starting',
            'plan_sha256':sha(PLAN),'preparation_sha256':sha(EVIDENCE/'prepare.json'),
            'project':str(PROJECT),'native_acceptance':False}
    with NATIVE_LOCK.open('r+b') as lock:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try:
            write(receipt,result)
            run=subprocess.run([str(CORE),'mod-project','cook','--project',str(PROJECT),
                                '--editor',CFG['art_editor'],'--timeout','1200'],
                               capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1300)
            log=EVIDENCE/'native-cook.log'
            log.write_text('EXIT '+str(run.returncode)+'\n'+run.stdout+'\n'+run.stderr,encoding='utf-8')
            result.update(exit_code=run.returncode,log=str(log),log_sha256=sha(log))
            if run.returncode:raise RuntimeError('Native identity cook failed; see preserved log')
            config=read(PROJECT/'mod-project.json')
            if len(config['cooks'])!=1:raise ValueError('One fresh native identity cook required')
            cook=config['cooks'][0];archive=owned(cook['archive'])
            if sha(archive)!=cook['sha256']:raise ValueError('Native archive hash mismatch')
            listed=subprocess.run([str(ARCH),'list','--verify',str(archive)],
                                  capture_output=True,text=True,check=True,timeout=120)
            listing=json.loads(listed.stdout)
            if not listing['archive']['verification']['verified']:raise ValueError('Archive verification failed')
            expected={f'attrib/attachments/attachment_lists/garrison/v60ids/{r["derived_name"]}.rgd'
                      for r in read(PLAN)['entries']}
            actual={m['path'] for m in listing['members'] if m['path'].startswith('attrib/')}
            if actual!=expected|{'attrib/v60ids.rgd'}:
                raise ValueError('Native private attachment member set differs')
            result.update(status='fresh_private_identities_cooked_readback_pending',
                          archive=str(archive),archive_sha256=sha(archive),
                          private_attachment_members=sorted(expected),
                          configuration_sha256=sha(PROJECT/'mod-project.json'))
            write(receipt,result)
        except BaseException as error:
            result.update(status='failed_diagnostics_preserved',error=str(error));write(receipt,result)
            raise
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
