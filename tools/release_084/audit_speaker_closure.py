"""Read-only recursive actor/attachment speaker audit against current official bytes."""
from collections import defaultdict
import argparse
import json
from pathlib import Path
import subprocess
import sys

from pipeline import guard,digest,save_json
from providers import ROOT,OUT
from references import active_speaker_edge,reference_category


def main():
    guard()
    parser=argparse.ArgumentParser();parser.add_argument('--include-production-monk',action='store_true');args=parser.parse_args()
    cfg=json.loads((ROOT/'workspace.json').read_text())
    sys.path.insert(0,cfg['garrison_extension'])
    from garrison_shared import rgd
    from speech_inventory import iterate
    evidence=OUT/'inventory'/('speaker-closure-v3' if args.include_production_monk else 'speaker-closure-v2')
    evidence.mkdir(parents=True,exist_ok=True)
    frozen=json.loads((OUT/'inventory/official-lookup.json').read_text())
    archive=Path(frozen['archive'])
    if digest(archive)!=frozen['sha256']:raise RuntimeError('Official archive changed; refresh the donor baseline explicitly')
    listing_file=evidence/'official-list.json'
    if listing_file.exists():listing=json.loads(listing_file.read_text())
    else:
        listing=json.loads(subprocess.check_output([cfg['archive_tool'],'list',str(archive),'--verify']))
        save_json(listing_file,listing)
    if not listing['archive']['verification']['verified']:raise RuntimeError('Official archive integrity failed')
    official_lookup=defaultdict(list)
    for row in listing['members']:
        member=row['path'];parts=member.split('/')
        if len(parts)>2 and parts[0]=='attrib':official_lookup[(parts[1],Path(member).stem)].append(member)
    base=ROOT/'output/release_083/delivery/final-v2/readback'
    proof=json.loads((base.parent/'verification.json').read_text())
    files={};lookup={};documents={}
    def admit(member,path,expected):
        if digest(path)!=expected:raise RuntimeError('Changed retained donor '+str(path))
        key=(member.split('/')[1],Path(member).stem)
        if key in lookup and lookup[key]!=member:raise RuntimeError('Ambiguous retained resource '+str(key))
        files[member]=dict(file=str(path),sha256=expected)
        lookup[key]=member
    for category in ['sbps','ebps','attachments']:
        for path in (base/'attrib'/category).rglob('*.rgd'):
            member=path.relative_to(base).as_posix();admit(member,path,proof['member_sha256'][member])
    prior=json.loads((OUT/'inventory/official-speakers.json').read_text())
    for row in prior['rows']:admit(row['member'],Path(row['file']),row['sha256'])
    consumer_file=OUT/'inventory'/('consumers-complete.json' if args.include_production_monk else 'consumers.json')
    consumers=json.loads(consumer_file.read_text())['rows']
    if args.include_production_monk:
        for row in json.loads((OUT/'inventory/production-routes-v2/donors.json').read_text()):
            admit(row['member'],Path(row['file']),row['sha256'])
    for row in consumers:
        if row.get('source')=='current_official_Attrib.sga':admit(row['member'],Path(row.get('source_file',str(OUT/'official-naval'/row['member']))),row['sha256'])
    for row in json.loads((evidence/'downloaded.json').read_text()) if (evidence/'downloaded.json').exists() else []:
        admit(row['member'],Path(row['file']),row['sha256'])
    # Include inactive packaged human owners as audit roots only. This does not
    # admit them for generation or suppress any native speech.
    owners=defaultdict(set)
    for row in consumers:
        if row['roles']:owners[row['member']].add(row['name'])
    edges=[];unresolved=[];processed=set();downloaded=[]
    while True:
        pending=[m for m in owners if m not in processed]
        if not pending:break
        wanted=set()
        for member in pending:
            doc=documents.setdefault(member,rgd.read(Path(files[member]['file']).read_bytes()))
            for route,path,node in iterate(doc.nodes):
                if node.kind not in ('List','List2'):continue
                fields={n.key:n.value for n in node.value};category=reference_category(fields.get('$PBGMAP',''))
                if not active_speaker_edge(member.split('/')[1],path,category):continue
                reference=fields.get('$PBGNAME','')
                if not reference:continue
                key=(category,reference.split(':')[-1].replace('\\','/').split('/')[-1])
                target=lookup.get(key)
                if not target:
                    matches=official_lookup.get(key,[])
                    if len(matches)!=1:
                        unresolved.append(dict(member=member,path=path,reference=reference,matches=matches));continue
                    wanted.add(matches[0]);target=matches[0]
                edges.append(dict(member=member,path=path,target=target,reference=reference))
                owners[target].update(owners[member])
            processed.add(member)
        if wanted:
            folder=evidence/'official'
            command=[cfg['archive_tool'],'extract',str(archive),str(folder)]
            for member in sorted(wanted):command+=['--member',member]
            result=json.loads(subprocess.check_output(command))
            save_json(evidence/f'extraction-{len(processed)}.json',result)
            for member in sorted(wanted):
                path=folder/member;sha=digest(path);admit(member,path,sha)
                downloaded.append(dict(member=member,file=str(path),sha256=sha))
            # Preserve the entire cumulative receipt across subsequent runs.
            old=json.loads((evidence/'downloaded.json').read_text()) if (evidence/'downloaded.json').exists() else []
            save_json(evidence/'downloaded.json',list({r['member']:r for r in old+downloaded}.values()))
        print('SPEAKER_CLOSURE_AUDIT',len(processed),'resources;',len(wanted),'new official donors',flush=True)
    # Propagate owners through cycles and branches discovered in later passes.
    changed=True
    while changed:
        changed=False
        for edge in edges:
            before=len(owners[edge['target']]);owners[edge['target']].update(owners[edge['member']])
            changed |= len(owners[edge['target']])!=before
    rows=[]
    for member in sorted(processed):
        doc=documents[member]
        fields=[dict(path=path,kind=node.kind,value=node.value) for _,path,node in iterate(doc.nodes)
                if node.key in ['attachment_speaker_code','squad_speaker_code','speaker','speaker_code'] and not isinstance(node.value,list)]
        tables=[path for _,path,node in iterate(doc.nodes) if node.key in ['speech_ext','squad_speech_ext'] and node.kind in ['List','List2']]
        rows.append(dict(member=member,**files[member],owners=sorted(owners[member]),speaker_fields=fields,
                         nonempty_speaker_fields=[f for f in fields if f['value']],speech_tables=tables,
                         source='private_083' if member in proof['member_sha256'] else 'current_official'))
    save_json(evidence/'audit.json',dict(schema='ccp-084-recursive-speaker-closure/v2',official_archive=str(archive),
              official_archive_sha256=frozen['sha256'],rows=rows,edges=edges,unresolved=unresolved,
              source_modified=False,native_suppression=False,
              limits=['Includes inactive human roots for ownership audit only.','No runtime availability or audible overlap proof.',
                      'Tier replacements are inventoried separately; parent inheritance is already resolved in native RGDs.']))
    print('RECURSIVE_SPEAKER_AUDIT',len(rows),'resources',len(unresolved),'unresolved',flush=True)


if __name__=='__main__':main()
