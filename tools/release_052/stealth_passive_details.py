"""Describe native spy passive nodes, guards, and action properties."""
from __future__ import annotations
import json
from pathlib import Path
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_052/stealth/official')

def main():
    src=json.loads((OUT/'stealth-state-trees.json').read_text(encoding='utf-8'))
    objects={x['id']:x for x in src['selected_objects']}
    roots={x['id']:x['fields']['m_name']['text'] for x in src['root_hits']}
    def chain(o):
        result=[]
        for _ in range(40):
            result.append(o)
            o=objects.get(o['owner'])
            if o is None:break
        return result
    rows=[]
    for o in src['selected_objects']:
        lineage=chain(o)
        if not any(x['id'] in roots and roots[x['id']]=='passive_stealth_ayy' for x in lineage):continue
        if not any(s in o['type'] for s in ('StateNode','Condition','Track_','EntityTrack','Provider_','Property')):continue
        rows.append({'type':o['type'],'name':o['fields'].get('m_name',{}).get('text'),
                     'parent_names':[x['fields'].get('m_name',{}).get('text') for x in lineage[1:] if x['fields'].get('m_name',{}).get('text')],
                     'fields':{k:v for k,v in o['fields'].items() if k not in ('m_objectID','m_typeID','m_parent','m_children','m_trackGroup','m_conditionGroup')}})
    target=OUT/'passive-spy-details.json';target.write_text(json.dumps({'schema':'ccp.release052.spy-passive-details/v1',
        'rows':rows},indent=2)+'\n',encoding='utf-8')
    for x in rows:
        if 'Condition_' in x['type'] or 'EntityTrack_SetStealthAllowed' in x['type'] or x['type']=='StateTree::StateNodePlayable':
            print(x['type'],x['name'],x['parent_names'][:3],x['fields'])
    print('PASSIVE_SPY_DETAILS',len(rows),target)

if __name__=='__main__':main()
