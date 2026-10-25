"""Pin final053 Vietnamese compiled stock actor/squad consumer leaves."""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import CFG, OUT, ROOT, guard, owned, read, sha, write

sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd

DERIVE=OUT/'integration/private-land-identities/derive-plan-v5.json'
BASE=OUT/'baseline/final053/archive-members/attrib'
TARGET=OUT/'integration/private-land-graph/vietnam-stock-consumer-edges-v1.json'


def main():
    guard()
    by_target={}
    for row in read(DERIVE)['entries']:
        kind=row['stock_member'].split('/')[1]
        if kind not in ('ebps','sbps'):
            continue
        key=(kind,Path(row['stock_member']).stem)
        if key in by_target:raise ValueError('Ambiguous stock actor/squad target')
        by_target[key]=row
    rows=[]
    for kind in ('ebps','sbps'):
        for path in sorted((BASE/kind/'vietnam').rglob('*.rgd')):
            raw=path.read_bytes()
            doc=rgd.read(raw)
            if rgd.write(doc)!=raw:raise ValueError('Baseline native codec mismatch '+str(path))
            member='attrib/'+path.relative_to(BASE).as_posix()
            source=ROOT/'assets/attrib/instances'/path.relative_to(BASE).with_suffix('.xml')
            source_nodes=[]
            if source.is_file():
                for node in ET.parse(source).getroot().iter('instance_reference'):
                    source_nodes.append({'field':node.attrib.get('name'),'value':node.attrib.get('value'),
                                         'mod':node.attrib.get('mod')})
            for leaf,node in rgd.flatten(doc.nodes):
                if node.kind!='CString' or node.key!='$PBGNAME' or '/parent_pbg/' in leaf:
                    continue
                parent=leaf.rsplit('/',1)[0]
                try:mapping=rgd.find(doc.nodes,parent+'/$PBGMAP').value
                except (KeyError,ValueError):continue
                target=by_target.get((mapping,node.value))
                if not target:continue
                full_stock=target['stock_source'].replace('/','\\')
                matches=[x for x in source_nodes if x['value']==full_stock]
                rows.append({'compiled_member':member,'compiled_baseline_sha256':sha(path),
                             'path':leaf,'name_map':mapping,'before_value':node.value,
                             'target_private_member':target['private_member'],
                             'after_value':CFG['project_guid'].replace('-','')+':'+target['derived_name'],
                             'source':str(source) if source.is_file() else None,
                             'source_sha256':sha(source) if source.is_file() else None,
                             'direct_source_match_count':len(matches),
                             'source_matching_fields':sorted({x['field'] for x in matches})})
    if len({(x['compiled_member'],x['path']) for x in rows})!=len(rows):
        raise ValueError('Duplicate Vietnamese stock consumer leaf')
    data={'schema':'ccp-060-vietnam-stock-consumer-edges/v1',
          'status':'compiled_exact_before_values_source_direct_or_inherited_classified',
          'derive_plan_sha256':sha(DERIVE),'baseline_sga':'final053',
          'edges':rows,'active_source_or_archive_changed':False}
    if TARGET.exists():
        if read(TARGET)!=data:raise ValueError('Preserve existing stock consumer plan')
    else:write(owned(TARGET),data)
    print({'edges':len(rows),'direct':sum(x['direct_source_match_count']>0 for x in rows),
           'inherited':sum(x['direct_source_match_count']==0 for x in rows),'receipt':str(TARGET)})


if __name__=='__main__':main()
