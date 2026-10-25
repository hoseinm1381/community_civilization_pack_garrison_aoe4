"""Stage remaining reachable local body-list refs on top of first-ten payloads.

Only identity references are staged here. New media and inherited stock actor,
squad and Vietnamese producer edges require later qualification and staging.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from common import CFG, OUT, ROOT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd
from prepare_foot_source_delta import transform

import sys
sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd

GRAPH = OUT/'integration/private-land-graph/plan-v3.json'
PLAN = OUT/'integration/private-land-identities/derive-plan-v5.json'
REGISTERED = OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
FIRST_COMPILED = OUT/'integration/private-foot-compiled-r1/bindings.json'
FIRST_SOURCE = OUT/'integration/private-foot-source-overlay'
DEST = OUT/'integration/private-land-graph-stage-r2'
GUID = CFG['project_guid'].replace('-','')


def main():
    guard()
    if DEST.exists():
        raise FileExistsError('Preserve existing graph stage')
    graph, plan, registered = read(GRAPH), read(PLAN), read(REGISTERED)
    if registered['plan_sha256'] != sha(PLAN):
        raise ValueError('Native identities belong to different graph plan')
    by_member = {x['stock_member']:x for x in registered['entries']
                 if x['role']=='unit_body_list'}
    if len(by_member) != len(graph['unit_actor_lists']):
        raise ValueError('Reachable local list identity count differs')
    first = read(FIRST_COMPILED)
    first_payloads = {x['member']:x for x in first['payloads']}
    if len(first_payloads) != len(first['payloads']):
        raise ValueError('First-ten payload collision')
    freeze = read(OUT/'baseline/final053/freeze.json')
    source_edits = defaultdict(dict)
    compiled_edits = defaultdict(dict)
    list_rows = []
    for row in graph['unit_actor_lists']:
        stock = row['stock_member']
        identity = by_member[stock]
        source_stock = Path(identity['stock_path'])
        if sha(source_stock) != identity['stock_sha256']:
            raise ValueError('Native stock list drift')
        raw = source_stock.read_bytes()
        native = rgd.read(raw)
        changes = [{'path':path,'before':node.value,'after':identity['pbgid']}
                   for path,node in rgd.flatten(native.nodes) if node.key=='pbgid']
        changed, proof = patch_visual_rgd(raw,changes,'body')
        member = identity['private_member']
        list_rows.append({'member':member,'data':changed,'kind':'new_private_list_identity_only',
                          'stock_member':stock,'stock_sha256':sha(source_stock),'edits':proof})
        for consumer in row['source_consumers']:
            relative = consumer['relative_source']
            if not relative:
                continue  # Inherited stock actors have separate private copies.
            src = ROOT/relative
            if sha(src) != consumer['source_sha256']:
                raise ValueError('Reachable source actor drift '+relative)
            before = consumer['before']
            after = identity['private_reference'].replace('/','\\')
            key=(before,after)
            source_edits[relative][key]=None
            compiled = relative.replace('assets/attrib/instances/','attrib/').removesuffix('.xml')+'.rgd'
            compiled_edits[compiled][key]=None
    # Build actual source edit counts from current XML so each byte substitution
    # has a concrete old tag and owner. This is checked against graph edge counts.
    source_rows=[]
    source_counts=defaultdict(lambda:defaultdict(int))
    for relative, mapping in source_edits.items():
        active=ROOT/relative
        upstream=FIRST_SOURCE/relative
        base=upstream if upstream.is_file() else active
        base_bytes=base.read_bytes()
        import xml.etree.ElementTree as ET
        tree=ET.fromstring(base_bytes)
        edits=[]
        for (before,after) in mapping:
            matches=[n for n in tree.iter('instance_reference')
                     if n.attrib.get('value')==before and
                        n.attrib.get('name') in ('attachments','animator_attachments')]
            if not matches:
                raise ValueError('No source node for reachable visual edge '+relative+' '+before)
            owners={(n.attrib.get('name'),n.attrib.get('mod')) for n in matches}
            for field,old_mod in owners:
                count=sum(n.attrib.get('name')==field and n.attrib.get('mod')==old_mod for n in matches)
                edits.append({'field':field,'before':before,'before_mod':old_mod,
                              'after':after,'expected_count':count})
                compiled=relative.replace('assets/attrib/instances/','attrib/').removesuffix('.xml')+'.rgd'
                source_counts[compiled][(before,after)]+=count
        updated,proof=transform(base_bytes,edits)
        target=owned(DEST/'source'/relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(updated)
        source_rows.append({'relative':relative,'active_sha256':sha(active),'upstream':str(base),
                            'upstream_sha256':sha(base),'staged':str(target),'staged_sha256':sha(target),
                            'edits':proof})
    for identity in by_member.values():
        import xml.etree.ElementTree as ET
        tree=ET.Element('instance',version='2',description='Private 0.6.0 Vietnamese land visual identity',
                        template=r'attachments\attachment_lists')
        ET.SubElement(tree,'uniqueid',name='pbgid',value=str(identity['pbgid']))
        ET.SubElement(tree,'instance_reference',name='parent_pbg',
                      value=identity['stock_source'].replace('/','\\'))
        ET.indent(tree,space='\t')
        relative='assets/attrib/instances/'+identity['private_reference']+'.xml'
        target=owned(DEST/'source'/relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n')
        source_rows.append({'relative':relative,'active_sha256':None,'upstream':None,
                            'upstream_sha256':None,'staged':str(target),'staged_sha256':sha(target),
                            'private_pbgid':identity['pbgid']})
    compiled_rows=[]
    for member,mapping in compiled_edits.items():
        upstream=first_payloads.get(member)
        source=Path(upstream['path']) if upstream else OUT/'baseline/final053/archive-members'/member
        if upstream:
            if sha(source)!=upstream['sha256']:
                raise ValueError('First-ten actor payload drift')
        elif sha(source)!=freeze['archive_members'][member]['sha256']:
            raise ValueError('Frozen actor drift')
        raw=source.read_bytes()
        doc=rgd.read(raw)
        changes=[]
        counts={key:0 for key in mapping}
        for path,node in rgd.flatten(doc.nodes):
            if node.kind!='CString' or node.key!='$PBGNAME':
                continue
            for before,after in mapping:
                if node.value != Path(before.replace('\\','/')).name:
                    continue
                parent=path.rsplit('/',1)[0]
                if rgd.find(doc.nodes,parent+'/$PBGMAP').value != r'attachments\attachment_lists':
                    continue
                changes.append({'path':path,'before':node.value,
                                'after':GUID+':'+Path(after.replace('\\','/')).name})
                counts[(before,after)]+=1
        if dict(counts)!=dict(source_counts[member]):
            raise ValueError('Source/compiled visual edge count differs '+member+' '+str(counts))
        result,proof=patch_visual_rgd(raw,changes,'actor_extended')
        target=owned(DEST/'payload'/member)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(result)
        compiled_rows.append({'member':member,'kind':'changed_reachable_vietnamese_actor',
                              'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size,
                              'baseline_sha256':freeze['archive_members'][member]['sha256'],
                              'upstream_sha256':sha(source),'edits':proof})
    list_payloads=[]
    for row in list_rows:
        target=owned(DEST/'payload'/row['member'])
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(row.pop('data'))
        list_payloads.append({**row,'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
    aggregate=dict(first_payloads)
    for row in compiled_rows+list_payloads:
        aggregate[row['member']]=row
    new_actor_count=sum(row['member'] not in first_payloads for row in compiled_rows)
    if len(aggregate)!=len(first_payloads)+len(list_payloads)+new_actor_count:
        raise ValueError('Unexpected aggregate member replacement count')
    full_rows=[]
    for member,row in sorted(aggregate.items()):
        path=Path(row['path'])
        if sha(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:
            raise ValueError('Aggregate payload changed before manifest '+member)
        baseline=freeze['archive_members'].get(member)
        full_rows.append({**row,'baseline_before_sha256':baseline['sha256'] if baseline else None})
    write(DEST/'stage.json',{'schema':'ccp-060-private-land-graph-stage/v1',
          'status':'local_actor_and_list_identity_stage_inherited_graph_media_pending',
          'graph_sha256':sha(GRAPH),'identity_receipt_sha256':sha(REGISTERED),
          'first_ten_compiled_sha256':sha(FIRST_COMPILED),
          'first_ten_source_sha256':sha(FIRST_SOURCE/'source-delta.json'),
          'source_rows':source_rows,'payloads':full_rows,
          'full_baseline_to_aggregate_changed_member_allowlist':sorted(aggregate),
          'new_list_count':len(list_payloads),'changed_actor_count':len(compiled_rows),
          'active_source_or_final_archive_changed':False,'native_match_acceptance':False})
    print(json.dumps({'stage':str(DEST/'stage.json'),'payloads':len(aggregate),
                      'sources':len(source_rows)},indent=2))


if __name__=='__main__':main()
