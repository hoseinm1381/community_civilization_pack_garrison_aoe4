"""Explicit official-resource inventory and private visual integration for 0.1.0.

NativeTree's generic schema reader was adapted from the Berber workflow. All data
is freshly extracted from official archives into this project's owned output.
"""
import copy, hashlib, json, os, re, shutil, sqlite3, struct, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from common import ROOT, OUT, STAGING, CONFIG, CORE, ARCH, ART_EDITOR, sha, read, write, run_logged as shared_run_logged
from integration_native import NativeTree
sys.path.insert(0,CONFIG['garrison_extension'])
from garrison_shared import relic_chunky as rc, rgd, model_variants as mv, building_project as bp
WORK=OUT/'integration'
CACHEWORK=WORK
PROJECT=WORK/'library/Mods/community_010_bindings'
CONSUMERS=['vn_building_house_control_chi','vn_building_house_control_faster_chi',
           'vn_building_bambo_outpost_chi','vn_building_defense_outpost_bambo_chi']

def log_label(label):return label if WORK==CACHEWORK else label+'-'+WORK.name

def run_logged(label,command,**kwargs):
    return shared_run_logged(log_label(label),command,**kwargs)

def stock(member):
    member=member.replace('\\','/').lower()
    index=CACHEWORK/'official-index.json'; records=read(index) if index.exists() else {}
    db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
    row=db.execute('select archive_path from resolved_assets where lower(logical_path)=?',(member,)).fetchone();db.close()
    if not row and member.startswith('attrib/'):
        row=('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',)
    if not row and member.startswith('art/stamps/'):
        row=('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Data.sga',)
    assert row,('Official resource unresolved',member)
    archive=Path(row[0]); stat=archive.stat(); fingerprint={'path':str(archive),'size':stat.st_size,'mtime_ns':stat.st_mtime_ns}
    previous=records.get(member)
    path=Path(previous['file']) if previous else CACHEWORK/'official'/member
    if not previous or previous['archive']!=fingerprint or not path.exists() or sha(path)!=previous['sha256']:
        CACHEWORK.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=CACHEWORK) as temp:
            extracted=Path(temp)/Path(member).name
            subprocess.run([str(ARCH),'extract-member',str(archive),member,str(extracted)],capture_output=True,check=True)
            digest=sha(extracted)
            if path.exists() and sha(path)!=digest:path=CACHEWORK/'official-content'/digest/Path(member).name
            if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(extracted,path)
            assert sha(path)==digest
    records[member]={'archive':fingerprint,'sha256':sha(path),'file':str(path)};write(index,records)
    return path

