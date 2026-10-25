"""Stage first-ten private native body bindings from qualified media only.

No active source or final archive writes. Original native list metadata and all
animation owners survive exactly; generated identity scaffolds are never used.
"""
import argparse
import json
from pathlib import Path
import sys
from common import CFG, OUT, RECIPES, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd
from ranged_media_pairs_060 import qualify_geometry_material_pair
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',type=Path,required=True)
    parser.add_argument('--label',required=True)
    args=parser.parse_args();guard()
    if not args.label.isalnum():raise ValueError('Use a unique alphanumeric stage label')
    selection=read(owned(args.selection))
    plan_path=RECIPES/'foot-body-private-binding-plan.json';plan=read(plan_path)
    ids_path=OUT/'integration/private-foot-identities/registered-identities.json';ids=read(ids_path)
    if ids['plan_sha256']!=sha(plan_path) or sha(ids['archive'])!=ids['archive_sha256']:
        raise ValueError('Private identity registration drift')
    by_id={entry['slug']:entry for entry in ids['entries']}
    if set(selection)!=set(by_id):raise ValueError('Require exact first-ten consumer selection')
    target=owned(OUT/'integration'/('private-foot-compiled-'+args.label))
    if target.exists():raise FileExistsError('Preserve existing native binding stage')
    baseline=OUT/'baseline/final053';freeze=read(baseline/'freeze.json')
    pairs={};payloads=[];actor_edits={}
    for row in plan['entries']:
        slug=row['slug'];chosen=selection[slug]
        pair=qualify_geometry_material_pair(chosen['geometry_slug'],Path(chosen['material_verification']))
        donor=read(pair['stock_manifest'])
        if donor['resources']['model']['logical_path'].replace('\\','/').removesuffix('.rgm')!=row['stock_model']:
            raise ValueError('Media does not belong to exact selected body: '+slug)
        pairs[slug]=pair
        original_path=Path(row['stock_slots'][0]['raw_archive_member_path'])
        if sha(original_path)!=by_id[slug]['stock_sha256']:
            raise ValueError('Pinned native stock body changed')
        original=original_path.read_bytes();document=rgd.read(original);changes=[]
        private_model=pair['model_logical_path'].removesuffix('.rgm').replace('/','\\')
        render_count=0
        for path,node in rgd.flatten(document.nodes):
            if node.key=='pbgid':
                changes.append({'path':path,'before':node.value,'after':by_id[slug]['pbgid']})
            elif node.kind=='CString' and node.key.startswith('animator') and node.value.replace('\\','/')==row['stock_model']:
                changes.append({'path':path,'before':node.value,'after':private_model});render_count+=1
        if render_count!=len(row['stock_slots']):raise ValueError('Exact native render slot count differs')
        native,proof=patch_visual_rgd(original,changes,'body')
        member='attrib/'+row['private_reference']+'.rgd'
        payloads.append({'member':member,'data':native,'kind':'new_private_body','slug':slug,'edits':proof})
        for suffix,key in [('.rgm','private_supported_variant_rgm'),('.rgo','private_supported_variant_rgo'),
                           ('.rrgeom','native_qualified_authored_rrgeom'),('.rrmaterial','private_albedo_only_rrmaterial'),
                           ('.rrtex','private_albedo_rrtex')]:
            item=pair[key];art_member=pair['replacement_rrgeom_logical_path'] if suffix=='.rrgeom' else item['member']
            if sha(item['path'])!=item['sha256']:raise ValueError('Qualified media readback drift')
            payloads.append({'member':art_member,'data':Path(item['path']).read_bytes(),'kind':'new_private_art','slug':slug})
        for node in row['actor_consumers']:
            member=node['source']['asset_relative_path'].replace('attrib/instances/','attrib/',1).removesuffix('.xml')+'.rgd'
            before=node['before_value'].split('\\')[-1]
            after=CFG['project_guid'].replace('-','')+':'+Path(row['private_reference']).name
            entry=actor_edits.setdefault(member,{})
            record=entry.setdefault(before,{'after':after,'expected_count':0})
            if record['after']!=after:raise ValueError('Ambiguous actor body identity')
            record['expected_count']+=1
    for member,mapping in actor_edits.items():
        source=baseline/'archive-members'/member
        if sha(source)!=freeze['archive_members'][member]['sha256']:raise ValueError('Frozen actor drift')
        document=rgd.read(source.read_bytes());changes=[];counts={k:0 for k in mapping}
        for path,node in rgd.flatten(document.nodes):
            if node.kind!='CString' or node.key!='$PBGNAME' or node.value not in mapping:continue
            if '/tier_ext/' not in path or '/attachments/$PBGNAME' not in path:continue
            if rgd.find(document.nodes,path.rsplit('/',1)[0]+'/$PBGMAP').value!=r'attachments\attachment_lists':
                raise ValueError('Compiled visual reference map differs')
            counts[node.value]+=1
            changes.append({'path':path,'before':node.value,'after':mapping[node.value]['after']})
        if any(counts[k]!=v['expected_count'] for k,v in mapping.items()):
            raise ValueError('Source and compiled visual counts differ: '+member+' '+str(counts))
        native,proof=patch_visual_rgd(source.read_bytes(),changes,'actor')
        payloads.append({'member':member,'data':native,'kind':'changed_vietnamese_actor','before_sha256':sha(source),'edits':proof})
    names=[p['member'].casefold() for p in payloads]
    if len(set(names))!=len(names):raise ValueError('Duplicate private payload member')
    # All validation is complete before the first staged payload is written.
    rows=[]
    for payload in payloads:
        path=owned(target/'payload'/payload['member']);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload.pop('data'))
        rows.append({**payload,'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
    write(target/'bindings.json',{'schema':'ccp-060-private-foot-compiled-visual-delta/v1',
        'status':'first_ten_native_visual_bindings_staged_only','selection':str(args.selection),'selection_sha256':sha(args.selection),
        'plan_sha256':sha(plan_path),'identity_receipt_sha256':sha(ids_path),'baseline_sga_sha256':freeze['sga_sha256'],
        'pairs':pairs,'payloads':rows,'existing_actors':len(actor_edits),'private_body_lists':len(pairs),
        'all_nonvisual_bytes_exact_after_edit_reversal':True,'active_source_or_final_archive_changed':False,
        'native_match_acceptance':False})
    print(json.dumps({'status':'staged','receipt':str(target/'bindings.json'),'payloads':len(rows)}))


if __name__=='__main__':main()
