"""Selectively read current official actor/list donors; never modify game files."""
import json
from pathlib import Path
import subprocess
import sys
from pipeline import digest, guard, save_json
from providers import ROOT, OUT


def main():
    guard()
    cfg=json.loads((ROOT/'workspace.json').read_text())
    archive=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
    closure=json.loads((OUT/'inventory/speech-closure.json').read_text())
    wanted={(x['category'],x['reference'].replace('\\','/').split('/')[-1]) for x in closure['unresolved'] if x.get('reference')}
    # Include all seven current ship actors for the private ownership plan.
    naval=json.loads((OUT/'inventory/consumers.json').read_text())['rows']
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    from speech_inventory import iterate
    for row in naval:
        if row.get('source')!='current_official_Attrib.sga':continue
        doc=rgd.read((OUT/'official-naval'/row['member']).read_bytes())
        for route,path,node in iterate(doc.nodes):
            if '/squad_loadout_ext/' not in '/'+path or node.kind not in ('List','List2'):continue
            fields={x.key:x.value for x in node.value}
            if fields.get('$PBGMAP')=='ebps' and fields.get('$PBGNAME'):
                wanted.add(('ebps',fields['$PBGNAME'].replace('\\','/').split('/')[-1]))
    listing=json.loads(subprocess.check_output([cfg['archive_tool'],'list',str(archive),'--verify']))
    matches={key:[] for key in wanted}
    for member in listing['members']:
        path=member['path']
        parts=path.split('/')
        if len(parts)>2 and parts[0]=='attrib':
            key=(parts[1],Path(path).stem)
            if key in matches:matches[key].append(path)
    ambiguous={str(k):v for k,v in matches.items() if len(v)!=1}
    save_json(OUT/'inventory/official-lookup.json',dict(archive=str(archive),sha256=digest(archive),
        verification=listing['archive']['verification'],matches={str(k):v for k,v in matches.items()},unresolved=ambiguous))
    selected=sorted({v[0] for v in matches.values() if len(v)==1})
    target=OUT/'official-speakers'
    revision=1
    while target.exists():
        revision+=1;target=OUT/f'official-speakers-v{revision}'
    command=[cfg['archive_tool'],'extract',str(archive),str(target)]
    for member in selected:command+=['--member',member]
    result=json.loads(subprocess.check_output(command))
    save_json(OUT/'inventory/official-extraction.json',result)
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    rows=[]
    for member in selected:
        path=target/member;doc=rgd.read(path.read_bytes())
        fields=[dict(path=p,kind=n.kind,value=n.value) for p,n in rgd.flatten(doc.nodes)
                if n.key in ['attachment_speaker_code','squad_speaker_code','speaker','speaker_code'] and not isinstance(n.value,list)]
        rows.append(dict(member=member,file=str(path),sha256=digest(path),speaker_fields=fields,
                         nonempty_speaker_fields=[x for x in fields if x['value']]))
    save_json(OUT/'inventory/official-speakers.json',dict(rows=rows,lookup_ambiguities=ambiguous))
    print('084_OFFICIAL_SPEAKER_AUDIT',len(rows),'DONORS',sum(bool(x['nonempty_speaker_fields']) for x in rows),
          'WITH_SPEAKER_OVERRIDES',len(ambiguous),'UNRESOLVED_NAMES')


if __name__=='__main__':main()
