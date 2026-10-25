"""Stage private stock actor/squad graph and Vietnamese consumer redirects.

The source stage remains a rebuild input. The exact compiled overlay is still
required after a Content Editor build, including three inherited producer rows.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from common import CFG, OUT, ROOT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd
from prepare_foot_source_delta import transform

sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd

REGISTERED=OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
REFERENCES=OUT/'integration/private-land-graph/private-reference-edges-v1.json'
CONSUMERS=OUT/'integration/private-land-graph/vietnam-stock-consumer-edges-v1.json'
FIRST_SOURCE=OUT/'integration/private-foot-source-overlay/source-delta.json'
UPSTREAM=OUT/'integration/private-land-graph-stage-r2/stage.json'
DEST=OUT/'integration/private-inherited-graph-stage-r1'
GUID=CFG['project_guid'].replace('-','')


def source_map():
    result={}
    for row in read(FIRST_SOURCE)['files']:
        relative='assets/'+row['asset_relative_path']
        result[relative]={'relative':relative,'source_sha256':row['source_sha256'],
                          'staged_path':row['staged_path'],'staged_sha256':row['staged_sha256']}
    for row in read(UPSTREAM)['source_rows']:
        relative=row['relative']
        result[relative]={'relative':relative,'source_sha256':row['active_sha256'],
                          'staged_path':row['staged'],'staged_sha256':row['staged_sha256']}
    return result


def main():
    guard()
    if DEST.exists():raise FileExistsError('Preserve existing private graph stage')
    ids,refs,consumers,upstream=read(REGISTERED),read(REFERENCES),read(CONSUMERS),read(UPSTREAM)
    if refs['derive_plan_sha256']!=ids['plan_sha256'] or consumers['derive_plan_sha256']!=ids['plan_sha256']:
        raise ValueError('Private graph plans do not match registered IDs')
    freeze=read(OUT/'baseline/final053/freeze.json')
    by_member={x['private_member']:x for x in ids['entries']}
    initial={x['member']:x for x in upstream['payloads']}
    if len(initial)!=len(upstream['payloads']):raise ValueError('Upstream payload collision')
    graph_edits=defaultdict(list)
    for edge in refs['edges']:
        owner=edge['owner_private_member']
        target=by_member[edge['target_private_member']]
        graph_edits[owner].append({'path':edge['path'],'before':edge['before_value'],
                                   'after':GUID+':'+target['derived_name'],
                                   'name_map':edge['name_map']})
    private_rows=[]
    for identity in ids['entries']:
        member=identity['private_member']
        if member in initial:continue  # 27 local lists already staged and pinned.
        source=Path(identity['stock_path'])
        if sha(source)!=identity['stock_sha256']:
            raise ValueError('Official original native drift '+member)
        raw=source.read_bytes();doc=rgd.read(raw)
        changes=[{'path':path,'before':node.value,'after':identity['pbgid']}
                 for path,node in rgd.flatten(doc.nodes) if node.key=='pbgid']
        approved=set()
        for edit in graph_edits[member]:
            old=rgd.find(doc.nodes,edit['path'])
            parent=edit['path'].rsplit('/',1)[0]
            if old.value!=edit['before'] or rgd.find(doc.nodes,parent+'/$PBGMAP').value!=edit['name_map']:
                raise ValueError('Official graph edge changed '+member+' '+edit['path'])
            approved.add(edit['path'])
            changes.append({k:edit[k] for k in ('path','before','after')})
        native,proof=patch_visual_rgd(raw,changes,'graph',approved_paths=approved)
        target=owned(DEST/'payload'/member);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(native)
        private_rows.append({'member':member,'path':str(target),'sha256':sha(target),
                             'bytes':target.stat().st_size,'before_sha256':None,
                             'kind':'new_private_native_graph','stock_member':identity['stock_member'],
                             'stock_sha256':sha(source),'edits':proof})
    vn_edits=defaultdict(list)
    for edge in consumers['edges']:
        vn_edits[edge['compiled_member']].append(edge)
    vietnamese_rows=[]
    for member,edges in vn_edits.items():
        previous=initial.get(member)
        source=Path(previous['path']) if previous else OUT/'baseline/final053/archive-members'/member
        if previous:
            if sha(source)!=previous['sha256']:raise ValueError('Prior actor/squad stage drift')
        elif sha(source)!=freeze['archive_members'][member]['sha256']:
            raise ValueError('Frozen Vietnam actor/squad drift')
        raw=source.read_bytes();doc=rgd.read(raw);changes=[];approved=set()
        for edge in edges:
            node=rgd.find(doc.nodes,edge['path'])
            parent=edge['path'].rsplit('/',1)[0]
            if node.value!=edge['before_value'] or rgd.find(doc.nodes,parent+'/$PBGMAP').value!=edge['name_map']:
                raise ValueError('Vietnamese stock consumer changed '+member+' '+edge['path'])
            approved.add(edge['path'])
            changes.append({'path':edge['path'],'before':edge['before_value'],'after':edge['after_value']})
        native,proof=patch_visual_rgd(raw,changes,'graph',approved_paths=approved)
        target=owned(DEST/'payload'/member);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(native)
        vietnamese_rows.append({'member':member,'path':str(target),'sha256':sha(target),
                                'bytes':target.stat().st_size,
                                'before_sha256':freeze['archive_members'][member]['sha256'],
                                'upstream_sha256':sha(source),'kind':'changed_vietnamese_stock_consumer',
                                'edits':proof})
    # Direct XML rows are changed byte-narrowly; inherited native parent spawn
    # rows have no local source element and remain explicit post-build overlays.
    staged_source=source_map()
    direct=defaultdict(set)
    inherited=[]
    for edge in consumers['edges']:
        if edge['direct_source_match_count']:
            source=Path(edge['source'])
            target=by_member[edge['target_private_member']]
            direct[source.relative_to(ROOT).as_posix()].add((target['stock_source'].replace('/','\\'),
                                                              target['private_reference'].replace('/','\\')))
        else:inherited.append(edge)
    changed_source=[]
    for relative,mapping in direct.items():
        active=ROOT/relative
        old=staged_source.get(relative)
        base=Path(old['staged_path']) if old else active
        if old and sha(base)!=old['staged_sha256']:
            raise ValueError('Upstream source stage drift')
        if not active.is_file():raise FileNotFoundError(active)
        original=base.read_bytes();tree=ET.fromstring(original);changes=[]
        for before,after in mapping:
            matches=[x for x in tree.iter('instance_reference') if x.attrib.get('value')==before]
            if not matches:raise ValueError('Direct source reference missing '+relative+' '+before)
            owners={(x.attrib.get('name'),x.attrib.get('mod')) for x in matches}
            for field,mod in owners:
                count=sum(x.attrib.get('name')==field and x.attrib.get('mod')==mod for x in matches)
                changes.append({'field':field,'before':before,'before_mod':mod,
                                'after':after,'expected_count':count})
        result,proof=transform(original,changes)
        target=owned(DEST/'source'/relative);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(result)
        record={'relative':relative,'source_sha256':sha(active),
                'staged_path':str(target),'staged_sha256':sha(target),'upstream_sha256':sha(base),
                'edits':proof}
        staged_source[relative]=record;changed_source.append(record)
    aggregate=dict(initial)
    for row in private_rows+vietnamese_rows:aggregate[row['member']]=row
    rows=[]
    for member,row in sorted(aggregate.items()):
        file=Path(row['path'])
        if sha(file)!=row['sha256'] or file.stat().st_size!=row['bytes']:
            raise ValueError('Aggregate payload drift')
        before=freeze['archive_members'].get(member)
        rows.append({**row,'before_sha256':before['sha256'] if before else None})
    source_rows=[]
    for relative,row in sorted(staged_source.items()):
        active=ROOT/relative
        if row['source_sha256'] is not None and sha(active)!=row['source_sha256']:
            raise ValueError('Active source drift '+relative)
        if sha(row['staged_path'])!=row['staged_sha256']:
            raise ValueError('Staged source drift '+relative)
        source_rows.append(row)
    write(DEST/'stage.json',{'schema':'ccp-060-private-inherited-graph-stage/v1',
          'status':'identity_graph_and_vietnamese_consumer_references_staged_media_pending',
          'identity_receipt_sha256':sha(REGISTERED),'reference_plan_sha256':sha(REFERENCES),
          'consumer_plan_sha256':sha(CONSUMERS),'upstream_stage_sha256':sha(UPSTREAM),
          'payloads':rows,'full_baseline_to_aggregate_changed_member_allowlist':sorted(aggregate),
          'source_rows':source_rows,'inherited_producer_compiled_overlays_without_source_elements':inherited,
          'new_private_native_graph_count':len(private_rows),
          'changed_vietnamese_consumer_count':len(vietnamese_rows),
          'active_source_or_final_archive_changed':False,'native_match_acceptance':False,
          'rebuild_policy':'After Content Editor build, reapply this pinned original-native compiled overlay and final qualified media; source-only build does not recreate private visual bytes.'})
    print(json.dumps({'stage':str(DEST/'stage.json'),'payloads':len(rows),
                      'source_files':len(source_rows),'inherited_overrides':len(inherited)},indent=2))


if __name__=='__main__':main()