def active_visuals(tree):
    root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
    array=tree.field(root,root['fields']['m_blueprints']);rows=[]
    for i in range(array['count']):
        slot=array['data_address']+8*i;obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
        if obj['type']=='VisualStampBlueprint':
            transform=bytes.fromhex(tree.field(obj,obj['fields']['m_transform'])['raw'])
            rows.append({'id':str(obj['id']),'model':tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/'),'transform':list(struct.unpack('<10f',transform))})
    return rows

def inventory():
    from workspace_support import check_storage
    check_storage(ROOT,CONFIG)
    consumers=[];tiers={};stamps={}
    for name in CONSUMERS:
        path=STAGING/'baseline_source/assets/attrib/instances/ebps/vietnam'/(name+'.xml');doc=ET.parse(path).getroot()
        rows=[]
        def walk(node,prefix):
            for i,n in enumerate(node):
                p=prefix+'/'+n.get('name',n.tag)+'['+str(i)+']'
                if n.tag=='instance_reference' and n.get('name') in ['attachments','animator_attachments'] and n.get('value'):
                    ref=n.get('value');rows.append({'path':p,'value':ref,'mod':n.get('mod')})
                    if ref not in tiers:
                        member='attrib/'+ref.replace('\\','/')+'.rgd';raw=stock(member)
                        parsed=rgd.read(raw.read_bytes());fields=[]
                        for field,native in rgd.flatten(parsed.nodes):
                            if native.kind=='CString' and native.value and any(k in native.key for k in ['stamp','animator','mesh','category']):
                                fields.append({'path':field,'value':native.value})
                                if native.key=='stamp':
                                    stamp=native.value.replace('\\','/')+'.bin'
                                    if stamp not in stamps:
                                        tree=NativeTree(stock(stamp));stamps[stamp]={'visuals':active_visuals(tree),'object_types':{t:sum(o['type']==t for o in tree.objects.values()) for t in set(o['type'] for o in tree.objects.values())},'sha256':sha(tree.path)}
                        tiers[ref]={'member':member,'file':str(raw),'fields':fields}
                walk(n,p)
        walk(doc,'')
        consumers.append({'name':name,'source':str(path),'sha256':sha(path),'visual_references':rows,'scale':[(n.get('name'),n.get('value')) for n in doc.iter('float') if n.get('name') in ['animator_scale','entity_scale']]})
    result={'schema':'community.release010.native-graph/v1','status':'official source inventory','consumers':consumers,'tiers':tiers,'stamps':stamps,'runtime':'unverified'}
    write(WORK/'native-graph.json',result)
    print('NATIVE_GRAPH',len(consumers),'consumers',len(tiers),'tiers',len(stamps),'stamps')

def cli(*args):
    env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
    result=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True,encoding='utf8',errors='replace',env=env)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    return result.stdout

def derive():
    """Allocate private identities through installed Garrison generator."""
    from workspace_support import check_storage
    check_storage(ROOT,CONFIG)
    if not (PROJECT/'mod-project.json').exists():cli('mod-project','create','--library',WORK/'library','--name',PROJECT.name)
    cli('mod-project','settings','--project',PROJECT,'--live-reload','off','--mod-id',CONFIG['project_guid'])
    record=read(PROJECT/'mod-project.json'); existing={r['name'] for r in record.get('derived_blueprints',[])}
    graph=read(WORK/'native-graph.json');rows=[]
    for source,contract in graph['tiers'].items():
        if '\\outskirts\\' in source:continue
        if 'house_chi' in source:name='vn_house_age0'+re.search(r'tier(\d)',source).group(1)+'_visual'
        elif source.endswith('military_tent_a'):name='vn_trap_thicket_visual'
        elif source.endswith('military_tent_b'):name='vn_trap_palisade_visual'
        elif source.endswith('substruct_firewood'):name='vn_trap_parent_visual'
        else:raise AssertionError(source)
        if name not in existing:cli('mod-project','derive','--project',PROJECT,'--source',source.replace('\\','/'),'--name',name)
        rows.append({'source':source,'name':name,'contract':contract})
    write(WORK/'derived-contracts.json',{'project':str(PROJECT),'tiers':rows})
    print('PRIVATE_LISTS_ALLOCATED',len(rows))

def cook(project,label):
    """Only call while holding the root's exclusive native cook token."""
    project=Path(project);canonical=project
    source_hashes={p.relative_to(project).as_posix():sha(p) for p in project.rglob('*') if p.is_file() and p.name!='.garrison.lock'}
    short=Path(CONFIG['external_root'])/'c'/label
    assert short.resolve().is_relative_to(Path(CONFIG['external_root']).resolve()) and not short.exists()
    shutil.copytree(project,short,ignore=shutil.ignore_patterns('.garrison.lock'))
    copied_hashes={p.relative_to(short).as_posix():sha(p) for p in short.rglob('*') if p.is_file() and p.name!='.garrison.lock'}
    assert source_hashes==copied_hashes,'Cook copy is not byte-identical'
    assert sha(project/'mod-project.json')==sha(short/'mod-project.json')
    project=short;record=read(project/'mod-project.json')
    assert record['game_mode']['enabled'] is False and record['game_mode']['live_reload'] is False
    previous=len(record.get('cooks',[]))
    command=run_logged('integration-'+label,[CORE,'mod-project','cook','--project',project,'--editor',ART_EDITOR,'--timeout','900'])
    record=read(project/'mod-project.json');assert len(record.get('cooks',[]))==previous+1
    result=record['cooks'][-1];assert result['live_reload'] is False and sha(result['archive'])==result['sha256']
    after_hashes={p.relative_to(canonical).as_posix():sha(p) for p in canonical.rglob('*') if p.is_file() and p.name!='.garrison.lock'}
    assert after_hashes==source_hashes,'Canonical source changed during native cook'
    back=WORK/('readback-'+label+'-'+result['sha256'][:12]);assert not back.exists()
    run_logged('integration-'+label+'-unpack',[ARCH,'unpack',result['archive'],'--output',back])
    write(WORK/(label+'-cook.json'),{'status':'passed','canonical_project':str(canonical),'canonical_config_sha256':sha(canonical/'mod-project.json'),'canonical_sources_sha256':source_hashes,'short_copy_byte_identical_before_cook':True,'canonical_source_parity_after_cook':True,'project':str(project),'cook':result,'readback':str(back),'command':command,'native_runtime':'unverified'})
    print('FRESH_ART_COOK',label,result['sha256'],flush=True)

def prepare_traps(scope='qualification'):
    from workspace_support import check_storage
    check_storage(ROOT,CONFIG)
    recipe=read(ROOT/'art/recipes/release_010/traps_010.json')
    names=['stake_thicket'] if scope=='qualification' else ['stake_thicket','stake_fan']
    sources={}
    for name in names:
        source=ROOT/'art/exports/traps_010'/name
        sources[name]={p.name:sha(p) for p in source.iterdir() if p.is_file()}
        cli('mod-project','building','--project',PROJECT,'--source',source,'--name',name,'--profile','english-house','--integration','script')
    record=read(PROJECT/'mod-project.json')
    if 'vn_trap_parent_native' not in {v['name'] for v in record.get('model_variants',[])}:
        cli('mod-project','variant','--project',PROJECT,'--source','art/civilizations/common/props/wood_firewood/wood_firewood','--name','vn_trap_parent_native')
    write(WORK/('traps-'+scope+'-input.json'),{'sources':sources,'recipe_sha256':sha(ROOT/'art/recipes/release_010/traps_010.json'),'project':str(PROJECT),'status':'prepared'})
    print('TRAP_INPUTS_FROZEN',scope,flush=True)

def prepare_house_qualification():
    ready=read(OUT/'houses/materials-ready.json');source=Path(ready['project']);target=WORK/'house-qualification-project'
    assert not target.exists();shutil.copytree(source,target,ignore=shutil.ignore_patterns('.garrison.lock'))
    config=read(target/'mod-project.json');config['model_variants']=[v for v in config['model_variants'] if v['name'] in ['vn_house_age01','vn_house_age01_main']]
    assert len(config['model_variants'])==2;write(target/'mod-project.json',config)
    inputs={t['image']:t['sha256'] for m in ready['models'] if m['age']==1 for material in m['materials'] for t in material['textures']}
    assert all(sha(p)==digest for p,digest in inputs.items())
    write(WORK/'house-qualification-inputs.json',{'canonical_project':str(source),'project':str(target),'models':[m for m in ready['models'] if m['age']==1],'inputs':inputs})
    print('HOUSE_QUALIFICATION_PREPARED',flush=True)

def private_stamp(source,output,replacements,remove_ids=()):
    """Only fixed-width model strings, native graph IDs, root visual reachability.

    Fresh native reference cook separately validates all replacement models. No
    terrain/functional object is reconstructed or removed.
    """
    tree=NativeTree(source);memory=bytearray(tree.memory.payload)
    objects=bytearray(tree.chunks[b'ROBJ'].payload);creation=bytearray(tree.chunks[b'RNEW'].payload)
    identities={oid:int.from_bytes(hashlib.sha256(('community010:'+str(output)+':'+str(oid)).encode()).digest()[:8],'little') for oid in tree.objects}
    changes=[]
    for index,(oid,obj) in enumerate(tree.objects.items()):
        off=8+index*36;old,tid,address,owner,checksum=struct.unpack_from('<QQQQI',objects,off)
        assert old==oid;struct.pack_into('<QQQQI',objects,off,identities[oid],tid,address,identities.get(owner,0),checksum)
        for name,field in obj['fields'].items():
            at=obj['offset']+int(field.get('Offset'))-tree.memory.payload_offset
            if name=='m_objectID':
                old=struct.unpack_from('<Q',memory,at)[0]
                if old in identities:struct.pack_into('<Q',memory,at,identities[old])
            if name=='m_blueprint':
                old=tree.field(obj,field)['text'];new=replacements.get(old.replace('\\','/'))
                if new is None:continue
                assert field.get('FieldTypeName')=='util::ReflectString<StdTraits>','Fresh key-table route required for hashed string'
                displacement,count=struct.unpack_from('<qQ',memory,at);value=new.replace('/','\\').encode();assert len(value)<=count
                start=at+displacement;memory[start:start+count]=value+b'\0'*(count-len(value));struct.pack_into('<Q',memory,at+8,len(value))
                changes.append({'id':str(oid),'before':old,'after':new})
    assert len(changes)==len(replacements)
    for index in range(struct.unpack_from('<Q',creation)[0]):
        at=8+29*index;oid=struct.unpack_from('<Q',creation,at)[0];struct.pack_into('<Q',creation,at,identities[oid])
    root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
    field=root['fields']['m_blueprints'];array=tree.field(root,field);kept=[];removed=[]
    for i in range(array['count']):
        slot=array['data_address']+8*i;obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
        if str(obj['id']) in set(map(str,remove_ids)):
            assert obj['type']=='VisualStampBlueprint';removed.append(str(obj['id']))
        else:kept.append(obj)
    assert set(removed)==set(map(str,remove_ids))
    if removed:
        at=root['offset']+int(field.get('Offset'))-tree.memory.payload_offset;struct.pack_into('<II',memory,at+8,len(kept),array['capacity'])
        for i,obj in enumerate(kept):
            slot=array['data_address']+8*i;struct.pack_into('<q',memory,slot-tree.memory.payload_offset,obj['offset']-slot)
        for i in range(len(kept),array['count']):struct.pack_into('<q',memory,array['data_address']+8*i-tree.memory.payload_offset,0)
    edits={tree.memory.offset:bytes(memory),tree.chunks[b'ROBJ'].offset:bytes(objects),tree.chunks[b'RNEW'].offset:bytes(creation)}
    raw=rc.rebuild(tree.document,lambda c:edits.get(c.offset));Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_bytes(raw)
    final=NativeTree(output);assert len(final.objects)==len(tree.objects)
    return {'source':str(source),'source_sha256':sha(source),'output':str(output),'sha256':sha(output),'changed_model_strings':changes,'removed_visual_ids':removed,'preserved_native_objects':len(tree.objects),'before':active_visuals(tree),'after':active_visuals(final),'native_terrain_records':'not reconstructed; other records retained','runtime':'unverified'}

def register_identities(cook_label):
    cook=read(WORK/(cook_label+'-cook.json'));back=Path(cook['readback']);rows=[]
    for contract in read(WORK/'derived-contracts.json')['tiers']:
        name=contract['name'];member=f'attrib/attachments/attachment_lists/garrison/{PROJECT.name}/{name}.rgd';source=back/member
        data=rgd.read(source.read_bytes());ids={n.value for p,n in rgd.flatten(data.nodes) if n.key=='pbgid'};assert len(ids)==1;identity=next(iter(ids))
        root=ET.Element('instance',version='2',description='Garrison-owned visual identity. Full native list supplied by approved release_010 integration recipe.',template=r'attachments\attachment_lists')
        ET.SubElement(root,'uniqueid',name='pbgid',value=str(identity));ET.SubElement(root,'instance_reference',name='parent_pbg',value=contract['source'])
        relative='attrib/instances/attachments/attachment_lists/vietnam/'+name+'.xml';target=ROOT/'assets'/relative
        ET.indent(root,space='\t');raw=ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'
        if target.exists():
            previous=target.read_bytes()
            assert previous==raw or previous.replace(b"encoding='utf8'",b"encoding='utf-8'")==raw,('Private identity source drift',target)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        rows.append({'source':relative,'name':name,'pbgid':identity,'generated_member':member,'generated_sha256':sha(source),'final_member':'attrib/attachments/attachment_lists/vietnam/'+name+'.rgd'})
    write(WORK/'registered-identities.json',rows);print('REGISTERED_PRIVATE_IDENTITIES',len(rows))

def put(member,raw,rows):
    path=WORK/'payload'/member;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    rows.append({'member':member,'file':str(path),'sha256':sha(path),'bytes':len(raw)})

def rebase_model(raw,stem):
    doc=rc.parse(raw);bana=[c for c in rc.walk(doc.roots) if c.tag==b'BANA'];assert len(bana)==1
    return rc.rebuild(doc,lambda c:rc.lp_string(stem.replace('/','\\')) if c.offset==bana[0].offset else None)

def scoped_material(raw,edits):
    doc=rc.parse(raw);changes={}
    assert set(edits)<={c.decoded_name.removesuffix('_collection') for c in doc.roots if c.tag==b'GMat'}
    for c in doc.roots:
        name=c.decoded_name.removesuffix('_collection')
        if c.tag!=b'GMat' or name not in edits:continue
        one=rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,version=c.version,name=c.name)])
        updated=mv.rewrite_material(one,edits[name],{})
        changes[c.offset]=rc.parse(updated).roots[0].payload
    return rc.rebuild(doc,lambda c:changes.get(c.offset))

