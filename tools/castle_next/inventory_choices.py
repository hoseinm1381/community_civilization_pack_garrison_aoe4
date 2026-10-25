"""Pin official Age-II/Castle-transition landmark choices from actor contracts.

Reads official Attrib.sga only. Actor names are a candidate list; reported
Castle-age status is determined from decoded actor requirements, never filename.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
from common import ROOT, OUT, CORE, CFG, guarded, sha, write

ARCH = Path(CFG['archive_tool'])
ATTRIB = Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga')
RACE_PATHS = {'english':'english','french':'french','chinese':'chinese','hre':'hre',
              'delhi':'sultanate','rus':'rus','mongols':'mongol'}

def run(args):
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode: raise RuntimeError(f'Failed {args}: {p.stdout[-1000:]} {p.stderr[-1000:]}')
    return p.stdout

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--verify-only', action='store_true'); args=ap.parse_args(); guarded()
    listed = json.loads(run([ARCH, 'list', ATTRIB, '--verify']))
    known = {r['path'].lower() for r in listed['members']}
    base = OUT / 'inventory' / 'choices'; rows=[]
    for race, native_race in RACE_PATHS.items():
        prefix=f'attrib/ebps/races/{native_race}/buildings/'
        members=sorted(r['path'] for r in listed['members'] if r['path'].lower().startswith(prefix)
                       and r['path'].lower().endswith('.rgd')
                       and re.search(r'/building_(?:landmark|wonder)_',r['path'].lower()))
        candidates=[]
        for member in members:
            stem = member.rsplit('/',1)[-1][:-4]
            if member.lower() not in known:
                rows.append({'race': race, 'member': member, 'status':'blocked', 'blocker':'official actor member absent'}); continue
            folder = base / race / stem; binary=folder/(stem+'.rgd'); xml=folder/(stem+'.xml')
            if not binary.exists():
                binary.parent.mkdir(parents=True,exist_ok=True); run([ARCH,'extract-member',ATTRIB,member,binary])
            if not xml.exists(): run([ARCH,'decode-rgd',binary,xml])
            root=ET.parse(xml).getroot()
            fields=[]
            for n in root.iter('RGDNode'):
                key=(n.get('Key') or '').lower(); val=n.get('Value')
                if val is not None and any(s in key for s in ('age','require','landmark','tier','unit_type','schema','attachments','animator_attachments','stamp','blueprint','state_tree')):
                    fields.append({'key':n.get('Key'),'value':val})
            # Actor requirements often serialize minimum_age/required_age under a
            # construction or requirement node. Preserve every age-bearing field.
            age_fields=[r for r in fields if 'age' in r['key'].lower() or r['key'].lower() in ('unit_type','required_age','minimum_age')]
            unit_types=sorted({r['value'] for r in fields if r['key'].lower()=='unit_type'})
            action_trees=sorted({r['value'] for r in fields if r['key'].lower()=='state_tree' and 'landmark_age_2' in r['value'].lower()})
            refs=[]
            for n in root.iter('RGDNode'):
                if n.get('Key') not in ('attachments','animator_attachments','schema','construction_stamp'): continue
                vals={c.get('Key'):c.get('Value') for c in n.findall('RGDNode')}
                if n.get('Key')=='construction_stamp': refs.append({'kind':'construction_stamp','value':n.get('Value')})
                elif vals.get('$PBGMAP') and vals.get('$PBGNAME'):
                    refs.append({'kind':n.get('Key'),'value':vals['$PBGMAP'].replace('\\','/')+'/'+vals['$PBGNAME']})
                elif n.get('Value'): refs.append({'kind':n.get('Key'),'value':n.get('Value')})
            # Require a decoded, explicit Castle-transition age contract; do not
            # infer it from the candidate filename.
            normalized=sorted({r['value'].lower() for r in age_fields})
            castle_markers=[v for v in unit_types if re.fullmatch(r'age2_landmark[12]',v)]
            row={'race':race,'member':member,'actor_sha256':sha(binary),'decoded_xml_sha256':sha(xml),
                         'decoded_xml':str(xml),'age_requirement_fields':age_fields,
                         'age_requirement_values':normalized,'castle_requirement_evidence':castle_markers,
                         'actor_unit_type_requirements':unit_types,
                         'castle_age_action_tree_evidence':action_trees,
                         'status':'qualified_actor_requirement' if castle_markers else 'excluded_by_actor_requirement',
                         'visual_owner_refs':refs,'native_runtime':'unverified'}
            candidates.append(row)
        selected=[r for r in candidates if r['castle_requirement_evidence']
                  and 'mobile_building' not in r['actor_unit_type_requirements']]
        rows.extend(selected if len(selected)==2 else candidates)
    report={'schema':'community-civilization-pack/castle-next-landmark-choices/v1',
            'source_archive':str(ATTRIB),'archive_sha256':sha(ATTRIB),'archive_index_sha256':listed['archive'].get('sha256'),
            'choice_count':sum(r.get('status')=='qualified_actor_requirement' for r in rows),'candidate_count':len(rows),'expected_choices':14,
            'status':'qualified' if len(rows)==14 and all(r.get('status')=='qualified_actor_requirement' for r in rows) else 'blocked',
            'selection_rule':'Keep the two stationary native actor unit_type values age2_landmark1/age2_landmark2 for each race; moving Mongol transforms also carry the landmark slot type but are filtered by their mobile_building actor requirement. The Castle transition is selected by actor requirements irrespective of filename age.',
            'choices':rows}
    target=OUT/'inventory'/'castle-age-choices.json'; write(target,report)
    print(json.dumps({'status':report['status'],'report':str(target),'choice_count':report['choice_count'],
                      'choices':[{'race':r['race'],'actor':r['member'],'unit_type':r['castle_requirement_evidence'],
                                  'schema_refs':[x['value'] for x in r.get('visual_owner_refs',[]) if x['kind']=='schema'],
                                  'attachments':[x['value'] for x in r.get('visual_owner_refs',[]) if x['kind']=='attachments']}
                                 for r in rows if r.get('status')=='qualified_actor_requirement']},indent=2))
    return 0 if report['status']=='qualified' else 2
if __name__=='__main__': raise SystemExit(main())
