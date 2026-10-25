"""Stage private weapon identities and Vietnam-only selector edges, offline."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from common import CFG, OUT, ROOT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd
from prepare_foot_source_delta import transform

sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd

PLAN = OUT/'integration/private-equipment-graph/derive-plan-v1.json'
EDGES = OUT/'integration/private-equipment-graph/compiled-edges-v1.json'
IDS = OUT/'integration/private-equipment-identities/native-batch-v1/registered-identities.json'
UPSTREAM = OUT/'integration/private-inherited-graph-stage-r1/stage.json'
DEST = OUT/'integration/private-equipment-stage-r1'
GUID = CFG['project_guid'].replace('-', '')


def main():
    guard()
    if DEST.exists():
        raise FileExistsError('Preserve existing equipment stage')
    plan, edge_plan, ids, upstream = read(PLAN), read(EDGES), read(IDS), read(UPSTREAM)
    if ids['plan_sha256'] != sha(PLAN) or edge_plan['derive_plan_sha256'] != sha(PLAN):
        raise ValueError('Equipment identities and edges belong to another plan')
    if edge_plan['upstream_stage_sha256'] != sha(UPSTREAM):
        raise ValueError('Upstream graph changed after equipment edge pin')
    by_member = {x['private_member']:x for x in ids['entries']}
    if set(by_member) != {x['private_member'] for x in plan['entries']}:
        raise ValueError('Registered equipment identity set differs')
    prior = {x['member']:x for x in upstream['payloads']}
    if len(prior) != len(upstream['payloads']):
        raise ValueError('Upstream payload collision')
    freeze = read(OUT/'baseline/final053/freeze.json')
    new_rows = []
    for identity in ids['entries']:
        raw_path = Path(identity['stock_path'])
        if sha(raw_path) != identity['stock_sha256']:
            raise ValueError('Stock equipment RGD drift')
        raw = raw_path.read_bytes()
        doc = rgd.read(raw)
        changes = [{'path':p,'before':n.value,'after':identity['pbgid']}
                   for p,n in rgd.flatten(doc.nodes) if n.key == 'pbgid']
        edited, proof = patch_visual_rgd(raw, changes, 'body')
        member = identity['private_member']
        target = owned(DEST/'payload'/member)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(edited)
        new_rows.append({'member':member,'path':str(target),'sha256':sha(target),
                         'bytes':target.stat().st_size,'before_sha256':None,
                         'kind':'new_private_equipment_identity_only',
                         'stock_member':identity['stock_member'],
                         'stock_sha256':sha(raw_path),'edits':proof})
    per_actor = defaultdict(list)
    for edge in edge_plan['edges']:
        per_actor[edge['owner_member']].append(edge)
    changed_actors = []
    for member, edges in sorted(per_actor.items()):
        previous = prior[member]
        source = Path(previous['path'])
        if sha(source) != previous['sha256']:
            raise ValueError('Upstream actor payload drift '+member)
        raw = source.read_bytes()
        doc = rgd.read(raw)
        changes = []
        approved = set()
        for edge in edges:
            path = edge['path']
            parent = path.rsplit('/',1)[0]
            node = rgd.find(doc.nodes,path)
            if node.value != edge['before_value'] or rgd.find(doc.nodes,parent+'/$PBGMAP').value != edge['name_map']:
                raise ValueError('Native weapon leaf drift '+member+' '+path)
            identity = by_member[edge['target_private_member']]
            changes.append({'path':path,'before':edge['before_value'],
                            'after':GUID+':'+identity['derived_name']})
            approved.add(path)
        edited, proof = patch_visual_rgd(raw, changes, 'graph', approved_paths=approved)
        target = owned(DEST/'payload'/member)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(edited)
        changed_actors.append({'member':member,'path':str(target),'sha256':sha(target),
                              'bytes':target.stat().st_size,
                              'before_sha256':freeze['archive_members'][member]['sha256'],
                              'upstream_sha256':sha(source),
                              'kind':'changed_vietnamese_weapon_selector','edits':proof})
    staged_source = {x['relative']:x for x in upstream['source_rows']}
    source_edits = defaultdict(dict)
    for row in plan['entries']:
        identity = by_member[row['private_member']]
        old = row['stock_source'].replace('/','\\')
        new = identity['private_reference'].replace('/','\\')
        for consumer in row['source_consumers']:
            source_edits[consumer['source']][(old,new)] = consumer['expected_source_occurrences']
    changed_source = []
    for relative, replacements in sorted(source_edits.items()):
        active = ROOT/relative
        previous = staged_source.get(relative)
        if sha(active) != (previous['source_sha256'] if previous else sha(active)):
            raise ValueError('Active actor source drift '+relative)
        base = Path(previous['staged_path']) if previous else active
        if previous and sha(base) != previous['staged_sha256']:
            raise ValueError('Upstream actor source drift '+relative)
        raw = base.read_bytes()
        tree = ET.fromstring(raw)
        changes = []
        for (old,new), expected in replacements.items():
            matches = [x for x in tree.iter('instance_reference')
                       if x.get('name') == 'animator_attachments' and x.get('value') == old]
            if len(matches) != expected:
                raise ValueError('Source weapon selector count drift '+relative+' '+old)
            owners = {(x.get('name'),x.get('mod')) for x in matches}
            for field,mod in owners:
                count = sum(x.get('name')==field and x.get('mod')==mod for x in matches)
                changes.append({'field':field,'before':old,'before_mod':mod,
                                'after':new,'expected_count':count})
        edited, proof = transform(raw,changes)
        target = owned(DEST/'source'/relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(edited)
        row = {'relative':relative,'source_sha256':sha(active),
               'staged_path':str(target),'staged_sha256':sha(target),
               'upstream_sha256':sha(base),'edits':proof}
        staged_source[relative] = row
        changed_source.append(row)
    for identity in ids['entries']:
        relative = 'assets/attrib/instances/'+identity['private_reference']+'.xml'
        if relative in staged_source or (ROOT/relative).exists():
            raise ValueError('Private equipment source identity collision '+relative)
        tree = ET.Element('instance', version='2',
                          description='Private 0.6.0 Vietnamese equipment visual identity',
                          template=r'attachments\attachment_lists')
        ET.SubElement(tree,'uniqueid',name='pbgid',value=str(identity['pbgid']))
        ET.SubElement(tree,'instance_reference',name='parent_pbg',
                      value=identity['stock_source'].replace('/','\\'))
        ET.indent(tree,space='\t')
        target = owned(DEST/'source'/relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n')
        staged_source[relative] = {'relative':relative,'source_sha256':None,
                                   'staged_path':str(target),'staged_sha256':sha(target),
                                   'upstream_sha256':None,'private_pbgid':identity['pbgid']}
    aggregate = dict(prior)
    for row in new_rows+changed_actors:
        aggregate[row['member']] = row
    payloads = []
    for member,row in sorted(aggregate.items()):
        path = Path(row['path'])
        if sha(path) != row['sha256'] or path.stat().st_size != row['bytes']:
            raise ValueError('Aggregate equipment payload drift '+member)
        before = freeze['archive_members'].get(member)
        payloads.append({**row,'before_sha256':before['sha256'] if before else None})
    source_rows = []
    for relative,row in sorted(staged_source.items()):
        if row['source_sha256'] is not None and sha(ROOT/relative) != row['source_sha256']:
            raise ValueError('Aggregate active source drift '+relative)
        if sha(row['staged_path']) != row['staged_sha256']:
            raise ValueError('Aggregate staged source drift '+relative)
        source_rows.append(row)
    write(DEST/'stage.json',{'schema':'ccp-060-private-equipment-stage/v1',
          'status':'equipment_identity_and_consumer_refs_staged_media_pending',
          'identity_receipt_sha256':sha(IDS),'equipment_plan_sha256':sha(PLAN),
          'equipment_edge_plan_sha256':sha(EDGES),'upstream_stage_sha256':sha(UPSTREAM),
          'payloads':payloads,'source_rows':source_rows,
          'full_baseline_to_aggregate_changed_member_allowlist':sorted(aggregate),
          'new_private_equipment_count':len(new_rows),
          'changed_vietnamese_actor_count':len(changed_actors),
          'source_changed_file_count':len(changed_source),
          'compiled_edge_count':len(edge_plan['edges']),
          'active_source_or_final_archive_changed':False,
          'rebuild_policy':'Reapply pinned original-native compiled overlay and final qualified media after Content Editor build; source-only build is insufficient.'})
    print(json.dumps({'stage':str(DEST/'stage.json'), 'payloads':len(payloads),
                      'source_files':len(source_rows),
                      'changed_actor_files':len(changed_actors)},indent=2))


if __name__ == '__main__':
    main()