def houses_media(label,scope='all'):
    cooked=read(WORK/(label+'-cook.json'));back=Path(cooked['readback']);ready=read(OUT/'houses/materials-ready.json');geom=read(OUT/'houses/geometry-validation.json')
    records=[]
    for model in ready['models']:
        age=model['age']
        if scope=='qualification' and age!=1:continue
        row=next(m for m in geom['models'] if m['age']==age);assert sha(row['native_geometry'])==row['native_geometry_sha256']
        donor=f'art/civilizations/chinese/structures/house/chi_house_control_a_age0{age}/chi_house_control_a_age0{age}'
        final=f'art/scenario/cc010/h{age}/model';edits={};payloads=[]
        for material in model['materials']:
            edits[material['name']]={}
            for texture in material['textures']:
                assert sha(texture['image'])==texture['sha256']
                member=mv.texture_member('community_civilization_pack',material['carrier'],texture['slot']).replace('\\','/')+'.rrtex'
                if scope=='qualification' and not (back/member).exists():continue
                assert (back/member).exists(),member
                edits[material['name']][texture['slot']]=member
                put(member,(back/member).read_bytes(),payloads)
        original_model=stock(donor+'.rgm').read_bytes();raw=rebase_model(original_model,final)
        put(final+'.rgm',raw,payloads);put(final+'.rgo',stock(donor+'.rgo').read_bytes(),payloads)
        put(final+'.rrgeom',Path(row['native_geometry']).read_bytes(),payloads)
        native_material=stock(donor+'.rrmaterial').read_bytes();material=scoped_material(native_material,edits)
        put(final+'.rrmaterial',material,payloads)
        checks=[]
        for old,new in zip(rc.parse(native_material).roots,rc.parse(material).roots):
            def slots(c):return mv.material_slots(rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,name=c.name,version=c.version)]))
            before,after=slots(old),slots(new);name=old.decoded_name.removesuffix('_collection')
            for slot,value in before['textures'].items():
                if slot not in edits.get(name,{}):assert after['textures'][slot]==value,(age,name,slot)
            assert before['parameters']==after['parameters']
            checks.append({'name':name,'native_nonrepaint_slots_and_shader_parameters_preserved':True})
        stamp=WORK/'payload'/f'art/stamps/cc010/house_age0{age}.bin';source=stock(f'art/stamps/civ_chinese/chi_house_a_age_0{age}.bin')
        report=private_stamp(source,stamp,{donor:final})
        payloads.append({'member':stamp.relative_to(WORK/'payload').as_posix(),'file':str(stamp),'sha256':sha(stamp),'bytes':stamp.stat().st_size})
        records.append({'age':age,'principal':final,'geometry_route':'native donor known vertex spans only; topology, all native lifecycle collections and UV data retained','geometry':row,'native_rgo_sha256':sha(stock(donor+'.rgo')),'native_model_nonpath_fields_preserved':True,'material_checks':checks,'stamp':report,'payloads':payloads})
    write(WORK/('houses-'+scope+'-media.json'),{'status':'passed native structural assembly','cook_label':label,'cook':cooked,'models':records,'runtime':'unverified'})
    print('HOUSE_MEDIA',len(records),flush=True)

