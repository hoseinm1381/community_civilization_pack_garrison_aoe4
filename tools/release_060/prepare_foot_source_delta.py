"""Stage byte-narrow private visual bindings; never writes active assets.

Qualified art and complete roster coverage remain separate delivery gates.
"""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from common import CFG, OUT, ROOT, guard, owned, read, sha, write
from unit_binding_plan import PLAN, EVIDENCE, prepare_plan

DEST=OUT/'integration/private-foot-source-overlay'
GUID=CFG['project_guid'].replace('-','')


def transform(original,changes):
    """Preserve every byte except enumerated instance-reference attributes."""
    text=original.decode('utf-8')
    proofs=[]
    for change in changes:
        count=0
        def replace(match):
            nonlocal count
            tag=match[0];element=ET.fromstring(tag)
            if element.get('name')!=change['field'] or element.get('value')!=change['before']:
                return tag
            if element.get('mod')!=change['before_mod']:
                raise ValueError('Reference owner differs from pinned source')
            new=tag.replace('value="'+change['before']+'"',
                            'value="'+change['after']+'"',1)
            if element.get('mod') is None:
                new=new.replace('/>',' mod="'+GUID+'"/>',1)
            else:new=new.replace('mod="'+element.get('mod')+'"','mod="'+GUID+'"',1)
            count+=1;proofs.append({'before_element':tag,'after_element':new})
            return new
        text=re.sub(r'<instance_reference\b[^<>]*/>',replace,text)
        if count!=change['expected_count']:
            raise ValueError(f'Visual replacement count {count} != {change["expected_count"]}')
    restored=text
    for proof in reversed(proofs):
        restored=restored.replace(proof['after_element'],proof['before_element'],1)
    if restored.encode('utf-8')!=original:raise ValueError('Nonvisual source bytes changed')
    ET.fromstring(text)
    return text.encode('utf-8'),proofs


def main():
    guard();plan=prepare_plan()
    identities=read(EVIDENCE/'registered-identities.json')
    if identities['plan_sha256']!=sha(PLAN):raise ValueError('Registered identity plan drift')
    if DEST.exists():raise FileExistsError('Preserve prior source overlay')
    by_slug={r['slug']:r for r in identities['entries']}
    actors={}
    for row in plan['entries']:
        for node in row['actor_consumers']:
            relative=node['source']['asset_relative_path']
            actor=actors.setdefault(relative,{'source':node['source'],'changes':{}})
            tree=ET.parse(node['source']['path'])
            xpath=node['node_path'].removeprefix('/instance/').replace(' and ','][')
            matches=tree.getroot().findall(xpath)
            if len(matches)!=1 or matches[0].get('value')!=node['before_value']:
                raise ValueError('Exact source node no longer matches inventory')
            key=(node['field'],node['before_value'],node['mod'])
            edit=actor['changes'].setdefault(key,{'field':node['field'],
                'before':node['before_value'],'before_mod':node['mod'],
                'after':row['private_reference'].replace('/','\\'),'expected_count':0})
            edit['expected_count']+=1
    rows=[]
    for relative,actor in actors.items():
        pinned=Path(actor['source']['path']);active=ROOT/'assets'/relative
        if sha(pinned)!=actor['source']['sha256'] or active.read_bytes()!=pinned.read_bytes():
            raise ValueError('Active source drift, resolve deliberately: '+relative)
        changed,proofs=transform(pinned.read_bytes(),list(actor['changes'].values()))
        target=owned(DEST/'assets'/relative);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(changed)
        rows.append({'asset_relative_path':relative,'source_sha256':sha(pinned),
                     'staged_path':str(target),'staged_sha256':sha(target),'edits':proofs})
    for row in plan['entries']:
        identity=by_slug[row['slug']]
        tree=ET.Element('instance',version='2',description='Private 0.6.0 Vietnamese unit visual identity',
                        template=r'attachments\attachment_lists')
        ET.SubElement(tree,'uniqueid',name='pbgid',value=str(identity['pbgid']))
        ET.SubElement(tree,'instance_reference',name='parent_pbg',
                      value=row['stock_member'].removeprefix('attrib/').removesuffix('.rgd').replace('/','\\'))
        ET.indent(tree,space='\t')
        relative='attrib/instances/'+row['private_reference']+'.xml'
        target=owned(DEST/'assets'/relative);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n')
        rows.append({'asset_relative_path':relative,'source_sha256':None,
                     'staged_path':str(target),'staged_sha256':sha(target),'private_pbgid':identity['pbgid']})
    receipt=DEST/'source-delta.json'
    write(receipt,{'schema':'ccp-060-private-foot-source-delta/v1',
                   'status':'staged_identity_references_only_no_art_activation',
                   'plan_sha256':sha(PLAN),'identity_receipt_sha256':sha(EVIDENCE/'registered-identities.json'),
                   'existing_actor_count':len(actors),'new_private_attachment_count':len(plan['entries']),
                   'files':rows,'active_source_modified':False,
                   'limits':'Staged source only. Art, native compiled bindings, full roster coverage and final archive still required.'})
    print(json.dumps({'status':'staged','actors':len(actors),'private_attachments':len(plan['entries']),
                      'receipt':str(receipt)},indent=2))


if __name__=='__main__':main()
