"""Inventory every stock simulation stealth action and the graphs that invoke it."""
from __future__ import annotations
import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from stealth_state_trace import Tree,OUT,CFG,ROOT,sha
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage

def main():
    check_storage(ROOT,CFG)
    tree=Tree(OUT/'statetree-simulation.bin',OUT/'reflect.db')
    objects=tree.objects
    def name(o):
        f=o['fields'].get('m_name')
        return tree.field(o,f).get('text') if f is not None and f.get('FieldTypeName')=='Reflect::ReflectStringHash' else None
    def ancestors(o):
        chain=[];seen=set()
        while o is not None and o['id'] not in seen and len(chain)<64:
            seen.add(o['id']);chain.append({'id':o['id'],'type':o['type'],'name':name(o)})
            o=objects.get(o['owner'])
        return chain
    actions=[];rootids=set()
    for o in objects.values():
        if o['type']=='StateTree::EntityTrack_SetStealthAllowed':
            chain=ancestors(o)
            roots=[x for x in chain if x['type'] in ('StateTree::StateNodeRoot','StateTree::StateNodeBank')]
            root=roots[-1] if roots else next((x for x in reversed(chain) if x['name']),chain[-1])
            rootids.add(root['id'])
            actions.append({'action':tree.describe(o),'ancestry':chain,'root':root})
    # Native references are comparatively rare; resolve graph-level incoming links.
    referenced={}
    for o in objects.values():
        for field_name in ('m_referenceNode','m_parent'):
            f=o['fields'].get(field_name)
            if f is None or not f.get('FieldTypeName','').startswith('util::ReflectObjectRef<'):continue
            target=tree.field(o,f).get('object_ref')
            if target in rootids or target in objects and name(objects[target]) and 'stealth' in name(objects[target]).lower():
                referenced.setdefault(target,[]).append({'from':o['id'],'from_type':o['type'],
                    'field':field_name,'caller_ancestry':ancestors(o)})
    for row in actions:row['incoming_to_root']=referenced.get(row['root']['id'],[])
    report={'schema':'ccp.release052.all-native-stealth-actions/v1','source':str(OUT/'statetree-simulation.bin'),
            'sha256':sha(OUT/'statetree-simulation.bin'),'validated_objects':len(objects),
            'action_count':len(actions),'actions':actions,'status':'read_only_reflected'}
    target=OUT/'all-stealth-actions.json';target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for row in actions:
        print(row['action']['fields'].get('m_setStealthAllowed'),row['root']['type'],row['root']['name'],
              ' < '.join(x['name'] or x['type'].split('::')[-1] for x in row['ancestry'][1:6]))
    print('STEALTH_GRAPH_INVENTORY',len(actions),len(rootids),target)

if __name__=='__main__':main()
