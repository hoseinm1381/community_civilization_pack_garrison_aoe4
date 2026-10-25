"""Audit actual final compiled visual bindings and their private resource closure.

Official, unchanged resources are terminal leaves with freshly extracted hashes and
archive provenance. Every custom model/material/texture must exist in this archive.
"""
import json, re, subprocess, sys
from pathlib import Path
import integration as build
from common import CONFIG, OUT, ARCH, sha, read, write
from garrison_shared import rgd, relic_chunky as rc, model_variants as mv
from integration_native import NativeTree

def audit(archive, readback, work=None):
    archive=Path(archive);readback=Path(readback);work=Path(work) if work else OUT/'integration'
    private={};native={};edges=[];actor_proofs=[];stamp_proofs=[]
    guid=CONFIG['project_guid'].replace('-','')
    reference=read(work/'reference-cook.json');assert reference['status']=='passed'
    def present(member):
        member=member.replace('\\','/').lower();path=readback/member
        assert path.is_file(),('Dangling custom resource',member)
        private[member]={'member':member,'sha256':sha(path),'bytes':path.stat().st_size};return path
    def official(member):
        member=member.replace('\\','/').lower()
        assert not member.startswith(('art/scenario/cc010/','art/stamps/cc010/','art/scenario/garrison/')),('Custom dependency cannot fall back to official data',member)
        path=build.stock(member);record=read(build.CACHEWORK/'official-index.json')[member]
        assert record['sha256']==sha(path)
        native[member]={'member':member,**record};return path
    def edge(owner,target,kind):edges.append({'owner':owner,'target':target,'kind':kind})
    bindings=read(work/'private-bindings.json');identities={r['name']:r for r in read(work/'registered-identities.json')}
    mapping={r['source'].split('\\')[-1]:r['name'] for r in read(work/'derived-contracts.json')['tiers']}
    # Compare every compiled actor field against the actual frozen baseline,
    # allowing only the original native visual attachment $PBGNAME references.
    for name in build.CONSUMERS:
        member=f'attrib/ebps/vietnam/{name}.rgd';path=present(member)
        original=rgd.read((work/'baseline-archive-readback'/member).read_bytes());actual=rgd.read(path.read_bytes());restored=rgd.read(path.read_bytes());changes=[]
        original_nodes=dict(rgd.flatten(original.nodes));actual_nodes=dict(rgd.flatten(actual.nodes));assert original_nodes.keys()==actual_nodes.keys()
        for field,old in original_nodes.items():
            node=actual_nodes[field]
            if old.kind=='CString' and old.key=='$PBGNAME' and field.endswith(('/attachments/$PBGNAME','/animator_attachments/$PBGNAME')) and old.value in mapping:
                target=mapping[old.value];assert node.value==guid+':'+target,(name,field,node.value)
                rgd.find(restored.nodes,field).value=old.value;changes.append({'path':field,'before':old.value,'after':node.value})
                edge(member,identities[target]['final_member'],'private_attachment')
        assert changes and rgd.write(restored)==rgd.write(original),(name,'Compiled nonvisual or unexpected binding change')
        actor_proofs.append({'member':member,'changes':changes,'all_other_compiled_fields_identical':True})
    models=set();stamps=set()
    for row in bindings['payloads']:
        path=present(row['member']);assert sha(path)==row['sha256']
        data=rgd.read(path.read_bytes());name=Path(row['member']).stem;identity=identities[name]
        assert {n.value for p,n in rgd.flatten(data.nodes) if n.key=='pbgid'}=={identity['pbgid']}
        for field,node in rgd.flatten(data.nodes):
            if node.kind!='CString' or not node.value:continue
            if node.key=='stamp':
                target=node.value.replace('\\','/').lower()+'.bin';edge(row['member'],target,'stamp')
                if target.startswith('art/stamps/cc010/'):present(target);stamps.add(target)
                else:official(target)
            elif node.key=='parent_animator':
                target=node.value.replace('\\','/').lower();edge(row['member'],target,'model')
                if target.startswith('art/scenario/cc010/'):models.add(target)
                else:official(target+'.rgm')
    expected_stamps={f'art/stamps/cc010/house_age0{i}.bin':f'art/scenario/cc010/h{i}/model' for i in range(1,5)}
    expected_stamps.update({'art/stamps/cc010/stake_thicket.bin':'art/scenario/cc010/t1/model','art/stamps/cc010/stake_fan.bin':'art/scenario/cc010/t2/model'})
    assert stamps==set(expected_stamps)
    for stamp in sorted(stamps):
        path=present(stamp);tree=NativeTree(path);visuals=build.active_visuals(tree);custom=[]
        for visual in visuals:
            model=visual['model'].lower();edge(stamp,model,'active_visual')
            if model.startswith('art/scenario/cc010/'):models.add(model);custom.append(model)
            else:official(model+'.rgm')
        assert custom==[expected_stamps[stamp]],('Missing or duplicate complete architecture',stamp,custom)
        assert not any('/structures/house/' in v['model'] or '/structures/tent/' in v['model'] for v in visuals),('Obsolete native principal remains active',stamp)
        stamp_proofs.append({'member':stamp,'custom_principal':custom,'active_visuals':len(visuals),'functional_records':len(tree.objects)-sum(o['type']=='VisualStampBlueprint' for o in tree.objects.values())})
    assert models==set(reference['models'])
    for model in sorted(models):
        for ext in ['.rgm','.rgo','.rrgeom','.rrmaterial']:
            member=model+ext;path=present(member)
            assert sha(path)==reference['exact_inputs_sha256'][member],('Stale native model qualification',member)
            edge(model,member,'model_component')
        doc=rc.load(present(model+'.rgm'));bana=[c for c in rc.walk(doc.roots) if c.tag==b'BANA'];assert len(bana)==1
        name,at=rc.read_lp_string(bana[0].payload,0);assert name.replace('\\','/').lower()==model
        material=rc.load(present(model+'.rrmaterial'))
        for root in material.roots:
            if root.tag!=b'GMat':continue
            raw=rc.pack_document([rc.pack_chunk(root.kind,root.tag,root.payload,name=root.name,version=root.version)])
            for slot,value in mv.material_slots(raw)['textures'].items():
                if not value:continue
                if slot=='__default' and value=='__default':continue # Native engine binding sentinel, not a file path.
                member=value.replace('\\','/').lower()
                if not member.endswith('.rrtex'):member+='.rrtex'
                edge(model+'.rrmaterial',member,'texture:'+slot)
                if member.startswith(('art/scenario/cc010/','art/scenario/garrison/')):
                    path=present(member);assert sha(path)==reference['exact_inputs_sha256'][member],('Stale texture qualification',member)
                else:official(member)
    result={'status':'passed','archive':str(archive),'archive_sha256':sha(archive),'actors':actor_proofs,'private_stamps':stamp_proofs,'private_models':sorted(models),'visited_private_entries':list(private.values()),'resolved_native_entries':list(native.values()),'dependency_edges':edges,'native_leaf_policy':'Unchanged official assets terminate at exact extracted bytes plus official archive fingerprint. Every introduced custom dependency must resolve in final archive.','runtime':'unverified'}
    write(work/'closure.json',result);return result

if __name__=='__main__':
    result=audit(*sys.argv[1:]);print('FINAL_COMPILED_CLOSURE',len(result['visited_private_entries']),len(result['resolved_native_entries']))
