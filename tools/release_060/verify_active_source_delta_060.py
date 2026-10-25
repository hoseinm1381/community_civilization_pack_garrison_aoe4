"""Verify active editable source delta plus original identities, art and normal edition."""
import argparse
import json
from pathlib import Path

from common import CFG, OUT, ROOT, files, guard, owned, read, sha, write
from pin_final053 import ABILITY, RECEIPT, verify as verify_baseline
from verify_archive_delta import compare_maps, safe_member


def historical_art_records(groups):
    return {category+'/'+relative:item for category,records in groups.items()
            for relative,item in records.items()}


def source_rows(stage,baseline):
    rows=stage.get('source_rows',stage.get('files',[]));entries=[];selection=[]
    if not rows:raise ValueError('Explicit final editable source selection required')
    for row in rows:
        relative=safe_member(row.get('relative') or row['asset_relative_path']).removeprefix('assets/')
        staged=owned(row.get('staged') or row['staged_path'])
        digest=row.get('staged_sha256')
        before=baseline.get(relative,{}).get('sha256')
        expected=row.get('active_sha256',row.get('source_sha256'))
        if before!=expected:raise ValueError('Source selection does not declare exact final053 bytes: '+relative)
        if sha(staged)!=digest:raise ValueError('Selected editable source changed: '+relative)
        if before is not None:
            if not relative.startswith(('attrib/instances/ebps/vietnam/','attrib/instances/sbps/vietnam/')):
                raise ValueError('Existing editable source outside Vietnamese actor/squad closure')
        elif not (relative.startswith('attrib/instances/') and '/vietnam/release_060/' in relative and relative.endswith('.xml')):
            raise ValueError('New editable source outside private Vietnamese namespace')
        if before==digest:raise ValueError('Unchanged editable source must not be allowlisted')
        entries.append({'member':relative,'before_sha256':before,'after_sha256':digest})
        selection.append({'relative':relative,'staged':str(staged),'sha256':digest})
    if len({r['member'].casefold() for r in entries})!=len(entries):raise ValueError('Duplicate editable source selection')
    return entries,selection


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source-stage',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();guard()
    target=owned(args.report)
    if target.exists():raise FileExistsError('Preserve previous source verification')
    frozen=verify_baseline();stage=read(owned(args.source_stage))
    entries,selection=source_rows(stage,frozen['inputs']['assets'])
    actual=files(ROOT/'assets',reject_links=True,exclude_release_060=False)
    result=compare_maps(frozen['inputs']['assets'],actual,entries,{ABILITY})
    identities={name:{'sha256':sha(ROOT/name),'bytes':(ROOT/name).stat().st_size}
                for name in frozen['inputs']['identities']}
    if identities!=frozen['inputs']['identities']:raise ValueError('Original workspace/project identities changed')
    normal=files(Path(CFG['source_root']),reject_links=True,exclude_release_060=False)
    if normal!=frozen['inputs']['normal']:raise ValueError('Preserved normal edition differs')
    historical=historical_art_records(read(OUT/'baseline/preparation-freeze.json')['inputs']['prior_art'])
    for relative,item in historical.items():
        path=ROOT/'art'/relative
        if not path.is_file() or sha(path)!=item['sha256'] or path.stat().st_size!=item['bytes']:
            raise ValueError('Earlier editable art/source changed: '+relative)
    result.update(schema='ccp-060-active-source-preservation-verification/v1',
        status='explicit_source_delta_and_preserved_normal_identities_prior_art_verified',
        baseline_freeze_sha256=sha(RECEIPT),source_stage=str(args.source_stage),
        source_stage_sha256=sha(args.source_stage),selection=selection,active_assets=actual,
        normal_file_count=len(normal),historical_art_file_count=len(historical),
        native_acceptance=False,source_only_content_editor_rebuild_recreates_final_visuals=False,
        rebuild_note='Run the separately retained final native-media overlay recipe after source compilation')
    write(target,result)
    print(json.dumps({'status':result['status'],'changed':len(result['changed']),'added':len(result['added']),
                      'normal_files_preserved':len(normal),'historical_art_files_preserved':len(historical)}))


if __name__=='__main__':main()
