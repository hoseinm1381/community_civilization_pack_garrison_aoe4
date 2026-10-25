"""Freeze reached separate equipment/cart/elephant models for native material cook."""
from __future__ import annotations
import json
from pathlib import Path
from common import EXPORT,OUT,guard,owned,read,write

HERE=Path(__file__).resolve().parent

def item(key,revision,scope,map_name='material-map.json',map_receipt=None):
    base=EXPORT/'remaining_roster/nonhumanoid'/key/revision
    row={'key':key,'source_receipt':str(OUT/'qualification/remaining_roster/nonhumanoid'/key/revision/'authoring.json'),
         'material_map':str(base/map_name),'geometry_scope':scope}
    if map_receipt:row['material_map_receipt']=str(OUT/'qualification/remaining_roster/nonhumanoid'/key/revision/map_receipt)
    return row

def main():
    guard()
    target=owned(HERE/'remaining-equipment-materials-registry.json')
    conditional=owned(HERE/'conditional-crossbow-weapon-materials.json')
    if target.exists() or conditional.exists():raise FileExistsError('Preserve registry')
    rows=[
       item('bow_recurve','v3','reached separate archer II-IV weapon; stock bow rig/actions retained'),
       item('monk_staff3','v1','reached separate monk III staff; stock grip/animation retained'),
       item('spear_basic','v1','reached separate spear I-II melee/charge/brace weapon; stock mechanics retained'),
       item('spear_ji','v1','reached separate spear III-IV charge/brace weapon; normal inherited melee owner pending'),
       item('combat_elephant3','v1','reached Sultanate elephant III body/rider; stock animation retained'),
       item('siege_cart3','v1','reached English trebuchet cart skin; stock construction and cart mechanics retained',
            'material-map-v3.json','material-map-v3-receipt.json'),
    ]
    write(target,rows)
    write(conditional,[item(key,'v3','decoded weapon; Vietnamese selector still being independently verified')
                       for key in ('bow_cross','bow_arbalest')])
    print(json.dumps({'ready':str(target),'ready_count':len(rows),
                      'conditional':str(conditional)}))

if __name__=='__main__':main()
