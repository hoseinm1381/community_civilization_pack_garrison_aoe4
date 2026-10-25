"""Compile staged editable identities; preserve the 083 owning archive for release."""
import json
import msvcrt
from pathlib import Path
import re
import subprocess
import sys
from pipeline import guard,digest,save_json
from providers import ROOT,OUT
from exclusive_job import exclusive_job


def main():
    guard();cfg=json.loads((ROOT/'workspace.json').read_text())
    newer=OUT/'integration/source-draft-v2.json'
    revision='v2' if newer.exists() else 'v1'
    source_receipt=newer if newer.exists() else OUT/'integration/source-draft-v1.json'
    draft=json.loads(source_receipt.read_text())
    source=Path(draft['root']);project=Path(draft['project'])
    if digest(project)!=draft['project_sha256']:raise RuntimeError('Staged project changed')
    for row in draft['added']:
        if digest(row['path'])!=row['sha256']:raise RuntimeError('Staged identity source changed')
    baseline=json.loads((OUT/'baseline.json').read_text())
    assets=ROOT/'assets'
    for path,sha in baseline['protected'].items():
        p=Path(path)
        if p.is_relative_to(assets):
            if digest(p)!=sha or digest(source/'assets'/p.relative_to(assets))!=sha:
                raise RuntimeError('Baseline source changed')
    prefix='source-draft-v2' if revision=='v2' else 'source-draft'
    inheritance=json.loads((OUT/'integration'/(prefix+'-inheritance.json')).read_text())
    tuning=json.loads((OUT/'integration'/(prefix+'-tuning.json')).read_text())
    if inheritance['errors'] or tuning['summary']['errors']:raise RuntimeError('Source preflight failed')
    sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
    check(ROOT,baseline['sga'])
    work=Path(cfg['external_root'])/'staging/release_084'/('native-reference-'+revision)
    evidence=OUT/'integration'/('native-reference-'+revision)
    if work.exists() or evidence.exists():raise FileExistsError('Preserve native compile attempts')
    work.mkdir(parents=True);evidence.mkdir(parents=True)
    build=work/'build';logs=work/'logs'
    command=[cfg['content_editor'],'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report',
             '--no_source_control','--log_path',str(logs),'--build_mod',str(project),'--build_path',str(build),
             '--no_burn_window','--burn_cache_type','Local','--burn_max_threads','1','--burn_platform','PC',
             '--burn_log_path',str(work/'burn.log'),'--intermediate_path',str(work/'intermediate')]
    save_json(evidence/'input-freeze.json',dict(command=command,source_receipt_sha256=digest(source_receipt),
              staged_files={str(p):digest(p) for p in source.rglob('*') if p.is_file()},
              baseline_archive_sha256=baseline['sga_sha256']))
    lock=Path(cfg['external_root'])/'output/release_020/native-build.lock'
    with lock.open('r+b') as stream:
        msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        try:
            process=subprocess.run(command,cwd=Path(cfg['content_editor']).parent,capture_output=True,
                       text=True,encoding='utf-8',errors='replace',timeout=1800)
        finally:
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
    log=process.stdout+'\n'+process.stderr
    (evidence/'content-editor.log').write_text('EXIT '+str(process.returncode)+'\n'+log,encoding='utf-8')
    expected=len(list((source/'assets/attrib/instances').rglob('*.xml')))
    counts=re.findall(r'(\d+) instances validated',log)
    errors=[line for line in log.splitlines() if 'EssenceEditor.exe Error:' in line]
    if process.returncode or errors or not counts or int(counts[-1])!=expected:
        raise RuntimeError('Native compile failed or did not validate all staged instances; diagnostics retained')
    archives=list(build.rglob('*.sga'))
    if len(archives)!=1 or 'copied to' not in log:raise RuntimeError('No completed native archive copy')
    archive=archives[0];check(ROOT,archive)
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    readback=evidence/'readback';members={}
    for row in draft['added']:
        relative=Path(row['path']).relative_to(source/'assets/attrib/instances').with_suffix('.rgd')
        member='attrib/'+relative.as_posix();target=readback/member;target.parent.mkdir(parents=True,exist_ok=True)
        proc=subprocess.run([cfg['archive_tool'],'extract-member',str(archive),member,str(target)],capture_output=True,text=True)
        if proc.returncode:raise RuntimeError('Native identity readback failed '+member)
        actual_ids={n.value for _,n in rgd.flatten(rgd.read(target.read_bytes()).nodes) if n.key=='pbgid'}
        if actual_ids!={row['pbgid']}:raise RuntimeError('Compiled PBGID differs from staged identity '+member)
        members[member]=dict(file=str(target),sha256=digest(target),pbgid=row['pbgid'])
    save_json(evidence/'receipt.json',dict(schema='ccp-084-native-editable-identity-reference/v1',
              native_validated_instances=expected,new_identity_instances=len(members),
              archive=str(archive),archive_sha256=digest(archive),archive_identity=cfg['project_guid'].replace('-',''),
              readback=members,source_receipt_sha256=digest(source_receipt),
              native_source_identity_compile=True,complete_voice_integration_compile=False,
              final_release_archive=False,installed=False,published=False,
              note='Reference compilation only. Final assembly must retain all compiled-only 083 owning resources.'))
    print('NATIVE_EDITABLE_IDENTITY_REFERENCE_COMPILED',expected,'instances;',len(members),'new identity readbacks',flush=True)


if __name__=='__main__':
    guard()
    with exclusive_job('native source reference compile'):main()
