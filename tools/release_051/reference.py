"""Fresh native reference cook of the exact seven repaired model inputs."""
import hashlib,re,shutil,subprocess,sys,xml.etree.ElementTree as ET
from common import *
from release import verify,unpack
MODELS=['art/scenario/cccastle/imperial_citadel/model','art/scenario/cccastle/resistance_hq/model',
        'art/scenario/cc050/imperial_citadel_campaign/model',
        *[f'art/scenario/cccastle/monastery{suffix}_age0{age}/model' for age in (3,4) for suffix in ('','_detail')]]
def cook(label):
    verify();candidate=read(OUT/'candidate.json');back=unpack(candidate['archive'],'candidate051')
    old=OUT.parent/'castle_next/reference/rlbr01'
    root=OUT/'reference'/label;assert not root.exists();source=root/'source';source.mkdir(parents=True)
    shutil.copy2(old/'reference.aoe4mod',root/'reference.aoe4mod')
    inputs={}
    for model in MODELS:
        folder=back/Path(model).parent;assert folder.is_dir()
        for p in folder.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(back);target=source/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
            if p.suffix=='.rrmaterial':shutil.copy2(target,target.with_suffix('.material'))
    template=old/'source/art/stamps/cccastle/reference_0.rdo'
    burn=(old/'source/_default.burnproj').read_text(encoding='utf-8-sig')
    burn=re.sub(r'<BurnRule>.*?</BurnRule>',lambda m:m[0].replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>'),burn,flags=re.S)
    rules=[];refs=[]
    for i,model in enumerate(MODELS):
        tree=ET.parse(template).getroot(); ids={n.get('Id'):str(int.from_bytes(hashlib.sha256(('051:'+label+':'+str(i)+':'+n.get('Id')).encode()).digest()[:8],'little')) for n in tree.iter('DataObject')}
        for n in tree.iter():
            for attr in ('Id','OwnerId'):
                if n.get(attr) in ids:n.set(attr,ids[n.get(attr)])
            if n.tag=='DataValue' and n.text in ids:n.text=ids[n.text]
            if n.tag=='DataProperty' and n.get('Name')=='m_objectID' and n.get('Value') in ids:n.set('Value',ids[n.get('Value')])
            if n.tag=='DataProperty' and n.get('Name')=='m_blueprint':n.set('Value',model.replace('/','\\'))
        member=f'art/stamps/cc051/reference_{i}';target=source/(member+'.rdo');target.parent.mkdir(parents=True,exist_ok=True)
        ET.indent(tree);target.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True))
        rules.append('<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true"/><Includes>'+member.replace('/','\\')+'.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>')
        refs.append({'member':member+'.bin','model':model})
    assert burn.count('</Rules>')==1
    (source/'_default.burnproj').write_text(burn.replace('</Rules>',''.join(rules)+'</Rules>'),encoding='utf-8')
    inputs={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()};write(root/'inputs.json',inputs)
    run=OUT/'reference-runs'/label
    with exclusive_native():
        log=run_logged('reference051-'+label,[CORE,'essence','build-mod','--editor',ART_EDITOR,'--mod',root/'reference.aoe4mod','--run-root',run,'--timeout','900'],timeout=1100)
    state=read(run/'run.json');assert state['status']=='succeeded' and state['exit_code']==0
    archives=list((run/'output').rglob('*.sga'));assert len(archives)==1;archive=archives[0]
    sys.path.insert(0,str(ROOT/'tools/release_010'))
    from integration_native import NativeTree
    import integration as native
    outputs=[]
    for r in refs:
        dest=root/'readback'/r['member'];dest.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(ARCH),'extract-member',str(archive),r['member'],str(dest)],capture_output=True,check=True)
        actual=[v['model'] for v in native.active_visuals(NativeTree(dest))];assert actual==[r['model']],actual
        outputs.append({**r,'sha256':sha(dest)})
    assert inputs=={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    for r in candidate['payloads']:
        if r['member'].endswith(('.rgm','.rrgeom')):assert inputs[r['member']]==r['sha256']
    result={'status':'passed','candidate_sha256':candidate['sha256'],'archive':str(archive),'archive_sha256':sha(archive),'run':state,'model_references':outputs,'exact_inputs_sha256':inputs,'log':log,'qualification':'Native reference cook/readback of already cooked model resources; no FBX recook or in-game rendering claim','native_match':'pending user testing'}
    write(OUT/'reference/receipt.json',result);print('REFERENCE051_PASSED',len(outputs))
if __name__=='__main__':cook(sys.argv[1])
