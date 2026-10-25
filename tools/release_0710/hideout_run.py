"""Serialized isolated authoring and cook; immutable per-attempt outputs."""
import msvcrt,re,shutil
from common import *
def main(mode,variant='default',label='v1'):
 guard();out=OUT/'hideout';log=out/'logs';lock=OUT.parent/'release_020/native-build.lock'
 with lock.open('r+b') as f:
  msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
  try:
   if mode=='composite':
    print(run('compound-'+variant+'-'+label,[CFG['blender'],'--background','--factory-startup','--python-exit-code','1','--python',ROOT/'tools/release_0710/hideout_composite.py','--',variant],folder=log,timeout=1800)[-500:]);return
   if mode=='author':
    print(run('author-'+variant+'-'+label,[CFG['blender'],'--background','--factory-startup','--python-exit-code','1','--python',ROOT/'tools/release_0710/hideout_author.py','--','shelter_'+variant],folder=log,timeout=1800)[-1000:]);return
   if mode=='cook':
    source=EXPORT/'hideout'/('shelter_'+variant);work=STAGE/('hideout-'+variant+'-'+label);assert not work.exists();work.mkdir(parents=True)
    library=work/'library';key='cc710h'+variant;project=library/'Mods'/key
    frozen={p.name:sha(p) for p in source.iterdir() if p.is_file()};write(out/('freeze-'+variant+'-'+label+'.json'),frozen)
    core=CFG['garrison_core']
    for tag,args in [('create',['mod-project','create','--library',library,'--name',key]),('settings',['mod-project','settings','--project',project,'--live-reload','off']),('register',['mod-project','building','--project',project,'--source',source,'--name','hideout','--profile','english-house','--integration','script']),('derive',['mod-project','derive','--project',project,'--source','attachments/attachment_lists/civilizations/chinese/buildings/defense_outpost_chi/defense_outpost_control_chi','--name','vn0710_fortified_visual']),('cook',['mod-project','cook','--project',project,'--editor',CFG['art_editor'],'--timeout','1800'])]:run(variant+'-'+label+'-'+tag,[core,*args],folder=log,timeout=2000)
    archive=project/'dist'/(key+'.sga');back=out/('readback-'+variant+'-'+label)
    run(variant+'-'+label+'-readback',[CFG['archive_tool'],'extract',archive,back,'--filter','.'],folder=log)
    assert frozen=={p.name:sha(p) for p in source.iterdir() if p.is_file()}
    if variant=='default':
     sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import rgd
     generated=back/f'attrib/attachments/attachment_lists/garrison/{key}/vn0710_fortified_visual.rgd'
     identities={n.value for _,n in rgd.flatten(rgd.read(generated.read_bytes()).nodes) if n.key=='pbgid'};assert len(identities)==1;identity=identities.pop()
     import xml.etree.ElementTree as E
     target=ROOT/'assets/attrib/instances/attachments/attachment_lists/vietnam/release_0710/vn_0710_hideout_fortified_visual.xml';doc=E.parse(target);doc.getroot().find('uniqueid').set('value',str(identity));doc.write(target,encoding='utf-8',xml_declaration=True)
     write(out/'allocated-identity.json',{'pbgid':identity,'generated':str(generated),'sha256':sha(generated),'allocator':'installed Garrison mod-project derive then native cook','project':str(project)})
    write(out/('cook-'+variant+'-'+label+'.json'),{'archive':str(archive),'sha256':sha(archive),'readback':str(back),'key':key,'model':str(back/f'art/scenario/garrison/{key}/buildings/hideout/model'),'source':str(source),'fresh_native_cook':True});return
   if mode=='compile':
    run('identity-precompile-'+label,[CFG['python'],ROOT/'tools/release_073/check_identity.py','--archive',BASE/'community_civilization_pack.sga'],folder=log)
    work=STAGE/('hideout-bindings-'+label);assert not work.exists();src=work/'src';shutil.copytree(ROOT/'assets',src/'assets');shutil.copy2(ROOT/CFG['project_file'],src/CFG['project_file'])
    run('binding-compile-'+label,[CFG['garrison_core'],'essence','build-mod','--editor',CFG['content_editor'],'--mod',src/CFG['project_file'],'--run-root',work/'run','--timeout','900'],folder=log,timeout=1200)
    state=read(work/'run/run.json');assert state['status']=='succeeded' and state['exit_code']==0
    logs='\n'.join(p.read_bytes().rstrip(b'\0').decode('utf-8',errors='replace') for p in (work/'run/logs').glob('*') if p.suffix in ('.log','.txt'))
    validated=re.findall(r'(\d+) instances validated',logs);assert validated and int(validated[-1])==len(list((src/'assets/attrib/instances').rglob('*.xml')))
    archives=list((work/'run/output').rglob('*.sga'));assert len(archives)==1
    run('identity-postcompile-'+label,[CFG['python'],ROOT/'tools/release_073/check_identity.py','--archive',archives[0]],folder=log)
    back=out/('binding-readback-'+label);run('binding-readback-'+label,[CFG['archive_tool'],'extract',archives[0],back,'--filter','.'],folder=log)
    write(out/('compile-'+label+'.json'),{'archive':str(archives[0]),'sha256':sha(archives[0]),'readback':str(back),'validated_instances':int(validated[-1]),'status':'native_compile_passed'});return
   raise ValueError(mode)
  finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
if __name__=='__main__':main(*sys.argv[1:])
