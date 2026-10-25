"""Allocate and natively cook isolated identities; never activate speech suppression."""
import json
import argparse
import msvcrt
from pathlib import Path
import subprocess
import sys

from pipeline import guard,digest,save_json
from providers import ROOT,OUT


def main():
    guard()
    parser=argparse.ArgumentParser();parser.add_argument('--monk-extra',action='store_true');args=parser.parse_args()
    cfg=json.loads((ROOT/'workspace.json').read_text())
    audit_file=OUT/'inventory'/('speaker-closure-v3' if args.monk_extra else 'speaker-closure-v2')/'audit.json'
    audit=json.loads(audit_file.read_text())
    if audit['unresolved']:raise RuntimeError('Resolve recursive speaker donors first')
    consumers=json.loads((OUT/'inventory'/('consumers-complete.json' if args.monk_extra else 'consumers.json')).read_text())['rows']
    active={r['name'] for r in consumers if r['generation_admitted']}
    selected=[r for r in audit['rows'] if r['source']=='current_official' and active.intersection(r['owners'])
              and (r['nonempty_speaker_fields'] or r['speech_tables'])]
    base_file=OUT/'integration/voice-identities-v1/receipt.json';base=None
    if args.monk_extra:
        base=json.loads(base_file.read_text())
        base_audit=json.loads((base_file.parent/'identity-audit.json').read_text())
        if not base_audit['passed'] or base_audit['receipt_sha256']!=digest(base_file):raise RuntimeError('Base identity proof changed')
        existing={r['source'] for r in base['identities']}
        selected=[r for r in selected if r['member']not in existing]
        if len(selected)!=2 or any(Path(r['member']).stem!='unit_monk_3_chi' for r in selected):
            raise RuntimeError('Review changed extra monk identity scope')
    elif len(selected)!=18:raise RuntimeError('Review changed identity scope before cooking')
    label='voice-identities-monk-v1' if args.monk_extra else 'voice-identities-v1'
    work=Path(cfg['external_root'])/'staging/release_084'/label
    evidence=OUT/'integration'/label
    if work.exists() or evidence.exists():raise FileExistsError('Preserve identity attempts; do not allocate replacements')
    for row in selected:
        if digest(row['file'])!=row['sha256']:raise RuntimeError('Changed official donor')
    work.mkdir(parents=True);evidence.mkdir(parents=True)
    library=work/'library';name='cc084monkids' if args.monk_extra else 'cc084voiceids';project=library/'Mods'/name
    core=cfg['garrison_core'];archive_tool=cfg['archive_tool']
    plan=[]
    for row in selected:
        category=row['member'].split('/')[1]
        prefix={'sbps':'s','ebps':'e','attachments':'a'}[category]
        derived='vn084_'+prefix+'_'+Path(row['member']).stem
        plan.append(dict(source=row['member'],source_file=row['file'],source_sha256=row['sha256'],
                         name=derived,category=category,owners=sorted(active.intersection(row['owners']))))
    save_json(evidence/'plan.json',dict(audit_sha256=digest(audit_file),identities=plan,
              scope='Native identity preparation only; no active source, gameplay or speech binding changes.'))
    def run(label,args,timeout=180):
        result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        (evidence/(label+'.log')).write_text('EXIT '+str(result.returncode)+'\n'+result.stdout+'\n'+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('Identity step failed: '+label)
        return result.stdout
    lock=Path(cfg['external_root'])/'output/release_020/native-build.lock'
    with lock.open('r+b') as stream:
        msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        try:
            run('create',[core,'mod-project','create','--library',library,'--name',name])
            run('settings',[core,'mod-project','settings','--project',project,'--live-reload','off','--mod-id',cfg['project_guid']])
            for row in plan:
                run('derive-'+row['name'],[core,'mod-project','derive','--project',project,
                        '--source',row['source'].removeprefix('attrib/').removesuffix('.rgd'),'--name',row['name']])
            settings=json.loads((project/'mod-project.json').read_text())
            if settings['game_mode']['enabled'] or settings['game_mode']['live_reload'] or len(settings['derived_blueprints'])!=len(plan):
                raise RuntimeError('Unexpected identity project configuration')
            print('VOICE_IDENTITIES_PREPARED',len(plan),flush=True)
            run('native-cook',[core,'mod-project','cook','--project',project,'--editor',cfg['art_editor'],'--timeout','1800'],2100)
        finally:
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
    archive=project/'dist'/(name+'.sga')
    listing=json.loads(run('list-verify',[archive_tool,'list',archive,'--verify'],600))
    if not listing['archive']['verification']['verified']:raise RuntimeError('Identity SGA integrity failed')
    readback=evidence/'readback'
    run('fresh-readback',[archive_tool,'extract',archive,readback,'--filter','.'],600)
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    ids=set()
    for row in plan:
        candidates=list((readback/'attrib'/row['category']).rglob(row['name']+'.rgd'))
        if len(candidates)!=1:raise RuntimeError('Missing native identity readback '+row['name'])
        path=candidates[0];doc=rgd.read(path.read_bytes())
        identities={node.value for _,node in rgd.flatten(doc.nodes) if node.key=='pbgid'}
        if len(identities)!=1:raise RuntimeError('Ambiguous native PBGID '+row['name'])
        identity=next(iter(identities))
        if identity in ids:raise RuntimeError('Duplicate allocated identity')
        ids.add(identity)
        row.update(compiled=str(path),compiled_sha256=digest(path),pbgid=identity)
    save_json(evidence/'receipt.json',dict(schema='ccp-084-native-voice-identities/v1',
              status='Garrison-derived identity payloads after an empty native base cook; not a complete 0.8.4 compile',
              project=str(project),project_config_sha256=digest(project/'mod-project.json'),
              archive=str(archive),archive_sha256=digest(archive),archive_name=listing['archive']['name'],
              identities=plan,native_base_instances=0,derived_payloads_after_native_burn=True,
              eighteen_xml_instances_native_compiled=False,full_084_native_compilation=False,
              active_source_modified=False,native_suppression=False,
              native_game_test=False,installed=False,published=False))
    if args.monk_extra:
        extra_file=evidence/'receipt.json'
        extra=json.loads(extra_file.read_text())
        combined=OUT/'integration/voice-identities-complete.json'
        if combined.exists():raise FileExistsError('Preserve combined identity receipts')
        save_json(combined,dict(schema='ccp-084-native-voice-identities/v2',
                  status='20 Garrison-derived identity payloads; full editable-source compile pending',
                  identities=base['identities']+plan,
                  component_receipts=[dict(file=str(p),sha256=digest(p)) for p in [base_file,extra_file]],
                  archives=[dict(file=r['archive'],sha256=r['archive_sha256'],name=r['archive_name']) for r in [base,extra]],
                  native_base_instances=0,derived_payloads_after_native_burn=True,
                  full_084_native_compilation=False,active_source_modified=False,native_suppression=False))
    print('GARRISON_DERIVED_IDENTITIES_READBACK',len(plan),flush=True)


if __name__=='__main__':
    from exclusive_job import exclusive_job
    guard()
    with exclusive_job('native identity cook'):main()
