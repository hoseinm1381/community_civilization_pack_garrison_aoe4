"""Retain official native visual-upgrade analogues; no gameplay edits."""
from pathlib import Path
import json
import subprocess
import datetime
import xml.etree.ElementTree as ET
from common import ARCH, OUT, guard, owned, sha, write

MEMBERS = (
 'attrib/ebps/races/chinese/units/unit_villager_1_chi.rgd',
 'attrib/upgrade/races/japanese_ha_sen/research/clan_upgrades/upgrade_tanegashima_pavise_jpn_ha_sen.rgd',
 'attrib/abilities/always_on_abilities/japanese_ha_sen/tanegashima_tate_ability_jpn_ha_sen.rgd',
 'attrib/abilities/modal_abilities/french/deploy_pavise_fre.rgd',
)

def flatten(node, path=''):
    here = path+'/'+node.get('Key', node.tag)
    if 'Value' in node.attrib:
        yield {'path': here, 'value': node.get('Value'), 'type':node.get('Type')}
    for child in node:
        yield from flatten(child, here)

def run():
    guard()
    config = Path.home()/'AppData/Local/Garrison/Kit/game-assets.local.json'
    game = json.loads(config.read_text(encoding='utf-8'))
    archive = Path(game['game_root'])/'cardinal/archives/Attrib.sga'
    run_label = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    records = []
    for member in MEMBERS:
        dest = owned(OUT/'rattan-probe/runs'/run_label/Path(member).name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        xml = dest.with_suffix('.xml')
        for command in ([ARCH,'extract-member',archive,member,dest], [ARCH,'decode-rgd',dest,xml]):
            result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode:
                raise RuntimeError(result.stderr)
        leaves = list(flatten(ET.parse(xml).getroot()))
        selected = [r for r in leaves if any(t in (r['path']+' '+str(r['value'])).lower()
                    for t in ('animator','attachment','state_tree','tier_requirements',
                              'upgrade_target','apply_to_future','filter_conditions','pavise'))]
        records.append({'member':member, 'xml':str(xml), 'rgd_sha256':sha(dest),
                        'relevant_fields':selected})
    report = {'schema':'ccp-060-rattan-official-analogues/v1',
              'status':'research-only-not-a-qualified-switch', 'archive':str(archive),
              'records':records,
              'constraint':'Keep existing vn_ratten_shield_vit and rattan_armor.scar behavior; no unit replacement.'}
    write(OUT/'rattan-probe/report.json',report)
    print(json.dumps({'report':str(OUT/'rattan-probe/report.json'),
        'field_counts':{Path(r['member']).name:len(r['relevant_fields']) for r in records}},indent=2))

if __name__=='__main__':
    run()
