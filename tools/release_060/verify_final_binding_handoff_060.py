"""Verify complete staged 0.6.0 bindings against original native bytes."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import CFG, OUT, RECIPES, ROOT, guard, owned, read, sha, write

sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd

STAGE = OUT/'integration/final-binding-source-complete-r2/stage.json'
REGISTRY = OUT/'integration/qualified-media-selection-r1.json'
FIRST = OUT/'integration/private-foot-identities/registered-identities.json'
LAND = OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
EQUIP = OUT/'integration/private-equipment-identities/native-batch-v1/registered-identities.json'
TUGH = OUT/'integration/worker-elephant-owner-stage-r2/stage.json'
PRODUCERS = OUT/'integration/private-land-graph/compiled-only-producer-replay-v1.json'
TARGET = OUT/'integration/final-binding-handoff-v2.json'
SCHEMA = 'ccp-060-final-private-binding-handoff/v2'
SOURCE_APPLIED = False


def raw_stock_sources():
    result={}
    foot_plan={x['slug']:x for x in read(RECIPES/'foot-body-private-binding-plan.json')['entries']}
    first=read(FIRST)
    for row in first['entries']:
        plan=foot_plan[row['slug']]
        source=Path(plan['stock_slots'][0]['raw_archive_member_path'])
        member='attrib/'+row['final_private_reference']+'.rgd'
        if sha(source)!=row['stock_sha256']:
            raise ValueError('First-ten stock native bytes drift '+member)
        result[member]={'source':source,'sha256':row['stock_sha256'],'pbgid':row['pbgid']}
    for receipt in (LAND,EQUIP):
        for row in read(receipt)['entries']:
            member=row['private_member']
            if member in result:
                raise ValueError('Private resource collision '+member)
            source=Path(row['stock_path'])
            if sha(source)!=row['stock_sha256']:
                raise ValueError('Registered stock native bytes drift '+member)
            result[member]={'source':source,'sha256':row['stock_sha256'],'pbgid':row['pbgid']}
    worker=read(TUGH)
    member=worker['actor2_only_private_list']
    original=Path(OUT/'integration/worker-elephant-owner-stage-r2/stock'/
                  'attrib/attachments/attachment_lists/civilizations/sultanate_ha_tug/units/tier2_worker_elephant_sul_ha_tug.rgd')
    if sha(original)!=worker['installed_tugh_list_sha256']:
        raise ValueError('Original Tugh donor bytes drift')
    result[member]={**result[member],'source':original,'sha256':sha(original),
                    'authorized_donor_rebase':'original_native_tugh_worker_owner'}
    return result


def inverse_native(original,final,member,identity=None,known_models=None,private_ids=None):
    a,b=rgd.read(original),rgd.read(final)
    if rgd.write(a)!=original or rgd.write(b)!=final:
        raise ValueError('RGD codec roundtrip differs '+member)
    old={p:(n.kind,n.value) for p,n in rgd.flatten(a.nodes) if not n.kind.startswith('List')}
    new={p:(n.kind,n.value) for p,n in rgd.flatten(b.nodes) if not n.kind.startswith('List')}
    if old.keys()!=new.keys():
        raise ValueError('Native node topology changed '+member)
    edits=[]
    for path,(kind,value) in old.items():
        if new[path]==(kind,value):
            continue
        after=new[path][1]
        if new[path][0]!=kind:
            raise ValueError('Native field type changed '+member+' '+path)
        if path.endswith('/pbgid'):
            if identity is None or after!=identity:
                raise ValueError('Unregistered identity change '+member+' '+path)
        elif path.endswith('/$PBGNAME'):
            if '/parent_pbg/' in path or after not in private_ids:
                raise ValueError('Unapproved native reference '+member+' '+path)
        elif (path.endswith('/parent_animator') or path.endswith('/animator')
              or '/meshes/animator' in path or path.endswith('/alternate_sua')):
            if not isinstance(after,str) or after not in known_models:
                raise ValueError('Unqualified visual model '+member+' '+path+' '+str(after))
        else:
            raise ValueError('Nonvisual native field changed '+member+' '+path)
        edits.append({'path':path,'before':value,'after':after})
        rgd.find(b.nodes,path).value=value
    if not edits or rgd.write(b)!=original:
        raise ValueError('Final native bytes cannot be inverted to original '+member)
    return edits


def main():
    guard()
    if TARGET.exists():
        raise FileExistsError('Preserve existing binding handoff receipt')
    stage,registry=read(STAGE),read(REGISTRY)
    freeze=read(OUT/'baseline/final053/freeze.json')
    if stage['baseline_sga_sha256']!=freeze['sga_sha256']:
        raise ValueError('Final stage belongs to another frozen archive')
    if read(PRODUCERS)['producer_edge_count']!=3:
        raise ValueError('Compiled-only producer replay absent')
    known_models={row['private_model'].removesuffix('.rgm').replace('/','\\')
                  for row in registry['models'].values()}
    expected_art={p['member']:p['sha256'] for row in registry['models'].values()
                  for p in row['payloads']}
    if len(expected_art)!=registry['unique_payload_count']:
        raise ValueError('Unified media registry member collision')
    actual_art={row['member']:row['sha256'] for row in stage['payloads']
                if row['member'].startswith('art/')}
    if actual_art!=expected_art:
        raise ValueError('Final media payload map differs from unified qualified selection')
    donors=raw_stock_sources()
    ids={x['pbgid'] for x in donors.values()}
    if len(ids)!=80 or len(donors)!=80:
        raise ValueError('Expected 80 unique private land/equipment identities')
    guid=CFG['project_guid'].replace('-','')
    private_refs={guid+':'+Path(member).stem for member in donors}
    private_rows=[];existing_rows=[]
    seen=set()
    for row in stage['payloads']:
        member=row['member']
        if member in seen:
            raise ValueError('Duplicate final member '+member)
        seen.add(member)
        path=Path(row['path'])
        if sha(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:
            raise ValueError('Final staged payload drift '+member)
        baseline=freeze['archive_members'].get(member)
        if row['before_sha256']!=(baseline['sha256'] if baseline else None):
            raise ValueError('Final baseline before hash differs '+member)
        if not member.startswith('attrib/'):
            continue
        if member in donors:
            donor=donors[member]
            edits=inverse_native(donor['source'].read_bytes(),path.read_bytes(),member,
                                 donor['pbgid'],known_models,private_refs)
            private_rows.append({'member':member,'donor_sha256':donor['sha256'],
                                 'final_sha256':row['sha256'],'changed_leaves':len(edits),
                                 'original_native_inverse_bytes':True,
                                 **({'authorized_donor_rebase':donor['authorized_donor_rebase']}
                                    if 'authorized_donor_rebase' in donor else {})})
        elif baseline:
            if not member.startswith(('attrib/ebps/vietnam/','attrib/sbps/vietnam/')):
                raise ValueError('Existing non-Vietnamese resource changed '+member)
            original=OUT/'baseline/final053/archive-members'/member
            if sha(original)!=baseline['sha256']:
                raise ValueError('Frozen source member drift '+member)
            edits=inverse_native(original.read_bytes(),path.read_bytes(),member,None,
                                 known_models,private_refs)
            existing_rows.append({'member':member,'baseline_sha256':baseline['sha256'],
                                  'final_sha256':row['sha256'],'changed_leaves':len(edits),
                                  'frozen_native_inverse_bytes':True})
        else:
            raise ValueError('Unknown new native resource '+member)
    if len(private_rows)!=80 or len(existing_rows)!=62 or len(actual_art)!=305:
        raise ValueError('Final member cardinality differs')
    source_rows=stage['source_rows']
    if len(source_rows)!=140:
        raise ValueError('Final source closure count differs')
    source_receipts=[]
    for row in source_rows:
        relative=row['relative']
        staged=Path(row['staged_path'])
        if sha(staged)!=row['staged_sha256']:
            raise ValueError('Final staged XML drift '+relative)
        ET.fromstring(staged.read_bytes())
        active=ROOT/relative
        if SOURCE_APPLIED:
            if sha(active)!=row['staged_sha256']:
                raise ValueError('Applied active source differs from staged XML '+relative)
        elif row['source_sha256'] is None:
            if active.exists():
                raise ValueError('New private source already active '+relative)
        elif sha(active)!=row['source_sha256']:
            raise ValueError('Active original XML drift '+relative)
        source_receipts.append({'relative':relative,'before_sha256':row['source_sha256'],
                                'after_sha256':row['staged_sha256']})
    if sum(row['source_sha256'] is None for row in source_rows)!=80:
        raise ValueError('Private source identity count differs')
    data={'schema':SCHEMA,
          'status':'offline_source_compiled_media_allowlist_and_native_inverse_verified',
          'baseline_sga_sha256':freeze['sga_sha256'],'baseline_freeze_sha256':sha(OUT/'baseline/final053/freeze.json'),
          'stage':str(STAGE),'stage_sha256':sha(STAGE),'media_selection_sha256':sha(REGISTRY),
          'producer_replay_sha256':sha(PRODUCERS),'payload_count':len(stage['payloads']),
          'qualified_art_count':len(actual_art),'new_private_rgd_count':len(private_rows),
          'changed_vietnamese_rgd_count':len(existing_rows),'source_row_count':len(source_rows),
          'private_native_inverse_receipts':private_rows,
          'existing_native_inverse_receipts':existing_rows,
          'source_receipts':source_receipts,
          'payloads':stage['payloads'],'source_rows':source_rows,
          'full_baseline_to_aggregate_changed_member_allowlist':stage['full_baseline_to_aggregate_changed_member_allowlist'],
          'active_source_or_final_archive_changed':SOURCE_APPLIED,
          'rebuild_policy':'After Content Editor source build, replay pinned original-native compiled payload and qualified media; source-only build does not recreate final visual bytes.',
          'native_match_acceptance':False}
    write(owned(TARGET),data)
    print(json.dumps({'handoff':str(TARGET),'payloads':len(stage['payloads']),
                      'source_rows':len(source_rows),'private_rgd':len(private_rows),
                      'changed_vietnamese_rgd':len(existing_rows),'art':len(actual_art)},indent=2))


if __name__=='__main__':main()