def trap_media(label,name):
    from integration_codec import copy_native_markers,copy_native_skeleton_owner,intact_damage_conditions,visibility_evidence
    cooked=read(WORK/(label+'-cook.json'));back=Path(cooked['readback']);source=ROOT/'art/exports/traps_010'/name
    parts=read(source/'building.json')['parts'];letter='a' if name=='stake_thicket' else 'b';code='t1' if letter=='a' else 't2'
    base=f'art/scenario/garrison/{PROJECT.name}/buildings/{name}/model'
    donor=f'art/civilizations/campaign_english/structures/tent/eng_tent_control_{letter}/eng_tent_control_{letter}'
    final=f'art/scenario/cc010/{code}/model';native=stock(donor+'.rgm').read_bytes()
    raw=bp.construction_model((back/(base+'.rgm')).read_bytes(),native,parts,profile_id='english-house')
    raw,damage=intact_damage_conditions(raw);visibility=visibility_evidence(raw,parts)
    raw,markers=copy_native_markers(raw,native) if letter=='a' else copy_native_skeleton_owner(raw,native,parts)
    fresh_collection=next(c.payload for c in rc.walk(rc.load(back/(base+'.rgm')).roots) if c.tag==b'DATA')
    actual_collection=next(c.payload for c in rc.walk(rc.parse(raw).roots) if c.tag==b'DATA');assert fresh_collection==actual_collection
    raw=rebase_model(raw,final);payloads=[]
    put(final+'.rgm',raw,payloads);put(final+'.rgo',stock(donor+'.rgo').read_bytes(),payloads)
    for ext in ['.rrgeom','.rrmaterial']:put(final+ext,(back/(base+ext)).read_bytes(),payloads)
    for path in (back/Path(base).parent).glob('*.rrtex'):put(path.relative_to(back).as_posix(),path.read_bytes(),payloads)
    stamp=WORK/'payload'/f'art/stamps/cc010/{name}.bin';report=private_stamp(stock(f'art/stamps/campaign/eng_tent_{letter}.bin'),stamp,{donor:final})
    payloads.append({'member':stamp.relative_to(WORK/'payload').as_posix(),'file':str(stamp),'sha256':sha(stamp),'bytes':stamp.stat().st_size})
    result={'status':'passed native structural assembly','name':name,'principal':final,'source_cook':cooked,'fresh_geometry_byte_identical':True,'collection_data_byte_identical':True,'native_geometry_lods':1,'lower_lod_activation':'unsupported and unclaimed','native_rgo_sha256':sha(stock(donor+'.rgo')),'native_lifecycle_graph':'exact original consuming tent RGO','markers':markers,'visibility':visibility,'damage':damage,'stamp':report,'payloads':payloads,'runtime':'unverified'}
    write(WORK/(name+'-media.json'),result);print('TRAP_MEDIA_ASSEMBLED',name,flush=True)

