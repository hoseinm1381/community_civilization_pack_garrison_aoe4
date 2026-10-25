"""Nine redesigned media resources through the real native art cooker."""
from common import *
import re,shutil,msvcrt,xml.etree.ElementTree as ET
def main(label):
    guard();selection=read(RECIPES/'selection.json');control='--control' in sys.argv
    if control:selection={'javelin2':selection['javelin2']}
    dest=OUT/'cooks'/label;library=STAGE/label;key='a83';project=library/'Mods'/key
    dest.mkdir(parents=True,exist_ok=False);library.mkdir(parents=True,exist_ok=False)
    run('create',[CFG['garrison_core'],'mod-project','create','--library',library,'--name',key],dest)
    run('settings',[CFG['garrison_core'],'mod-project','settings','--project',project,'--live-reload','off'],dest)
    config=read(project/'mod-project.json');assert not config['game_mode']['enabled'] and not config['game_mode'].get('live_reload',False)
    source=project/'project/source';burn=source/'_default.burnproj';text=burn.read_text();records=[]
    template=ROOT/'art/recipes/release_079/art-burn-rules.xml';rules=[s for s in re.findall(r'<BurnRule>.*?</BurnRule>',template.read_text(),re.S) if '__MODEL_PATH__' in s];assert len(rules)==4
    shutil.copyfile(template,RECIPES/'art-burn-rules.xml')
    for family,revision in selection.items():
        e=EXPORT/family/revision;receipt=read(OUT/'art'/family/revision/'export.json');assert sha(receipt['source'])==receipt['source_sha256']
        assert receipt['files']=={p.name:sha(p) for p in e.iterdir() if p.is_file()}
        rel='art/scenario/garrison/cc076/'+family;body=source/rel;body.mkdir(parents=True)
        for name in receipt['files']:shutil.copyfile(e/name,body/name)
        if control:shutil.copyfile(ROOT/'art/exports/release_079/javelin2/r3/model.fbx',body/'model.fbx')
        prior=ROOT/'output/release_081/delivery/final-v1/readback'/rel/'model.rgo';shutil.copyfile(prior,body/'model.rgo')
        (body/'model.rgotemplate').write_text('<ObjectTemplate><LodDistances/></ObjectTemplate>\n')
        root=ET.Element('materialSet')
        for lod in [1,2,3]:
            mat=ET.SubElement(root,'material',{'name':'lod'+str(lod),'type':'shader','source':'unit' if family.startswith('skirmisher') else 'object'})
            slots={'albedoTexture':'albedo','normalMap':'normal','metalTex':'metalness','roughnessTex':'roughness'}
            if family.startswith('skirmisher'):slots['patternTex']='pattern'
            for slot,name in slots.items():ET.SubElement(mat,'param',{'name':slot,'type':'tex2D','value':rel+'/'+name+'.png'})
        ET.indent(root);(body/'model.material').write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
        text=text.replace('</Rules>','\n'.join(r.replace('__MODEL_PATH__',rel.replace('/','\\')) for r in rules)+'\n</Rules>',1)
        records.append({'family':family,'revision':revision,'member_root':rel,'source_files':{p.name:sha(p) for p in body.iterdir()},'source':receipt['source'],'source_sha256':receipt['source_sha256']})
    burn.write_text(text);ET.parse(burn);write(dest/'prepare.json',{'selection':selection,'records':records,'project':str(project)})
    work=library/'burn';work.mkdir();editor=Path(CFG['art_editor'])
    args=[editor,'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report','--no_source_control','--log_path',work/'logs','--build_mod',project/'project'/f'{key}.aoe4mod','--no_burn_window','--burn_verbose_log_level','--burn_cache_type','Local','--burn_max_threads','1','--burn_log_path',work/'logs/burn.log','--build_path',work/'output','--intermediate_path',work/'intermediate']
    (work/'logs').mkdir()
    lock=Path(CFG['external_root'])/'output/release_020/native-build.lock'
    with lock.open('r+b') as f:
        msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        try:run('native-cook',args,dest,1800,editor.parent)
        finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
    output_log=(dest/'native-cook.log').read_text()
    assert 'Package [Archive] created' in output_log or (' copied to [' in output_log and '.sga].' in output_log),'Missing native archive completion'
    for row in records:
        body=source/row['member_root'];assert row['source_files']=={p.name:sha(p) for p in body.iterdir()}
    archives=list((work/'output').rglob('*.sga'));assert len(archives)==1;archive=archives[0]
    listing=json.loads(run('list-verify',[CFG['archive_tool'],'list',archive,'--verify'],dest))
    run('readback',[CFG['archive_tool'],'extract',archive,dest/'readback','--filter','.'],dest)
    write(dest/'receipt.json',{'archive':str(archive),'archive_sha256':sha(archive),'records':records,'member_count':len(listing['members']),'fresh_native_cook':True,'completion_evidence':'native editor final intermediate SGA copied to final output; exit zero; fresh archive verified and extracted','diagnostic_control':control,'native_acceptance':False})
    print('083_NATIVE_COOK_COMPLETE',archive)
if __name__=='__main__':main(sys.argv[1])
