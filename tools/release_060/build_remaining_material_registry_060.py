"""Freeze exact ready material assignments; keep unresolved siege donor candidates apart."""
from __future__ import annotations
import json
from pathlib import Path
from common import EXPORT,OUT,ROOT,guard,owned,read,sha,write

HERE=Path(__file__).resolve().parent

def row(key,receipt,mapping,scope,map_receipt=None,expand=False):
    result={'key':key,'source_receipt':str(receipt),'material_map':str(mapping),
            'geometry_scope':scope}
    if map_receipt:result['material_map_receipt']=str(map_receipt)
    if expand:result['expand_shared_lod_albedo']=True
    return result

def main():
    guard()
    ready=owned(HERE/'remaining-materials-registry.json')
    candidates=owned(HERE/'unresolved-siege-donor-materials.json')
    monk_map=owned(EXPORT/'remaining_roster/monk3/v2/material-map.json')
    if any(p.exists() for p in (ready,candidates,monk_map)):
        raise FileExistsError('Preserve existing material registry')
    monk_receipt=OUT/'qualification/remaining_roster/monk3/v2/export.json'
    monk=read(monk_receipt)
    monk_albedo=EXPORT/'remaining_roster/monk3/v2/albedo.png'
    if sha(monk_albedo)!=monk['files']['albedo.png']['sha256']:
        raise RuntimeError('Monk III albedo drift')
    write(monk_map,{'schema':'ccp-060-humanoid-exact-material-map/1',
        'exact_native_model':monk['exact_native_body_model'],
        'donor_manifest':monk['donor_manifest'],
        'donor_manifest_sha256':monk['donor_manifest_sha256'],
        'groups':[{'native_material':'lod'+str(n),'albedo_png':str(monk_albedo),
                   'albedo_sha256':sha(monk_albedo),'texture_slot':'albedoTexture'}
                  for n in (1,2,3)],
        'geometry_route':'separately qualified skinned three-LOD source, material only here'})
    rows=[row('monk3',monk_receipt,monk_map,'humanoid exact three-LOD body')]
    horse_receipt=OUT/'representatives/horseman2/v4/authoring.json'
    horse_map=EXPORT/'representatives/horseman2/v4/material-map.json'
    rows.append(row('horseman2',horse_receipt,horse_map,'compatible stock mounted geometry; added source details excluded',expand=True))
    for key,rev in (('trade2','v1'),('trade3','v1'),('trade4','v2')):
        base=EXPORT/'remaining_roster/mounted'/key/rev
        rows.append(row(key,OUT/'qualification/remaining_roster/mounted'/key/rev/'authoring.json',
                        base/'material-map.json','compatible stock mounted/trade geometry; native goods retained'))
    for key in ('combat_elephant4','combat_elephant4_upgrade'):
        rows.append(row(key,OUT/'qualification/remaining_roster/nonhumanoid'/key/'v1/authoring.json',
                        EXPORT/'remaining_roster/nonhumanoid'/key/'v1/material-map.json',
                        'compatible stock combat-elephant geometry and motion'))
    key='siege_tower3'
    rows.append(row(key,OUT/'qualification/remaining_roster/nonhumanoid'/key/'v1/authoring.json',
                    EXPORT/'remaining_roster/nonhumanoid'/key/'v1/material-map-v3.json',
                    'exact attached English siege-tower body; native build/deploy state unchanged',
                    OUT/'qualification/remaining_roster/nonhumanoid'/key/'v1/material-map-v3-receipt.json'))
    write(ready,rows)
    unqualified=[]
    for key in ('ram3_candidate','springald3_candidate',
                'trebuchet4_counterweight_candidate','trebuchet4_traction_candidate'):
        unqualified.append(row(key,OUT/'qualification/remaining_roster/nonhumanoid'/key/'v1/authoring.json',
            EXPORT/'remaining_roster/nonhumanoid'/key/'v1/material-map-v3.json',
            'UNQUALIFIED English donor candidate; generic active render body and crew unresolved',
            OUT/'qualification/remaining_roster/nonhumanoid'/key/'v1/material-map-v3-receipt.json'))
    write(candidates,unqualified)
    print(json.dumps({'ready_registry':str(ready),'ready_models':len(rows),
                      'candidate_registry':str(candidates),'excluded_candidates':len(unqualified)}))

if __name__=='__main__':main()
