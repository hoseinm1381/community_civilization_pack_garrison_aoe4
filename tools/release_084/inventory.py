"""Current compiled consumer inventory, including variants and private aliases."""
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from pipeline import digest, save_json, guard
from providers import ROOT, OUT
from references import reference_category, active_speaker_edge

CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd


def walk(nodes, prefix=''):
    for n in nodes:
        path=prefix+'/'+str(n.key)
        yield path,n
        if isinstance(n.value,list):
            yield from walk(n.value,path)


def leaves(nodes):
    return [(p,n.value) for p,n in walk(nodes) if not isinstance(n.value,list)]


def role_for(name, speech):
    value=name.lower()
    if 'water_buffalo' in value:
        return None
    if 'war_elephant' in value:
        return None  # warelephant is not proof of a human speaker channel.
    for needle,role in [('skirmisher','SKIRMISHER'),('villager','CIV_M'),('scout','SCOUT'),
        ('official','OFFICIAL'),('trade_cart','TRADER'),('crossbow','CROSSBOW'),
        ('handcannon','GUNNER'),('horseman','CAVALRY'),('knight','CAVALRY'),
        ('spearman','INFANTRY'),('manatarms','INFANTRY'),('archer','ARCHER'),('monk','MONK'),
        ('no_than','SIEGE'),('bombard','SIEGE'),('culverin','SIEGE'),('mangonel','SIEGE'),
        ('ribauldequin','SIEGE'),('springald','SIEGE'),('ram_','SIEGE'),('trebuchet','SIEGE'),('siege_tower','SIEGE')]:
        if needle in value:return role
    return {'scout':'SCOUT','spearman':'INFANTRY','manatarms':'INFANTRY','archer':'ARCHER',
            'crossbowman':'CROSSBOW','handcannon':'GUNNER','horseman':'CAVALRY','knight':'CAVALRY',
            'monk':'MONK','official':'OFFICIAL','cart':'TRADER','ram':'SIEGE','springald':'SIEGE',
            'trebuchet':'SIEGE','siege_tower':'SIEGE'}.get(speech)


