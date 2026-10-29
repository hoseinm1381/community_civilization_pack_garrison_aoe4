"""Apply the 2026-10-29 private construction-time repair from current evidence.

Run inspect_korea_construction.py first. Does not create or alter identities.
"""
import gzip, hashlib, json, re
from pathlib import Path
import xml.etree.ElementTree as E
from korea_resource_contract import semantic_digest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'work/korea_construction_20261029'
OFFICIAL = json.loads((OUT/'official.json').read_text())
XPATH = "list/template_reference[@value='ebpextensions\\cost_ext']/group[@name='time_cost']/float[@name='time_seconds']"

def official_time(key):
    tree = E.fromstring(OFFICIAL['instances\\'+key+'.xml'])
    value = tree.find(XPATH)
    if value is not None:
        return key, value.get('value')
    return official_time(tree.find("instance_reference[@name='parent_pbg']").get('value'))

def main():
    ledger = ROOT/'docs/korea-construction.json'
    if ledger.exists():
        raise SystemExit('Repair ledger already exists; use tests to verify it instead of repeating the migration.')
    changes=[]
    for path in sorted((ROOT/'assets/attrib/instances/ebps/korea').glob('kr_building*chi_ha_01.xml')):
        raw=path.read_bytes(); tree=E.fromstring(raw); nodes=tree.findall(XPATH)
        if not nodes or path.stem in (
            'kr_building_dynasty_pagoda_control_chi_ha_01',
            'kr_building_landmark_age1_meditation_gardens_control_chi_ha_01'):
            continue  # Korean Seowon and its retained 30-second academy.
        assert len(nodes)==1, path
        before=nodes[0].get('value')
        if 'landmark_age' in path.stem:
            # Korean roles differ from their visual donors: age1_prefecture is
            # Stone Pagoda (Feudal), shaolin/white_deer are Castle landmarks.
            age=1 if 'age1_' in path.stem else 2 if 'age2_' in path.stem else 3
            evidence, after=official_time('ebps\\races\\core\\buildings\\building_wonder_age'+str(age))
        else:
            evidence, after=official_time(tree.find("instance_reference[@name='parent_pbg']").get('value'))
        if before==after:continue
        relative=path.relative_to(ROOT).as_posix()
        snapshot=OUT/'before'/relative
        snapshot.parent.mkdir(parents=True,exist_ok=True)
        snapshot.with_suffix('.xml.gz').write_bytes(gzip.compress(raw))
        # Patch only the one existing scalar; preserve exact XML serialization.
        pattern=rb'(<float name="time_seconds" value=")'+before.encode()+rb'("[^>]*/>)'
        updated,count=re.subn(pattern,lambda m:m[1]+after.encode()+m[2],raw)
        assert count==1, path
        restored=E.fromstring(updated); restored.find(XPATH).set('value',before)
        assert semantic_digest(restored)==semantic_digest(tree)
        path.write_bytes(updated)
        changes.append({'blueprint':'ebps\\korea\\'+path.stem,'file':relative,'xpath':XPATH,
                        'before':before,'after':after,'official_time_owner':evidence,
                        'before_sha256':hashlib.sha256(raw).hexdigest(),
                        'before_semantic_sha256':semantic_digest(tree)})
    ledger.write_text(json.dumps({'reason':'Owner-reported inherited construction inflation; normal single-builder times',
        'official_archive':str(__import__('official_archive').archive_path()),
        'changes':changes},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({x['blueprint'].split('\\')[-1]:[x['before'],x['after']] for x in changes},indent=2))

if __name__=='__main__':main()
