"""Complete editable source identity graph for private inherited native resources."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from common import OUT, ROOT, guard, owned, read, sha, write

UPSTREAM = OUT/'integration/qualified-siege-actor-media-stage-r1/stage.json'
IDS = OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
DEST = OUT/'integration/final-binding-source-complete-r2'


def main():
    guard()
    if DEST.exists():
        raise FileExistsError('Preserve existing inherited source identity stage')
    upstream, registered = read(UPSTREAM), read(IDS)
    existing = {x['relative']:x for x in upstream['source_rows']}
    additions=[]
    identities=[x for x in registered['entries'] if x['role']!='unit_body_list']
    if len(identities)!=28:
        raise ValueError('Expected 28 private inherited stock identity resources')
    for identity in identities:
        source=identity['stock_source']
        category=source.split('/',1)[0]
        if category=='attachments':
            template=r'attachments\attachment_lists'
        elif category in ('ebps','sbps'):
            template=category
        else:
            raise ValueError('Unsupported private source template '+source)
        relative='assets/attrib/instances/'+identity['private_reference']+'.xml'
        if relative in existing or (ROOT/relative).exists():
            raise ValueError('Private inherited source identity collision '+relative)
        tree=ET.Element('instance',version='2',
                        description='Private 0.6.0 Vietnamese inherited native identity',
                        template=template)
        ET.SubElement(tree,'uniqueid',name='pbgid',value=str(identity['pbgid']))
        ET.SubElement(tree,'instance_reference',name='parent_pbg',
                      value=source.replace('/','\\'))
        ET.indent(tree,space='\t')
        target=owned(DEST/'source'/relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n')
        parsed=ET.fromstring(target.read_bytes())
        if (parsed.get('template')!=template or
                [(x.get('name'),x.get('value')) for x in parsed.iter('uniqueid')]!=[('pbgid',str(identity['pbgid']))] or
                [(x.get('name'),x.get('value')) for x in parsed.iter('instance_reference')]!=[('parent_pbg',source.replace('/','\\'))]):
            raise ValueError('Private identity source readback differs '+relative)
        additions.append({'relative':relative,'source_sha256':None,
                          'staged_path':str(target),'staged_sha256':sha(target),
                          'upstream_sha256':None,'private_pbgid':identity['pbgid'],
                          'stock_parent':source,'stock_parent_sha256':identity['stock_sha256'],
                          'kind':'private_inherited_identity_stock_parent_only'})
    source_rows=sorted(upstream['source_rows']+additions,key=lambda x:x['relative'])
    if len(source_rows)!=140 or len({x['relative'].casefold() for x in source_rows})!=140:
        raise ValueError('Expected 140 unique final editable source XML rows')
    for row in source_rows:
        if row['source_sha256'] is not None and sha(ROOT/row['relative'])!=row['source_sha256']:
            raise ValueError('Original active source drift '+row['relative'])
        if sha(row['staged_path'])!=row['staged_sha256']:
            raise ValueError('Staged source drift '+row['relative'])
    payloads=upstream['payloads']
    if len(payloads)!=447:
        raise ValueError('Do not alter 447 verified compiled/art payloads')
    write(DEST/'stage.json',{'schema':'ccp-060-final-binding-source-complete-stage/v2',
          'status':'complete_private_identity_source_graph_native_overlay_still_required',
          'upstream_stage_sha256':sha(UPSTREAM),
          'baseline_sga_sha256':upstream['baseline_sga_sha256'],
          'added_private_identity_source_count':len(additions),
          'new_source_count':sum(x['source_sha256'] is None for x in source_rows),
          'changed_existing_source_count':sum(x['source_sha256'] is not None for x in source_rows),
          'payloads':payloads,'source_rows':source_rows,
          'full_baseline_to_aggregate_changed_member_allowlist':upstream['full_baseline_to_aggregate_changed_member_allowlist'],
          'active_source_or_final_archive_changed':False,
          'rebuild_policy':'Content Editor can resolve private names from stock-parent identities; exact original-native graph and qualified media overlay remains mandatory after compilation.'})
    print(json.dumps({'stage':str(DEST/'stage.json'),'source_rows':len(source_rows),
                      'new_identities':len(additions),'payloads':len(payloads)},indent=2))


if __name__=='__main__':main()
