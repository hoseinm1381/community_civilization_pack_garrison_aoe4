"""Exact old media plus visual-only actor fields over freshly compiled gameplay.

Run with the configured Blender Python (compiled Garrison RGD codec is cp313).
"""
from freeze import *
from build import run,STAGING
import copy,re,argparse,shutil,collections
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd
BASE=STAGING/'baseline-native'
def visual_refs(tree):
    rows={}
    for path,node in rgd.flatten(tree.nodes):
        if node.kind not in ('List','List2'):continue
        fields={n.key:n.value for n in node.children if n.kind not in ('List','List2')}
        if fields.get('$PBGMAP')=='attachments\\attachment_lists' and str(fields.get('$PBGNAME','')).startswith(GUID+':'):
            rows[path]=node
    return rows
def refs(tree):
    return [(path,n.value)for path,n in rgd.flatten(tree.nodes)if n.key=='$PBGNAME' and n.kind=='CString' and str(n.value).startswith(GUID+':')]
def assemble(label,source_label=None):
    source_label=source_label or label
    original=json.loads((ROOT/'output/release_071/package-post1.json').read_text())
    assert sha(ROOT/'output/release_071/delivery/community_civilization_pack.sga')==original['sga_sha256']
    assert {p.relative_to(BASE).as_posix():sha(p)for p in files(BASE)}=={k:v['sha256']for k,v in original['all_members_sha256'].items()},'Cached 0.7.1 native inputs changed'
    source=json.loads((OUT/('native-source-'+source_label+'.json')).read_text());assert source['passed']
    source_archive=Path(source['archives'][0]);assert sha(source_archive)==source['archive_sha256']
    work=STAGING/('assemble-'+label);assert not work.exists(),'Use a new label to preserve evidence'
    work.mkdir(parents=True);fresh=work/'fresh'
    run('extract-source-'+label,[CFG['archive_tool'],'extract',source_archive,fresh,'--filter',''])
    payload=work/'payload';payload.mkdir();overlay={};actor_edits=[]
    # Every model/material/stamp byte is preserved; no stock actor is replaced.
    for p in files(BASE/'art'):
        key=p.relative_to(BASE).as_posix();overlay[key]=p
    for p in files(BASE/'attrib/attachments'):
        key=p.relative_to(BASE).as_posix();overlay[key]=p
    old_actors={(kind,p.stem):p for kind in ('ebps','sbps')for p in (BASE/('attrib/'+kind)).rglob('*.rgd')}
    private_aliases={v.rsplit('\\',1)[-1]:(k.split('\\',1)[0],k.rsplit('\\',1)[-1])for k,v in json.loads((OUT/'source-port.json').read_text())['redirects'].items()}
    visual_parents={}
    import xml.etree.ElementTree as E
    with zipfile.ZipFile(OUT/'freeze/garrison.zip')as z:
        for name in z.namelist():
            if '/instances/attachments/'not in name:continue
            t=E.fromstring(z.read(name));parent=t.find("instance_reference[@name='parent_pbg']")
            if parent is not None:visual_parents[Path(name).stem]=parent.get('value','').rsplit('\\',1)[-1]
    skipped_weapon_visuals=[];inherited_variant_visuals=[];changed_gameplay_identities=[]
    for p in [p for kind in ('ebps','sbps')for p in (fresh/('attrib/'+kind)).rglob('*.rgd')]:
        kind=p.relative_to(fresh).parts[1];oldkey=(kind,p.stem)
        if oldkey not in old_actors:continue
        before=p.read_bytes();tree=rgd.read(before);old=rgd.read(old_actors[oldkey].read_bytes());changed=[]
        bindings=visual_refs(old)
        alias_paths=set()
        for path,node in rgd.flatten(old.nodes):
            if node.kind not in ('List','List2'):continue
            fields={n.key:n.value for n in node.children if n.kind not in ('List','List2')}
            name=str(fields.get('$PBGNAME',''))
            if not name.startswith(GUID+':'):continue
            short=name.split(':',1)[1]
            if short in private_aliases and fields.get('$PBGMAP')==private_aliases[short][0]:
                bindings[path]=node;alias_paths.add(path)
        for path,node in bindings.items():
            try:target=rgd.find(tree.nodes,path)
            except Exception as exc:raise ValueError(('Visual path changed; review required',p.stem,path))from exc
            if target is None:
                branch,rest=path.split('/',1)
                # Sparse native variants inherit default. Do not reconstruct an
                # obsolete campaign weapon list just to repeat its bow model.
                section=rest.split('/',1)[0]
                if branch!='default' and rgd.find(tree.nodes,branch+'/'+section)is None and rgd.find(tree.nodes,'default/'+section)is not None:
                    oldname=next(n.value for n in node.children if n.key=='$PBGNAME')
                    defaults=[next(n.value for n in v.children if n.key=='$PBGNAME')for q,v in visual_refs(old).items()if q.startswith('default/'+section+'/')]
                    if oldname in defaults:
                        inherited_variant_visuals.append({'actor':p.stem,'path':path,'visual':oldname,'via':'default/'+section});continue
                raise ValueError(('Visual path absent in fresh native actor',p.stem,path))
            if target.kind!=node.kind:raise ValueError(('Visual field type changed',p,path))
            if path in alias_paths and target.value!=node.value:
                selected=next(n.value for n in node.children if n.key=='$PBGNAME').split(':',1)[1]
                fields={n.key:n.value for n in target.children if n.kind not in ('List','List2')}
                if (fields.get('$PBGMAP'),fields.get('$PBGNAME'))!=private_aliases[selected]:
                    assert p.stem not in private_aliases,('Retained visual identity donor changed unexpectedly',p,path,fields)
                    changed_gameplay_identities.append({'actor':p.stem,'path':path,'v12_reference':fields,'old_private_visual_identity':selected,'reason':'Normal v12 deliberately changed the produced unit or actor; keep fresh gameplay'})
                    continue
            if '/combat_ext/'in path and target.value!=node.value:
                selected=next(n.value for n in node.children if n.key=='$PBGNAME').split(':',1)[-1]
                actual=next((n.value for n in target.children if n.key=='$PBGNAME'),'')
                if actual!=visual_parents.get(selected):
                    skipped_weapon_visuals.append({'actor':p.stem,'path':path,'new_visual':actual,'old_private_visual':selected,'reason':'v12 weapon uses a different visual donor; retain its intended new weapon'})
                    continue
            if target.value!=node.value:
                changed.append({'path':path,'kind':'equivalent-private-visual-identity'if path in alias_paths else'attachment-render-reference','before':[(q,n.value)for q,n in rgd.flatten([copy.deepcopy(target)])if n.kind not in ('List','List2')],
                                'after':[(q,n.value)for q,n in rgd.flatten([copy.deepcopy(node)])if n.kind not in ('List','List2')]})
                target.value=copy.deepcopy(node.value)
        if changed:
            # Revert the admitted leaves and demand exact fresh-byte recovery.
            reverted=copy.deepcopy(tree);original=rgd.read(before)
            for row in changed:rgd.find(reverted.nodes,row['path']).value=copy.deepcopy(rgd.find(original.nodes,row['path']).value)
            assert rgd.write(reverted)==before,'Actor changed outside visual fields'
            key=p.relative_to(fresh).as_posix();dest=payload/key;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(rgd.write(tree));overlay[key]=dest
            actor_edits.append({'member':key,'old_visual_owner':str(old_actors[oldkey]),'fields':changed,'fresh_sha256':sha(p),'assembled_sha256':sha(dest),'revert_recovers_exact_fresh_bytes':True})
    current=source_archive
    mounts={x['path']:x['toc']for x in source['listing']['members']}
    baselist=json.loads(run('baseline-list-'+label,[CFG['archive_tool'],'list',ROOT/'output/release_071/delivery/community_civilization_pack.sga','--verify']))
    oldmounts={x['path']:x['toc']for x in baselist['members']}
    for key in overlay:mounts[key]=oldmounts.get(key,'attrib' if key.startswith('attrib/')else'data')
    dump(OUT/('overlay-'+label+'.json'),{'media':{k:sha(v)for k,v in overlay.items()if not k.startswith(('attrib/ebps/','attrib/sbps/'))},'actor_visual_edits':actor_edits,'skipped_changed_weapon_donors':skipped_weapon_visuals,'kept_v12_production_changes':changed_gameplay_identities,'inherited_variant_visuals':inherited_variant_visuals,'policy':'Exact old art/attachment resources; fresh actor gameplay with listed attachment references and donor-proven equivalent visual identities changed'})
    for toc in ('attrib','data'):
        rows=[(k,v)for k,v in overlay.items()if mounts[k]==toc]
        mapping=work/(toc+'.txt');mapping.write_text('\n'.join(k+'='+str(v)for k,v in rows)+'\n',encoding='utf-8')
        target=work/(toc+'.sga');run('assemble-'+toc+'-'+label,[CFG['archive_tool'],'set-members',current,mapping,target,'--alias',toc]);current=target
    delivery=OUT/'delivery';delivery.mkdir(exist_ok=True);final=delivery/'community_civilization_pack.sga';shutil.copy2(current,final)
    listing=json.loads(run('final-list-'+label,[CFG['archive_tool'],'list',final,'--verify']));assert listing['archive']['verification']['verified']
    assert {x['path']:x['toc']for x in listing['members']}==mounts,'Unexpected member/mount delta'
    back=work/'readback';run('final-readback-'+label,[CFG['archive_tool'],'extract',final,back,'--filter',''])
    expected={p.relative_to(fresh).as_posix():sha(p)for p in files(fresh)};expected.update({k:sha(v)for k,v in overlay.items()})
    actual={p.relative_to(back).as_posix():sha(p)for p in files(back)};assert actual==expected
    # Every own compiled blueprint reference must resolve to a packaged definition.
    known=collections.defaultdict(set)
    for p in (back/'attrib').rglob('*.rgd'):
        t=rgd.read(p.read_bytes())
        for path,n in rgd.flatten(t.nodes):
            if n.key=='pbgid':known[n.value].add(p.as_posix())
    bad=[];refcount=0;names={p.stem for p in (back/'attrib').rglob('*.rgd')}
    for p in (back/'attrib').rglob('*.rgd'):
        for path,v in refs(rgd.read(p.read_bytes())):
            refcount+=1
            if v.split(':',1)[1] not in names:bad.append([p.relative_to(back).as_posix(),path,v])
    assert not bad,bad
    retired=json.loads((NORMAL/'work/vietnam_redesign/runtime_v12_20261023/cleanup-ledger.json').read_text())
    assert not ({Path(x['path']).stem for x in retired['files']}&names),'Retired gameplay returned'
    dump(OUT/('assembly-'+label+'.json'),{'passed':True,'source_label':source_label,'sga_sha256':sha(final),'members':actual,'mounts':mounts,'old_art_members_preserved':len([k for k in overlay if not k.startswith(('attrib/ebps/','attrib/sbps/'))]),'patched_actor_count':len(actor_edits),'own_blueprint_references_checked':refcount,'unresolved':bad,'native_game_tested':False})
    print(json.dumps({'passed':True,'members':len(actual),'old_art_members':len(overlay)-len(actor_edits),'patched_actors':len(actor_edits),'sga_sha256':sha(final)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',default='v1');p.add_argument('--source-label');a=p.parse_args();assemble(a.label,a.source_label)
