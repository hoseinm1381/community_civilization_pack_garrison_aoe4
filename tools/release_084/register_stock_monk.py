"""Record the default Pagoda's inherited stock monk as an explicit voice alias."""
import copy
import json
from pathlib import Path
import sys
from pipeline import guard,digest,save_json
from providers import ROOT,OUT


def main():
    guard();cfg=json.loads((ROOT/'workspace.json').read_text());sys.path.insert(0,cfg['garrison_extension'])
    from garrison_shared import rgd
    from inventory import leaves
    audit_file=OUT/'inventory/production-routes-v2/audit.json';audit=json.loads(audit_file.read_text())
    if audit['unresolved']:raise RuntimeError('Default production routes remain unresolved')
    member='attrib/sbps/races/chinese/unit_monk_3_chi.rgd'
    row=next(r for r in audit['additional_squad_consumers'] if r['member']==member)
    if digest(row['file'])!=row['sha256']:raise RuntimeError('Changed stock-monk donor')
    flat=leaves(rgd.read(Path(row['file']).read_bytes()).nodes)
    female=next(v for k,v in flat if k=='/default/squad_female_chance' or k.endswith('/squad_female_chance') and k.startswith('/default/'))
    if female!=0:raise RuntimeError('Review unexpected monk gender variants')
    source=json.loads((OUT/'inventory/consumers.json').read_text());result=copy.deepcopy(source)
    incoming=[dict(member=e['member'],path='/'+e['path'],route=e['route']) for e in audit['edges']
              if e['target']==member and '/vietnam/'in e['member']]
    if len(incoming)!=1 or '/pagodas/'not in incoming[0]['member']:raise RuntimeError('Unexpected inherited monk production scope')
    extra=dict(name='unit_monk_3_chi',member=member,sha256=row['sha256'],roles=['MONK'],ages=[3,4],
               age_policy='player_age',female_chance=female,generation_admitted=True,incoming=incoming,
               source='current_official_Attrib.sga',source_file=row['file'],
               speech=[dict(path=k,value=v) for k,v in flat if k.endswith('/squad_speaker_code')],
               voice_alias=dict(role='MONK',ages=[3,4],reason='Same Vietnamese monk character and role; independent existing role recordings already cover these ages.'),
               private_derivation_status='pending additional verified stock squad and actor identities',
               scope='Private Pagoda default spawner only; preserve stock monk artwork, costs, requirements and abilities.')
    result['rows'].append(extra)
    result.update(schema='ccp-084-current-voice-consumers/v2',production_audit_sha256=digest(audit_file),
                  original_inventory_sha256=digest(OUT/'inventory/consumers.json'),
                  animal_exclusions=['vn_unit_water_buffalo_vit','vn_unit_war_elephant_handcannon_4_vit_free'],
                  campaign_only_exclusion='unit_naval_scout_2_chi is referenced only by the Dock campaign table; not an ordinary default-mode voice consumer.')
    target=OUT/'inventory/consumers-complete.json'
    if target.exists() and json.loads(target.read_text())!=result:raise RuntimeError('Preserve consumer reconciliation revision')
    save_json(target,result)
    print('RECONCILED_DEFAULT_HUMAN_CONSUMERS',sum(r['generation_admitted'] for r in result['rows']),
          'new synthesis jobs: 0; additional native identity pair still required',flush=True)


if __name__=='__main__':main()
