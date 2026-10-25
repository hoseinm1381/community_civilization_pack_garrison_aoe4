"""Typed, reversible voice overlays on an isolated compiled baseline.

Full output is gated on complete bank coverage. --plan-only never mutes anything.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from pipeline import guard,digest,save_json
from providers import ROOT,OUT
from references import reference_category
from speech_inventory import iterate
from voice_scope import require_stock_effort_preservation


def patch_nodes(nodes,speech_tables,speaker_fields,rewires):
    changes=[]
    def visit(children,prefix=''):
        index=0
        while index<len(children):
            node=children[index];path=(prefix+'/'+str(node.key)).strip('/')
            if path in speech_tables:
                if node.key not in {'speech_ext','squad_speech_ext'} or not isinstance(node.value,list):
                    raise ValueError('Unexpected native speech table '+path)
                changes.append(dict(op='remove',path=path,parent=children,index=index,node=node))
                children.pop(index);continue
            if path in speaker_fields and node.value:
                if node.key!='attachment_speaker_code' or node.kind!='CString':
                    raise ValueError('Unexpected attachment speech field '+path)
                changes.append(dict(op='set',path=path,node=node,before=node.value,after=''))
                node.value=''
            if isinstance(node.value,list):
                fields={n.key:n for n in node.value}
                category=fields.get('$PBGMAP');name=fields.get('$PBGNAME')
                if category and name and node.key!='parent_pbg':
                    # Explicit namespaces identify another owning resource;
                    # preserve them. Stock references may use native path forms.
                    stem=name.value.replace('\\','/').split('/')[-1] if ':' not in name.value else name.value
                    target=rewires.get((reference_category(category.value),stem))
                    if target:
                        if name.kind!='CString':raise ValueError('Unexpected native reference type')
                        changes.append(dict(op='set',path=path+'/$PBGNAME',node=name,before=name.value,after=target))
                        name.value=target
                visit(node.value,path)
            index+=1
    visit(nodes)
    return changes


def undo_changes(changes):
    for change in reversed(changes):
        if change['op']=='set':change['node'].value=change['before']
        else:change['parent'].insert(change['index'],change['node'])


def public_changes(changes):
    return [{k:v for k,v in c.items() if k not in {'node','parent'}} for c in changes]


def verify_speech_removed(nodes,tables,fields):
    for _,path,node in iterate(nodes):
        if path in tables:raise RuntimeError('Native speech table survived overlay')
        if path in fields and node.value:raise RuntimeError('Attachment speaker survived overlay')


def main():
    guard();parser=argparse.ArgumentParser();parser.add_argument('--plan-only',action='store_true')
    parser.add_argument('--label',required=True);parser.add_argument('--bank',type=Path,default=OUT/'integration/bank-complete')
    args=parser.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,50}',args.label):raise ValueError('Invalid immutable overlay label')
    cfg=json.loads((ROOT/'workspace.json').read_text());guid=cfg['project_guid'].replace('-','')
    identities_file=OUT/'integration/voice-identities-complete.json'
    identities=json.loads(identities_file.read_text())
    audit=json.loads((OUT/'integration/voice-identities-complete-audit.json').read_text())
    if not audit['passed'] or audit['receipt_sha256']!=digest(identities_file):raise RuntimeError('Identity audit differs')
    for part in identities['component_receipts']:
        if digest(part['file'])!=part['sha256']:raise RuntimeError('Identity component changed')
    consumers_file=OUT/'inventory/consumers-complete.json'
    consumers=json.loads(consumers_file.read_text())['rows'];active={r['name'] for r in consumers if r['generation_admitted']}
    closure_file=OUT/'inventory/speaker-closure-v3/audit.json';closure=json.loads(closure_file.read_text())
    if closure['unresolved']:raise RuntimeError('Unresolved speaker ownership')
    speakers={r['member']:r for r in closure['rows'] if active.intersection(r['owners']) and (r['speech_tables'] or r['nonempty_speaker_fields'])}
    derived={r['source']:r for r in identities['identities']}
    for member,row in speakers.items():
        if row['source']=='current_official' and member not in derived:raise RuntimeError('Shared speaker lacks private identity: '+member)
    rewires={(r['category'],Path(r['source']).stem):guid+':'+r['name'] for r in identities['identities']}
    if not args.plan_only:
        bank=json.loads((args.bank/'receipt.json').read_text())
        if not bank['complete'] or bank['partial_preview']:raise RuntimeError('Incomplete consumers must retain original speech')
        if bank['identity_receipt_sha256']!=digest(identities_file) or bank['consumer_inventory_sha256']!=digest(consumers_file):
            raise RuntimeError('Bank ownership proof changed')
        if bank['bank_sha256']!=digest(args.bank/'voice_bank_084.scar'):raise RuntimeError('Bank bytes changed')
        if bank['codec']!='vorbis-64k-mono-48k':raise RuntimeError('Final package requires compressed voices')
        stock_effort_proof=None
        if bank.get('delivery_scope_sha256'):
            from stock_efforts import load_stock_efforts
            stock=load_stock_efforts()
            preservation=OUT/'integration/stock-efforts-v1/receipt.json'
            if bank.get('stock_effort_receipt_sha256')!=digest(preservation):raise RuntimeError('Stock effort bank proof differs')
            stock_effort_proof=dict(stock_effort_preservation_complete=True,receipt_sha256=digest(preservation),
                    native_sources=len(stock['exports']),aliases=stock['aliases'],native_scheduling_preserved=False)
            require_stock_effort_preservation(stock_effort_proof)
        from native_reference_proof import audit as audit_native_reference
        native_proof=audit_native_reference()
    dest=OUT/'integration'/args.label
    if dest.exists():raise FileExistsError('Preserve previous overlays')
    dest.mkdir(parents=True)
    plan=dict(identity_receipt_sha256=digest(identities_file),consumer_inventory_sha256=digest(consumers_file),
              closure_sha256=digest(closure_file),human_consumers=len(active),speaker_resources=len(speakers),
              private_identities=len(derived),reference_policy='Typed PBGMAP/PBGNAME refs only; parent metadata and AI aliases remain original',
              suppressed_resources=sorted(speakers),compressed_audio=True,final_zip_limit_bytes=400000000,
              active_source_modified=False,plan_only=args.plan_only)
    save_json(dest/'plan.json',plan)
    if args.plan_only:
        print('VOICE_OVERLAY_PLAN_ONLY',len(speakers),'owners; no native speech changed',flush=True);return
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    baseline=ROOT/'output/release_083/delivery/final-v2'
    proof=json.loads((baseline/'verification.json').read_text())
    if digest(baseline/'community_civilization_pack.sga')!=proof['sga_sha256']:raise RuntimeError('083 owning archive changed')
    sources={}
    for member,sha in proof['member_sha256'].items():
        if not member.startswith('attrib/') or not member.endswith('.rgd'):continue
        path=baseline/'readback'/member
        if digest(path)!=sha:raise RuntimeError('083 compiled baseline readback changed: '+member)
        sources[member]=(path,speakers.get(member))
    for row in identities['identities']:
        if digest(row['compiled'])!=row['compiled_sha256']:raise RuntimeError('Derived payload changed')
        family='attachments/attachment_lists' if row['category']=='attachments' else row['category']
        member='attrib/'+family+'/vietnam/release_084/'+row['name']+'.rgd'
        if member in sources or member in proof['member_sha256']:raise RuntimeError('New identity collides with baseline member')
        sources[member]=(Path(row['compiled']),speakers.get(row['source']))
    payload={};deltas=[];changed_speakers=set()
    for member,(path,speaker) in sources.items():
        original=path.read_bytes();doc=rgd.read(original)
        tables=set(speaker['speech_tables']) if speaker else set()
        fields={f['path'] for f in speaker['nonempty_speaker_fields']} if speaker else set()
        changes=patch_nodes(doc.nodes,tables,fields,rewires)
        encoded=rgd.write(doc)
        # Verify edited readback, then reverse only the logged operations.
        reread=rgd.read(encoded)
        verify_speech_removed(reread.nodes,tables,fields)
        undo_changes(changes)
        if rgd.write(doc)!=original:raise RuntimeError('Presentation overlay exact-byte undo failed: '+member)
        if not changes and member in proof['member_sha256']:continue
        target=dest/'payload'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encoded)
        payload[member]=dict(file=str(target),sha256=digest(target))
        deltas.append(dict(member=member,source=str(path),source_sha256=hashlib.sha256(original).hexdigest(),
                          after_sha256=digest(target),changes=public_changes(changes),exact_byte_undo=True))
        if speaker:changed_speakers.add(speaker['member'])
    if changed_speakers!=set(speakers):raise RuntimeError('Not every admitted speaker was privately covered')
    save_json(dest/'payload-map.json',payload)
    save_json(dest/'receipt.json',dict(**plan,payloads=len(payload),deltas=deltas,
              native_reference_proof=native_proof,
              stock_effort_proof=stock_effort_proof,
              baseline_archive_sha256=proof['sga_sha256'],bank_receipt_sha256=digest(args.bank/'receipt.json'),
              all_nonpresentation_bytes_restorable=True,native_compilation_of_suppression=False,
              native_voice_playback=False,installed=False,published=False))
    print('VOICE_OVERLAY_PREPARED',len(payload),'compiled payloads; all changes exactly reversible',flush=True)


if __name__=='__main__':main()
