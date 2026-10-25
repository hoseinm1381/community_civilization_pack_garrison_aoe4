"""Catalog official ability activation and state-tree field pairings."""
from __future__ import annotations
import json,xml.etree.ElementTree as ET
from pathlib import Path
BASE=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_052/stealth/official/reference-abilities')
OUT=BASE.parent
FIELDS=('activation','entity_tree','squad_tree','ability_activate_deferred_tree',
        'ability_activate_entity_tree','can_queue_passive_ability','recharge_time')
def main():
    rows=[]
    for path in BASE.rglob('*.xml'):
        root=ET.parse(path).getroot();bag=root.find("./group[@name='ability_bag']")
        if bag is None:continue
        values={key:next((x.get('value') for x in bag.iter() if x.get('name')==key),None) for key in FIELDS}
        if values['entity_tree'] or values['ability_activate_deferred_tree']:
            rows.append({'file':str(path.relative_to(BASE)),'fields':values})
    target=OUT/'ability-activation-patterns.json';target.write_text(json.dumps({'schema':'ccp.release052.ability-patterns/v1',
        'inspected_count':len(list(BASE.rglob('*.xml'))),'rows':rows},indent=2)+'\n',encoding='utf-8')
    always=[x for x in rows if x['fields']['activation']=='always_on']
    deferred=[x for x in always if x['fields']['ability_activate_deferred_tree']]
    print('ABILITY_PATTERNS',len(rows),'always_on',len(always),'always_on_deferred',len(deferred))
    for row in deferred:print(row['file'],row['fields'])

if __name__=='__main__':main()