def parent_media():
    donor='art/civilizations/common/props/wood_firewood/wood_firewood';final='art/scenario/cc010/tp/model';raw=stock(donor+'.rgm').read_bytes();doc=rc.parse(raw);edits={};rows=[]
    for c in rc.walk(doc.roots):
        if c.tag==b'MSD ' and len(c.payload)>4:
            name,at=rc.read_lp_string(c.payload,0);count=struct.unpack_from('<I',c.payload,at)[0]
            if count:edits[c.offset]=rc.lp_string(name)+struct.pack('<I',0)
    assert len(edits)==2
    hidden=rebase_model(rc.rebuild(doc,lambda c:edits.get(c.offset)),final)
    put(final+'.rgm',hidden,rows)
    for ext in ['.rgo','.rrgeom','.rrmaterial']:put(final+ext,stock(donor+ext).read_bytes(),rows)
    before=[(c.tag,c.payload) for c in rc.walk(doc.roots) if c.tag not in [b'MODL',b'MSHS',b'MSLC',b'MSCL',b'MSD ',b'BANA'] and c.kind!=b'FOLD']
    after=[(c.tag,c.payload) for c in rc.walk(rc.parse(hidden).roots) if c.tag not in [b'MODL',b'MSHS',b'MSLC',b'MSCL',b'MSD ',b'BANA'] and c.kind!=b'FOLD']
    assert before==after
    write(WORK/'trap-parent-media.json',{'status':'passed','principal':final,'payloads':rows,'native_rgo_sha256':sha(stock(donor+'.rgo')),'mesh_selector_membership_cleared':len(edits),'native_markers_and_nonselector_leaf_chunks':'byte-identical','runtime':'unverified'})

def bind_sources():
    """Mirror generator-owned identity stubs and exact original actor refs."""
    ids={r['name']:r for r in read(WORK/'registered-identities.json')};mapping={r['source']:r['name'] for r in read(WORK/'derived-contracts.json')['tiers']}
    changed=[]
    for name in CONSUMERS:
        path=ROOT/'assets/attrib/instances/ebps/vietnam'/(name+'.xml');text=path.read_text();changes=[]
        def replace(match):
            value=re.search(r'value="([^"]+)"',match[0]).group(1)
            if value not in mapping:return match[0]
            target='attachments\\attachment_lists\\vietnam\\'+mapping[value];new=match[0].replace('value="'+value+'"','value="'+target+'"')
            assert ' mod=' not in new
            new=new.replace('value="'+target+'"','value="'+target+'" mod="'+CONFIG['project_guid'].replace('-','')+'"')
            changes.append({'before':value,'after':target});return new
        updated=re.sub(r'<instance_reference name="(?:attachments|animator_attachments)"[^>]+/>',replace,text)
        if changes:path.write_text(updated,encoding='utf8',newline='')
        else:
            own={r.get('value') for r in ET.fromstring(updated).iter('instance_reference') if r.get('name') in ['attachments','animator_attachments'] and r.get('mod')==CONFIG['project_guid'].replace('-','')}
            expected={'attachments\\attachment_lists\\vietnam\\'+n for s,n in mapping.items() if any(r.get('value')==s for r in ET.parse(STAGING/'baseline_source/assets/attrib/instances/ebps/vietnam'/(name+'.xml')).getroot().iter('instance_reference'))}
            assert own==expected,(name,'bound source drift',own,expected)
        changed.append({'source':path.relative_to(ROOT/'assets').as_posix(),'changes':changes})
    from source_policy import verify
    proof=verify([r['source'] for r in ids.values()]);write(WORK/'source-bindings.json',{'actors':changed,'source_new_files':[r['source'] for r in ids.values()],'preservation':proof})
    print('ACTOR_SOURCES_BOUND',len(changed),flush=True)

