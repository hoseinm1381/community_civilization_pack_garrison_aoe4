"""Fresh, isolated art and native reference qualification; no activation/package API."""
from __future__ import annotations
import argparse
import contextlib
import copy
import hashlib
import json
import msvcrt
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from common import ROOT, OUT, WORK, CFG, CORE, ARCH, ART_EDITOR, NATIVE_LOCK, guarded, read, sha, write, run_logged
from native_support import native, rc, mv, bp, lifecycle, intact_damage_conditions, copy_native_markers
from lifecycle_modes import install as install_modes

@contextlib.contextmanager
def exclusive_native():
    """Shares the same Windows open-file exclusion as the 040 FileStream lock."""
    guarded()
    with NATIVE_LOCK.open('r+b') as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError('Native build lock is busy; retry after the current job ends') from error
        try:yield
        finally:
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)

def asset_inputs(kind):
    if kind=='landmarks':
        rows=[]
        for key in ('imperial_citadel','resistance_hq'):
            row=read(OUT/'landmarks'/key/'handoff.json')
            rows.append({'key':key,'folder':row['export_directory'],'blend':row['source_blend'],
                         'blend_sha256':row['source_blend_sha256'],'parts':row['building']['parts']})
    else:
        rows=[]
        for row in read(OUT/'buildings/details/details-validation.json')['models']:
            folder=Path(row['export_dir'])
            rows.append({'key':f"detail_{row['family']}_age0{row['age']}",'folder':str(folder),
                         'blend':row['source_blend'],'blend_sha256':row['source_blend_sha256'],
                         'parts':read(folder/'building.json')['parts']})
        assert len(rows)==5
    for row in rows:
        folder=Path(row['folder'])
        row['files']={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
        assert {'model.fbx','building.json','albedo.png','normal.png','roughness.png','metalness.png'}<=row['files'].keys()
        assert sha(row['blend'])==row['blend_sha256']
    return rows

def cook(kind,label,owner_colour=False):
    with exclusive_native():
        frozen=asset_inputs(kind)
        name='community_castle_next_'+kind
        project=OUT/'cook'/label/'library/Mods'/name
        assert not project.exists(), 'Use a fresh append-only label'
        project.parent.parent.mkdir(parents=True,exist_ok=True)
        run_logged(label+'-create',[CORE,'mod-project','create','--library',project.parent.parent,'--name',name])
        run_logged(label+'-settings',[CORE,'mod-project','settings','--project',project,'--live-reload','off'])
        for row in frozen:
            run_logged(label+'-'+row['key'],[CORE,'mod-project','building','--project',project,
                       '--source',row['folder'],'--name',row['key'],'--profile','english-house','--integration','script'])
        config=read(project/'mod-project.json')
        assert not config['game_mode']['enabled'] and not config['game_mode']['live_reload']
        owner_recipe=None
        if owner_colour:
            assert kind=='landmarks'
            from owner_colour import prepare_project
            owner_recipe=prepare_project(project,frozen)
            project=Path(owner_recipe['candidate_project'])
        write(OUT/'cook'/label/'input-freeze.json',{'kind':kind,'project':str(project),'assets':frozen,
              'config_sha256':sha(project/'mod-project.json'),'owner_colour_recipe':owner_recipe})
        native.WORK=WORK;native.PROJECT=project
        native.cook(project,'ccnext-'+label)
        assert asset_inputs(kind)==frozen,'Source changed during art cook'
        receipt=WORK/('ccnext-'+label+'-cook.json')
        write(OUT/'cook'/(kind+'-pointer.json'),{'receipt':str(receipt),'inputs':str(OUT/'cook'/label/'input-freeze.json')})
        return read(receipt)

def put(member,raw,rows):
    assert member.startswith('art/scenario/cccastle/'),member
    target=WORK/'payload'/member
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    row={'member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size}
    if member in {r['member'] for r in rows}:assert next(r for r in rows if r['member']==member)==row
    else:rows.append(row)
    return target

def adopt_native(kind,label):
    """Read back a successful Essence cook rejected for repeated texture names.

    The native structure burner emits the same packed texture for multiple
    layers. Garrison's package wrapper rejects those repeated names. Preserve
    that failure; admit only a zero-exit native run with verified archive bytes
    and identical repeat metadata. Final selective composition uses unique
    private resource members and never ships this prototype archive.
    """
    guarded()
    frozen=read(OUT/'cook'/label/'input-freeze.json')
    assert frozen['kind']==kind and frozen['assets']==asset_inputs(kind)
    canonical=Path(frozen['project'])
    assert sha(canonical/'mod-project.json')==frozen['config_sha256']
    short=Path(CFG['external_root'])/'c'/('ccnext-'+label)
    runs=list((short/'dist/cook').glob('*/run.json'));assert len(runs)==1
    state=read(runs[0]);assert state['status']=='succeeded' and state['exit_code']==0
    log=OUT/'logs'/('integration-ccnext-'+label+'.log')
    assert log.read_text().startswith('ERROR: duplicate cooked archive member:')
    archives=list((runs[0].parent/'output').rglob('*.sga'));assert len(archives)==1
    archive=archives[0]
    listing=json.loads(subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,check=True).stdout)
    assert listing['archive']['verification']['verified']
    unique={};repeats=[];ambiguous={}
    for row in listing['members']:
        if row['path'] in unique:
            assert row['path'].endswith('.rrtex'),row
            if row!=unique[row['path']]:ambiguous.setdefault(row['path'],[unique[row['path']]]).append(row)
            repeats.append(row)
        else:unique[row['path']]=row
    assert repeats
    choices={}
    if ambiguous:
        # The structure burner and the generic PNG rule choose different
        # compression for the auxiliary (overlay/charred) atlas. Select the
        # exact successful object-PBR cook of the same source PNG explicitly.
        prior=read(WORK/'ccnext-rland02-cook.json')
        prior_inputs=read(OUT/'cook/rland02/input-freeze.json')
        assert sha(prior['cook']['archive'])==prior['cook']['sha256']
        expected={f"art/scenario/garrison/community_castle_next_landmarks/buildings/{r['key']}/albedo.rrtex" for r in frozen['assets']}
        assert set(ambiguous)<=expected,set(ambiguous)
        for member,variants in ambiguous.items():
            key=member.split('/')[-2]
            new=next(r for r in frozen['assets'] if r['key']==key)
            old=next(r for r in prior_inputs['assets'] if r['key']==key)
            assert new['files']['albedo.png']==old['files']['albedo.png']
            selected=WORK/'native-texture-choices'/label/key/'albedo.rrtex'
            selected.parent.mkdir(parents=True,exist_ok=True)
            if not selected.exists():
                run_logged(label+'-choose-'+key,[ARCH,'extract-member',prior['cook']['archive'],member,selected])
            old_back=Path(prior['readback'])/member
            assert sha(selected)==sha(old_back)
            assert selected.stat().st_size>0
            choices[member]={'file':str(selected),'sha256':sha(selected),'source_png_sha256':new['files']['albedo.png'],
                             'source_native_archive_sha256':prior['cook']['sha256'],'native_variants':variants,
                             'policy':'Use the independently qualified object-PBR RGBA atlas of the exact same PNG for auxiliary overlay/charred texture slots; primary structure packed albedo stays unchanged.'}
    source_hashes={p.relative_to(canonical).as_posix():sha(p) for p in canonical.rglob('*') if p.is_file() and p.name!='.garrison.lock'}
    for relative,digest in source_hashes.items():
        if relative=='mod-project.json':assert read(short/relative)==read(canonical/relative)
        else:assert sha(short/relative)==digest,relative
    back=WORK/('readback-ccnext-'+label+'-'+sha(archive)[:12]);assert not back.exists()
    run_logged(label+'-native-readback',[ARCH,'unpack',archive,'--output',back])
    assert all((back/member).is_file() for member in unique)
    receipt={'status':'passed','route':'Garrison-generated source -> supported Essence CLI native cook/readback',
        'project':str(short),'canonical_project':str(canonical),'canonical_config_sha256':sha(canonical/'mod-project.json'),
        'canonical_sources_sha256':source_hashes,'readback':str(back),
        'cook':{'archive':str(archive),'sha256':sha(archive),'live_reload':False,'native_run':state},
        'package_wrapper_status':'rejected repeated packed texture member names; retained diagnostic',
        'wrapper_log':str(log),'duplicate_texture_entries':repeats,'unique_resources':len(unique),
        'repeat_entry_metadata_identical_except_explicit_auxiliary_choices':True,
        'auxiliary_texture_choices':choices,'archive_verification':listing['archive']['verification'],
        'final_composition':'one payload per private resource path; prototype archive is never shipped',
        'native_runtime':'not tested'}
    path=WORK/('ccnext-'+label+'-cook.json');write(path,receipt)
    write(OUT/'cook'/(kind+'-pointer.json'),{'receipt':str(path),'inputs':str(OUT/'cook'/label/'input-freeze.json')})
    print('NATIVE_COOK_READBACK_QUALIFIED',label,len(unique),len(repeats));return receipt

def material(raw,base,final,back,rows):
    descriptors={x.payload[4:].decode('utf-8','replace') for x in rc.walk(rc.parse(raw).roots) if x.tag==b'MatD'}
    if 'structure' in descriptors:
        from owner_colour import structure_parameters
        raw=mv.rewrite_material(raw,{},structure_parameters())
    edits={};textures={}
    for mat in rc.parse(raw).roots:
        if mat.tag!=b'GMat':continue
        name=mat.decoded_name.removesuffix('_collection')
        one=rc.pack_document([rc.pack_chunk(mat.kind,mat.tag,mat.payload,name=mat.name,version=mat.version)])
        edits[name]={}
        for slot,value in mv.material_slots(one)['textures'].items():
            if not value or value=='__default':continue
            member=value.replace('\\','/').lower()
            if not member.endswith('.rrtex'):member+='.rrtex'
            assert member.startswith(base.rsplit('/',1)[0]+'/'),member
            private=final.rsplit('/',1)[0]+'/'+member.rsplit('/',1)[1]
            edits[name][slot]=private;textures[private]=back/member
    put(final+'.rrmaterial',native.scoped_material(raw,edits),rows)
    choices={}
    if 'structure' in descriptors:
        pointer=read(OUT/'cook/landmarks-pointer.json')
        choices=read(pointer['receipt']).get('auxiliary_texture_choices',{})
    for member,path in textures.items():
        original_member=base.rsplit('/',1)[0]+'/'+member.rsplit('/',1)[1]
        if original_member in choices:
            selected=choices[original_member];assert sha(selected['file'])==selected['sha256'];path=Path(selected['file'])
        put(member,path.read_bytes(),rows)
    return edits

def assemble(kind):
    guarded();rows=[];models=[]
    pointer=read(OUT/'cook'/(kind+'-pointer.json'));cooked=read(pointer['receipt'])
    assert cooked['status']=='passed' and sha(cooked['cook']['archive'])==cooked['cook']['sha256']
    frozen=read(pointer['inputs']);assert frozen['assets']==asset_inputs(kind)
    back=Path(cooked['readback']);project_name='community_castle_next_'+kind
    if kind=='landmarks':
        contracts={r['key']:r for r in read(OUT/'lifecycle/source-contract.json')['actors']}
        for row in frozen['assets']:
            key=row['key'];owner=contracts[key]['qualified_owners'][0]
            base=f'art/scenario/garrison/{project_name}/buildings/{key}/model'
            final=f'art/scenario/cccastle/{key}/model'
            original=native.stock(owner+'.rgm').read_bytes()
            raw=bp.construction_model((back/(base+'.rgm')).read_bytes(),original,row['parts'],profile_id='english-house')
            raw,damage=intact_damage_conditions(raw)
            raw,ruins=install_modes(raw)
            raw,markers=copy_native_markers(raw,original)
            model_file=put(final+'.rgm',native.rebase_model(raw,final),rows)
            put(final+'.rrgeom',(back/(base+'.rrgeom')).read_bytes(),rows)
            rgo=native.stock(owner+'.rgo');rgo_file=put(final+'.rgo',rgo.read_bytes(),rows)
            edits=material((back/(base+'.rrmaterial')).read_bytes(),base,final,back,rows)
            models.append({'key':key,'model':final,'model_file':str(model_file),'rgo_file':str(rgo_file),
                           'native_owner':owner,'owner_sha256':sha(rgo),'markers':markers,
                           'damage':damage,'ruins':ruins,'materials':edits})
    else:
        for row in read(OUT/'buildings/model-validation.json')['models']:
            final=row['private_model_stem'];original=row['stock_model_stem']
            geometry=Path(row['native_geometry']);assert sha(geometry)==row['native_geometry_sha256']
            source_model=native.stock(original+'.rgm')
            if row.get('native_model'):
                source_model=Path(row['native_model'])
                assert sha(source_model)==row['native_model_sha256']
            put(final+'.rgm',native.rebase_model(source_model.read_bytes(),final),rows)
            put(final+'.rrgeom',geometry.read_bytes(),rows)
            for ext in ('.rgo','.rrmaterial'):put(final+ext,native.stock(original+ext).read_bytes(),rows)
            models.append({'key':row['name'],'model':final,'native_owner':original,
                           'kind':'remodeled_native_base','preserved_native_owner_mask':True,
                           'hidden_native_selector_names':row.get('hidden_native_selector_names',[]),
                           'source_model_sha256':sha(source_model)})
        assert len(models)==5
        details=read(OUT/'buildings/details/details-validation.json')['models']
        for row in frozen['assets']:
            key=row['key'];info=next(d for d in details if key==f"detail_{d['family']}_age0{d['age']}")
            final=info['private_model_stem']
            base=f'art/scenario/garrison/{project_name}/buildings/{key}/model'
            raw,damage=intact_damage_conditions((back/(base+'.rgm')).read_bytes())
            _,pairs=lifecycle._pairs(raw)
            assert not any(c[-1]=='ruins' for _,chunk in pairs for c in lifecycle._conditions(chunk))
            put(final+'.rgm',native.rebase_model(raw,final),rows)
            for ext in ('.rrgeom','.rgo'):put(final+ext,(back/(base+ext)).read_bytes(),rows)
            edits=material((back/(base+'.rrmaterial')).read_bytes(),base,final,back,rows)
            models.append({'key':key,'model':final,'kind':'authored_detail','damage':damage,'materials':edits})
    result={'schema':'ccp.castle-isolated-media/v1','status':'passed','kind':kind,
            'payloads':rows,'models':models,'cook':cooked,'active_bindings_applied':False,'native_runtime':'not tested'}
    write(WORK/('landmark-media.json' if kind=='landmarks' else 'building-media.json'),result)
    print('CASTLE_MEDIA_READY',kind,len(models),len(rows))
    return result

def reference(kind,label,with_branches=False):
    with exclusive_native():
        media=read(WORK/('landmark-media.json' if kind=='landmarks' else 'building-media.json'))
        cooked=media['cook'];models=list(media['models']);rows=list(media['payloads'])
        if with_branches:
            assert kind=='landmarks'
            binding=read(OUT.parent/'release_050/integration/private-bindings.json')
            assert binding['status']=='passed'
            for row in binding['branch_variants']:models.append({'model':row['model'],'key':'campaign_variant'})
            rows.extend(r for r in binding['payloads'] if r['member'].startswith('art/scenario/cc050/'))
            assert len({r['member'] for r in rows})==len(rows)
        project=Path(cooked['project'])/'project'
        root=OUT/'reference'/label;assert not root.exists();source=root/'source';source.mkdir(parents=True)
        mods=list(project.glob('*.aoe4mod'));assert len(mods)==1
        shutil.copy2(mods[0],root/'reference.aoe4mod')
        for row in rows:
            assert sha(row['file'])==row['sha256']
            target=source/row['member'];target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(row['file'],target)
            if target.suffix=='.rrmaterial':shutil.copy2(target,target.with_suffix('.material'))
        template=next((project/'source/art/stamps').rglob('*.rdo'))
        burn=(project/'source/_default.burnproj').read_text(encoding='utf-8-sig')
        burn=re.sub(r'<BurnRule>.*?</BurnRule>',lambda m:m[0].replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>'),burn,flags=re.S)
        rules=[];refs=[]
        for index,row in enumerate(models):
            doc=ET.parse(template);tree=doc.getroot()
            ids={n.get('Id'):str(int.from_bytes(hashlib.sha256(('castle:'+label+':'+str(index)+':'+n.get('Id')).encode()).digest()[:8],'little')) for n in tree.iter('DataObject')}
            for node in tree.iter():
                for attr in ('Id','OwnerId'):
                    if node.get(attr) in ids:node.set(attr,ids[node.get(attr)])
                if node.tag=='DataValue' and node.text in ids:node.text=ids[node.text]
                if node.tag=='DataProperty' and node.get('Name')=='m_objectID' and node.get('Value') in ids:node.set('Value',ids[node.get('Value')])
                if node.tag=='DataProperty' and node.get('Name')=='m_blueprint':node.set('Value',row['model'].replace('/','\\'))
            member=f'art/stamps/cccastle/reference_{index}'
            target=source/(member+'.rdo');target.parent.mkdir(parents=True,exist_ok=True)
            ET.indent(tree);target.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True))
            rules.append('<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true"/><Includes>'+member.replace('/','\\')+'.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>')
            refs.append({'member':member+'.bin','model':row['model']})
        assert burn.count('</Rules>')==1
        (source/'_default.burnproj').write_text(burn.replace('</Rules>',''.join(rules)+'</Rules>'),encoding='utf-8')
        inputs={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
        write(root/'input-freeze.json',{'files':inputs,'references':refs})
        runroot=OUT/'reference-runs'/label
        command=run_logged('reference-'+label,[CORE,'essence','build-mod','--editor',ART_EDITOR,'--mod',root/'reference.aoe4mod','--run-root',runroot,'--timeout','900'],timeout=1100)
        state=read(runroot/'run.json');assert state['status']=='succeeded' and state['exit_code']==0
        archives=list((runroot/'output').rglob('*.sga'));assert len(archives)==1
        back=[]
        for row in refs:
            target=root/'readback'/row['member'];target.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run([str(ARCH),'extract-member',str(archives[0]),row['member'],str(target)],capture_output=True,check=True)
            actual=[v['model'].replace('\\','/').lower() for v in native.active_visuals(native.NativeTree(target))]
            assert actual==[row['model'].lower()],(row,actual)
            back.append({'member':row['member'],'sha256':sha(target),'model':actual[0]})
        assert inputs=={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
        result={'status':'passed','kind':kind,'archive':str(archives[0]),'sha256':sha(archives[0]),
                'run':state,'model_references':back,'exact_inputs_sha256':inputs,'command':str(command),
                'active_bindings_applied':False,'native_match':'not tested'}
        write(WORK/(kind+('-branches' if with_branches else '')+'-reference.json'),result)
        print('CASTLE_REFERENCE_PASS',kind,len(back));return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('cook','adopt-native','assemble','reference'));parser.add_argument('kind',choices=('landmarks','details'));parser.add_argument('label',nargs='?',default='r001');parser.add_argument('--owner-colour',action='store_true');parser.add_argument('--with-branches',action='store_true');args=parser.parse_args()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}',args.label)
    if args.action=='cook':cook(args.kind,args.label,args.owner_colour)
    elif args.action=='adopt-native':adopt_native(args.kind,args.label)
    elif args.action=='assemble':assemble(args.kind)
    else:reference(args.kind,args.label,args.with_branches)
