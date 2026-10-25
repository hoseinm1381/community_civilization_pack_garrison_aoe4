"""Read-only 0.5.2 villager-stealth dependency and baseline inventory."""
from __future__ import annotations
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CFG=configuration(ROOT)
OUT=Path(CFG['external_root'])/'output/release_052/stealth'
ABILITY=ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'
ARCHER=ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_for_archer.xml'
SCAR=ROOT/'assets/scar/vietnam/landmarks.scar'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def field(root,name):
    nodes=[x for x in root.iter() if x.get('name')==name]
    return [{'tag':x.tag,'value':x.get('value'),'path_parent':None} for x in nodes]

def main():
    check_storage(ROOT,CFG)
    ability=ET.parse(ABILITY).getroot();archer=ET.parse(ARCHER).getroot()
    wanted=('activation','entity_tree','squad_tree','recharge_time','can_queue_passive_ability',
            'can_use_ability_check_interval','disable_when_active','outer_radius','duration',
            'nearby_collision_filter','structure_name')
    select=lambda root:{name:field(root,name) for name in wanted}
    consumer=[]
    for path in (ROOT/'assets/attrib/instances').rglob('*.xml'):
        if path==ABILITY:continue
        if 'vn_activate_stealth_forvills_vit' in path.read_text(encoding='utf-8',errors='replace'):
            consumer.append({'file':str(path),'sha256':sha(path)})
    text=SCAR.read_text(encoding='utf-8')
    report={'schema':'ccp.release052.stealth-inventory/v1','status':'source_inventory_only',
            'villager_ability':{'file':str(ABILITY),'sha256':sha(ABILITY),'fields':select(ability)},
            'working_archer_control':{'file':str(ARCHER),'sha256':sha(ARCHER),'fields':select(archer)},
            'consumers':consumer,'landmarks_scar':{'file':str(SCAR),'sha256':sha(SCAR),
                'availability_gate':('Player_SetAbilityAvailability' in text),
                'casts_or_reissues_stealth':any(x in text for x in ('Entity_DoAbility','Squad_DoAbility','Entity_ActivateAbility'))},
            'runtime_flicker':'reported_by_user_on_051','native_mechanism':'awaiting current official Fort EBPS trace'}
    assert len(consumer)>=5 and report['landmarks_scar']['availability_gate']
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'inventory.json';target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('STEALTH_INVENTORY',len(consumer),sha(ABILITY),sha(ARCHER))

if __name__=='__main__':main()