def main():
    guard()
    baseline=json.loads((OUT/'baseline.json').read_text())
    assert digest(baseline['sga'])==baseline['sga_sha256']
    base=Path(baseline['sga']).parent/'readback'
    verification=json.loads((base.parent/'verification.json').read_text())
    documents={}
    for p in (base/'attrib').rglob('*.rgd'):
        member=p.relative_to(base).as_posix()
        assert digest(p)==verification['member_sha256'][member]
        documents[member]=rgd.read(p.read_bytes())
    # Current official effective lists can expose gender/speaker branches absent
    # from the private child; their byte hashes were audited separately.
    official_file=OUT/'inventory/official-speakers.json'
    if official_file.exists():
        for row in json.loads(official_file.read_text())['rows']:
            p=Path(row.get('file',str(OUT/'official-speakers'/row['member'])))
            assert digest(p)==row['sha256']
            documents.setdefault(row['member'],rgd.read(p.read_bytes()))
    incoming={}
    lookup={(m.split('/')[1],Path(m).stem):d for m,d in documents.items()}
    for member,doc in documents.items():
        for path,node in walk(doc.nodes):
            if node.kind in ('List','List2'):
                vals={x.key:x.value for x in node.value}
                if vals.get('$PBGMAP')=='sbps':
                    name=vals.get('$PBGNAME','')
                    incoming.setdefault(name,[]).append(dict(member=member,path=path))
    source={}
    for p in (ROOT/'assets/attrib/instances/sbps').rglob('*.xml'):
        tree=ET.parse(p).getroot()
        parent=tree.find("instance_reference[@name='parent_pbg']")
        source[p.stem]=dict(path=str(p),sha256=digest(p),parent=parent.get('value','') if parent is not None else '')
    rows=[]
    for member,doc in documents.items():
        if not member.startswith('attrib/sbps/'):continue
        name=Path(member).stem
        flat=leaves(doc.nodes)
        default=[(p,v) for p,v in flat if p.startswith('/default/')]
        speech=next((v for p,v in default if p.endswith('/squad_name_code')),'')
        lineage=source.get(name,{}).get('parent','')
        role=role_for(name+' '+lineage,speech)
        refs=incoming.get(CFG['project_guid'].replace('-','')+':'+name,[])
        refs=[x for x in refs if x['member']!=member]
        female=next((v for p,v in default if p.endswith('/squad_female_chance')),0)
        # Private hashed aliases may retain a donor's old classification tag.
        # Explicit owning blueprint/parent tier outranks that stale tag.
        age_match=re.search(r'_([1-4])(?:_|$)',name+' '+lineage)
        tags=[v for p,v in default if p.endswith('/squad_type') and isinstance(v,str) and v.startswith('scar_age')]
        upgrades=[v for p,v in default if p.endswith('/upgrade_name/$PBGNAME')]
        tier=int(age_match[1]) if age_match else (int(tags[0][-1]) if tags else 1)
        if role in ['CIV_M','SCOUT','OFFICIAL','MONK','TRADER','SIEGE']:
            minimum={'MONK':3,'TRADER':2}.get(role,1)
            if role=='SIEGE':
                minimum=max([{'feudal_age':2,'castle_age':3,'imperial_age':4}.get(x,1) for x in upgrades] or [tier])
            ages=list(range(minimum,5));policy='player_age'
        else:ages=[tier];policy='unit_tier'
        roles=[role] if role else []
        attachment_speakers=[]
        pending=[(member,doc)];visited=set()
        while pending:
            current_member,current=pending.pop()
            if id(current) in visited:continue
            visited.add(id(current))
            for key,node in walk(current.nodes):
                if key.endswith('/attachment_speaker_code') and node.value:
                    attachment_speakers.append(dict(path=key,value=node.value))
                if node.kind in ('List','List2'):
                    vals={x.key:x.value for x in node.value}
                    category=reference_category(vals.get('$PBGMAP',''))
                    if active_speaker_edge(current_member.split('/')[1],key,category):
                        target=vals.get('$PBGNAME','').split(':')[-1].replace('\\','/').split('/')[-1]
                        linked=lookup.get((category,target))
                        if linked is not None:
                            linked_member=next(m for m,d in documents.items() if d is linked)
                            pending.append((linked_member,linked))
        if role and (female>0 or any('female' in x['value'].lower() for x in attachment_speakers)):
            roles.append('CIV_F' if role=='CIV_M' else role+'_F')
        speakers=[dict(path=p,value=v) for p,v in flat if p.endswith('/squad_speaker_code')]
        rows.append(dict(name=name,member=member,sha256=verification['member_sha256'][member],
            roles=roles,ages=ages,age_policy=policy,female_chance=female,incoming=refs,
            generation_admitted=bool(role and refs),speech=speakers,attachment_speakers=attachment_speakers,source=source.get(name),
            exclusion='animal_or_unverified_human_elephant_channel' if role is None else ('no_current_incoming_reference' if not refs else None)))
    naval={'fishing_boat':'NAVAL_FISH','trade_ship':'NAVAL_TRADE','transport_ship':'NAVAL_TRANSPORT',
           'combat_ship':'NAVAL_MILITARY','combat_warship':'NAVAL_MILITARY','war_galley':'NAVAL_MILITARY','fireship':'NAVAL_FIRE'}
    for p in (OUT/'official-naval/attrib/sbps/races/chinese').glob('*.rgd'):
        family=next((v for k,v in naval.items() if k in p.stem),None)
        if family is None:continue
        refs=incoming.get(p.stem,[])
        if not refs:continue
        doc=rgd.read(p.read_bytes());flat=leaves(doc.nodes)
        upgrades=[v for k,v in flat if k.startswith('/default/') and k.endswith('/upgrade_name/$PBGNAME')]
        minimum=max([{'feudal_age':2,'castle_age':3,'imperial_age':4}.get(x,1) for x in upgrades] or [1])
        rows.append(dict(name=p.stem,member=p.relative_to(OUT/'official-naval').as_posix(),sha256=digest(p),
            roles=[family],ages=list(range(minimum,5)),age_policy='player_age',female_chance=0,
            generation_admitted=True,incoming=refs,source='current_official_Attrib.sga',
            speech=[dict(path=k,value=v) for k,v in flat if k.endswith('/squad_speaker_code')],
            scope='Vietnam player only; shared stock owners require private derivation before suppression'))
    save_json(OUT/'inventory/consumers.json',dict(schema='ccp-084-current-voice-consumers/v1',
        baseline_sga_sha256=baseline['sga_sha256'],rows=rows,limits=['Static incoming references are not native availability proof.',
        'Naval role queues require current dock confirmation before suppression.','Elephant voices remain excluded pending human-channel proof.']))
    summary={}
    for row in rows:
        if row['generation_admitted']:
            for role in row['roles']:summary.setdefault(role,set()).update(row['ages'])
    print('084_CONSUMERS',len(rows),'ADMITTED',sum(x['generation_admitted'] for x in rows),
          'ROLE_AGES',json.dumps({k:sorted(v) for k,v in summary.items()}))


if __name__=='__main__':main()
