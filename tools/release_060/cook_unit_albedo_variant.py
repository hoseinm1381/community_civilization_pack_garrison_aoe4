"""Fresh, isolated supported albedo-only stock variant; no actor integration.

All native mutations use the existing shared byte lock. Supply a saved shared
albedo PNG and its expected hash; previews and player colors must not be baked.
Earlier probes are never resumed or overwritten by this runner.
"""
import argparse
import json
import msvcrt
from pathlib import Path
import re
import shutil
import subprocess

from common import CFG, CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key',required=True)
    parser.add_argument('--model',required=True)
    parser.add_argument('--albedo',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--slot',choices=('albedoTexture','albedoTex'),default='albedoTexture')
    args=parser.parse_args()
    guard()
    if not re.fullmatch(r'v60[a-z0-9]{1,8}',args.key):
        raise ValueError('Use a short, fresh private v60 project key')
    model=args.model.replace('\\','/').removesuffix('.rgm')
    if not model.startswith('art/') or any(p in ('','..','.') for p in model.split('/')) or ':' in model:
        raise ValueError('Expected a stock art model logical path')
    image=owned(args.albedo)
    if image.suffix.lower()!='.png' or sha(image)!=args.sha256:
        raise ValueError('Shared albedo PNG/hash mismatch')
    library=owned(STAGING/'m')
    project=owned(library/'Mods'/args.key)
    output=owned(OUT/'qualification/albedo-variants'/args.key)
    image_copy=owned(library/(args.key+'.png'))
    if project.exists() or output.exists() or image_copy.exists():
        raise FileExistsError('Preserve earlier variant project/evidence; use a fresh key')
    output.mkdir(parents=True)
    # A short owned input path avoids the known long-path native texture route.
    library.mkdir(parents=True,exist_ok=True)
    shutil.copy2(image,image_copy)
    record={'schema':'ccp-060-albedo-only-variant/v1','status':'prepared',
            'project':str(project),'source_model':model,
            'source_image':str(image),'source_image_sha256':args.sha256,
            'staged_image':str(image_copy),'staged_image_sha256':sha(image_copy),
            'only_overridden_slot':args.slot,'steps':[],
            'limits':'Cook/readback only. No consumer binding, import, appearance, gameplay or multiplayer acceptance.'}
    receipt=output/'cook.json'
    write(receipt,record)

    def run(label,argv,timeout=300):
        result=subprocess.run(list(map(str,argv)),capture_output=True,text=True,
                              encoding='utf-8',errors='replace',timeout=timeout)
        log=owned(output/(label+'.log'))
        log.write_text('COMMAND: '+subprocess.list2cmdline(list(map(str,argv)))+
                       '\nEXIT: '+str(result.returncode)+'\nSTDOUT:\n'+result.stdout+
                       '\nSTDERR:\n'+result.stderr,encoding='utf-8')
        record['steps'].append({'label':label,'exit_code':result.returncode,
                                'log':str(log),'log_sha256':sha(log)})
        write(receipt,record)
        if result.returncode:
            raise RuntimeError(f'{label} failed; preserved {log}')
        return result

    with NATIVE_LOCK.open('r+b') as lock:
        try:
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            record['status']='lock_busy_no_native_mutation'
            write(receipt,record)
            raise
        try:
            run('create',[CORE,'mod-project','create','--library',library,'--name',args.key])
            run('settings',[CORE,'mod-project','settings','--project',project,'--live-reload','off'])
            run('variant',[CORE,'mod-project','variant','--project',project,'--source',model,'--name','body'])
            run('albedo',[CORE,'mod-project','variant-set','--project',project,'--name','body',
                          '--slot',args.slot,'--image',image_copy])
            source=read(project/'mod-project.json')
            if source.get('game_mode',{}).get('enabled') or source.get('runtime_modules',{}).get('files'):
                raise RuntimeError('Unexpected gameplay content in isolated art project')
            run('cook',[CORE,'mod-project','cook','--project',project,'--editor',CFG['art_editor'],
                        '--timeout','1200'],1300)
            cooked=read(project/'mod-project.json')
            if len(cooked.get('cooks',[]))!=1:
                raise RuntimeError('Expected exactly one fresh cook')
            cook=cooked['cooks'][0]
            archive=owned(Path(cook['archive']))
            if sha(archive)!=cook['sha256'] or sha(image)!=args.sha256:
                raise RuntimeError('Fresh archive or input changed')
            listing=run('archive-verify',[CFG['archive_tool'],'list','--verify',archive])
            verification=json.loads(listing.stdout)['archive']['verification']
            if not verification['verified'] or verification['crc_mismatches'] or verification['sha1_mismatches']:
                raise RuntimeError('Archive stored-byte verification failed')
            record.update(status='cooked_archive_verified_material_readback_pending',
                          archive=str(archive),archive_sha256=sha(archive),
                          archive_verification=verification)
            write(receipt,record)
        except BaseException as error:
            record.update(status='failed_diagnostics_preserved',error=f'{type(error).__name__}: {error}')
            write(receipt,record)
            raise
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    print(json.dumps({'status':record['status'],'receipt':str(receipt)}))


if __name__=='__main__':
    main()
