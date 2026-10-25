"""Fresh 051 native source compile and exact inherited trap parity."""
from __future__ import annotations
import copy, re, shutil, subprocess, sys, tempfile
from common import *
sys.path.insert(0,CONFIG['garrison_extension'])
from garrison_shared import rgd
NAMES=('vn_building_bambo_outpost_chi','vn_building_defense_outpost_bambo_chi')
def extract(archive,member,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    assert target.resolve().is_relative_to(OUT.resolve())
    with tempfile.TemporaryDirectory(dir=target.parent) as scratch:
        fresh=Path(scratch)/target.name
        subprocess.run([str(ARCH),'extract-member',str(archive),member,str(fresh)],capture_output=True,check=True)
        if target.exists():assert target.read_bytes()==fresh.read_bytes(),'Existing readback drifted'
        else:shutil.copy2(fresh,target)
    return target
def inheritance(parent,child):
    old=rgd.read(parent.read_bytes());new=rgd.read(child.read_bytes());restored=copy.deepcopy(new)
    a=dict(rgd.flatten(old.nodes)); b=dict(rgd.flatten(new.nodes));changes=[];identities=[]
    # Restore only native identity fields and the two intended impass fields.
    for path,node in a.items():
        if node.kind in ('List','List2'):
            if path.endswith('/impass_ext/block_path'):
                assert path in b and b[path].value==[]
                rgd.find(restored.nodes,path).value=copy.deepcopy(node.value)
                changes.append(path)
            continue
        if path.endswith('/pbgid') or '/parent_pbg/' in path or path in (
            'default/district_bonuses_ext/district_bonuses/district_bonus/id',
            'campaign/district_bonuses_ext/district_bonuses/district_bonus/id'):
            assert path in b
            if b[path].value!=node.value:identities.append({'path':path,'parent':node.value,'child':b[path].value})
            rgd.find(restored.nodes,path).value=node.value
        elif path.endswith('/impass_ext/impass_simboxes/default_simbox'):
            assert b[path].value is False
            rgd.find(restored.nodes,path).value=node.value;changes.append(path)
    # Removing the sole block_path entries also removes their unused key name
    # from native KEYS. Restore that dictionary entry with its restored nodes.
    assert set(new.keys)<=set(old.keys)
    removed_keys=set(old.keys)-set(new.keys)
    assert all(name=='path_type' for _,name in removed_keys),removed_keys
    restored.keys=copy.deepcopy(old.keys)
    assert changes and rgd.write(restored)==rgd.write(old),'Passable child differs outside identity/passage fields'
    return {'parent_sha256':sha(parent),'child_sha256':sha(child),'passage_paths':changes,'identity_fields':identities,'removed_unused_passage_keys':sorted(removed_keys),'all_other_compiled_fields_byte_identical':True}
def compile(label):
    guarded();assert re.fullmatch(r'r[a-z0-9-]{2,15}',label)
    root=OUT/'native-source'/label;assert not root.exists()
    root.mkdir(parents=True);source=root/'source';source.mkdir()
    shutil.copytree(ROOT/'assets',source/'assets');shutil.copy2(ROOT/CONFIG['project_file'],source/CONFIG['project_file'])
    inputs={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    write(root/'inputs.json',inputs)
    with exclusive_native():
        log=run_logged('source051-'+label,[EDITOR,'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report','--no_source_control','--log_path',root/'native-logs','--build_mod',source/CONFIG['project_file'],'--build_path',root/'build','--no_burn_window','--burn_cache_type','Local','--burn_max_threads','1','--burn_platform','PC','--burn_log_path',root/'burn.log','--intermediate_path',root/'intermediate'],cwd=EDITOR.parent,timeout=1800)
    return finish(label,log)
def finish(label,log=None):
    guarded();root=OUT/'native-source'/label;source=root/'source'
    log=Path(log or OUT/'logs'/('source051-'+label+'.log'));text=log.read_text(errors='replace')
    assert 'EssenceEditor.exe Error:' not in text
    count=len(list((source/'assets/attrib/instances').rglob('*.xml')))
    assert int(re.findall(r'(\d+) instances validated',text)[-1])==count
    archives=list((root/'build').rglob('*.sga'));assert len(archives)==1;archive=archives[0]
    inventory=__import__('json').loads(subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,check=True).stdout)
    assert inventory['archive']['verification']['verified']
    members={m['path'].lower():m['path'] for m in inventory['members']}
    proofs={};payloads=[];ids=read(OUT/'traps/identities.json')
    for name,pid in zip(NAMES,ids['pbg_ids']):
        stem='attrib/ebps/vietnam/'+name
        parent=extract(archive,members[stem+'.rgd'],root/'parents'/(name+'.rgd'))
        accepted=extract(BASELINE,stem+'.rgd',root/'accepted'/(name+'.rgd'))
        assert sha(parent)==sha(accepted),'Original blocking trap compile changed'
        member=members[stem+'_passable.rgd'];child=extract(archive,member,root/'payload'/member)
        doc=rgd.read(child.read_bytes());assert rgd.find(doc.nodes,'default/pbgid').value==pid
        for path,node in rgd.flatten(doc.nodes):
            if path.endswith('/parent_pbg/$PBGNAME'):assert node.value==GUID.replace('-','')+':'+name
        proofs[name]=inheritance(parent,child)
        payloads.append({'member':member,'file':str(child),'sha256':sha(child),'bytes':child.stat().st_size})
    for logical in ('scar/vietnam/traps.scar','scar/vietnam/prematch_precache.scar','scar/winconditions/vietnammode.bin'):
        member=members[logical];target=extract(archive,member,root/'payload'/member)
        if logical.endswith('.scar'):assert target.read_bytes()==(ROOT/'assets'/logical).read_bytes()
        payloads.append({'member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
    assert read(root/'inputs.json')=={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    result={'status':'passed','validated_instances':count,'archive':str(archive),'archive_sha256':sha(archive),'payloads':payloads,'inherited_trap_parity':proofs,'log':str(log),'native_match':'pending'}
    write(root/'receipt.json',result);write(OUT/'native-source/current.json',{'file':str(root/'receipt.json'),'sha256':sha(root/'receipt.json')})
    print('NATIVE051_PASSED',count,len(payloads));return result
if __name__=='__main__':compile(sys.argv[2]) if sys.argv[1]=='compile' else finish(sys.argv[2])
