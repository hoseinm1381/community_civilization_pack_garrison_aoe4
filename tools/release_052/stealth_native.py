"""Fresh source cook of the diagnostic-C XML overlay; active assets stay untouched."""
import copy,msvcrt,re,shutil
from common import *
from garrison_shared import rgd

MEMBER='attrib/abilities/vietnam/vn_activate_stealth_forvills_vit.rgd'
SOURCE='attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'
FIELDS={'default/ability_bag/disable_when_active':False,
        'default/ability_bag/recharge_time':0.0,
        'default/ability_bag/can_queue_passive_ability':False}

def extract(archive,member,dest):
    dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists()
    result=subprocess.run([str(ARCH),'extract-member',str(archive),member,str(dest)],capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    return dest

def compile(label,editor_kind='steam'):
    guard();assert re.fullmatch(r'r[a-z0-9-]{2,15}',label)
    root=OUT/'stealth/native'/label;assert not root.exists()
    source=root/'source';source.mkdir(parents=True)
    frozen=read(OUT/'baseline/freeze.json')['inputs']
    assert files(ROOT/'assets')==frozen['assets']
    shutil.copytree(ROOT/'assets',source/'assets')
    project=source/CONFIG['project_file'];shutil.copy2(ROOT/CONFIG['project_file'],project)
    assert files(source/'assets')==frozen['assets']
    overlay=OUT/'stealth/diagnostic-c/vn_activate_stealth_forvills_vit.xml'
    receipt=read(OUT/'stealth/diagnostic-c/receipt.json')
    # Pin this fully inspected, byte-reversible overlay, independent of receipt shape.
    assert sha(overlay)=='7f0d8c6380b73474a8e4794ce14d336be76900371e369c01978cf1c4b3dba382'
    shutil.copy2(overlay,source/'assets'/SOURCE)
    actual=files(source/'assets');changed={p for p in actual if actual[p]!=frozen['assets'].get(p)}
    assert changed=={SOURCE}
    inputs={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    write(root/'inputs.json',inputs)
    assert editor_kind in ('steam','garrison')
    editor=Path(CONFIG['art_editor'] if editor_kind=='garrison' else CONFIG['content_editor'])
    run_root=Path(CONFIG['external_root'])/'c'/('cc052-stealth-'+label)
    assert run_root.resolve().is_relative_to(Path(CONFIG['external_root']).resolve()) and not run_root.exists()
    write(root/'runner.json',{'run_root':str(run_root),'editor':str(editor),'source_project':str(project)})
    lock=OUT.parent/'release_020/native-build.lock'
    with lock.open('r+b') as f:
        try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:raise RuntimeError('Native cook slot is in use; wait for the other worker')
        try:
            log=command('stealth-source052-'+label,[CONFIG['garrison_core'],'essence','build-mod',
                '--editor',editor,'--mod',project,'--run-root',run_root,'--timeout','900'],cwd=editor.parent)
        finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
    return finish(label,log)

def finish(label,log=None):
    guard();root=OUT/'stealth/native'/label;source=root/'source'
    log=Path(log or OUT/'logs'/('stealth-source052-'+label+'.log'))
    text=log.read_text(errors='replace');assert 'EssenceEditor.exe Error:' not in text
    runner=read(root/'runner.json') if (root/'runner.json').exists() else None
    if runner:
        run_root=Path(runner['run_root']);state=read(run_root/'run.json')
        assert state['status']=='succeeded' and state['exit_code']==0,state
        # The supported runner records application stdout in its own run root.
        for name in ('stdout.log','EssenceEditorLog.txt'):
            application_log=run_root/'logs'/name
            if application_log.exists():text+='\n'+application_log.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace')
        build=run_root/'output'
    else:state=None;build=root/'build'
    count=len(list((source/'assets/attrib/instances').rglob('*.xml')))
    assert int(re.findall(r'(\d+) instances validated',text)[-1])==count
    assert read(root/'inputs.json')=={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    archives=list(build.rglob('*.sga'));assert len(archives)==1;archive=archives[0]
    listing=json.loads(subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,check=True).stdout)
    assert listing['archive']['verification']['verified']
    output=extract(archive,MEMBER,root/'payload'/MEMBER)
    baseline=extract(BASELINE,MEMBER,root/'baseline'/MEMBER)
    old,new=rgd.read(baseline.read_bytes()),rgd.read(output.read_bytes())
    a,b=dict(rgd.flatten(old.nodes)),dict(rgd.flatten(new.nodes))
    assert set(a)==set(b)
    changed={p for p in a if a[p].kind not in ('List','List2') and a[p].value!=b[p].value}
    assert changed==set(FIELDS),changed
    restored=copy.deepcopy(new)
    for path,value in FIELDS.items():
        assert b[path].value==value and a[path].kind==b[path].kind
        rgd.find(restored.nodes,path).value=a[path].value
    assert rgd.write(restored)==rgd.write(old),'Unexpected native compiled differences'
    assert sha(ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_for_archer.xml')=='c0ee10a5c456d069d0c1d03992ee1d34d8b2cae256b4ec820d47eb6ab6894d99'
    result={'status':'passed_native_source_compile','validated_instances':count,'archive':str(archive),'archive_sha256':sha(archive),
        'compiled_changes':{p:{'old':a[p].value,'new':b[p].value} for p in changed},'all_other_compiled_fields_byte_identical':True,
        'source_changes':[SOURCE],'active_source_untouched':True,'archer_activated_ability_byte_identical':True,
        'payloads':[{'member':MEMBER,'file':str(output),'sha256':sha(output),'bytes':output.stat().st_size}],
        'log':str(log),'native_run':state,'native_archive_verified':True,'native_match':'pending user stealth comparison'}
    write(root/'receipt.json',result);write(OUT/'stealth/native/current.json',{'file':str(root/'receipt.json'),'sha256':sha(root/'receipt.json')})
    print('STEALTH052_NATIVE_PASSED',count,sha(output),flush=True);return result

if __name__=='__main__':compile(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'steam') if sys.argv[1]=='compile' else finish(sys.argv[2])