def bind_payloads(cook_label):
    identity={r['name']:r for r in read(WORK/'registered-identities.json')};rows=[];proof=[]
    for contract in read(WORK/'derived-contracts.json')['tiers']:
        name=contract['name'];original=rgd.read(Path(contract['contract']['file']).read_bytes());data=copy.deepcopy(original);changes=[]
        for path,node in rgd.flatten(data.nodes):
            if node.key=='pbgid':node.value=identity[name]['pbgid'];continue
            if node.kind!='CString':continue
            value=node.value
            if name.startswith('vn_house_age') and node.key=='stamp' and re.fullmatch(r'art\\stamps\\civ_chinese\\chi_house_[abc]_age_0\d',value):
                age=re.search(r'age0(\d)',name).group(1);node.value=f'art\\stamps\\cc010\\house_age0{age}'
            elif name=='vn_trap_thicket_visual' and node.key=='stamp' and value==r'art\stamps\campaign\eng_tent_a':node.value=r'art\stamps\cc010\stake_thicket'
            elif name=='vn_trap_palisade_visual' and node.key=='stamp' and value==r'art\stamps\campaign\eng_tent_b':node.value=r'art\stamps\cc010\stake_fan'
            elif name=='vn_trap_parent_visual' and node.key=='parent_animator' and value==r'art\civilizations\common\props\wood_firewood\wood_firewood':node.value=r'art\scenario\cc010\tp\model'
            if value!=node.value:changes.append({'path':path,'before':value,'after':node.value})
        assert changes,name
        restored=copy.deepcopy(data)
        for path,node in rgd.flatten(restored.nodes):
            if node.key=='pbgid':node.value=rgd.find(original.nodes,path).value
        for change in changes:rgd.find(restored.nodes,change['path']).value=change['before']
        assert rgd.write(restored)==rgd.write(original),'Nonvisual/list identity changed'
        raw=rgd.write(data);put(identity[name]['final_member'],raw,rows)
        decoded=rgd.read(raw)
        for change in changes:assert rgd.find(decoded.nodes,change['path']).value==change['after']
        proof.append({'name':name,'changes':changes,'pbgid':identity[name]['pbgid'],'all_other_native_fields_and_variants_preserved':True})
    write(WORK/'private-bindings.json',{'status':'passed','payloads':rows,'tiers':proof,'source_cook':read(WORK/(cook_label+'-cook.json')),'runtime':'unverified'})
    print('NATIVE_LISTS_BOUND',len(rows),flush=True)

def media_payloads():
    rows=[]
    for model in read(WORK/'houses-all-media.json')['models']:rows.extend(model['payloads'])
    for name in ['stake_thicket','stake_fan']:rows.extend(read(WORK/(name+'-media.json'))['payloads'])
    rows.extend(read(WORK/'trap-parent-media.json')['payloads'])
    unique={}
    for row in rows:
        assert sha(row['file'])==row['sha256']
        if row['member'] in unique:assert unique[row['member']]['sha256']==row['sha256']
        unique[row['member']]=row
    return list(unique.values())

