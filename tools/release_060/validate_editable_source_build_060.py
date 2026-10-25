"""Isolated source-name/schema build; final visuals still use exact native overlay."""
import argparse
import json
import msvcrt
from pathlib import Path
import re
import shutil
import subprocess

from common import ARCH, CFG, CORE, NATIVE_LOCK, OUT, STAGING, copy_manifest, files, guard, owned, read, sha, write
from pin_final053 import PIN, verify as verify_baseline
from verify_active_source_delta_060 import source_rows


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--handoff',type=Path,required=True)
    ap.add_argument('--label',required=True);args=ap.parse_args();guard()
    if not re.fullmatch('[a-z0-9]{1,8}',args.label):raise ValueError('Short isolated source-build label required')
    handoff=read(owned(args.handoff));frozen=verify_baseline()
    if handoff['baseline_sga_sha256']!=frozen['sga_sha256']:raise ValueError('Different source basis')
    _,selection=source_rows(handoff,frozen['inputs']['assets'])
    folder=owned(OUT/'qualification/editable-source-build'/args.label)
    source=owned(STAGING/'s'/args.label/'src');run_root=owned(STAGING/'s'/args.label/'run')
    if folder.exists() or source.exists() or run_root.exists():raise FileExistsError('Preserve previous source-build attempt')
    copy_manifest(PIN/'source/assets',source/'assets',frozen['inputs']['assets'])
    for row in selection:
        target=owned(source/'assets'/row['relative']);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(row['staged'],target)
        if sha(target)!=row['sha256']:raise ValueError('Source snapshot overlay changed')
    project=source/CFG['project_file'];shutil.copy2(PIN/'source/identity'/CFG['project_file'],project)
    expected=files(source/'assets',reject_links=True,exclude_release_060=False)
    expected_project=sha(project);expected_instances=sum(name.startswith('attrib/instances/') and name.endswith('.xml') for name in expected)
    write(folder/'source-inputs.json',{'assets':expected,'project_sha256':expected_project,
        'handoff':str(args.handoff),'handoff_sha256':sha(args.handoff),'staged_source_rows':len(selection)})
    command=[str(CORE),'essence','build-mod','--editor',CFG['content_editor'],'--mod',str(project),
             '--run-root',str(run_root),'--timeout','900']
    write(folder/'runner.json',{'command':command,'source':str(source),'run_root':str(run_root),
          'scope':'source target-name/schema validation only; this output is not the final060 archive'})
    with NATIVE_LOCK.open('r+b') as lock:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try:
            result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=960)
            (folder/'command.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    state_path=run_root/'run.json';state=read(state_path) if state_path.exists() else {}
    log=result.stdout+'\n'+result.stderr
    for path in (run_root/'logs').glob('*'):
        if path.is_file() and path.suffix.lower() in ('.log','.txt'):
            log+='\n'+path.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace')
    (folder/'application-logs.txt').write_text(log,encoding='utf-8')
    errors=[line for line in log.splitlines() if 'EssenceEditor.exe Error:' in line or 'System does not support' in line]
    validated=re.findall(r'(\d+) instances validated',log)
    input_unchanged=(files(source/'assets',reject_links=True,exclude_release_060=False)==expected and sha(project)==expected_project)
    archives=list((run_root/'output').rglob('*.sga'))
    passed=(result.returncode==0 and state.get('status')=='succeeded' and state.get('exit_code')==0
            and not errors and validated and int(validated[-1])==expected_instances and input_unchanged and len(archives)==1)
    receipt={'schema':'ccp-060-editable-source-build-validation/v1','status':'source_build_failed_diagnostics_preserved',
        'exit_code':result.returncode,'native_run':state,'source_inputs_sha256':sha(folder/'source-inputs.json'),
        'expected_instances':expected_instances,'validated_counts':validated,'errors':errors,
        'source_inputs_unchanged':input_unchanged,'active_source_changed':False,
        'final_visual_archive_from_this_compile':False,'post_build_exact_native_overlay_required':True,
        'native_match_acceptance':False}
    if passed:
        archive=archives[0]
        verify=subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,timeout=120)
        listing=json.loads(verify.stdout) if verify.returncode==0 else {}
        passed=bool(listing.get('archive',{}).get('verification',{}).get('verified'))
        if passed:
            receipt.update(status='editable_source_names_and_schemas_native_build_verified',archive=str(archive),
                archive_sha256=sha(archive),archive_members=len(listing['members']),
                archive_verification=listing['archive']['verification'])
    write(folder/'receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'expected_instances':expected_instances,'validated_counts':validated,
                      'receipt':str(folder/'receipt.json')}))
    if not passed:raise RuntimeError('Editable-source validation failed; preserve diagnostics and repair deliberately')


if __name__=='__main__':main()
