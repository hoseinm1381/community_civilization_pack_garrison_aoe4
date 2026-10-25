"""Read-only closure of current squad/entity/attachment speech consumers."""
import json
from pathlib import Path
import sys
from pipeline import digest, guard, save_json
from providers import ROOT, OUT
from references import reference_category, active_speaker_edge


def iterate(nodes, indices=(), names=()):
    for index,node in enumerate(nodes):
        route=indices+(index,);path=names+(str(node.key),)
        yield route,'/'.join(path),node
        if isinstance(node.value,list):yield from iterate(node.value,route,path)


def main():
    guard()
    cfg=json.loads((ROOT/'workspace.json').read_text());sys.path.insert(0,cfg['garrison_extension'])
    from garrison_shared import rgd
    base=ROOT/'output/release_083/delivery/final-v2/readback'
    verification=json.loads((base.parent/'verification.json').read_text())
    documents={};lookup={}
    for category in ['sbps','ebps','attachments']:
        for p in (base/'attrib'/category).rglob('*.rgd'):
            member=p.relative_to(base).as_posix()
            assert digest(p)==verification['member_sha256'][member]
            doc=rgd.read(p.read_bytes());assert rgd.write(doc)==p.read_bytes()
            documents[member]=doc;lookup[(category,p.stem)]=member
    consumers=json.loads((OUT/'inventory/consumers.json').read_text())['rows']
    closure={};unresolved=[]
    for row in consumers:
        if not row['generation_admitted']:continue
        start=row['member']
        if start not in documents:
            unresolved.append(dict(consumer=row['name'],reason='shared official naval owner requires private derivation',member=start));continue
        pending=[start];visited=set()
        while pending:
            member=pending.pop()
            if member in visited:continue
            visited.add(member)
            closure.setdefault(member,set()).add(row['name'])
            doc=documents[member]
            for route,path,node in iterate(doc.nodes):
                if node.kind not in ('List','List2'):continue
                fields={x.key:x.value for x in node.value};category=reference_category(fields.get('$PBGMAP',''))
                if not active_speaker_edge(member.split('/')[1],path,category):continue
                reference=fields.get('$PBGNAME','')
                if not reference:continue
                target=reference.split(':')[-1].replace('\\','/').split('/')[-1]
                found=lookup.get((category,target))
                if found:pending.append(found)
                else:unresolved.append(dict(consumer=row['name'],from_member=member,path=path,
                                            category=category,reference=reference,reason='external resource not yet audited'))
    changes=[];consumers_by_resource={}
    for member,owners in sorted(closure.items()):
        fields=[]
        for route,path,node in iterate(documents[member].nodes):
            if node.key in ['speech_ext','squad_speech_ext'] and node.kind in ('List','List2'):
                fields.append(dict(route=list(route),path=path,operation='remove_effective_speech_table',kind=node.kind))
            if node.key=='attachment_speaker_code' and node.kind=='CString' and node.value:
                fields.append(dict(route=list(route),path=path,operation='clear_private_speaker_override',
                                   kind=node.kind,before=node.value,after=''))
        if fields:changes.append(dict(member=member,sha256=verification['member_sha256'][member],
            owning_consumers=sorted(owners),fields=fields,ownership_admission='pending complete incoming-reference audit'))
        consumers_by_resource[member]=sorted(owners)
    # Enumerate incoming references from every owning resource, including buildings,
    # so a shared attachment cannot be mistaken for a private unit-only list.
    incoming={member:[] for member in closure}
    for member,doc in documents.items():
        for route,path,node in iterate(doc.nodes):
            if node.kind not in ('List','List2'):continue
            fields={x.key:x.value for x in node.value};category=reference_category(fields.get('$PBGMAP',''))
            reference=fields.get('$PBGNAME','')
            if category not in ('ebps','attachments') or not reference:continue
            target=lookup.get((category,reference.split(':')[-1].replace('\\','/').split('/')[-1]))
            if target in incoming:incoming[target].append(dict(member=member,path=path,reference=reference))
    for change in changes:
        outside=[x for x in incoming[change['member']] if x['member'] not in closure]
        change['outside_closure_incoming']=outside
        change['ownership_admission']='requires_private_copy' if outside else 'all_packaged_incoming_owners_covered'
    save_json(OUT/'inventory/speech-closure.json',dict(schema='ccp-084-speech-closure/v1',
        candidate_changes=changes,unresolved=unresolved,closure=consumers_by_resource,
        limits=['No source or compiled field has been changed.','Shared official resources require separate private derivation.',
                'Candidate speech suppression is blocked until complete audio and ownership coverage.']))
    print('084_SPEECH_CLOSURE',len(closure),'RESOURCES',len(changes),'CANDIDATE_MEMBERS',
          sum(len(x['fields']) for x in changes),'FIELDS',len(unresolved),'EXTERNAL_EDGES')


if __name__=='__main__':main()
