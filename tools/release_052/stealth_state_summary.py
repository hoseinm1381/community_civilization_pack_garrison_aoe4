"""Summarize the two stock stealth graphs from the validated reflected trace."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_052/stealth/official')

def main():
    source=json.loads((OUT/'stealth-state-trees.json').read_text(encoding='utf-8'))
    objects={x['id']:x for x in source['selected_objects']}
    roots={x['id']:x['fields']['m_name']['text'] for x in source['root_hits']}
    def ancestry(o):
        chain=[]
        for _ in range(32):
            name=o['fields'].get('m_name',{}).get('text')
            chain.append({'id':o['id'],'type':o['type'],'name':name})
            o=objects.get(o['owner'])
            if o is None:break
        return chain
    keep=('Stealth','Camouflage','Modifier','Timer','Cooldown','Spawn','AbilityBagProperty','Condition_CompareBool')
    selected=[]
    for o in source['selected_objects']:
        if any(token in o['type'] for token in keep):
            chain=ancestry(o)
            selected.append({'type':o['type'],'id':o['id'],'root':next((roots[x['id']] for x in chain if x['id'] in roots),None),
                             'ancestry':chain,'fields':o['fields']})
    report={'schema':'ccp.release052.stealth-state-summary/v1','source':str(OUT/'stealth-state-trees.json'),
            'roots':list(roots.values()),'actions':selected}
    target=OUT/'stealth-state-summary.json';target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for x in selected:
        if 'Stealth' in x['type'] or 'Camouflage' in x['type'] or 'Timer' in x['type']:
            print(x['root'],x['type'],{k:v for k,v in x['fields'].items() if k not in ('m_objectID','m_typeID')},
                  [(a['type'],a['name']) for a in x['ancestry'][:5]])
    print('STEALTH_STATE_SUMMARY',len(selected),target)

if __name__=='__main__':main()