def reference_cook(trap_label):
    """Validate exact final model/material/geometry inputs in native Reflect."""
    cooked=read(WORK/(trap_label+'-cook.json'));template=Path(cooked['project'])/'project';suffix='' if WORK==CACHEWORK else '-'+WORK.name;q=Path(CONFIG['external_root'])/('c/ref'+suffix)
    assert not q.exists();source=q/'source';source.mkdir(parents=True)
    original=template/f'source/art/stamps/garrison/{PROJECT.name}/stake_thicket.rdo';assert original.exists(),original
    native_mod=next(template.glob('*.aoe4mod'));shutil.copy2(native_mod,q/'reference.aoe4mod')
    media=media_payloads();models=[]
    for record in read(WORK/'houses-all-media.json')['models']:models.append(record['principal'])
    for name in ['stake_thicket','stake_fan']:models.append(read(WORK/(name+'-media.json'))['principal'])
    models.append(read(WORK/'trap-parent-media.json')['principal'])
    for row in media:
        if row['member'].endswith('.bin'):continue
        target=source/row['member'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(row['file'],target)
        if target.suffix=='.rrmaterial':shutil.copy2(target,target.with_suffix('.material'))
    burn=(template/'source/_default.burnproj').read_text(encoding='utf-8-sig')
    burn=re.sub(r'<BurnRule>.*?</BurnRule>',lambda m:m[0].replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>'),burn,flags=re.S)
    rules=[];references=[]
    for i,model in enumerate(models):
        doc=ET.parse(original);root=doc.getroot();ids={n.get('Id'):str(int.from_bytes(hashlib.sha256(('cc010:validator:'+str(i)+n.get('Id')).encode()).digest()[:8],'little')) for n in root.iter('DataObject')}
        for node in root.iter():
            for key in ['Id','OwnerId']:
                if node.get(key) in ids:node.set(key,ids[node.get(key)])
            if node.tag=='DataValue' and node.text in ids:node.text=ids[node.text]
            if node.tag=='DataProperty' and node.get('Name')=='m_objectID' and node.get('Value') in ids:node.set('Value',ids[node.get('Value')])
            if node.tag=='DataProperty' and node.get('Name')=='m_blueprint':node.set('Value',model.replace('/','\\'))
        member=f'art/stamps/cc010/reference_{i}';target=source/(member+'.rdo');target.parent.mkdir(parents=True,exist_ok=True);ET.indent(root);target.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
        rules.append('<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true"/><Includes>'+member.replace('/','\\')+'.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>')
        references.append({'member':member+'.bin','model':model})
    assert burn.count('</Rules>')==1;(source/'_default.burnproj').write_text(burn.replace('</Rules>',''.join(rules)+'</Rules>'),encoding='utf8')
    inputs={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()};write(WORK/'reference-inputs.json',{'inputs':inputs,'models':models,'references':references,'source':str(source)})
    runroot=Path(CONFIG['external_root'])/('c/ref-run'+suffix)
    command=run_logged('integration-reference',[CORE,'essence','build-mod','--editor',ART_EDITOR,'--mod',q/'reference.aoe4mod','--run-root',runroot,'--timeout','900'])
    state=read(runroot/'run.json');assert state['status']=='succeeded' and state['exit_code']==0
    archives=list((runroot/'output').rglob('*.sga'));assert len(archives)==1
    for row in references:
        target=WORK/'reference-readback'/row['member'];target.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(ARCH),'extract-member',str(archives[0]),row['member'],str(target)],capture_output=True,check=True)
        assert [v['model'] for v in active_visuals(NativeTree(target))]==[row['model']]
    assert inputs=={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    write(WORK/'reference-cook.json',{'status':'passed','archive':str(archives[0]),'sha256':sha(archives[0]),'command':command,'native_run':state,'models':models,'exact_inputs_sha256':inputs,'limitation':'Fresh Reflect references compile exact final models; final stamps retain native byte-preserving records, not full Reflect round-trip. Native culling/lifecycle appearance remain unverified.'})
    print('FINAL_MODELS_NATIVE_REFERENCE_QUALIFIED',len(models),flush=True)

def compile_candidate(attempt=''):
    from common import EDITOR
    from source_policy import verify
    sources=read(WORK/'source-bindings.json')['source_new_files'];proof=verify(sources)
    suffix='-'+attempt if attempt else ''
    source=WORK/('candidate_source'+suffix);assert not source.exists();source.mkdir()
    shutil.copytree(ROOT/'assets',source/'assets');shutil.copy2(ROOT/CONFIG['project_file'],source/CONFIG['project_file'])
    before={p.relative_to(source/'assets').as_posix():sha(p) for p in (source/'assets').rglob('*') if p.is_file()}
    write(WORK/('candidate-input-freeze'+suffix+'.json'),{'assets':before,'source_preservation':proof,'project_sha256':sha(source/CONFIG['project_file'])})
    target=WORK/('candidate-native'+suffix);command=run_logged('integration-candidate'+suffix+'-build',[EDITOR,'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report','--no_source_control','--log_path',WORK/('candidate-logs'+suffix),'--build_mod',source/CONFIG['project_file'],'--build_path',target,'--no_burn_window','--burn_cache_type','Local','--burn_max_threads','1','--burn_platform','PC','--burn_log_path',WORK/('candidate-burn'+suffix+'.log'),'--intermediate_path',WORK/('candidate-intermediate'+suffix)],cwd=EDITOR.parent,timeout=1800)
    output=Path(command['log']).read_text(encoding='utf8',errors='replace')
    errors=[line for line in output.splitlines() if 'EssenceEditor.exe Error:' in line or 'System does not support' in line]
    missing=[line for line in output.splitlines() if str(source).lower() in line.lower() and ("doesn't exist" in line or 'does not exist' in line)]
    assert not errors and not missing,('Native candidate source load/reference error',errors,missing)
    assert '244 instances validated' in output,'Native candidate did not load all237 original +7 visual identities'
    archives=list(target.rglob('*.sga'));assert len(archives)==1
    assert before=={p.relative_to(source/'assets').as_posix():sha(p) for p in (source/'assets').rglob('*') if p.is_file()}
    write(WORK/'candidate-build.json',{'status':'passed','archive':str(archives[0]),'sha256':sha(archives[0]),'source_frozen':True,'command':command,'source_preservation':proof})
    print('CANDIDATE_SOURCE_NATIVE_BUILD_PASSED',flush=True)

def finalize_candidate(attempt):
    """Re-audit a finished native attempt without reburning its exact source."""
    suffix='-'+attempt;source=WORK/('candidate_source'+suffix);target=WORK/('candidate-native'+suffix)
    command=read(OUT/(log_label('integration-candidate'+suffix+'-build')+'-command.json'));assert command['exit_code']==0
    output=Path(command['log']).read_text(encoding='utf8',errors='replace')
    errors=[line for line in output.splitlines() if 'EssenceEditor.exe Error:' in line or 'System does not support' in line]
    missing=[line for line in output.splitlines() if str(source).lower() in line.lower() and ("doesn't exist" in line or 'does not exist' in line)]
    assert not errors and not missing and '244 instances validated' in output
    source_hashes={p.relative_to(source/'assets').as_posix():sha(p) for p in (source/'assets').rglob('*') if p.is_file()}
    active_hashes={p.relative_to(ROOT/'assets').as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()};assert source_hashes==active_hashes
    assert sha(source/CONFIG['project_file'])==sha(ROOT/CONFIG['project_file'])
    from source_policy import verify
    proof=verify(read(WORK/'source-bindings.json')['source_new_files']);archives=list(target.rglob('*.sga'));assert len(archives)==1
    write(WORK/'candidate-build.json',{'status':'passed','archive':str(archives[0]),'sha256':sha(archives[0]),'source_frozen':True,'command':command,'source_preservation':proof,'native_loaded_and_validated_instances':244,'native_source_errors':errors,'native_source_missing_references':missing,'scope':'Exact completed native attempt re-audited; no repeated cook'})
    print('CANDIDATE_SOURCE_NATIVE_ATTEMPT_VERIFIED',attempt,flush=True)

def archive():
    """Compose exact visual allowlist onto frozen original archive."""
    reference=read(WORK/'reference-cook.json');assert reference['status']=='passed'
    for row in media_payloads():
        if not row['member'].endswith('.bin'):assert row['sha256']==reference['exact_inputs_sha256'][row['member']],('Stale native reference qualification',row['member'])
    baseline=read(OUT/'baseline-build-result.json');base=Path(baseline['archive']);assert sha(base)==baseline['sha256']
    compiled=read(WORK/'candidate-build.json');assert sha(compiled['archive'])==compiled['sha256']
    from source_policy import verify
    current=verify(read(WORK/'source-bindings.json')['source_new_files'])
    assert compiled['source_preservation']['source_assets_sha256']==current['source_assets_sha256'],'Candidate compiled from stale source'
    rows=media_payloads()+read(WORK/'private-bindings.json')['payloads']
    for name in CONSUMERS:
        member=f'attrib/ebps/vietnam/{name}.rgd';target=WORK/'candidate-actor-readback'/member;target.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(ARCH),'extract-member',compiled['archive'],member,str(target)],capture_output=True,check=True)
        rows.append({'member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
    payloads={r['member']:r for r in rows};assert len(payloads)==len(rows),'Duplicate payload entry'
    write(WORK/'changed-resource-allowlist.json',{'status':'frozen before composition','payloads':rows,'baseline':baseline,'candidate_source_build':compiled})
    current=base
    for alias,prefix in [('data','art/'),('attrib','attrib/')]:
        subset=[r for r in rows if r['member'].startswith(prefix)];mapping=WORK/(alias+'-members.txt')
        mapping.write_text('\n'.join(r['member']+'='+r['file'] for r in subset)+'\n',encoding='utf8')
        target=WORK/(alias+'-candidate.sga');assert not target.exists()
        run_logged('integration-set-'+alias,[ARCH,'set-members',current,mapping,target,'--alias',alias]);current=target
    final=WORK/'candidate/community_civilization_pack.sga';final.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(current,final)
    def inventory(path):
        p=subprocess.run([str(ARCH),'list',str(path),'--verify'],capture_output=True,text=True,encoding='utf8',check=True);data=json.loads(p.stdout);assert data['archive']['verification']['verified'];return data
    old=inventory(base);new=inventory(final);old_members={r['path'] for r in old['members']};new_members={r['path'] for r in new['members']}
    assert new_members==old_members|set(payloads)
    assert new['archive']['name'].replace('-','').lower()==CONFIG['project_guid'].replace('-','')
    checks=[]
    for label,path in [('baseline',base),('final',final)]:
        back=WORK/(label+'-archive-readback');assert not back.exists();run_logged('integration-readback-'+label,[ARCH,'unpack',path,'--output',back])
    changed=[]
    for member in sorted(old_members):
        if sha(WORK/'baseline-archive-readback'/member)!=sha(WORK/'final-archive-readback'/member):
            assert member in payloads,member;changed.append(member)
    for member,row in payloads.items():assert sha(WORK/'final-archive-readback'/member)==row['sha256']
    actors={f'attrib/ebps/vietnam/{name}.rgd' for name in CONSUMERS};assert set(changed)<=actors
    receipt={'status':'passed','verification_status':'passed','archive':str(final),'sha256':sha(final),'project_guid':CONFIG['project_guid'],'baseline_archive':str(base),'baseline_sha256':baseline['sha256'],'changed_existing_members':changed,'new_members':sorted(new_members-old_members),'source_new_files':read(WORK/'source-bindings.json')['source_new_files'],'unchanged_existing_members':len(old_members)-len(changed),'all_untouched_members_sha256_identical':True,'archive_crc_sha1_verified':True,'payloads':rows,'candidate_source_build':compiled,'native_reference_cook':read(WORK/'reference-cook.json'),'native_runtime':'unverified'}
    import integration_closure
    receipt['closure']=integration_closure.audit(final,WORK/'final-archive-readback',WORK)
    write(WORK/'candidate.json',receipt);print('FINAL_CANDIDATE_VERIFIED',len(changed),len(new_members-old_members),flush=True)

def verify_authoring():
    """Rebuild admitted frozen exports; authoring changes require a new handoff."""
    houses=read(OUT/'houses/house-handoff.json');project=Path(houses['project'])
    assert sha(project/'mod-project.json')==houses['project_sha256']
    def owned(value):
        p=Path(value);return p if p.is_absolute() else ROOT/p
    for row in houses['models']:
        for field in ['geometry','editable_blend','donor_blend']:
            assert sha(owned(row[field]))==row[field+'_sha256'],('Frozen house input changed',row['age'],field)
    ready=read(OUT/'houses/materials-ready.json')
    for model in ready['models']:
        for material in model['materials']:
            for texture in material['textures']:assert sha(owned(texture['image']))==texture['sha256']
    traps=read(OUT/'traps/final-handoff.json')
    for row in traps['assets']:
        for path,digest in row['source_files'].items():assert sha(ROOT/path)==digest
        for path,digest in row['export_files'].items():assert sha(ROOT/row['export_directory']/path)==digest
        assert [r['first_stage'] for r in read(ROOT/row['export_directory']/'building.json')['parts']]==[0,20]
    return {'status':'passed','houses_handoff_sha256':sha(OUT/'houses/house-handoff.json'),'traps_handoff_sha256':sha(OUT/'traps/final-handoff.json'),'house_project':str(project)}

def rebuild(label):
    """Fresh serial artifact pipeline; use a distinct label for every attempt.

    The root wrapper runs independent validation, packaging and cleanup. This
    stage regenerates final native media and compiled visual bindings only.
    """
    global WORK,PROJECT
    assert re.fullmatch(r'[a-z][a-z0-9-]{1,24}',label),label
    WORK=CACHEWORK/'runs'/label;assert not WORK.exists(),'Never overwrite prior evidence; choose a new label'
    PROJECT=WORK/'library/Mods/community_010_bindings';WORK.mkdir(parents=True)
    write(WORK/'authoring-verification.json',verify_authoring())
    schema=CACHEWORK/'schema/reflect.db'
    if not schema.exists():
        schema.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(ARCH),'extract-member','E:/Games/steamapps/common/Age of Empires IV/engine/archives/reflect.sga','reflect.db',str(schema)],capture_output=True,check=True)
    inventory();derive()
    house_label=label+'-h';trap_label=label+'-t'
    cook(read(OUT/'houses/materials-ready.json')['project'],house_label);houses_media(house_label,'all')
    prepare_traps('all');cook(PROJECT,trap_label)
    register_identities(trap_label);bind_sources();bind_payloads(trap_label)
    for name in ['stake_thicket','stake_fan']:trap_media(trap_label,name)
    parent_media();reference_cook(trap_label);compile_candidate();archive()
    result=read(WORK/'candidate.json');receipt={'status':'passed','candidate':str(WORK/'candidate.json'),'sha256':result['sha256']}
    write(OUT/('rebuild-'+label+'.json'),receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':
    from workspace_support import check_storage
    check_storage(ROOT,CONFIG)
    globals()[sys.argv[1]](*sys.argv[2:])
